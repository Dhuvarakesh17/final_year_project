"""
End-to-End Pipeline Coordinator
Executes asynchronous video processing pipeline:
  Video Ingestion -> Frame Extraction (Blur/SSIM filter) ->
  Weed Detection & Tracking (YOLOv8 + ByteTrack) ->
  Leaf Pathology Classification (EfficientNet-B0) ->
  Lesion Spot Localization & Severity Calculation ->
  Crop Health Index Synthesis ->
  Calibrated Yield Prediction ->
  ReportLab 12-Section PDF Report Generation with Bounding Box Annotations & Leaf Crops.
"""
import os
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import cv2
import numpy as np
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.models.entities import (
    Video, AnalysisJob, ExtractedFrame, DetectedObject, DiseaseFinding, WeedFinding, YieldPrediction, Report
)
from backend.app.services.video_processing.frame_extractor import VideoFrameExtractor
from backend.app.services.ml_inference.weed_detector import WeedDetectorTracker
from backend.app.services.ml_inference.disease_classifier import LeafDiseaseClassifier
from backend.app.services.ml_inference.lesion_segmenter import FoliarLesionSegmenter
from backend.app.services.ml_inference.gradcam import GradCAMExplainer
from backend.app.services.health_assessment.health_engine import CropHealthEngine
from backend.app.services.health_assessment.treatment_advisory import TreatmentAdvisoryEngine
from backend.app.services.yield_prediction.yield_engine import CropYieldEngine
from backend.app.services.pdf_report.report_generator import AgroReportGenerator

