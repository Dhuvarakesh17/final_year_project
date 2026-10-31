# Database Schema Design

The schema is built for PostgreSQL using SQLAlchemy 2.0. Foreign key relations ensure strong referential integrity, and cascading delete options maintain storage hygiene.

```mermaid
erDiagram
    VIDEOS ||--o{ EXTRACTED_FRAMES : "contains"
    VIDEOS ||--o{ ANALYSIS_JOBS : "processed by"
    ANALYSIS_JOBS ||--o{ DETECTED_OBJECTS : "identifies"
    ANALYSIS_JOBS ||--o{ YIELD_PREDICTIONS : "estimates"
    ANALYSIS_JOBS ||--o{ REPORTS : "summarized in"
    EXTRACTED_FRAMES ||--o{ DETECTED_OBJECTS : "localized on"
    DETECTED_OBJECTS ||--o| DISEASE_FINDINGS : "evaluated as leaf"
    DETECTED_OBJECTS ||--o| WEED_FINDINGS : "evaluated as weed"

    VIDEOS {
        uuid id PK
        string original_filename
        string file_path
        string sha256_hash
        float duration_sec
        float fps
        int width
        int height
        float file_size_mb
        timestamp created_at
    }

    ANALYSIS_JOBS {
        uuid id PK
        uuid video_id FK
        string status
        float progress_pct
        string current_stage
        jsonb config_json
        string error_message
        timestamp started_at
        timestamp completed_at
    }

    EXTRACTED_FRAMES {
        uuid id PK
        uuid video_id FK
        int frame_number
        float timestamp_sec
        string file_path
        float blur_score
        float ssim_score
        boolean is_valid
        timestamp created_at
    }

    DETECTED_OBJECTS {
        uuid id PK
        uuid frame_id FK
        uuid analysis_id FK
        int track_id
        string object_type
        float confidence
        jsonb bbox
        jsonb polygon_mask
        string crop_image_path
        timestamp created_at
    }

    DISEASE_FINDINGS {
        uuid id PK
        uuid object_id FK
        uuid analysis_id FK
        string crop_name
        string disease_name
        float classification_confidence
        float lesion_area_pct
        string severity_category
        float health_score
        string mask_overlay_path
        jsonb top5_probabilities
        timestamp created_at
    }

    WEED_FINDINGS {
        uuid id PK
        uuid object_id FK
        uuid analysis_id FK
        int track_id
        string weed_species
        float confidence
        float canopy_coverage_pct
        timestamp created_at
    }

    YIELD_PREDICTIONS {
        uuid id PK
        uuid analysis_id FK
        string crop_type
        string growth_stage
        float field_area_ha
        float plant_density_m2
        float weed_pressure_idx
        float mean_health_score
        float predicted_yield_t_ha
        float ci_lower
        float ci_upper
        jsonb feature_importances
        jsonb agronomic_inputs
        string status
        timestamp created_at
    }

    REPORTS {
        uuid id PK
        uuid analysis_id FK
        string pdf_path
        int file_size_bytes
        string sha256_hash
        jsonb executive_summary
        timestamp generated_at
    }
```

