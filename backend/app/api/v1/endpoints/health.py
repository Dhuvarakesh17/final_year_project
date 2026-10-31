import platform
from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter()

@router.get("/health", tags=["System"])
def health_check():
    cuda_available = False
    device_name = "CPU"
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            device_name = torch.cuda.get_device_name(0)
    except ImportError:
        pass

    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cuda_available": cuda_available,
        "compute_device": device_name,
        "directories": {
            "data": str(settings.DATA_DIR),
            "raw_videos": str(settings.RAW_VIDEOS_DIR),
            "evidence": str(settings.EVIDENCE_DIR),
            "reports": str(settings.REPORTS_DIR),
        }
    }

