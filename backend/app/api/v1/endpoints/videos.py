import os
import uuid
import hashlib
import cv2
import aiofiles
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from starlette.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.entities import Video
from backend.app.schemas.schemas import VideoResponse

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}

@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Supported formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    video_id = str(uuid.uuid4())
    safe_filename = f"{video_id}_{file.filename}"
    destination_path = settings.RAW_VIDEOS_DIR / safe_filename

    # Save uploaded file and compute SHA-256 hash
    hasher = hashlib.sha256()
    file_size_bytes = 0

    async with aiofiles.open(destination_path, "wb") as out_file:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            file_size_bytes += len(chunk)
            hasher.update(chunk)
            await out_file.write(chunk)

    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    sha256_hash = hasher.hexdigest()

    # Extract Video Properties using OpenCV
    cap = cv2.VideoCapture(str(destination_path))
    if not cap.isOpened():
        if destination_path.exists():
            os.remove(destination_path)
        raise HTTPException(status_code=400, detail="Corrupted or unreadable video file.")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration_sec = round(total_frames / fps, 2) if fps > 0 else 0.0
    cap.release()

    video_record = Video(
        id=video_id,
        original_filename=file.filename,
        file_path=str(destination_path),
        sha256_hash=sha256_hash,
        duration_sec=duration_sec,
        fps=fps,
        width=width,
        height=height,
        file_size_mb=file_size_mb,
    )
    db.add(video_record)
    db.commit()
    db.refresh(video_record)

    return video_record

@router.get("/sample-video")
def get_sample_video():
    sample_path = settings.BASE_DIR / "sample_video_for_upload.mp4"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample video file not found on server.")
    return FileResponse(
        path=str(sample_path),
        media_type="video/mp4",
        filename="sample_video_for_upload.mp4"
    )

@router.get("", response_model=list[VideoResponse])
def list_videos(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Video).offset(skip).limit(limit).all()

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")
    return video

