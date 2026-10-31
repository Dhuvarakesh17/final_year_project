"""
Synthetic Agricultural Test Video Generator
Creates an MP4 field video containing simulated crop foliage, moving weeds,
and necrotic disease spots to test the full computer vision and tracking pipeline.
"""
import os
import cv2
import numpy as np
from pathlib import Path

def generate_sample_field_video(
    output_path: str = r"d:\final_year_project\data\raw_videos\sample_field_inspection.mp4",
    duration_sec: int = 4,
    fps: int = 24,
    width: int = 640,
    height: int = 480
):
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_frames = duration_sec * fps
    print(f"Generating synthetic agricultural video ({total_frames} frames, {duration_sec}s, {width}x{height})...")

    # Positions of simulated objects
    # Crop foliage (large green ellipse in center)
    crop_center = (width // 2, height // 2)
    crop_axes = (180, 140)

    # Simulated weed moving across the frame
    weed_start_x, weed_start_y = 60, 80
    weed_end_x, weed_end_y = width - 120, height - 100

    for f_idx in range(total_frames):
        alpha = f_idx / float(total_frames)
        
        # Soil / field ground texture (dark brown/tan)
        frame = np.full((height, width, 3), (35, 60, 85), dtype=np.uint8)
        
        # Add slight natural noise/texture
        noise = np.random.randint(-10, 10, (height, width, 3), dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # Draw main crop foliage (healthy lush green)
        cv2.ellipse(frame, crop_center, crop_axes, 15, 0, 360, (30, 160, 45), -1)
        cv2.ellipse(frame, (crop_center[0] - 50, crop_center[1] + 30), (80, 60), -25, 0, 360, (40, 175, 55), -1)

        # Draw pathological necrotic disease lesions on foliage (brown/yellow spots)
        cv2.circle(frame, (crop_center[0] - 20, crop_center[1] - 30), 18, (15, 70, 130), -1)  # Necrotic core
        cv2.circle(frame, (crop_center[0] - 20, crop_center[1] - 30), 22, (20, 150, 190), 2)   # Chlorotic halo
        cv2.circle(frame, (crop_center[0] + 45, crop_center[1] + 15), 14, (10, 60, 120), -1)

        # Draw tracked invasive weed moving across field (lighter distinct yellowish-green weed cluster)
        curr_weed_x = int(weed_start_x + (weed_end_x - weed_start_x) * alpha)
        curr_weed_y = int(weed_start_y + (weed_end_y - weed_start_y) * alpha)
        cv2.ellipse(frame, (curr_weed_x, curr_weed_y), (35, 25), 45, 0, 360, (35, 190, 130), -1)
        cv2.circle(frame, (curr_weed_x - 10, curr_weed_y - 8), 12, (45, 210, 140), -1)

        out.write(frame)

    out.release()
    print(f"Sample video created successfully: {output_path}")

if __name__ == "__main__":
    generate_sample_field_video()

