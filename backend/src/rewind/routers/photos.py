from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from rewind.config import settings
from rewind.db import get_db

router = APIRouter(prefix="/api/photos", tags=["photos"])


def _find_photo_file(directory, identifier: str):
    for ext in (".jpeg", ".jpg", ".png", ".gif", ".heic", ".webp"):
        path = directory / f"{identifier}{ext}"
        if path.exists():
            return path
    return None


@router.get("/{photo_id}/thumbnail")
def get_thumbnail(photo_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT identifier FROM photos WHERE id = ?", (photo_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Photo not found")

        path = _find_photo_file(settings.THUMBNAILS_DIR, row["identifier"])
        if not path:
            raise HTTPException(status_code=404, detail="Thumbnail not found")

        return FileResponse(path, media_type="image/jpeg")
    finally:
        conn.close()


@router.get("/{photo_id}/full")
def get_full(photo_id: int):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT identifier, file_type FROM photos WHERE id = ?", (photo_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Photo not found")

        path = _find_photo_file(settings.PHOTOS_DIR, row["identifier"])
        if not path:
            raise HTTPException(status_code=404, detail="Photo file not found")

        media_types = {
            ".jpeg": "image/jpeg", ".jpg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif",
            ".heic": "image/heic", ".webp": "image/webp",
        }
        media_type = media_types.get(path.suffix.lower(), "application/octet-stream")
        return FileResponse(path, media_type=media_type)
    finally:
        conn.close()
