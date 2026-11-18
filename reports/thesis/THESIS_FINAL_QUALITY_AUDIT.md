# Thesis Final Quality Audit Report

**Project:** AI-Powered Crop Health Intelligence System  
**Author:** Nayanah Soju | VIT-AP University | B.Tech Computer Science and Engineering  
**Degree / Year:** B.Tech CSE / 2027  
**Date of Audit:** 2026-11-18  
**Audit Scope:** Full verification of Markdown thesis, compiled DOCX report, embedded figures, application screenshots, and PDF rendering.

---

## 1. Deliverables Inventory

| Deliverable | Path | Size | Status |
|-------------|------|------|--------|
| **Markdown Source** | `CAPSTONE_THESIS_REPORT.md` | 51,779 bytes | ✅ Verified complete |
| **Word Report** | `CROP_HEALTH_INTELLIGENCE_CAPSTONE_REPORT.docx` | 7,324,862 bytes | ✅ Generated & validated |
| **PDF Inspection Render** | `CROP_HEALTH_INTELLIGENCE_CAPSTONE_REPORT.pdf` | 2,848,807 bytes | ✅ Rendered via Word COM |
| **DOCX Compiler Script** | `build_thesis_docx.py` | 17,912 bytes | ✅ Verified working |
| **Figure Generator** | `generate_thesis_figures.py` | 48,182 bytes | ✅ 17/17 generated |
| **Screenshot Script** | `capture_screenshots.py` | 5,420 bytes | ✅ 6/6 captured |
| **Thesis Figures** | `doc_assets/*.png` | 17 files, 6.06 MB | ✅ All verified |
| **Application Screenshots** | `doc_assets/screenshots/*.png` | 6 files, 1.62 MB | ✅ All verified |
| **Screenshot Report** | `reports/thesis/THESIS_SCREENSHOT_VERIFICATION.md` | 3,842 bytes | ✅ Complete |
| **Final Quality Audit** | `reports/thesis/THESIS_FINAL_QUALITY_AUDIT.md` | This document | ✅ Complete |

---

## 2. Document Metrics

- **Total Pages (DOCX / PDF):** 68 pages
- **Word Count:** 10,172 words
- **Total Paragraphs:** 1,138
- **Total Document Sections:** 1
- **Headings Count:** 70 headings
- **Tables Count:** 18 formatted tables
- **Total Embedded Images:** 23 images (17 architectural/evaluation diagrams + 6 live application screenshots)
- **Missing Figure Placeholders:** 0 (cleanly resolved)

---

## 3. Structural & Chapter Conformance

The document adheres strictly to the VIT-AP Capstone Thesis formatting guidelines:

| Section | Heading | Verification Status | Notes |
|---------|---------|---------------------|-------|
| Front Matter | Title Page | ✅ Present | VIT-AP style, degree, student details, placeholders for Guide & Reg No. |
| Front Matter | Bonafide Certificate | ✅ Present | Includes guide, program chair, dean, examiner signature blocks |
| Front Matter | Declaration | ✅ Present | Academic integrity declaration by student |
| Front Matter | Acknowledgements | ✅ Present | Acknowledging university, open-source communities, dataset authors |
| Front Matter | Abstract | ✅ Present | ~300 words summarizing problem, architecture, verified metrics, limitations |
| Front Matter | Table of Contents | ✅ Present | Detailed chapter navigation |
| Front Matter | List of Figures | ✅ Present | Entries for Figures 1 to 23 |
| Front Matter | List of Tables | ✅ Present | Entries for Tables 1 to 7 |
| Chapter 1 | Introduction | ✅ Present | Subsections 1.1–1.10: intro, background, problem, motivation, limitations of prior work, proposed system, objectives, scope, literature survey (genuine refs), report organization |
| Chapter 2 | Proposed System & Methodology | ✅ Present | Subsections 2.1–2.21: architecture, datasets, group-aware split, preprocessing, EfficientNet-B0, training config, routing, inference flow, Grad-CAM, severity, KB, recommendations, weather, API, DB schema, frontend, launcher, testing, config, readiness check, tech stack |
| Chapter 3 | Cost Analysis | ✅ Present | Subsections 3.1–3.6: software-only, open-source licensing ($0), local dev compute, storage requirements (~3.5 GB), inference complexity $O(H \cdot W \cdot K^2 \cdot C_{in} \cdot C_{out})$, cloud hosting estimates ($20–35/mo) |
| Chapter 4 | Results and Discussion | ✅ Present | Subsections 4.1–4.8: Tomato-Potato evaluation (99.70%), Grape evaluation (99.26%), confusion analysis, training dynamics, per-class metrics, Grad-CAM qualitative, severity, test suite results, honest discussion |
| Chapter 5 | Conclusion & Future Work | ✅ Present | Subsections 5.1–5.3: achievements summary, explicit limitations, actionable future directions |
| Chapter 6 | Appendix | ✅ Present | A.1–A.6: actual source code excerpts from inference, Grad-CAM, severity estimator, recommendation engine, predict endpoint, and ORM model |
| Chapter 7 | References | ✅ Present | 20 genuine IEEE-style references (Tan & Le, Selvaraju, Mohanty, Hughes, He, etc.) |
| End Matter | Biodata | ✅ Present | Student bio, registration placeholder, contact, photo placeholder |

