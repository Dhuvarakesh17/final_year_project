"""
Real-time Single-Leaf Diagnostic & Explainable AI Endpoint
Accepts single leaf image upload, classifies pathology with calibrated confidence,
computes pixel-exact lesion segmentation, generates Grad-CAM attention heatmap,
and outputs actionable agronomic treatment prescriptions.
"""
import os
import uuid
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.core.config import settings
from backend.app.services.ml_inference.disease_classifier import LeafDiseaseClassifier
from backend.app.services.ml_inference.lesion_segmenter import FoliarLesionSegmenter
from backend.app.services.ml_inference.gradcam import GradCAMExplainer
from backend.app.services.health_assessment.health_engine import CropHealthEngine
from backend.app.services.health_assessment.treatment_advisory import TreatmentAdvisoryEngine

router = APIRouter()

# Singletons for fast sub-50ms inference
_classifier = None
_segmenter = None
_gradcam = None

def get_ml_services():
    global _classifier, _segmenter, _gradcam
    if _classifier is None:
        _classifier = LeafDiseaseClassifier()
    if _segmenter is None:
        _segmenter = FoliarLesionSegmenter()
    if _gradcam is None:
        _gradcam = GradCAMExplainer(_classifier.model, device=_classifier.device)
    return _classifier, _segmenter, _gradcam

@router.post("/single-leaf")
async def diagnose_single_leaf(file: UploadFile = File(...)):
    """
    Sub-50ms single-leaf diagnostic endpoint returning:
    - Disease classification with calibrated probability
    - Lesion segmentation ratio & mask
    - Grad-CAM saliency attention heatmap
    - Health score (0-100) & triage status
    - Actionable agronomic chemical/biological treatment prescription
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG leaf image.")

    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image exceeds 15 MB limit.")

    # 1. Decode Image
    np_arr = np.frombuffer(content, np.uint8)
    bgr_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if bgr_img is None:
        raise HTTPException(status_code=400, detail="Corrupted image file.")

    classifier, segmenter, gradcam = get_ml_services()

    sample_id = f"single_{uuid.uuid4().hex[:8]}"

    # Save original leaf crop
    crop_filename = f"{sample_id}_crop.jpg"
    crop_path = settings.EVIDENCE_DIR / crop_filename
    cv2.imwrite(str(crop_path), bgr_img)

    # 2. Lesion Segmentation
    seg_res = segmenter.segment_lesions(bgr_img, sample_id=sample_id)

    # 3. Disease Classification (Calibrated)
    rgb_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_img)
    cls_res = classifier.predict_leaf(pil_img)

    # 4. Grad-CAM Explainable AI Heatmap
    tensor = classifier.transform(pil_img).unsqueeze(0).to(classifier.device)
    heatmap_2d = gradcam.generate_heatmap(tensor, class_idx=cls_res["predicted_class_id"])
    overlay_bgr = gradcam.overlay_heatmap(bgr_img, heatmap_2d)

    gradcam_filename = f"{sample_id}_gradcam.jpg"
    gradcam_path = settings.EVIDENCE_DIR / gradcam_filename
    cv2.imwrite(str(gradcam_path), overlay_bgr)

    # 5. Crop Health Scoring
    health_res = CropHealthEngine.evaluate_leaf_health(
        disease_name=cls_res["full_class"],
        classification_confidence=cls_res["confidence"],
        lesion_area_pct=seg_res["lesion_area_pct"]
    )

    # 6. Treatment Advisory Engine
    advisory = TreatmentAdvisoryEngine.get_prescription(
        disease_name=cls_res["full_class"],
        lesion_pct=seg_res["lesion_area_pct"],
        health_score=health_res["health_score"]
    )

    return {
        "sample_id": sample_id,
        "disease": {
            "name": cls_res["full_class"],
            "species": cls_res["crop_species"],
            "pathology": cls_res["pathology"],
            "confidence": round(cls_res["confidence"], 4),
            "temperature_calibrated": True,
            "top_probabilities": cls_res.get("top_3_probabilities", [])
        },
        "health": {
            "health_score": health_res["health_score"],
            "triage_level": health_res["triage_level"],
            "is_healthy": health_res["is_healthy"],
            "lesion_area_pct": seg_res["lesion_area_pct"]
        },
        "visual_evidence": {
            "original_crop_url": f"/static/evidence/{crop_filename}",
            "lesion_mask_url": f"/static/evidence/{Path(seg_res['mask_image_path']).name}",
            "gradcam_heatmap_url": f"/static/evidence/{gradcam_filename}"
        },
        "advisory": advisory
    }
