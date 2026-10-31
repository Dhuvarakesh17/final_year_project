import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Crop & Weed Monitoring System"
    API_V1_STR: str = "/api/v1"
    
    # Base Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "ml_models" / "weights"
    
    RAW_VIDEOS_DIR: Path = DATA_DIR / "raw_videos"
    EXTRACTED_FRAMES_DIR: Path = DATA_DIR / "extracted_frames"
    EVIDENCE_DIR: Path = DATA_DIR / "evidence"
    REPORTS_DIR: Path = DATA_DIR / "reports"
    DATASETS_DIR: Path = DATA_DIR / "datasets"

    # Database Configuration (Defaults to SQLite for local development, switchable to PostgreSQL)
    DATABASE_URL: str = f"sqlite:///{DATA_DIR}/crop_monitoring.db"
    
    # Computer Vision & Inference Thresholds
    BLUR_THRESHOLD: float = 100.0
    SSIM_THRESHOLD: float = 0.92
    DEFAULT_FRAME_INTERVAL: int = 15  # process every 15th frame by default
    
    # Model Thresholds
    WEED_CONF_THRESHOLD: float = 0.40
    DISEASE_CONF_THRESHOLD: float = 0.45
    LESION_IOU_THRESHOLD: float = 0.50

    # Device
    DEVICE: str = "cuda"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# Ensure directories exist
for folder in [
    settings.DATA_DIR,
    settings.MODELS_DIR,
    settings.RAW_VIDEOS_DIR,
    settings.EXTRACTED_FRAMES_DIR,
    settings.EVIDENCE_DIR,
    settings.REPORTS_DIR,
    settings.DATASETS_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)

