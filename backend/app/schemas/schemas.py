from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# --- Video Schemas ---
class VideoBase(BaseModel):
    original_filename: str

class VideoCreate(VideoBase):
    file_path: str
    sha256_hash: Optional[str] = None
    duration_sec: float = 0.0
    fps: float = 0.0
    width: int = 0
    height: int = 0
    file_size_mb: float = 0.0

class VideoResponse(VideoBase):
    id: str
    file_path: str
    sha256_hash: Optional[str]
    duration_sec: float
    fps: float
    width: int
    height: int
    file_size_mb: float
    created_at: datetime

    class Config:
        from_attributes = True

# --- Analysis Job Schemas ---
class AgronomicInputs(BaseModel):
    crop_type: str = "Tomato"
    growth_stage: str = "Vegetative"
    field_area_ha: Optional[float] = 1.0
    plant_density_m2: Optional[float] = None
    temp_c: Optional[float] = 25.0
    rainfall_mm: Optional[float] = 100.0
    soil_n: Optional[float] = 40.0
    soil_p: Optional[float] = 25.0
    soil_k: Optional[float] = 30.0
    soil_ph: Optional[float] = 6.5

class JobCreateRequest(BaseModel):
    video_id: str
    frame_interval: int = Field(default=15, ge=1, le=120)
    enable_blur_filter: bool = True
    blur_threshold: float = 100.0
    enable_ssim_filter: bool = True
    ssim_threshold: float = 0.92
    agro_inputs: Optional[AgronomicInputs] = None

class JobStatusResponse(BaseModel):
    job_id: str
    video_id: str
    status: str
    progress_percentage: float
    current_stage: str
    frames_processed: int
    total_frames: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True

# --- Findings & Evidence Schemas ---
class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class LeafFindingResponse(BaseModel):
    id: str
    object_id: str
    crop_name: str
    disease_name: str
    classification_confidence: float
    lesion_area_pct: float
    severity_category: str
    health_score: float
    bbox: BoundingBox
    crop_image_url: Optional[str] = None
    mask_overlay_url: Optional[str] = None
    timestamp_sec: float

    class Config:
        from_attributes = True

class WeedFindingResponse(BaseModel):
    id: str
    track_id: Optional[int]
    weed_species: str
    confidence: float
    canopy_coverage_pct: float
    bbox: BoundingBox
    timestamp_sec: float

    class Config:
        from_attributes = True

class AnalysisSummaryResponse(BaseModel):
    analysis_id: str
    total_frames_analyzed: int
    unique_weeds_detected: int
    mean_weed_canopy_pct: float
    total_leaves_analyzed: int
    healthy_leaves_count: int
    diseased_leaves_count: int
    mean_health_score: float
    predominant_disease: Optional[str]
    yield_prediction: Optional[Dict[str, Any]] = None

# --- Yield Prediction Schemas ---
class YieldPredictionRequest(BaseModel):
    crop_type: str
    growth_stage: str = "Vegetative"
    field_area_ha: float
    plant_density_m2: Optional[float] = None
    weed_canopy_ratio_pct: Optional[float] = 0.0
    mean_health_score: Optional[float] = 100.0
    temp_c: float
    rainfall_mm: float
    soil_n: float
    soil_p: float
    soil_k: float
    soil_ph: float

class YieldPredictionResponse(BaseModel):
    status: str  # SUCCESS, INSUFFICIENT_DATA
    predicted_yield_t_ha: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    feature_contributions: Optional[List[Dict[str, Any]]] = None
    limitations: List[str] = []
    missing_features: Optional[List[str]] = None

