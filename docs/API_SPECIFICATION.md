# API Specification

## Base URL: `/api/v1`

### 1. Video Management
- `POST /videos/upload`
  - Multipart form data: `file: UploadFile`
  - Response: `{ video_id: UUID, filename: str, duration_sec: float, fps: float, resolution: [int, int], file_size_mb: float, upload_timestamp: str }`
- `GET /videos`
  - Query parameters: `page: int = 1`, `limit: int = 20`
  - Response: List of registered videos with metadata.
- `GET /videos/{video_id}`
  - Returns metadata and processing state of a specific video.

### 2. Analysis Execution & Job Monitoring
- `POST /analysis/jobs`
  - Request Body:
    ```json
    {
      "video_id": "uuid",
      "frame_interval": 15,
      "enable_blur_filter": true,
      "blur_threshold": 100.0,
      "enable_ssim_filter": true,
      "ssim_threshold": 0.92,
      "agro_inputs": {
        "crop_type": "Tomato",
        "growth_stage": "Vegetative",
        "field_area_ha": 2.5,
        "temperature_c": 26.5,
        "rainfall_mm": 110.0,
        "soil_n": 45.0,
        "soil_p": 25.0,
        "soil_k": 30.0,
        "soil_ph": 6.5
      }
    }
    ```
  - Response: `{ job_id: UUID, status: "QUEUED", created_at: str }`
- `GET /analysis/jobs/{job_id}/status`
  - Response:
    ```json
    {
      "job_id": "uuid",
      "status": "PROCESSING | COMPLETED | FAILED",
      "progress_percentage": 68.5,
      "current_stage": "LESION_SEGMENTATION",
      "frames_processed": 120,
      "total_frames": 180,
      "started_at": "2026-10-31T12:00:00Z",
      "estimated_remaining_sec": 14.2,
      "error": null
    }
    ```

### 3. Analysis Findings & Evidence Dossier
- `GET /analysis/{analysis_id}/summary`
  - Response: High-level overview: Total unique weeds detected, dominant weed species, leaf count, healthy vs diseased breakdown, average health score, yield prediction summary.
- `GET /analysis/{analysis_id}/findings/leaves`
  - Filter by `severity: "healthy" | "mild" | "moderate" | "severe" | "critical"`, `crop_type`, `page`, `limit`.
  - Response: Paginated leaf records with bounding box, crop image URL, mask URL, classification, confidence, lesion area %, health score.
- `GET /analysis/{analysis_id}/findings/weeds`
  - Response: Unique tracked weeds, species classification, bounding boxes, timestamps, and estimated field coverage percentage.
- `GET /analysis/{analysis_id}/evidence/{evidence_id}`
  - Response: Complete traceable dossier including original frame screenshot, annotated overlay, individual leaf crop, lesion segmentation mask, and full diagnostic metrics.

### 4. Interactive Single-Image Inference (Diagnostics & Verification)
- `POST /inference/weed-detect`: Upload single field image -> returns YOLO detections & weed masks.
- `POST /inference/disease-classify`: Upload leaf image -> returns top-k disease classes & calibrated probabilities.
- `POST /inference/lesion-segment`: Upload leaf image -> returns segmented lesions, pixel counts, and lesion area percentage.

### 5. Crop Yield Prediction Engine
- `POST /yield/predict`
  - Request Body: Agronomic and visual features (or analysis ID to auto-populate visual features).
  - Response:
    ```json
    {
      "status": "SUCCESS | INSUFFICIENT_DATA",
      "predicted_yield_tonnes_per_hectare": 3.84,
      "confidence_interval_90": [3.41, 4.25],
      "feature_contributions": [
        {"feature": "mean_health_score", "impact": "+0.45 t/ha"},
        {"feature": "weed_canopy_ratio", "impact": "-0.32 t/ha"},
        {"feature": "soil_nitrogen", "impact": "+0.28 t/ha"}
      ],
      "limitations": [
        "Yield estimated for Tomato in Vegetative stage; weather anomalies post-sampling may affect actual harvest.",
        "Model trained on temperate and semi-arid agro-ecological zones."
      ]
    }
    ```

### 6. PDF Report Generation & Export
- `POST /reports/generate/{analysis_id}`
  - Triggers ReportLab compilation. Returns `{ report_id: UUID, pdf_url: str, status: "READY" }`.
- `GET /reports/{report_id}/download`
  - Downloads the compiled 12-section PDF document.