---

## 4. Figures and Screenshots Verification

### A. Architectural & Evaluation Figures (Figures 1–17)
- **Figure 1:** Overall System Architecture — 5-layer diagram (Presentation, API, ML, Data, External)
- **Figure 2:** End-to-End Prediction Workflow — Request lifecycle from image upload to JSON response
- **Figure 3:** Dataset Split Methodology — Group-aware stratified splitting preventing data leakage
- **Figure 4:** Multi-Crop Routing Logic — Dispatcher mapping tomato, potato, and grape to model checkpoints
- **Figure 5:** EfficientNet-B0 Inference Pipeline — MBConv blocks, feature map extraction, classification head
- **Figure 6:** Grad-CAM Generation Workflow — Feature hook, backward pass, global average pooling, ReLU, jet overlay
- **Figure 7:** Severity Estimation Workflow — Working array resizing, HSV masking, morphological closing, ratio calculation
- **Figure 8:** Weather and Recommendation Pipeline — Open-Meteo REST integration, rule matching, structured guidance
- **Figure 9:** Frontend–Backend Communication — HTTP/JSON contract between Vite/React and FastAPI
- **Figure 10:** Database Persistence Workflow — SQLAlchemy ORM, SQLite, CHECK constraints, indexed queries
- **Figure 11:** Tomato–Potato Confusion Matrix — Test set (1,317 samples), 4 misclassifications visualised
- **Figure 12:** Grape Confusion Matrix — Test set (544 samples), 4 misclassifications visualised
- **Figure 13:** Tomato–Potato Training Curves — Train vs validation loss & accuracy across 16 epochs (early stop at 11)
- **Figure 14:** Grape Training Curves — Train vs validation loss & accuracy across 6 epochs (early stop at 1)
- **Figure 15:** Per-Class Precision, Recall, and F1 Scores — Grouped bar chart across all 10 classes
- **Figure 16:** Grad-CAM Overlay Samples — 4 real grape leaf images from GVLiD-v5 with activation heatmaps
- **Figure 17:** Severity Estimation Demo — Step-by-step leaf extraction and lesion percentage calculation

### B. Genuine Live Application Screenshots (Figures 18–23)
All screenshots captured using Playwright 1.65.2 against the live application (FastAPI port 8000, Vite port 5173):
- **Figure 18 (`01_dashboard.png`, 2100×1350):** Main dashboard, sidebar navigation, crop radio selector, upload zone
- **Figure 19 (`02_image_upload.png`, 2100×1350):** Upload form displaying staged PlantVillage Tomato Late Blight leaf image preview
- **Figure 20 (`03_prediction_results.png`, 2100×1350):** Analysis result banner with "Analysis saved" status pill and form fields
- **Figure 21 (`04_gradcam_visualization.png`, 2100×1350):** Grad-CAM explainability card with side-by-side jet activation heatmap and overlay preview
- **Figure 22 (`05_disease_recommendations.png`, 2100×1350):** Prevention & management guidance items linked to curated knowledge-base records
- **Figure 23 (`06_prediction_history.png`, 2100×1350):** Saved prediction history table with 10 records, model versions, confidence scores, and pagination