def draw_annotated_frame(bgr_frame: np.ndarray, detected_objects: list, frame_idx: int, timestamp_sec: float) -> np.ndarray:
    """Draws bounding boxes, tracking labels, and metadata overlay onto keyframe."""
    annotated = bgr_frame.copy()
    h, w = annotated.shape[:2]

    # Timestamp and frame banner
    cv2.rectangle(annotated, (0, 0), (w, 36), (15, 23, 42), -1)
    banner_text = f"Keyframe #{frame_idx} | Time: {timestamp_sec:.2f}s | AgroVision AI Diagnostic Engine"
    cv2.putText(annotated, banner_text, (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    for det in detected_objects:
        bbox = det["bbox"]
        x1, y1 = int(bbox["x1"]), int(bbox["y1"])
        x2, y2 = int(bbox["x2"]), int(bbox["y2"])
        obj_type = det["object_type"]
        conf = det["confidence"]

        if obj_type == "weed":
            track_id = det.get("track_id", "N/A")
            box_color = (0, 140, 255)  # Orange/Yellow
            label = f"Weed #{track_id} ({conf*100:.1f}%)"
        else:
            box_color = (34, 197, 94)   # Emerald Green
            label = f"Crop Leaf ({conf*100:.1f}%)"

        # Draw bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, 2)

        # Label background pill
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(annotated, (x1, max(0, y1 - 22)), (x1 + lw + 8, max(22, y1)), box_color, -1)
        cv2.putText(annotated, label, (x1 + 4, max(16, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    return annotated

def run_video_pipeline(job_id: str):
    """
    Background worker task function.
    """
    db: Session = SessionLocal()
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        print(f"Error: Job {job_id} not found.")
        db.close()
        return

    try:
        job.status = "PROCESSING"
        job.started_at = datetime.utcnow()
        job.current_stage = "INITIALIZING_MODELS"
        job.progress_pct = 5.0
        db.commit()

        video = db.query(Video).filter(Video.id == job.video_id).first()
        config = json.loads(job.config_json) if job.config_json else {}

        frame_interval = config.get("frame_interval", settings.DEFAULT_FRAME_INTERVAL)
        blur_thresh = config.get("blur_threshold", settings.BLUR_THRESHOLD)
        ssim_thresh = config.get("ssim_threshold", settings.SSIM_THRESHOLD)
        agro_inputs = config.get("agro_inputs", {})

        # Initialize Services
        frame_extractor = VideoFrameExtractor(blur_threshold=blur_thresh, ssim_threshold=ssim_thresh)
        weed_tracker = WeedDetectorTracker()
        disease_classifier = LeafDiseaseClassifier()
        lesion_segmenter = FoliarLesionSegmenter()
        gradcam_explainer = GradCAMExplainer(disease_classifier.model, device=disease_classifier.device)

        # Step 1: Extract and Filter Frames
        job.current_stage = "FRAME_EXTRACTION_AND_FILTERING"
        job.progress_pct = 15.0
        db.commit()

        frames_metadata = list(frame_extractor.extract_keyframes(
            video_path=video.file_path,
            output_dir=str(settings.EXTRACTED_FRAMES_DIR),
            video_id=video.id,
            frame_step=frame_interval
        ))

        total_keyframes = len(frames_metadata)
        job.total_frames = total_keyframes
        db.commit()

        # Step 2: Multi-Model Inference Pipeline across Keyframes
        job.current_stage = "AI_INFERENCE_AND_TRACKING"
        weed_tracker.reset_tracking()

        all_leaf_findings = []
        all_weed_findings = []
        weed_canopy_measurements = []
        leaf_health_scores = []
        annotated_frames_for_report = []

        for idx, f_meta in enumerate(frames_metadata):
            frame_record = ExtractedFrame(
                video_id=video.id,
                analysis_id=job.id,
                frame_number=f_meta["frame_number"],
                timestamp_sec=f_meta["timestamp_sec"],
                file_path=f_meta["file_path"],
                blur_score=f_meta["blur_score"],
                ssim_score=f_meta["ssim_score"],
                is_valid=True,
            )
            db.add(frame_record)
            db.flush()

            bgr_frame = cv2.imread(f_meta["file_path"])
            if bgr_frame is None:
                continue

            # A. Weed Detection & Spatial Tracking
            weed_res = weed_tracker.process_frame(
                bgr_frame,
                frame_idx=f_meta["frame_number"],
                timestamp_sec=f_meta["timestamp_sec"]
            )
            weed_canopy_measurements.append(weed_res["frame_weed_canopy_pct"])

            frame_objects_to_draw = []

            for det in weed_res["detected_objects"]:
                obj_record = DetectedObject(
                    frame_id=frame_record.id,
                    analysis_id=job.id,
                    track_id=det["track_id"],
                    object_type=det["object_type"],
                    confidence=det["confidence"],
                    bbox_x1=det["bbox"]["x1"],
                    bbox_y1=det["bbox"]["y1"],
                    bbox_x2=det["bbox"]["x2"],
                    bbox_y2=det["bbox"]["y2"],
                )
                db.add(obj_record)
                db.flush()

                frame_objects_to_draw.append(det)

                if det["object_type"] == "weed":
                    weed_finding = WeedFinding(
                        object_id=obj_record.id,
                        analysis_id=job.id,
                        track_id=det["track_id"],
                        weed_species=det["species_name"],
                        confidence=det["confidence"],
                        canopy_coverage_pct=weed_res["frame_weed_canopy_pct"],
                        timestamp_sec=f_meta["timestamp_sec"],
                    )
                    db.add(weed_finding)
                    all_weed_findings.append({
                        "track_id": det["track_id"],
                        "weed_species": det["species_name"],
                        "confidence": det["confidence"],
                        "timestamp_sec": f_meta["timestamp_sec"],
                        "canopy_coverage_pct": weed_res["frame_weed_canopy_pct"],
                        "bbox": det["bbox"]
                    })

            # B. Foliar Pathology & Lesion Segmentation
            h, w = bgr_frame.shape[:2]
            crop_sample_id = f"{job.id[:8]}_f{f_meta['frame_number']}"
            
            # Analyze central foliage crop
            margin_y, margin_x = int(h * 0.15), int(w * 0.15)
            leaf_crop = bgr_frame[margin_y:h - margin_y, margin_x:w - margin_x]
            
            leaf_bbox_dict = {
                "x1": float(margin_x),
                "y1": float(margin_y),
                "x2": float(w - margin_x),
                "y2": float(h - margin_y)
            }

            if leaf_crop.shape[0] > 50 and leaf_crop.shape[1] > 50:
                # 1. Lesion Segmentation
                seg_res = lesion_segmenter.segment_lesions(leaf_crop, sample_id=crop_sample_id)
                
                # 2. Disease Classification
                rgb_crop = cv2.cvtColor(leaf_crop, cv2.COLOR_BGR2RGB)
                from PIL import Image
                pil_crop = Image.fromarray(rgb_crop)
                cls_res = disease_classifier.predict_leaf(pil_crop)

                # 2.5 Explainable AI: Grad-CAM Saliency Map
                try:
                    tensor = disease_classifier.transform(pil_crop).unsqueeze(0).to(disease_classifier.device)
                    cam_map = gradcam_explainer.generate_heatmap(tensor, class_idx=cls_res["predicted_class_id"])
                    gradcam_bgr = gradcam_explainer.overlay_heatmap(leaf_crop, cam_map)
                    gradcam_filename = f"leaf_{crop_sample_id}_gradcam.jpg"
                    gradcam_path = settings.EVIDENCE_DIR / gradcam_filename
                    cv2.imwrite(str(gradcam_path), gradcam_bgr)
                    # Also save legacy un-prefixed alias
                    cv2.imwrite(str(settings.EVIDENCE_DIR / f"{crop_sample_id}_gradcam.jpg"), gradcam_bgr)
                except Exception as ex:
                    print(f"Notice: GradCAM skipped on frame {f_meta['frame_number']}: {ex}")

                # 3. Health Scoring Engine
                health_res = CropHealthEngine.evaluate_leaf_health(
                    disease_name=cls_res["full_class"],
                    classification_confidence=cls_res["confidence"],
                    lesion_area_pct=seg_res["lesion_area_pct"]
                )
                leaf_health_scores.append(health_res["health_score"])

                # Add to objects to draw on frame
                frame_objects_to_draw.append({
                    "object_type": "crop_leaf",
                    "confidence": cls_res["confidence"],
                    "bbox": leaf_bbox_dict
                })

                # Store Detected Object & Disease Finding
                leaf_obj = DetectedObject(
                    frame_id=frame_record.id,
                    analysis_id=job.id,
                    object_type="crop_leaf",
                    confidence=cls_res["confidence"],
                    bbox_x1=leaf_bbox_dict["x1"],
                    bbox_y1=leaf_bbox_dict["y1"],
                    bbox_x2=leaf_bbox_dict["x2"],
                    bbox_y2=leaf_bbox_dict["y2"],
                    crop_image_path=seg_res["crop_image_path"],
                )
                db.add(leaf_obj)
                db.flush()

                dis_finding = DiseaseFinding(
                    object_id=leaf_obj.id,
                    analysis_id=job.id,
                    crop_name=cls_res["crop_name"],
                    disease_name=cls_res["disease_name"],
                    classification_confidence=cls_res["confidence"],
                    lesion_area_pct=seg_res["lesion_area_pct"],
                    severity_category=health_res["severity_category"],
                    health_score=health_res["health_score"],
                    mask_overlay_path=seg_res["mask_overlay_path"],
                    top5_probabilities_json=json.dumps(cls_res["top_5"]),
                )
                db.add(dis_finding)
                db.flush()

                finding_summary = {
                    "id": dis_finding.id,
                    "crop_name": cls_res["crop_name"],
                    "disease_name": cls_res["disease_name"],
                    "classification_confidence": cls_res["confidence"],
                    "lesion_area_pct": seg_res["lesion_area_pct"],
                    "severity_category": health_res["severity_category"],
                    "health_score": health_res["health_score"],
                    "timestamp_sec": f_meta["timestamp_sec"],
                    "crop_image_path": seg_res["crop_image_path"],
                    "mask_overlay_path": seg_res["mask_overlay_path"],
                    "bbox": leaf_bbox_dict
                }
                all_leaf_findings.append(finding_summary)

            # C. Generate and save annotated keyframe with bounding boxes
            annotated_frame = draw_annotated_frame(
                bgr_frame, frame_objects_to_draw, f_meta["frame_number"], f_meta["timestamp_sec"]
            )
            ann_filename = f"annotated_frame_{f_meta['frame_number']:06d}.jpg"
            ann_path = settings.EVIDENCE_DIR / ann_filename
            cv2.imwrite(str(ann_path), annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 92])

            if len(annotated_frames_for_report) < 2:
                annotated_frames_for_report.append({
                    "frame_number": f_meta["frame_number"],
                    "timestamp_sec": f_meta["timestamp_sec"],
                    "file_path": str(ann_path),
                    "blur_score": f_meta["blur_score"]
                })

            # Update Progress
            job.frames_processed = idx + 1
            job.progress_pct = 20.0 + round(((idx + 1) / max(1, total_keyframes)) * 60.0, 1)
            db.commit()

        # Step 3: Agronomic Aggregation & Calibrated Yield Prediction
        job.current_stage = "YIELD_PREDICTION"
        job.progress_pct = 85.0
        db.commit()

        mean_health = float(np.mean(leaf_health_scores)) if leaf_health_scores else 100.0
        mean_wcr = float(np.mean(weed_canopy_measurements)) if weed_canopy_measurements else 0.0
        unique_weeds = len(weed_tracker.confirmed_track_ids)

        yield_res = CropYieldEngine.predict_yield(
            inputs=agro_inputs,
            weed_canopy_ratio_pct=mean_wcr,
            mean_health_score=mean_health,
        )

        yield_record = YieldPrediction(
            analysis_id=job.id,
            crop_type=agro_inputs.get("crop_type", "Tomato"),
            growth_stage=agro_inputs.get("growth_stage", "Vegetative"),
            field_area_ha=agro_inputs.get("field_area_ha"),
            plant_density_m2=agro_inputs.get("plant_density_m2"),
            weed_pressure_idx=mean_wcr,
            mean_health_score=mean_health,
            predicted_yield_t_ha=yield_res.get("predicted_yield_t_ha"),
            ci_lower=yield_res.get("ci_lower"),
            ci_upper=yield_res.get("ci_upper"),
            feature_importances_json=json.dumps(yield_res.get("feature_contributions", [])),
            agronomic_inputs_json=json.dumps(agro_inputs),
            status=yield_res.get("status", "SUCCESS"),
        )
        db.add(yield_record)
        db.commit()

        # Step 4: PDF Report Generation with Bounding Boxes & Evidence Dossier
        job.current_stage = "REPORT_GENERATION"
        job.progress_pct = 95.0
        db.commit()

        pdf_filename = f"report_audit_{job.id[:8]}.pdf"
        pdf_path = settings.REPORTS_DIR / pdf_filename

        summary_dict = {
            "crop_type": agro_inputs.get("crop_type", "Tomato"),
            "total_frames_analyzed": total_keyframes,
            "unique_weeds_detected": unique_weeds,
            "mean_weed_canopy_pct": mean_wcr,
            "total_leaves_analyzed": len(all_leaf_findings),
            "healthy_leaves_count": len([l for l in all_leaf_findings if l["severity_category"] == "healthy"]),
            "diseased_leaves_count": len([l for l in all_leaf_findings if l["severity_category"] != "healthy"]),
            "mean_health_score": mean_health,
            "predominant_disease": all_leaf_findings[0]["disease_name"] if all_leaf_findings else "None Detected",
            "treatment_advisory": TreatmentAdvisoryEngine.get_prescription(
                disease_name=all_leaf_findings[0]["disease_name"] if all_leaf_findings else "Tomato_healthy",
                lesion_pct=float(np.mean([l.get("lesion_area_pct", 0) for l in all_leaf_findings])) if all_leaf_findings else 0.0,
                health_score=mean_health
            ) if all_leaf_findings else None
        }

        generator = AgroReportGenerator(str(pdf_path))
        generator.build_report(
            video_metadata={
                "filename": video.original_filename,
                "duration_sec": video.duration_sec,
                "fps": video.fps,
                "width": video.width,
                "height": video.height,
                "total_frames": video.duration_sec * video.fps,
                "frame_step": frame_interval,
            },
            summary_data=summary_dict,
            leaf_findings=all_leaf_findings,
            weed_findings=all_weed_findings,
            yield_data={**yield_res, **agro_inputs},
            annotated_frames=annotated_frames_for_report,
        )

        pdf_size = os.path.getsize(pdf_path) if pdf_path.exists() else 0
        report_record = Report(
            analysis_id=job.id,
            pdf_path=str(pdf_path),
            file_size_bytes=pdf_size,
            executive_summary_json=json.dumps(summary_dict),
        )
        db.add(report_record)

        # Complete Pipeline
        job.status = "COMPLETED"
        job.current_stage = "COMPLETED"
        job.progress_pct = 100.0
        job.completed_at = datetime.utcnow()
        db.commit()
        print(f"Pipeline job {job.id} completed successfully.")

    except Exception as e:
        db.rollback()
        job.status = "FAILED"
        job.current_stage = "ERROR"
        job.error_message = f"{str(e)}\n{traceback.format_exc()}"
        job.completed_at = datetime.utcnow()
        db.commit()
        print(f"Pipeline job {job.id} failed: {e}")
    finally:
        db.close()
