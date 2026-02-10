from collections import defaultdict

from fastapi import APIRouter, HTTPException, Query

from rewind.db import get_db
from rewind.models import EntryListResponse, EntryResponse, PhotoResponse

router = APIRouter(prefix="/api/entries", tags=["entries"])


@router.get("", response_model=EntryListResponse)
def list_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    q: str | None = None,
    tag: str | None = None,
    place: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> EntryListResponse:
    conn = get_db()
    try:
        where_clauses: list[str] = []
        params: list[str | int | float] = []

        if q:
            where_clauses.append(
                """(e.uuid IN (SELECT uuid FROM entries_fts WHERE entries_fts MATCH ?)
                   OR e.uuid IN (SELECT et.entry_uuid FROM entry_tags et
                                 JOIN tags t ON t.id = et.tag_id
                                 WHERE t.name LIKE ?))"""
            )
            params.extend([q, f"%{q}%"])
        if tag:
            where_clauses.append(
                "e.uuid IN (SELECT entry_uuid FROM entry_tags JOIN tags ON tags.id = entry_tags.tag_id WHERE tags.name = ?)"
            )
            params.append(tag)
        if place:
            where_clauses.append(
                "(e.place_name LIKE ? OR e.locality LIKE ? OR e.country LIKE ?)"
            )
            params.extend([f"%{place}%", f"%{place}%", f"%{place}%"])
        if date_from:
            where_clauses.append("e.creation_date >= ?")
            params.append(date_from)
        if date_to:
            where_clauses.append("e.creation_date <= ?")
            params.append(date_to)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        count_row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM entries e WHERE {where_sql}", params
        ).fetchone()
        total = count_row["cnt"]

        offset = (page - 1) * page_size
        entry_rows = conn.execute(
            f"""SELECT e.* FROM entries e
                WHERE {where_sql}
                ORDER BY e.creation_date DESC
                LIMIT ? OFFSET ?""",
            [*params, page_size, offset],
        ).fetchall()

        if not entry_rows:
            return EntryListResponse(
                entries=[], total=total, page=page, page_size=page_size
            )

        uuids = [r["uuid"] for r in entry_rows]
        placeholders = ",".join("?" * len(uuids))

        tag_rows = conn.execute(
            f"""SELECT et.entry_uuid, t.name
                FROM entry_tags et JOIN tags t ON t.id = et.tag_id
                WHERE et.entry_uuid IN ({placeholders})""",
            uuids,
        ).fetchall()
        tags_by_uuid: dict[str, list[str]] = defaultdict(list)
        for r in tag_rows:
            tags_by_uuid[r["entry_uuid"]].append(r["name"])

        photo_rows = conn.execute(
            f"""SELECT * FROM photos WHERE entry_uuid IN ({placeholders})""",
            uuids,
        ).fetchall()
        photos_by_uuid: dict[str, list[PhotoResponse]] = defaultdict(list)
        for r in photo_rows:
            photos_by_uuid[r["entry_uuid"]].append(
                PhotoResponse(
                    id=r["id"],
                    identifier=r["identifier"],
                    file_type=r["file_type"],
                    has_thumbnail=bool(r["has_thumbnail"]),
                )
            )

        entries = [
            EntryResponse(
                uuid=r["uuid"],
                creation_date=r["creation_date"],
                text=r["text"],
                snippet=r["snippet"],
                starred=bool(r["starred"]),
                latitude=r["latitude"],
                longitude=r["longitude"],
                place_name=r["place_name"],
                locality=r["locality"],
                admin_area=r["admin_area"],
                country=r["country"],
                weather_description=r["weather_description"],
                weather_temp_c=r["weather_temp_c"],
                word_count=r["word_count"],
                tags=tags_by_uuid.get(r["uuid"], []),
                photos=photos_by_uuid.get(r["uuid"], []),
            )
            for r in entry_rows
        ]

        return EntryListResponse(
            entries=entries, total=total, page=page, page_size=page_size
        )
    finally:
        conn.close()


@router.get("/{uuid}", response_model=EntryResponse)
def get_entry(uuid: str) -> EntryResponse:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM entries WHERE uuid = ?", (uuid,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Entry not found")

        tag_rows = conn.execute(
            """SELECT t.name FROM entry_tags et
               JOIN tags t ON t.id = et.tag_id
               WHERE et.entry_uuid = ?""",
            (uuid,),
        ).fetchall()
        tags = [r["name"] for r in tag_rows]

        photo_rows = conn.execute(
            "SELECT * FROM photos WHERE entry_uuid = ?", (uuid,)
        ).fetchall()
        photos = [
            PhotoResponse(
                id=r["id"],
                identifier=r["identifier"],
                file_type=r["file_type"],
                has_thumbnail=bool(r["has_thumbnail"]),
            )
            for r in photo_rows
        ]

        return EntryResponse(
            uuid=row["uuid"],
            creation_date=row["creation_date"],
            text=row["text"],
            snippet=row["snippet"],
            starred=bool(row["starred"]),
            latitude=row["latitude"],
            longitude=row["longitude"],
            place_name=row["place_name"],
            locality=row["locality"],
            admin_area=row["admin_area"],
            country=row["country"],
            weather_description=row["weather_description"],
            weather_temp_c=row["weather_temp_c"],
            word_count=row["word_count"],
            tags=tags,
            photos=photos,
        )
    finally:
        conn.close()
