import shutil
import sqlite3
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from rewind.config import settings
from rewind.importer.parser import parse_journal_json
from rewind.models import ImportStatus

_import_statuses: dict[str, ImportStatus] = {}


def get_import_status(import_id: str) -> ImportStatus | None:
    return _import_statuses.get(import_id)


class ImportPipeline:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.status = ImportStatus(
            id=str(uuid4()), status="uploading", progress=0, message="Starting..."
        )
        _import_statuses[self.status.id] = self.status

    def _update(self, status: str, progress: float, message: str, **kwargs) -> None:
        self.status.status = status
        self.status.progress = progress
        self.status.message = message
        for k, v in kwargs.items():
            setattr(self.status, k, v)

    def run(self, zip_path: Path, filename: str | None = None) -> ImportStatus:
        start = time.time()
        tmp_dir = None
        try:
            self._update("parsing", 10, "Extracting zip file...")
            tmp_dir = Path(tempfile.mkdtemp())

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_dir)

            journal_path = self._find_journal_json(tmp_dir)
            if not journal_path:
                self._update("error", 0, "No Journal.json found in zip")
                return self.status

            self._update("parsing", 25, "Parsing journal data...")
            entries = parse_journal_json(journal_path)

            self._update("importing", 40, f"Importing {len(entries)} entries...")
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("PRAGMA journal_mode=wal")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.row_factory = sqlite3.Row

            try:
                confirmed_tags = self._get_confirmed_tags(conn)
                self._clear_data(conn)
                self._restore_confirmed_tags(conn, confirmed_tags)

                self._update("importing", 50, "Inserting entries...")
                self._insert_entries(conn, entries)

                self._update("importing", 70, "Inserting tags...")
                tag_count = self._insert_tags_and_links(conn, entries)

                self._update("importing", 85, "Inserting photos...")
                photo_count = self._insert_photos(conn, entries)

                duration = time.time() - start
                conn.execute(
                    """INSERT INTO import_meta (imported_at, entry_count, tag_count, photo_count, filename, duration_seconds)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        datetime.now(timezone.utc).isoformat(),
                        len(entries),
                        tag_count,
                        photo_count,
                        filename,
                        round(duration, 2),
                    ),
                )
                conn.commit()

                self._update(
                    "done",
                    100,
                    f"Imported {len(entries)} entries, {tag_count} tags, {photo_count} photos in {duration:.1f}s",
                    entry_count=len(entries),
                    tag_count=tag_count,
                    photo_count=photo_count,
                )
            finally:
                conn.close()

        except Exception as e:
            self._update("error", 0, f"Import failed: {e}")
        finally:
            if tmp_dir and tmp_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)

        return self.status

    def _find_journal_json(self, root: Path) -> Path | None:
        for p in root.rglob("Journal.json"):
            return p
        return None

    def _get_confirmed_tags(self, conn: sqlite3.Connection) -> list[dict]:
        rows = conn.execute(
            "SELECT name, tag_type, ai_suggested_type FROM tags WHERE user_confirmed = 1"
        ).fetchall()
        return [
            {
                "name": r["name"],
                "tag_type": r["tag_type"],
                "ai_suggested_type": r["ai_suggested_type"],
            }
            for r in rows
        ]

    def _clear_data(self, conn: sqlite3.Connection) -> None:
        conn.execute("DELETE FROM entry_tags")
        conn.execute("DELETE FROM photos")
        conn.execute("DELETE FROM graph_edges")
        conn.execute("DELETE FROM graph_nodes")
        conn.execute("DELETE FROM entries")
        conn.execute("DELETE FROM tags")
        conn.execute("INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")
        conn.commit()

    def _restore_confirmed_tags(
        self, conn: sqlite3.Connection, tags: list[dict]
    ) -> None:
        if not tags:
            return
        conn.executemany(
            """INSERT INTO tags (name, tag_type, ai_suggested_type, user_confirmed)
               VALUES (:name, :tag_type, :ai_suggested_type, 1)""",
            tags,
        )
        conn.commit()

    def _insert_entries(
        self, conn: sqlite3.Connection, entries: list[dict]
    ) -> None:
        rows = [
            (
                e["uuid"],
                e["creation_date"],
                e["modified_date"],
                e["timezone"],
                e["text"],
                e["snippet"],
                e["starred"],
                e["latitude"],
                e["longitude"],
                e["place_name"],
                e["locality"],
                e["admin_area"],
                e["country"],
                e["weather_description"],
                e["weather_temp_c"],
                e["duration"],
                e["word_count"],
            )
            for e in entries
        ]
        conn.executemany(
            """INSERT OR REPLACE INTO entries
               (uuid, creation_date, modified_date, timezone, text, snippet, starred,
                latitude, longitude, place_name, locality, admin_area, country,
                weather_description, weather_temp_c, duration, word_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        conn.commit()

    def _insert_tags_and_links(
        self, conn: sqlite3.Connection, entries: list[dict]
    ) -> int:
        all_tag_names: set[str] = set()
        for e in entries:
            for t in e.get("tags", []):
                all_tag_names.add(t)

        for name in all_tag_names:
            conn.execute(
                "INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,)
            )
        conn.commit()

        tag_name_to_id: dict[str, int] = {}
        for row in conn.execute("SELECT id, name FROM tags").fetchall():
            tag_name_to_id[row["name"]] = row["id"]

        links = []
        for e in entries:
            for t in e.get("tags", []):
                tag_id = tag_name_to_id.get(t)
                if tag_id:
                    links.append((e["uuid"], tag_id))

        conn.executemany(
            "INSERT OR IGNORE INTO entry_tags (entry_uuid, tag_id) VALUES (?, ?)",
            links,
        )
        conn.commit()
        return len(all_tag_names)

    def _insert_photos(
        self, conn: sqlite3.Connection, entries: list[dict]
    ) -> int:
        photo_count = 0
        rows = []
        for e in entries:
            for p in e.get("photos", []):
                rows.append(
                    (
                        e["uuid"],
                        p["identifier"],
                        p.get("md5"),
                        p.get("file_type"),
                        p.get("width"),
                        p.get("height"),
                    )
                )
                photo_count += 1

        conn.executemany(
            """INSERT OR IGNORE INTO photos
               (entry_uuid, identifier, md5, file_type, width, height)
               VALUES (?, ?, ?, ?, ?, ?)""",
            rows,
        )
        conn.commit()
        return photo_count
