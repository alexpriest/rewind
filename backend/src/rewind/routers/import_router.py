import asyncio
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from rewind.config import settings
from rewind.importer.pipeline import ImportPipeline, get_import_status
from rewind.models import ImportStatus

router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/upload", response_model=ImportStatus)
async def upload_journal(file: UploadFile) -> ImportStatus:
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        content = await file.read()
        tmp.write(content)
        tmp.close()
    except Exception:
        tmp.close()
        Path(tmp.name).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    pipeline = ImportPipeline(db_path=settings.DB_PATH)
    import_id = pipeline.status.id

    async def _run():
        try:
            await asyncio.to_thread(
                pipeline.run, Path(tmp.name), file.filename
            )
        finally:
            Path(tmp.name).unlink(missing_ok=True)

    asyncio.create_task(_run())

    return pipeline.status


@router.get("/status/{import_id}", response_model=ImportStatus)
async def import_status(import_id: str) -> ImportStatus:
    status = get_import_status(import_id)
    if not status:
        raise HTTPException(status_code=404, detail="Import not found")
    return status
