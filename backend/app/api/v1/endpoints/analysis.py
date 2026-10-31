import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import (
    Video, AnalysisJob, ExtractedFrame, DetectedObject, DiseaseFinding, WeedFinding, YieldPrediction, Report
)
from backend.app.schemas.schemas import (
    JobCreateRequest, JobStatusResponse, LeafFindingResponse, WeedFindingResponse, AnalysisSummaryResponse, BoundingBox
)
from backend.app.tasks.pipeline_coordinator import run_video_pipeline

router = APIRouter()

@router.post("/jobs", response_model=JobStatusResponse)
def create_analysis_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(Video.id == request.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")

    config_dict = {
        "frame_interval": request.frame_interval,
        "enable_blur_filter": request.enable_blur_filter,
        "blur_threshold": request.blur_threshold,
        "enable_ssim_filter": request.enable_ssim_filter,
        "ssim_threshold": request.ssim_threshold,
        "agro_inputs": request.agro_inputs.dict() if request.agro_inputs else {},
    }

    job = AnalysisJob(
        video_id=video.id,
        status="QUEUED",
        progress_pct=0.0,
        current_stage="QUEUED",
        config_json=json.dumps(config_dict),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch asynchronously
    background_tasks.add_task(run_video_pipeline, job.id)

    return JobStatusResponse(
        job_id=job.id,
        video_id=job.video_id,
        status=job.status,
        progress_percentage=job.progress_pct,
        current_stage=job.current_stage,
        frames_processed=job.frames_processed,
        total_frames=job.total_frames,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
    )

@router.get("/jobs/latest", response_model=Optional[JobStatusResponse])
def get_latest_job(db: Session = Depends(get_db)):
    job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.status == "COMPLETED")
        .order_by(AnalysisJob.completed_at.desc())
        .first()
    )
    if not job:
        job = db.query(AnalysisJob).order_by(AnalysisJob.created_at.desc()).first()
    if not job:
        return None

    return JobStatusResponse(
        job_id=job.id,
        video_id=job.video_id,
        status=job.status,
        progress_percentage=job.progress_pct,
        current_stage=job.current_stage,
        frames_processed=job.frames_processed,
        total_frames=job.total_frames,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
    )

@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found.")

    return JobStatusResponse(
        job_id=job.id,
        video_id=job.video_id,
        status=job.status,
        progress_percentage=job.progress_pct,
        current_stage=job.current_stage,
        frames_processed=job.frames_processed,
        total_frames=job.total_frames,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
    )

@router.get("/{analysis_id}/summary", response_model=AnalysisSummaryResponse)
def get_analysis_summary(analysis_id: str, db: Session = Depends(get_db)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    leaves = db.query(DiseaseFinding).filter(DiseaseFinding.analysis_id == analysis_id).all()
    weeds = db.query(WeedFinding).filter(WeedFinding.analysis_id == analysis_id).all()
    yield_rec = db.query(YieldPrediction).filter(YieldPrediction.analysis_id == analysis_id).first()
    frames = db.query(ExtractedFrame).filter(ExtractedFrame.analysis_id == analysis_id).all()

    healthy_count = len([l for l in leaves if l.severity_category == "healthy"])
    diseased_count = len(leaves) - healthy_count
    mean_health = float(sum(l.health_score for l in leaves) / len(leaves)) if leaves else 100.0
    mean_wcr = float(sum(w.canopy_coverage_pct for w in weeds) / len(weeds)) if weeds else 0.0

    # Predominant disease
    disease_counts = {}
    for l in leaves:
        if l.severity_category != "healthy":
            disease_counts[l.disease_name] = disease_counts.get(l.disease_name, 0) + 1
    predominant = max(disease_counts, key=disease_counts.get) if disease_counts else "None"

    unique_tracks = len(set(w.track_id for w in weeds if w.track_id is not None))

    yield_dict = None
    if yield_rec:
        yield_dict = {
            "crop_type": yield_rec.crop_type,
            "predicted_yield_t_ha": yield_rec.predicted_yield_t_ha,
            "ci_lower": yield_rec.ci_lower,
            "ci_upper": yield_rec.ci_upper,
            "status": yield_rec.status,
        }

    return AnalysisSummaryResponse(
        analysis_id=analysis_id,
        total_frames_analyzed=len(frames),
        unique_weeds_detected=unique_tracks,
        mean_weed_canopy_pct=round(mean_wcr, 2),
        total_leaves_analyzed=len(leaves),
        healthy_leaves_count=healthy_count,
        diseased_leaves_count=diseased_count,
        mean_health_score=round(mean_health, 1),
        predominant_disease=predominant,
        yield_prediction=yield_dict,
    )

@router.get("/{analysis_id}/findings/leaves", response_model=List[LeafFindingResponse])
def get_leaf_findings(
    analysis_id: str,
    severity: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(DiseaseFinding).filter(DiseaseFinding.analysis_id == analysis_id)
    if severity:
        query = query.filter(DiseaseFinding.severity_category == severity.lower())
    
    findings = query.limit(limit).all()
    results = []

    for f in findings:
        obj = f.detected_object
        frame = obj.frame if obj else None
        
        # Build URL for images
        crop_url = None
        mask_url = None
        if obj and obj.crop_image_path:
            crop_url = f"/static/evidence/{Path(obj.crop_image_path).name}"
        if f.mask_overlay_path:
            mask_url = f"/static/evidence/{Path(f.mask_overlay_path).name}"

        results.append(LeafFindingResponse(
            id=f.id,
            object_id=f.object_id,
            crop_name=f.crop_name,
            disease_name=f.disease_name,
            classification_confidence=f.classification_confidence,
            lesion_area_pct=f.lesion_area_pct,
            severity_category=f.severity_category,
            health_score=f.health_score,
            bbox=BoundingBox(
                x1=obj.bbox_x1 if obj else 0.0,
                y1=obj.bbox_y1 if obj else 0.0,
                x2=obj.bbox_x2 if obj else 0.0,
                y2=obj.bbox_y2 if obj else 0.0,
            ),
            crop_image_url=crop_url,
            mask_overlay_url=mask_url,
            timestamp_sec=frame.timestamp_sec if frame else 0.0,
        ))

    return results

@router.get("/{analysis_id}/findings/weeds", response_model=List[WeedFindingResponse])
def get_weed_findings(
    analysis_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    findings = db.query(WeedFinding).filter(WeedFinding.analysis_id == analysis_id).limit(limit).all()
    results = []

    for f in findings:
        obj = f.detected_object
        results.append(WeedFindingResponse(
            id=f.id,
            track_id=f.track_id,
            weed_species=f.weed_species,
            confidence=f.confidence,
            canopy_coverage_pct=f.canopy_coverage_pct,
            bbox=BoundingBox(
                x1=obj.bbox_x1 if obj else 0.0,
                y1=obj.bbox_y1 if obj else 0.0,
                x2=obj.bbox_x2 if obj else 0.0,
                y2=obj.bbox_y2 if obj else 0.0,
            ),
            timestamp_sec=f.timestamp_sec,
        ))

    return results

