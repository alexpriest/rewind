import logging
import threading
import uuid as uuid_mod

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from rewind.config import settings
from rewind.models import ReportGenerateRequest, ReportStatusResponse
from rewind.services.report import _do_generate, _report_statuses, get_report_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate", response_model=ReportStatusResponse)
def start_report(request: ReportGenerateRequest) -> ReportStatusResponse:
    report_id = str(uuid_mod.uuid4())
    _report_statuses[report_id] = {
        "id": report_id,
        "status": "generating",
        "progress": 0.0,
        "message": "Starting report generation...",
        "person_name": None,
    }

    def _run():
        try:
            _do_generate(
                report_id, request.person_tag_id, request.date_from, request.date_to
            )
        except Exception as e:
            logger.exception("Report generation failed")
            _report_statuses[report_id].update({
                "status": "error",
                "progress": 0.0,
                "message": f"Error: {e}",
            })

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return ReportStatusResponse(**_report_statuses[report_id])


@router.get("/{report_id}/status", response_model=ReportStatusResponse)
def report_status(report_id: str) -> ReportStatusResponse:
    status = get_report_status(report_id)
    if not status:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportStatusResponse(**status)


@router.get("/{report_id}/html", response_class=HTMLResponse)
def report_html(report_id: str):
    report_path = settings.REPORTS_DIR / f"{report_id}.html"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return HTMLResponse(content=report_path.read_text(encoding="utf-8"))
