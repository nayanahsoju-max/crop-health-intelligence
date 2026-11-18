# Thesis Screenshot Verification Report

**Generated:** 2026-11-18  
**Method:** Playwright 1.65.2 headless Chromium, `capture_screenshots.py`  
**Source image:** `data/PlantVillage/Tomato_Late_blight/0003faa8-...___RS_Late.B 4946.JPG` (genuine dataset image)  
**Crop selected:** Tomato  
**Application:** Backend on port 8000, Frontend on port 5173 (started via `START_CROP_HEALTH.bat`)

---

## Screenshot Inventory

| # | Filename | Size (bytes) | Dimensions | Status |
|---|----------|-------------|------------|--------|
| 1 | `01_dashboard.png` | 194,691 | 2100 × 1350 | ✅ PASS |
| 2 | `02_image_upload.png` | 329,773 | 2100 × 1350 | ✅ PASS |
| 3 | `03_prediction_results.png` | 306,594 | 2100 × 1350 | ✅ PASS |
| 4 | `04_gradcam_visualization.png` | 312,997 | 2100 × 1350 | ✅ PASS |
| 5 | `05_disease_recommendations.png` | 310,794 | 2100 × 1350 | ✅ PASS |
| 6 | `06_prediction_history.png` | 163,291 | 2100 × 1350 | ✅ PASS |

**Total:** 6 files, 1,618,140 bytes  
**Viewport:** 1400 × 900 at 1.5× device scale factor (effective 2100 × 1350 pixels)

---

## Individual Verification

### 01_dashboard.png — ✅ PASS
- Shows the main "FIELDNOTES / CROP HEALTH" application with sidebar navigation
- "Understand what your leaves are telling you." heading visible
- Crop selector (Tomato / Potato / Grape radio buttons) with Tomato selected
- Image upload dropzone ("Choose a leaf image or drag it here")
- Location input field (optional)
- "WHAT YOU'LL RECEIVE" sidebar with 4 workflow steps
- Research prototype notice and disclaimer visible
- No loading states, errors, or blank panels

### 02_image_upload.png — ✅ PASS
- Tomato Late Blight leaf image preview visible in the upload area
- Filename displayed: `0003faa8-4b27-4c65-bf42-6d9e352ca1a5___RS_Late.B 4946.JPG`
- File size shown: `0.01 MB`
- Crop selector still shows Tomato selected
- Image preview is a genuine PlantVillage tomato late blight photograph
- No errors or loading indicators

### 03_prediction_results.png — ✅ PASS
- "ANALYSIS RESULT — Your crop health summary" heading visible with "Analysis saved" status pill
- Uploaded leaf image preview still visible above the result
- Form fields (Location, Lesion Mask, "Analyze leaf →" button) visible
- Beginning of the result stack visible at bottom of viewport
- No errors or incomplete loading

### 04_gradcam_visualization.png — ✅ PASS
- Section "06 EXPLAINABILITY — Grad-CAM view" clearly visible
- Two Grad-CAM images displayed side by side:
  - **Activation heatmap** — jet colormap with red/yellow hot region on the leaf
  - **Overlay preview** — heatmap blended with the original leaf photograph
- Caption: "Grad-CAM visualizes model activation; it does not prove biological cause."
- Above it: prevention and management guidance items with knowledge-base source links
- Section "05 WEATHER CONTEXT — Not requested" (no location was provided)
- All text is readable, images are clear and genuine model output

### 05_disease_recommendations.png — ✅ PASS
- Section "04 GENERAL GUIDANCE — Prevention and management" fully visible
- Six guidance items shown:
  - 3 PREVENTION items (inspect transplants, keep foliage dry, avoid solanaceous crops)
  - 3 GENERAL MANAGEMENT items (scout frequently, remove infected material, certified seed)
- Each item sourced: "Late blight of tomato and potato ↗"
- Weather context card: "Not requested"
- Grad-CAM view partially visible at bottom
- All text is readable, source attribution links present

### 06_prediction_history.png — ✅ PASS
- "Prediction history" navigation tab active in sidebar
- History table with 10 prediction records visible
- Columns: Date, Predicted class, Confidence, Severity, Weather, Model, Action
- Genuine entries:
  - Multiple "Tomato Early Blight" at 100.0% confidence
  - "Grape Black Rot" at 99.7% confidence
  - "Potato Early Blight" at 100.0% confidence
  - One entry with "Moderate" severity
  - Weather status varies: available / not_requested / unavailable
  - Model versions: `efficientnet_b0_tomato_potato_2026_11_17_b` and `efficientnet_b0_grape_2026_11_17_a`
- Pagination controls: Previous / Page 1 / Next
- Detail panel: "Select a history item to view its saved result details."
- No loading errors or blank panels

---

## Conclusion

All six application screenshots are **genuine captures of the running Crop Health Intelligence System**. No mockups, fabricated content, or placeholder images were used. All screenshots show the real application UI with real model predictions from the trained EfficientNet-B0 classifiers on genuine PlantVillage dataset images. Text is readable, layouts are complete, and no browser errors or loading states are present.

No recapture is necessary.
