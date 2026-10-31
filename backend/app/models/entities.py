import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, Text, ForeignKey, DateTime
)
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Video(Base):
    __tablename__ = "videos"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    sha256_hash = Column(String(64), nullable=True)
    duration_sec = Column(Float, default=0.0)
    fps = Column(Float, default=0.0)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    file_size_mb = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis_jobs = relationship("AnalysisJob", back_populates="video", cascade="all, delete-orphan")
    extracted_frames = relationship("ExtractedFrame", back_populates="video", cascade="all, delete-orphan")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="QUEUED")  # QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED
    progress_pct = Column(Float, default=0.0)
    current_stage = Column(String(100), default="INITIALIZING")
    frames_processed = Column(Integer, default=0)
    total_frames = Column(Integer, default=0)
    config_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    video = relationship("Video", back_populates="analysis_jobs")
    extracted_frames = relationship("ExtractedFrame", back_populates="analysis_job", cascade="all, delete-orphan")
    detected_objects = relationship("DetectedObject", back_populates="analysis_job", cascade="all, delete-orphan")
    disease_findings = relationship("DiseaseFinding", back_populates="analysis_job", cascade="all, delete-orphan")
    weed_findings = relationship("WeedFinding", back_populates="analysis_job", cascade="all, delete-orphan")
    yield_predictions = relationship("YieldPrediction", back_populates="analysis_job", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="analysis_job", cascade="all, delete-orphan")


class ExtractedFrame(Base):
    __tablename__ = "extracted_frames"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    analysis_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp_sec = Column(Float, nullable=False)
    file_path = Column(String(500), nullable=False)
    blur_score = Column(Float, default=0.0)
    ssim_score = Column(Float, default=0.0)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="extracted_frames")
    analysis_job = relationship("AnalysisJob", back_populates="extracted_frames")
    detected_objects = relationship("DetectedObject", back_populates="frame", cascade="all, delete-orphan")


class DetectedObject(Base):
    __tablename__ = "detected_objects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    frame_id = Column(String(36), ForeignKey("extracted_frames.id", ondelete="CASCADE"), nullable=False)
    analysis_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    track_id = Column(Integer, nullable=True)
    object_type = Column(String(50), nullable=False)  # "crop_leaf", "weed"
    confidence = Column(Float, nullable=False)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    polygon_mask_json = Column(Text, nullable=True)
    crop_image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    frame = relationship("ExtractedFrame", back_populates="detected_objects")
    analysis_job = relationship("AnalysisJob", back_populates="detected_objects")
    disease_finding = relationship("DiseaseFinding", uselist=False, back_populates="detected_object", cascade="all, delete-orphan")
    weed_finding = relationship("WeedFinding", uselist=False, back_populates="detected_object", cascade="all, delete-orphan")


class DiseaseFinding(Base):
    __tablename__ = "disease_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    object_id = Column(String(36), ForeignKey("detected_objects.id", ondelete="CASCADE"), nullable=False)
    analysis_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    crop_name = Column(String(100), nullable=False)
    disease_name = Column(String(150), nullable=False)
    classification_confidence = Column(Float, nullable=False)
    lesion_area_pct = Column(Float, default=0.0)
    severity_category = Column(String(50), default="healthy")  # healthy, mild, moderate, severe, critical
    health_score = Column(Float, default=100.0)
    mask_overlay_path = Column(String(500), nullable=True)
    top5_probabilities_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    detected_object = relationship("DetectedObject", back_populates="disease_finding")
    analysis_job = relationship("AnalysisJob", back_populates="disease_findings")


class WeedFinding(Base):
    __tablename__ = "weed_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    object_id = Column(String(36), ForeignKey("detected_objects.id", ondelete="CASCADE"), nullable=False)
    analysis_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    track_id = Column(Integer, nullable=True)
    weed_species = Column(String(100), default="Unknown Weed")
    confidence = Column(Float, nullable=False)
    canopy_coverage_pct = Column(Float, default=0.0)
    timestamp_sec = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    detected_object = relationship("DetectedObject", back_populates="weed_finding")
    analysis_job = relationship("AnalysisJob", back_populates="weed_findings")


class YieldPrediction(Base):
    __tablename__ = "yield_predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    crop_type = Column(String(100), nullable=False)
    growth_stage = Column(String(100), default="Vegetative")
    field_area_ha = Column(Float, nullable=True)
    plant_density_m2 = Column(Float, nullable=True)
    weed_pressure_idx = Column(Float, nullable=True)
    mean_health_score = Column(Float, nullable=True)
    predicted_yield_t_ha = Column(Float, nullable=True)
    ci_lower = Column(Float, nullable=True)
    ci_upper = Column(Float, nullable=True)
    feature_importances_json = Column(Text, nullable=True)
    agronomic_inputs_json = Column(Text, nullable=True)
    status = Column(String(50), default="SUCCESS")  # SUCCESS, INSUFFICIENT_DATA
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis_job = relationship("AnalysisJob", back_populates="yield_predictions")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    pdf_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    sha256_hash = Column(String(64), nullable=True)
    executive_summary_json = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis_job = relationship("AnalysisJob", back_populates="reports")

