# AgroVision Intelligence AI
### Autonomous Crop Health, Weed Localization & Calibrated Yield Prediction Platform

An enterprise-grade, multi-model agricultural intelligence platform developed as a Final Year Engineering Project. Accepts agricultural drone/field video footage (`.MP4`, `.MOV`, `.AVI`) to perform automated weed detection & tracking, foliar disease diagnosis, necrotic lesion segmentation, deterministic health triage scoring, and calibrated agronomic yield regression with 90% confidence intervals.

---

## 🌟 Key Capabilities & Architecture

```
                                  AGRICULTURAL FIELD VIDEO INGESTION
                                                  │
                                                  ▼
                        ┌──────────────────────────────────────────────────┐
                        │      Laplacian Blur & SSIM Frame Extraction      │
                        └─────────────────────────┬────────────────────────┘
                                                  │
                        ┌─────────────────────────┴────────────────────────┐
                        ▼                                                  ▼
       ┌─────────────────────────────────┐                ┌─────────────────────────────────┐
       │     Weed Detection & Tracking   │                │    Foliar Disease Pathology     │
       │    YOLOv8n + ByteTrack Spatial  │                │  EfficientNet-B0 + Temperature  │
       │     Deduplication & WCR %       │                │      Scaling Calibration        │
       └────────────────┬────────────────┘                └────────────────┬────────────────┘
                        │                                                  │
                        │                                                  ▼
                        │                                 ┌─────────────────────────────────┐
                        │                                 │   Necrotic Lesion Segmentation  │
                        │                                 │   Pixel-exact Area Ratio %      │
                        │                                 └────────────────┬────────────────┘
                        │                                                  │
                        └─────────────────────────┬────────────────────────┘
                                                  │
                                                  ▼
                        ┌──────────────────────────────────────────────────┐
                        │      Crop Health Scoring & Agronomic Triage      │
                        └─────────────────────────┬────────────────────────┘
                                                  │
                                                  ▼
                        ┌──────────────────────────────────────────────────┐
                        │     Calibrated Yield Prediction Engine           │
                        │     Multivariate Regression with 90% CI          │
                        └─────────────────────────┬────────────────────────┘
                                                  │
                                                  ▼
                        ┌──────────────────────────────────────────────────┐
                        │      12-Section Python ReportLab Audit PDF       │
                        │      Embedded Keyframes, Telemetry & Overlays    │
                        └──────────────────────────────────────────────────┘
```

### 1. Multi-Model AI Pipeline
* **Weed Detection & Multi-Object Tracking:** Fine-tuned **YOLOv8n** on the DeepWeeds benchmark dataset integrated with **ByteTrack** for spatial cross-frame deduplication and Weed Canopy Ratio (WCR %) estimation.
  * **mAP@50:** `95.7%` | **mAP@50-95:** `94.8%` | **Weed Recall:** `98.2%` | **Inference:** `0.7 ms/image`.
* **Foliar Pathology Classification:** Fine-tuned **EfficientNet-B0** on 16,504 PlantVillage Solanaceae images with post-hoc Temperature Scaling calibration ($T = 1.4972$).
  * **Validation Accuracy:** `99.73%` | **Validation Loss:** `0.0097`.
* **Pixel-Exact Lesion Segmentation:** Color-space transform + Otsu thresholding calculating necrotic area ratio:
  $$\text{Lesion Ratio (\%)} = \left(\frac{\text{Lesion Pixels}}{\text{Leaf Pixels}}\right) \times 100$$
* **Calibrated Agronomic Yield Engine:** Multivariate regression coupled with strict input gating (soil N/P/K, pH, temperature, precipitation, field area) generating 90% confidence intervals $[\hat{Y}_{0.05}, \hat{Y}_{0.95}]$.
* **Traceable Audit Reports:** Automated compilation of 12-section A4 audit documents via Python ReportLab, complete with full-color annotated keyframes, bounding box telemetry, lesion overlays, and agronomic remedy matrices.

---

## 📁 Repository Structure

```
final_year_project/
├── backend/                        # FastAPI Backend & ML Services
│   ├── app/
│   │   ├── api/v1/endpoints/       # REST API Endpoints (Health, Videos, Analysis, Reports)
│   │   ├── core/                   # Configuration & Settings
│   │   ├── db/                     # SQLite / SQLAlchemy Engine & Models
│   │   ├── services/
│   │   │   ├── video_processing/   # Frame extraction, Laplacian blur, SSIM
│   │   │   ├── ml_inference/       # YOLOv8, EfficientNet-B0, Lesion Segmenter
│   │   │   ├── health_assessment/  # Deterministic 0-100 Health Triage
│   │   │   ├── yield_prediction/   # Calibrated Agronomic Yield Regression
│   │   │   └── pdf_report/         # 12-Section Python ReportLab Generator
│   │   └── tasks/                  # Pipeline Coordinator & Async Job Runner
│   ├── scripts/                    # Model training, dataset preparation, and E2E verification
│   └── requirements.txt            # Python dependencies
├── frontend/                       # React 18 + Vite + Tailwind CSS Single-Page App
│   ├── src/
│   │   ├── App.tsx                 # 4-Tab Independent Dashboard & Inspection Suite
│   │   ├── context/ThemeContext.tsx # Persistent Dark & Light Mode Controller
│   │   └── index.css               # Universal Plus Jakarta Sans typography
│   ├── package.json
│   └── vite.config.ts
├── ml_models/
│   └── weights/                    # Serialized AI Model Weights (< 25 MB)
│       ├── efficientnet_disease.pt # Trained PlantVillage foliar classifier
│       ├── yolov8_weeds.pt         # Trained DeepWeeds weed detector
│       └── disease_classifier_metadata.json
├── data/                           # Data Directories (Ignored in Git, preserved via .gitkeep)
│   ├── raw_videos/
│   ├── extracted_frames/
│   ├── evidence/
│   └── reports/
├── docs/                           # Technical Specifications & Documentation
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── API_SPECIFICATION.md
│   └── DATABASE_SCHEMA.md
├── .gitignore                      # Git Ignore Policy
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
* Python 3.10+ (with CUDA 12.1+ support for GPU acceleration)
* Node.js 18+ & npm

### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/<your-username>/<your-repo-name>.git
cd final_year_project

# Create and activate Python virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start FastAPI Server (runs at http://127.0.0.1:8000)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
```bash
# In a new terminal:
cd frontend
npm install

# Start Vite Dev Server (runs at http://127.0.0.1:3000)
npm run dev -- --host 127.0.0.1 --port 3000
```

### 3. Open the Application
Navigate to `http://localhost:3000` in your browser.
* Use **Tab 1** to upload drone video footage (or click **"Quick Load Test Video"**).
* Inspect real-time KPI metrics in **Tab 2 (Analytics Dashboard)**.
* Review side-by-side lesion segmentation overlays in **Tab 3 (Traceable Evidence)**.
* Download the official 12-section audit PDF in **Tab 4 (PDF Reports)**.

---

## 📊 Benchmark Datasets
1. **PlantVillage Dataset:** 16,504 Solanaceae foliar images (Tomato, Potato, Pepper) spanning 15 pathological and healthy classes.
2. **DeepWeeds Benchmark:** 10,501 in-situ weed images capturing invasive rangeland weed species across Northern Australia.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