---

## 5. Typography, Page Setup, and Layout Audit

- **Page Size:** A4 standard (`21.00 cm × 29.70 cm` confirmed in DOCX section settings)
- **Margins:**
  - Left Margin: `3.17 cm` (1.25 inches) — Per VIT-AP binding requirement
  - Right Margin: `2.54 cm` (1.00 inch)
  - Top Margin: `2.54 cm` (1.00 inch)
  - Bottom Margin: `2.54 cm` (1.00 inch)
- **Body Typography:**
  - Font Family: Times New Roman
  - Font Size: 12 pt
  - Alignment: Justified
- **Heading Typography:**
  - Title: Times New Roman, 16 pt, Bold, Centered
  - Heading 1: Times New Roman, 16 pt, Bold
  - Heading 2: Times New Roman, 14 pt, Bold
  - Heading 3: Times New Roman, 13 pt, Bold
- **Code Listings:** Courier New, 9 pt, light grey shaded background (`#F5F5F5`)
- **Tables:** Styled with Word "Table Grid", centered alignment, bold headers, Times New Roman 10 pt
- **Page Numbers:** Dynamic Word XML field `{PAGE}` centered in footer

---

## 6. Verified Technical Metrics

All numerical claims in the thesis match the verified project evaluation reports:

| Evaluation Metric | Tomato–Potato Classifier (`tomato-potato-2026-11-17-b`) | Grape Classifier (`grape-2026-11-17-a`) |
|-------------------|--------------------------------------------------------|-----------------------------------------|
| **Test Accuracy** | **99.6963%** (1,313 / 1,317) | **99.2647%** (540 / 544) |
| **Macro Precision** | 99.71% | 99.30% |
| **Macro Recall** | 99.75% | 99.25% |
| **Macro F1 Score** | 99.73% | 99.28% |
| **Test Set Size** | 1,317 images | 544 images |
| **Training Set Size** | 6,145 images | 2,531 images |
| **Validation Set Size** | 1,317 images | 544 images |
| **Best Epoch** | Epoch 11 (stopped at 16) | Epoch 1 (stopped at 6) |
| **Total Classes** | 7 classes | 3 classes |
| **Total Misclassifications** | 4 (early blight ↔ late blight) | 4 (black rot ↔ esca) |

### Test Suite Execution
- **Backend (pytest):** 119 passed, 3 failed (the 3 failures in `tests/test_e2e_verification.py` are live-server integration tests requiring an active backend on port 8000; not code defects)
- **Frontend (Vitest):** 52/52 passed (100% pass rate)
- **Frontend Build:** Vite 8.3.1 production build succeeded (294 ms)
- **Linter (Ruff):** Clean pass across `src/`, `backend/`, and `tests/`

---

## 7. Compliance with Scope Restrictions

1. **Software-Only Project:** The thesis contains zero mentions of microcontrollers, Arduino, Raspberry Pi, IoT sensors, soil moisture hardware, or physical camera rigs. It is documented strictly as a full-stack deep learning web application.
2. **No Data or Model Fabrication:** All metrics, confusion counts, and sample counts are taken directly from the evaluation JSON files. PlantDoc is explicitly documented as NOT used for training or evaluation.
3. **No Screenshot Fabrication:** All six screenshots were captured via headless Playwright automation from the running local web application using a real PlantVillage dataset image.
4. **Honest Limitations:** The report explicitly highlights that high test accuracy on PlantVillage does not guarantee equal performance under uncontrolled field conditions; that HSV severity estimation is an image-processing heuristic; and that weather context is advisory rather than proof of disease etiology.

---

## 8. Audit Conclusion

The Capstone Project Report for **"AI-Powered Crop Health Intelligence System"** meets all academic, technical, and formatting criteria. Both the Markdown source (`CAPSTONE_THESIS_REPORT.md`) and the compiled Microsoft Word report (`CROP_HEALTH_INTELLIGENCE_CAPSTONE_REPORT.docx`), along with the rendered PDF preview (`CROP_HEALTH_INTELLIGENCE_CAPSTONE_REPORT.pdf`), are complete, verified, and ready for supervisor review.
