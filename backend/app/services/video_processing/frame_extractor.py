"""
Video Processing Service
Extracts frames from video files with configurable sampling rate,
evaluates Laplacian variance to reject blurry frames,
and uses SSIM to eliminate contiguous redundant keyframes.
"""
import os
import cv2
import numpy as np
from pathlib import Path
from typing import Generator, Tuple, Dict, Any, Optional

class VideoFrameExtractor:
    def __init__(
        self,
        blur_threshold: float = 100.0,
        ssim_threshold: float = 0.92,
        target_fps: Optional[float] = 2.0,  # Extract ~2 frames per second
    ):
        self.blur_threshold = blur_threshold
        self.ssim_threshold = ssim_threshold
        self.target_fps = target_fps

    @staticmethod
    def calculate_blur_score(gray_frame: np.ndarray) -> float:
        """Computes variance of Laplacian as motion blur metric."""
        return float(cv2.Laplacian(gray_frame, cv2.CV_64F).var())

    @staticmethod
    def calculate_ssim(gray1: np.ndarray, gray2: np.ndarray) -> float:
        """
        Fast approximated Structural Similarity Index for adjacent frame deduplication.
        """
        # Resize to thumbnail (128x128) for ultra-fast comparison
        t1 = cv2.resize(gray1, (128, 128)).astype(np.float32)
        t2 = cv2.resize(gray2, (128, 128)).astype(np.float32)

        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2

        mu1 = cv2.GaussianBlur(t1, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(t2, (11, 11), 1.5)

        mu1_sq = mu1 * mu1
        mu2_sq = mu2 * mu2
        mu1_mu2 = mu1 * mu2

        sigma1_sq = cv2.GaussianBlur(t1 * t1, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(t2 * t2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(t1 * t2, (11, 11), 1.5) - mu1_mu2

        num = (2 * mu1_mu2 + c1) * (2 * sigma12 + c2)
        den = (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)
        ssim_map = num / den
        return float(np.mean(ssim_map))

    def extract_keyframes(
        self,
        video_path: str,
        output_dir: str,
        video_id: str,
        frame_step: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Extracts keyframes and yields metadata for each valid frame.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Unable to open video source: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps

        # If frame_step not explicitly passed, compute from target_fps
        if frame_step is None:
            frame_step = max(1, int(fps / (self.target_fps or 2.0)))

        out_path = Path(output_dir) / video_id
        out_path.mkdir(parents=True, exist_ok=True)

        last_valid_gray = None
        frame_idx = 0
        saved_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_step == 0:
                timestamp_sec = frame_idx / fps
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur_score = self.calculate_blur_score(gray)

                # 1. Blur Check
                is_blurry = blur_score < self.blur_threshold
                if is_blurry:
                    frame_idx += 1
                    continue

                # 2. Duplicate / SSIM Check
                ssim_score = 0.0
                if last_valid_gray is not None:
                    ssim_score = self.calculate_ssim(gray, last_valid_gray)
                    if ssim_score > self.ssim_threshold:
                        # Redundant contiguous frame
                        frame_idx += 1
                        continue

                # Save Frame
                filename = f"frame_{frame_idx:06d}_{timestamp_sec:.2f}s.jpg"
                save_file = out_path / filename
                cv2.imwrite(str(save_file), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

                last_valid_gray = gray
                saved_count += 1

                yield {
                    "frame_number": frame_idx,
                    "timestamp_sec": round(timestamp_sec, 3),
                    "file_path": str(save_file),
                    "blur_score": round(blur_score, 2),
                    "ssim_score": round(ssim_score, 3),
                    "is_valid": True,
                    "total_video_frames": total_frames,
                    "video_fps": fps,
                    "video_duration_sec": duration,
                }

            frame_idx += 1

        cap.release()

