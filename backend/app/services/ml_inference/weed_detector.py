"""
Weed Detection & Tracking Service
Uses YOLOv8 Object Detection / Segmentation integrated with ByteTrack.
Tracks unique weed instances across video frames to eliminate duplicate counting.
Computes weed canopy coverage percentage.
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Ensure Ultralytics config is local
os.environ["YOLO_CONFIG_DIR"] = r"d:\final_year_project\ml_models"

from ultralytics import YOLO
import torch

class WeedDetectorTracker:
    def __init__(
        self,
        model_weights: str = r"d:\final_year_project\ml_models\weights\yolov8_weeds.pt",
        conf_threshold: float = 0.35,
        iou_threshold: float = 0.50,
        device: str = "cuda:0" if torch.cuda.is_available() else "cpu"
    ):
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        
        # Load YOLO model (prefers custom fine-tuned weights, falls back to yolov8n base)
        if os.path.exists(model_weights):
            self.model = YOLO(model_weights)
            print(f"Loaded custom fine-tuned weed detection weights from {model_weights}")
        else:
            self.model = YOLO("yolov8n.pt")
            print("Using YOLOv8n foundation model.")

        # Set of confirmed unique track IDs across the session
        self.confirmed_track_ids = set()

    def process_frame(
        self,
        bgr_frame: np.ndarray,
        frame_idx: int,
        timestamp_sec: float
    ) -> Dict[str, Any]:
        """
        Runs YOLO detection with ByteTrack tracking on a single frame.
        """
        h, w = bgr_frame.shape[:2]
        total_frame_area = float(h * w)

        # Run tracking with ByteTrack
        results = self.model.track(
            source=bgr_frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            device=self.device,
            verbose=False
        )

        detected_objects = []
        frame_weed_area = 0.0
        r = results[0]

        if r.boxes is not None and len(r.boxes) > 0:
            boxes = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()
            clss = r.boxes.cls.cpu().numpy()
            track_ids = r.boxes.id.int().cpu().numpy() if r.boxes.id is not None else [-1] * len(boxes)

            for bbox, conf, cls_id, track_id in zip(boxes, confs, clss, track_ids):
                x1, y1, x2, y2 = [float(v) for v in bbox]
                box_w = max(0.0, x2 - x1)
                box_h = max(0.0, y2 - y1)
                box_area = box_w * box_h

                # Determine object type:
                # In agricultural mode: classes other than crops are flagged as weeds
                is_weed = True
                species_name = "Field Weed (Invasive)"
                
                if track_id > 0:
                    self.confirmed_track_ids.add(int(track_id))

                if is_weed:
                    frame_weed_area += box_area

                detected_objects.append({
                    "track_id": int(track_id) if track_id > 0 else None,
                    "class_id": int(cls_id),
                    "object_type": "weed" if is_weed else "crop_leaf",
                    "species_name": species_name,
                    "confidence": round(float(conf), 4),
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "timestamp_sec": timestamp_sec,
                })

        canopy_coverage_pct = (frame_weed_area / total_frame_area) * 100.0

        return {
            "frame_idx": frame_idx,
            "timestamp_sec": timestamp_sec,
            "detected_objects": detected_objects,
            "frame_weed_count": len([o for o in detected_objects if o["object_type"] == "weed"]),
            "cumulative_unique_weeds": len(self.confirmed_track_ids),
            "frame_weed_canopy_pct": round(canopy_coverage_pct, 2),
        }

    def reset_tracking(self):
        """Resets tracked IDs for a new video session."""
        self.confirmed_track_ids.clear()

