import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import Report, AnalysisJob

router = APIRouter()

@router.get("/{analysis_id}/pdf")
def get_pdf_report(analysis_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.analysis_id == analysis_id).order_by(Report.generated_at.desc()).first()
    if not report or not os.path.exists(report.pdf_path):
        raise HTTPException(status_code=404, detail="PDF report not found or processing incomplete.")

    return FileResponse(
        path=report.pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(report.pdf_path)
    )

