"""
capture_screenshots.py
Capture genuine application screenshots using Playwright (headless Chromium).

Requirements:
  - Playwright installed: pip install playwright
  - Chromium installed: playwright install chromium
  - Backend running on http://127.0.0.1:8000
  - Frontend running on http://127.0.0.1:5173

Usage:
  python capture_screenshots.py

Output: doc_assets/screenshots/01_dashboard.png through 06_prediction_history.png
"""

import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent
OUT_DIR = PROJECT_ROOT / "doc_assets" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Pick a genuine sample image from the dataset (no spaces in name for reliability)
# First try a UUID-named tomato late blight image
SAMPLE_IMAGE = None
TOMATO_LB_DIR = PROJECT_ROOT / "data" / "PlantVillage" / "Tomato_Late_blight"
GRAPE_BR_DIR = PROJECT_ROOT / "data" / "GVLiD-v5" / "DATASET" / "Black rot"

for candidate_dir, crop in [(TOMATO_LB_DIR, "tomato"), (GRAPE_BR_DIR, "grape")]:
    if candidate_dir.exists():
        for f in sorted(candidate_dir.iterdir()):
            # Prefer files without spaces for simpler handling
            if f.suffix.lower() in (".jpg", ".jpeg", ".png") and " " not in f.name:
                SAMPLE_IMAGE = f
                SAMPLE_CROP = crop
                break
        if SAMPLE_IMAGE:
            break

if SAMPLE_IMAGE is None:
    # Fallback: use first image even if it has spaces
    for f in sorted(TOMATO_LB_DIR.iterdir()):
        if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
            SAMPLE_IMAGE = f
            SAMPLE_CROP = "tomato"
            break

if SAMPLE_IMAGE is None:
    print("ERROR: No sample leaf image found in dataset directories.")
    sys.exit(1)

print(f"Sample image: {SAMPLE_IMAGE}")
print(f"Crop: {SAMPLE_CROP}")
print(f"Output directory: {OUT_DIR}")


def wait_for_element(page, selector, timeout=30000):
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except PlaywrightTimeout:
        return False


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=1.5,  # Higher DPI for crisp screenshots
        )
        page = context.new_page()

        print("\n--- Screenshot 01: Dashboard ---")
        page.goto("http://127.0.0.1:5173", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1500)  # Let React fully render
        path_01 = str(OUT_DIR / "01_dashboard.png")
        page.screenshot(path=path_01, full_page=False)
        print(f"  Saved: {path_01}")

        print("\n--- Screenshot 02: Image Upload (file staged) ---")
        # Select the crop radio button
        if SAMPLE_CROP == "tomato":
            # Click tomato radio button
            tomato_label = page.locator("label.crop-option", has_text="Tomato")
            if tomato_label.count() > 0:
                tomato_label.click()
        elif SAMPLE_CROP == "grape":
            grape_label = page.locator("label.crop-option", has_text="Grape")
            if grape_label.count() > 0:
                grape_label.click()

        # Set the file input
        file_input = page.locator("input#leaf-image")
        file_input.set_input_files(str(SAMPLE_IMAGE))
        page.wait_for_timeout(1000)  # Let preview render

        path_02 = str(OUT_DIR / "02_image_upload.png")
        page.screenshot(path=path_02, full_page=False)
        print(f"  Saved: {path_02}")

        print("\n--- Submitting prediction (this takes ~10-30s on CPU) ---")
        submit_btn = page.locator("button.submit-button")
        submit_btn.click()

        # Wait for prediction result to appear — look for the result section
        print("  Waiting for prediction result...")
        result_appeared = wait_for_element(page, "[data-testid='prediction-result']", timeout=90000)
        if not result_appeared:
            # Try alternate selector
            result_appeared = wait_for_element(page, ".result-stack", timeout=30000)

        if not result_appeared:
            print("  WARNING: Prediction result did not appear within timeout.")
            # Take screenshot anyway to show current state
            page.screenshot(path=str(OUT_DIR / "03_prediction_results.png"), full_page=True)
        else:
            page.wait_for_timeout(1500)  # Let images load (Grad-CAM data URLs)

            print("\n--- Screenshot 03: Prediction Results (top) ---")
            path_03 = str(OUT_DIR / "03_prediction_results.png")
            page.screenshot(path=path_03, full_page=False)
            print(f"  Saved: {path_03}")

            print("\n--- Screenshot 04: Grad-CAM Visualization ---")
            # Scroll to the explainability card
            explain_card = page.locator(".explain-card")
            if explain_card.count() > 0:
                explain_card.scroll_into_view_if_needed()
                page.wait_for_timeout(800)
                # Capture just that region, or full page scrolled to it
                path_04 = str(OUT_DIR / "04_gradcam_visualization.png")
                page.screenshot(path=path_04, full_page=False)
                print(f"  Saved: {path_04}")
            else:
                # Scroll down and capture
                page.evaluate("window.scrollBy(0, 600)")
                page.wait_for_timeout(500)
                path_04 = str(OUT_DIR / "04_gradcam_visualization.png")
                page.screenshot(path=path_04, full_page=False)
                print(f"  Saved: {path_04}")

            print("\n--- Screenshot 05: Disease Info and Recommendations ---")
            # Scroll to guidance card
            guidance_card = page.locator(".guidance-card")
            if guidance_card.count() > 0:
                guidance_card.scroll_into_view_if_needed()
                page.wait_for_timeout(800)
            else:
                page.evaluate("window.scrollBy(0, 400)")
                page.wait_for_timeout(500)
            path_05 = str(OUT_DIR / "05_disease_recommendations.png")
            page.screenshot(path=path_05, full_page=False)
            print(f"  Saved: {path_05}")

        print("\n--- Screenshot 06: Prediction History ---")
        # Navigate to history view
        history_btn = page.locator("button.nav-item", has_text="Prediction history")
        if history_btn.count() > 0:
            history_btn.click()
        else:
            # Try by text content
            page.locator("nav button", has_text="history").click()

        page.wait_for_timeout(3000)  # Wait for history to load from API
        path_06 = str(OUT_DIR / "06_prediction_history.png")
        page.screenshot(path=path_06, full_page=False)
        print(f"  Saved: {path_06}")

        browser.close()

    print("\n=== Screenshot capture complete ===")
    print("Files saved:")
    for f in sorted(OUT_DIR.iterdir()):
        print(f"  {f.name}  ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    run()
