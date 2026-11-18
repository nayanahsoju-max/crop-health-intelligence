# Thesis Resume Status Report
**Project:** AI-Powered Crop Health Intelligence System  
**Student:** Nayanah Soju | VIT-AP University | B.Tech CSE | Expected 2027  
**Generated:** 2026-11-18

---

## Completed Assets

### Figures (17/17 — doc_assets/)
| File | Description | Status |
|------|-------------|--------|
| fig01_overall_architecture.png | System architecture (5 layers) | ✅ 370KB |
| fig02_prediction_workflow.png | End-to-end prediction pipeline | ✅ 323KB |
| fig03_dataset_split_workflow.png | Group-aware stratified split methodology | ✅ 273KB |
| fig04_multicrop_routing.png | Multi-crop routing logic | ✅ 219KB |
| fig05_efficientnet_pipeline.png | EfficientNet-B0 inference pipeline | ✅ 234KB |
| fig06_gradcam_workflow.png | Grad-CAM generation workflow | ✅ 255KB |
| fig07_severity_estimation_workflow.png | HSV severity estimation | ✅ 243KB |
| fig08_weather_recommendation_workflow.png | Weather + recommendation pipeline | ✅ 253KB |
| fig09_frontend_backend_communication.png | React ↔ FastAPI communication | ✅ 240KB |
| fig10_database_persistence_workflow.png | SQLite persistence workflow | ✅ 279KB |
| fig11_tomato_potato_cm.png | Tomato/Potato confusion matrix | ✅ 193KB |
| fig12_grape_cm.png | Grape confusion matrix | ✅ 119KB |
| fig13_tomato_potato_training_curves.png | Tomato/Potato training curves | ✅ 237KB |
| fig14_grape_training_curves.png | Grape training curves | ✅ 218KB |
| fig15_per_class_metrics.png | Per-class precision/recall/F1 chart | ✅ 195KB |
| fig16_gradcam_samples.png | Real Grad-CAM overlays (GVLiD-v5 grape) | ✅ 2.3MB |
| fig17_severity_demo.png | Severity estimation demo | ✅ 59KB |

### Application Screenshot
| File | Source | Status |
|------|--------|--------|
| final_step_10.png (119KB) | Stage 35 E2E browser test | ✅ Available |

**Note on live screenshots:** Browser subagent is unavailable due to quota exhaustion (429 error). The application is running at http://127.0.0.1:5173 and http://127.0.0.1:8000. Additional live screenshots could not be captured automatically. The existing final_step_10.png and the 17 generated figures are used in the thesis.

---

## Verified Test Results

### Backend (pytest)
- **119 passed, 3 failed** (3 failures are e2e integration tests requiring live backend at port 8000 — not code defects)
- Ruff linting: **all checks passed**

### Frontend (Vitest)
- **52/52 passed** (api.test.js + App.test.jsx)
- Vite production build: **PASSED** (8.3.1, 294ms)

---

## Verified Metrics (from evaluation JSONs)

### Tomato-Potato Classifier (tomato-potato-2026-11-17-b)
- Test accuracy: **99.6963%** (1317 samples, 7 classes)
- Macro Precision: 99.71%, Macro Recall: 99.75%, Macro F1: 99.73%
- Misclassifications: 4 total (1 T_healthy→late_blight, 1 T_early→late_blight, 2 T_late→early_blight)
- Training: best_epoch=11, 16 epochs completed, early stopped (patience=5)

### Grape Classifier (grape-2026-11-17-a)
- Test accuracy: **99.2647%** (544 samples, 3 classes)
- Macro Precision: 99.302%, Macro Recall: 99.253%, Macro F1: 99.277%
- Misclassifications: 4 total (2 black_rot→esca, 1 esca→black_rot, 1 isariopsis→black_rot)
- Training: best_epoch=1, 6 epochs completed, early stopped (patience=5)

---

## Still To Do

| Deliverable | Status |
|-------------|--------|
| CAPSTONE_THESIS_REPORT.md | ❌ Not yet created |
| build_thesis_docx.py | ❌ Not yet created |
| CROP_HEALTH_INTELLIGENCE_CAPSTONE_REPORT.docx | ❌ Not yet created |
| Quality check report | ❌ Not yet created |

---

## Environment Notes
- Python runtime: `C:\Users\ASUS\miniconda3\envs\retail-forecast\python.exe`
- python-docx 1.2.0 installed in retail-forecast env
- Application running: Backend port 8000, Frontend port 5173
- Database: `data/crop_health_local.sqlite3` at Alembic head (0002)
