import shutil
from pathlib import Path

from PIL import Image

THUMBNAIL_MAX_SIZE = 400


def process_photos(
    extract_dir: Path,
    entries: list[dict],
    photos_dir: Path,
    thumbnails_dir: Path,
) -> int:
    photo_dirs = list(extract_dir.rglob("photos"))
    if not photo_dirs:
        photo_dirs = [extract_dir]

    source_files: dict[str, Path] = {}
    for d in photo_dirs:
        if not d.is_dir():
            continue
        for f in d.iterdir():
            if f.is_file() and f.suffix.lower() in (".jpeg", ".jpg", ".png", ".gif", ".heic", ".webp"):
                source_files[f.stem] = f

    processed = 0
    for entry in entries:
        for photo in entry.get("photos", []):
            identifier = photo["identifier"]
            md5 = photo.get("md5")

            source = source_files.get(identifier) or source_files.get(md5)
            if not source:
                continue

            ext = source.suffix.lower()
            dest = photos_dir / f"{identifier}{ext}"
            thumb = thumbnails_dir / f"{identifier}{ext}"

            if not dest.exists():
                shutil.copy2(source, dest)

            if not thumb.exists():
                try:
                    _make_thumbnail(dest, thumb)
                    photo["has_thumbnail"] = True
                except Exception:
                    photo["has_thumbnail"] = False
            else:
                photo["has_thumbnail"] = True

            photo["stored_ext"] = ext
            processed += 1

    return processed


def _make_thumbnail(source: Path, dest: Path) -> None:
    with Image.open(source) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((THUMBNAIL_MAX_SIZE, THUMBNAIL_MAX_SIZE), Image.LANCZOS)
        img.save(dest, "JPEG", quality=85)
