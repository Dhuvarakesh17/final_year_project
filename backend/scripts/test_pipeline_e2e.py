"""
End-to-End Pipeline Verification Script
Runs full ingestion, multi-model vision inference, tracking, lesion segmentation,
calibrated yield prediction, and 12-section PDF report synthesis on sample field footage.
"""
import os
import json
from pathlib import Path
from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.models.entities import Video, AnalysisJob, Report, DiseaseFinding, WeedFinding, YieldPrediction
from backend.app.tasks.pipeline_coordinator import run_video_pipeline

def run_e2e_test():
    db = SessionLocal()
    sample_video_path = settings.RAW_VIDEOS_DIR / "sample_field_inspection.mp4"
    
    if not sample_video_path.exists():
        print(f"Sample video not found at {sample_video_path}. Please generate it first.")
        return

    print("--- 1. Registering Sample Field Video in Database ---")
    video = Video(
        original_filename="sample_field_inspection.mp4",
        file_path=str(sample_video_path),
        duration_sec=4.0,
        fps=24.0,
        width=640,
        height=480,
        file_size_mb=round(os.path.getsize(sample_video_path) / (1024 * 1024), 2),
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    print(f"Video registered with ID: {video.id}")

    print("\n--- 2. Enqueuing Analysis Pipeline Job ---")
    agro_inputs = {
        "crop_type": "Tomato",
        "growth_stage": "Vegetative",
        "field_area_ha": 2.5,
        "temp_c": 26.5,
        "rainfall_mm": 110.0,
        "soil_n": 45.0,
        "soil_p": 25.0,
        "soil_k": 30.0,
        "soil_ph": 6.5
    }
    
    job = AnalysisJob(
        video_id=video.id,
        status="QUEUED",
        current_stage="QUEUED",
        config_json=json.dumps({
            "frame_interval": 12, # Sample every 12th frame (2 fps)
            "blur_threshold": 80.0,
            "ssim_threshold": 0.95,
            "agro_inputs": agro_inputs
        })
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    print(f"Job created with ID: {job.id}")

    print("\n--- 3. Executing Pipeline Coordinator ---")
    run_video_pipeline(job.id)

    # Reload from DB
    db.refresh(job)
    print(f"\n--- 4. Verification Results (Job Status: {job.status}) ---")
    print(f"Progress:         {job.progress_pct}%")
    print(f"Stage:            {job.current_stage}")
    print(f"Frames Processed: {job.frames_processed} / {job.total_frames}")

    leaves = db.query(DiseaseFinding).filter(DiseaseFinding.analysis_id == job.id).all()
    print(f"Foliar Samples Analyzed: {len(leaves)}")
    for l in leaves[:3]:
        print(f"  - [{l.severity_category.upper()}] {l.crop_name} {l.disease_name} (Conf: {l.classification_confidence*100:.1f}%, Lesion: {l.lesion_area_pct}%, Health: {l.health_score}/100)")

    weeds = db.query(WeedFinding).filter(WeedFinding.analysis_id == job.id).all()
    print(f"Weed Detections:         {len(weeds)}")
    for w in weeds[:3]:
        print(f"  - Track #{w.track_id}: {w.weed_species} (Conf: {w.confidence*100:.1f}%, Canopy: {w.canopy_coverage_pct}%)")

    yield_rec = db.query(YieldPrediction).filter(YieldPrediction.analysis_id == job.id).first()
    if yield_rec:
        print(f"Yield Prediction:        {yield_rec.predicted_yield_t_ha} t/ha (90% CI: [{yield_rec.ci_lower} - {yield_rec.ci_upper}] t/ha)")

    report = db.query(Report).filter(Report.analysis_id == job.id).first()
    if report and os.path.exists(report.pdf_path):
        print(f"Audit PDF Generated:     {report.pdf_path} ({os.path.getsize(report.pdf_path)} bytes)")
    else:
        print("Notice: PDF report file was not found.")

    db.close()

if __name__ == "__main__":
    run_e2e_test()

