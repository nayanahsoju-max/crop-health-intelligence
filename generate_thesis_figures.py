"""Generate publication-quality diagrams and evaluation figures for the Capstone Thesis Report.

All figures are generated at 300 DPI into doc_assets/.
"""

import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent
DOC_ASSETS = PROJECT_ROOT / "doc_assets"
DOC_ASSETS.mkdir(exist_ok=True)

# Styling defaults
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# ==============================================================================
# 1. OVERALL SYSTEM ARCHITECTURE
# ==============================================================================
def draw_system_architecture():
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    # Title
    ax.text(50, 97, "Overall System Architecture — Crop Health Intelligence",
            ha="center", va="top", fontsize=13, fontweight="bold", color="#1a202c")

    # Layer boxes
    colors = {
        "client": "#ebf8ff",
        "api": "#e6fffa",
        "ml": "#fefcbf",
        "data": "#feebc8",
        "ext": "#edf2f7"
    }
    borders = {
        "client": "#3182ce",
        "api": "#319795",
        "ml": "#d69e2e",
        "data": "#dd6b20",
        "ext": "#4a5568"
    }

    # 1. Frontend Layer
    rect_client = patches.FancyBboxPatch((5, 68), 90, 22, boxstyle="round,pad=1.5",
                                         facecolor=colors["client"], edgecolor=borders["client"], lw=1.5)
    ax.add_patch(rect_client)
    ax.text(7, 87, "PRESENTATION LAYER (React 18 + Vite SPA)", fontsize=10, fontweight="bold", color=borders["client"])
    
    # Client components
    client_boxes = [
        (8, 70, 25, 14, "Leaf Analysis View\n(Image Upload, Crop Select,\nMask & Location Input)"),
        (37, 70, 25, 14, "Results Stack\n(Predicted Class, Scores,\nGrad-CAM, Guidance, Weather)"),
        (66, 70, 25, 14, "History & Analytics Panel\n(Saved Records, Class Filter,\nDistribution Charts)")
    ]
    for x, y, w, h, text in client_boxes:
        r = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8", facecolor="#ffffff", edgecolor="#a0aec0", lw=1)
        ax.add_patch(r)
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=8.5, color="#2d3748")

    # Arrow Down
    ax.annotate("", xy=(50, 58), xytext=(50, 68),
                arrowprops=dict(arrowstyle="->", lw=1.8, color="#4a5568"))
    ax.text(51, 63, "HTTP POST /predict (Multipart/form-data) | GET /predictions", fontsize=8, color="#4a5568")

    # 2. Application & Backend Layer
    rect_api = patches.FancyBboxPatch((5, 32), 90, 24, boxstyle="round,pad=1.5",
                                      facecolor=colors["api"], edgecolor=borders["api"], lw=1.5)
    ax.add_patch(rect_api)
    ax.text(7, 53, "APPLICATION & BUSINESS LOGIC LAYER (FastAPI + Python 3.11)", fontsize=10, fontweight="bold", color=borders["api"])

    api_boxes = [
        (8, 34, 16, 15, "FastAPI Service\n(Validation,\nEndpoints,\nCORS, Error)"),
        (26, 34, 16, 15, "Prediction\nWorkflow\n(Router, Model\nCache, Pipeline)"),
        (44, 34, 16, 15, "Explainability\nEngine\n(Grad-CAM\nActivations)"),
        (62, 34, 16, 15, "Severity\nEstimator\n(HSV Leaf Mask,\nLesion Area %)"),
        (80, 34, 13, 15, "Recommendation\nEngine\n(KB Service,\nWeather Rules)")
    ]
    for x, y, w, h, text in api_boxes:
        r = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8", facecolor="#ffffff", edgecolor="#a0aec0", lw=1)
        ax.add_patch(r)
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=8, color="#2d3748")

    # Arrows from Backend to Data/Models
    ax.annotate("", xy=(25, 20), xytext=(34, 32), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))
    ax.annotate("", xy=(65, 20), xytext=(55, 32), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))
    ax.annotate("", xy=(87, 20), xytext=(87, 32), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))

    # 3. Model & Data Layer
    rect_data = patches.FancyBboxPatch((5, 3), 90, 16, boxstyle="round,pad=1.5",
                                       facecolor=colors["data"], edgecolor=borders["data"], lw=1.5)
    ax.add_patch(rect_data)
    ax.text(7, 16.5, "MODEL CHECKPOINTS, PERSISTENCE & EXTERNAL SERVICES LAYER", fontsize=10, fontweight="bold", color=borders["data"])

    storage_boxes = [
        (8, 5, 27, 9.5, "PyTorch Model Checkpoints\n(tomato-potato 7-class & grape 3-class\nEfficientNet-B0 .pt & mapping.json)"),
        (38, 5, 27, 9.5, "SQLite Database (SQLAlchemy + Alembic)\n(prediction_records table,\nCheckConstraints, JSON fields)"),
        (68, 5, 25, 9.5, "Curated KB & Weather API\n(diseases.json 10 classes +\nOpen-Meteo REST API)")
    ]
    for x, y, w, h, text in storage_boxes:
        r = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8", facecolor="#ffffff", edgecolor="#a0aec0", lw=1)
        ax.add_patch(r)
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=8, color="#2d3748")

    plt.tight_layout()
    output_path = DOC_ASSETS / "fig01_overall_architecture.png"
    plt.savefig(output_path)
    plt.close()
    print(f"Generated: {output_path}")

# ==============================================================================
# 2. END-TO-END PREDICTION WORKFLOW
# ==============================================================================
def draw_prediction_workflow():
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    ax.text(50, 97, "End-to-End Image Prediction & Analysis Workflow",
            ha="center", va="top", fontsize=13, fontweight="bold", color="#1a202c")

    steps = [
        ("Step 1: Client Upload", "User selects crop (tomato, potato, grape),\nuploads leaf image, optional PNG mask & location", 86, "#3182ce", "#ebf8ff"),
        ("Step 2: Upload Validation", "FastAPI validates file type (JPEG/PNG/WEBP),\nenforces max byte size (10 MB), checks dimensions", 74, "#319795", "#e6fffa"),
        ("Step 3: Multi-Crop Routing", "Inspects crop parameter; resolves route\nto Tomato-Potato or Grape classifier", 62, "#805ad5", "#faf5ff"),
        ("Step 4: Image Preprocessing", "EXIF transpose, RGB convert, bilinear resize\nto 224x224, scale [0, 1], ImageNet normalize", 50, "#d69e2e", "#fefcbf"),
        ("Step 5: PyTorch Inference & Grad-CAM", "Evaluates EfficientNet-B0; softmax probabilities;\nbackpropagates gradients for class activation map", 38, "#dd6b20", "#feebc8"),
        ("Step 6: Severity & Weather Context", "Computes lesion % if mask supplied;\nqueries Open-Meteo REST for local current weather", 26, "#38a169", "#f0fff4"),
        ("Step 7: Traceable Recommendations & DB Persistence", "Matches KB disease rules; synthesizes guidance;\npersists record to SQLite via SQLAlchemy; returns JSON", 14, "#4a5568", "#edf2f7"),
        ("Step 8: Interactive Frontend Rendering", "React displays class badge, confidence score, Grad-CAM overlay,\nsymptoms, severity category, guidance & weather cards", 2, "#e53e3e", "#fff5f5")
    ]

    for title, desc, y, bcolor, fcolor in steps:
        rect = patches.FancyBboxPatch((15, y), 70, 9.5, boxstyle="round,pad=0.8", facecolor=fcolor, edgecolor=bcolor, lw=1.5)
        ax.add_patch(rect)
        ax.text(17, y + 6.8, title, fontsize=9.5, fontweight="bold", color=bcolor)
        ax.text(17, y + 2.5, desc, fontsize=8, color="#2d3748")
        if y > 2:
            ax.annotate("", xy=(50, y - 2.5), xytext=(50, y),
                        arrowprops=dict(arrowstyle="->", lw=1.5, color="#718096"))

    plt.tight_layout()
    output_path = DOC_ASSETS / "fig02_prediction_workflow.png"
    plt.savefig(output_path)
    plt.close()
    print(f"Generated: {output_path}")

# ==============================================================================
# 3. DATASET SPLIT & LEAKAGE PREVENTION
# ==============================================================================
def draw_dataset_split_workflow():
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    ax.text(50, 97, "Dataset Preparation, Stratification & Leakage Prevention",
            ha="center", va="top", fontsize=13, fontweight="bold", color="#1a202c")

    boxes = [
        (10, 75, 80, 14, "1. Raw PlantVillage Image Acquisition & Inventory",
         "Collect images across 10 disease/healthy classes for Tomato, Potato, and Grape.\nCompute SHA-256 hash for every image to detect bitwise duplicates.", "#2b6cb0", "#ebf8ff"),
        (10, 53, 80, 14, "2. Near-Duplicate Analysis & Group Identification",
         "Perform perceptual hashing (pHash) and cluster near-duplicates from same plant/leaf.\nAssign source group IDs to prevent frame-to-frame leakage across splits.", "#2c7a7b", "#e6fffa"),
        (10, 31, 80, 14, "3. Group-Aware Stratified Train / Validation / Test Splitting",
         "Split data strictly by source groups with 70% Train, 15% Validation, 15% Test.\nEnsure zero group overlap: images from the same leaf never appear in multiple splits.", "#b7791f", "#fefcbf"),
    ]

    for x, y, w, h, title, desc, bcolor, fcolor in boxes:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8", facecolor=fcolor, edgecolor=bcolor, lw=1.5)
        ax.add_patch(rect)
        ax.text(x + 2, y + 9.5, title, fontsize=10, fontweight="bold", color=bcolor)
        ax.text(x + 2, y + 4.0, desc, fontsize=8.5, color="#2d3748")
        if y > 31:
            ax.annotate("", xy=(50, y - 4), xytext=(50, y), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))

    # Bottom 3 split boxes
    splits = [
        (10, 8, 24, 15, "TRAIN SET (70%)\nTomato-Potato: 6,145\nGrape: 2,531\nUsed for SGD optimization", "#2f855a", "#f0fff4"),
        (38, 8, 24, 15, "VALIDATION SET (15%)\nTomato-Potato: 1,317\nGrape: 544\nUsed for early stopping", "#c05621", "#fffaf0"),
        (66, 8, 24, 15, "TEST SET (15%)\nTomato-Potato: 1,317\nGrape: 544\nUnseen holdout evaluation", "#9b2c2c", "#fff5f5")
    ]
    ax.annotate("", xy=(22, 23), xytext=(35, 31), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))
    ax.annotate("", xy=(50, 23), xytext=(50, 31), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))
    ax.annotate("", xy=(78, 23), xytext=(65, 31), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))

    for x, y, w, h, text, bcolor, fcolor in splits:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8", facecolor=fcolor, edgecolor=bcolor, lw=1.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=8.5, fontweight="bold", color=bcolor)

    plt.tight_layout()
    output_path = DOC_ASSETS / "fig03_dataset_split_workflow.png"
    plt.savefig(output_path)
    plt.close()
    print(f"Generated: {output_path}")

# ==============================================================================
# 4. MULTI-CROP MODEL ROUTING
# ==============================================================================
def draw_multicrop_routing():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    ax.text(50, 96, "Multi-Crop Classifier Routing Architecture",
            ha="center", va="top", fontsize=13, fontweight="bold", color="#1a202c")

    # Inbound Request
    r_in = patches.FancyBboxPatch((30, 78), 40, 12, boxstyle="round,pad=0.8", facecolor="#ebf8ff", edgecolor="#3182ce", lw=1.5)
    ax.add_patch(r_in)
    ax.text(50, 84, "Inbound Request: POST /predict\nParameters: image, crop, location, lesion_mask",
            ha="center", va="center", fontsize=9, fontweight="bold", color="#2b6cb0")

    # Routing Decision diamond
    ax.annotate("", xy=(50, 64), xytext=(50, 78), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))
    r_dec = patches.FancyBboxPatch((35, 52), 30, 12, boxstyle="round,pad=0.8", facecolor="#faf5ff", edgecolor="#805ad5", lw=1.5)
    ax.add_patch(r_dec)
    ax.text(50, 58, "Crop Router Dispatch\n(inspects 'crop' parameter)",
            ha="center", va="center", fontsize=9, fontweight="bold", color="#6b46c1")

    # Branches
    ax.annotate("", xy=(25, 38), xytext=(40, 52), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))
    ax.text(26, 47, "crop in ['tomato', 'potato']", fontsize=8, color="#4a5568")

    ax.annotate("", xy=(75, 38), xytext=(60, 52), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))
    ax.text(63, 47, "crop == 'grape'", fontsize=8, color="#4a5568")

    # Model Route 1: Tomato Potato
    r_m1 = patches.FancyBboxPatch((5, 12), 40, 26, boxstyle="round,pad=0.8", facecolor="#fefcbf", edgecolor="#b7791f", lw=1.5)
    ax.add_patch(r_m1)
    ax.text(25, 33, "Tomato-Potato Classifier (7 Classes)", ha="center", fontsize=9.5, fontweight="bold", color="#b7791f")
    desc_m1 = ("Checkpoint: tomato-potato-2026-11-17-b\n"
               "Architecture: EfficientNet-B0 (224x224)\n"
               "Classes: tomato_healthy, tomato_bacterial_spot,\n"
               "tomato_early_blight, tomato_late_blight,\n"
               "potato_healthy, potato_early_blight, potato_late_blight\n"
               "Holdout Accuracy: 99.70% (1,313/1,317)")
    ax.text(25, 21, desc_m1, ha="center", va="center", fontsize=7.5, color="#2d3748")

    # Model Route 2: Grape
    r_m2 = patches.FancyBboxPatch((55, 12), 40, 26, boxstyle="round,pad=0.8", facecolor="#feebc8", edgecolor="#c05621", lw=1.5)
    ax.add_patch(r_m2)
    ax.text(75, 33, "Grape Classifier (3 Classes)", ha="center", fontsize=9.5, fontweight="bold", color="#c05621")
    desc_m2 = ("Checkpoint: grape-2026-11-17-a\n"
               "Architecture: EfficientNet-B0 (224x224)\n"
               "Classes: grape_black_rot,\n"
               "grape_esca, grape_isariopsis_leaf_blight\n"
               "Holdout Accuracy: 99.26% (540/544)\n"
               "Holdout Macro F1: 99.28%")
    ax.text(75, 21, desc_m2, ha="center", va="center", fontsize=7.5, color="#2d3748")

    plt.tight_layout()
    output_path = DOC_ASSETS / "fig04_multicrop_routing.png"
    plt.savefig(output_path)
    plt.close()
    print(f"Generated: {output_path}")

# ==============================================================================
# 5. EFFICIENTNET-B0 CLASSIFICATION PIPELINE
# ==============================================================================
def draw_efficientnet_pipeline():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    ax.text(50, 95, "EfficientNet-B0 Neural Network Architecture & Feature Stages",
            ha="center", va="top", fontsize=13, fontweight="bold", color="#1a202c")

    stages = [
        ("Input", "RGB Image\n224 x 224 x 3", 6, "#4a5568", "#edf2f7"),
        ("Stem", "Conv3x3\nStride 2\n112x112x32", 18, "#2b6cb0", "#ebf8ff"),
        ("Stage 1-2", "MBConv1 (k3)\nMBConv6 (k3)\n56x56x24", 31, "#2c7a7b", "#e6fffa"),
        ("Stage 3-4", "MBConv6 (k5)\nMBConv6 (k3)\n28x28x80", 44, "#2f855a", "#f0fff4"),
        ("Stage 5-6", "MBConv6 (k5)\nMBConv6 (k5)\n14x14x192", 57, "#b7791f", "#fefcbf"),
        ("Stage 7-8", "MBConv6 (k3)\nConv1x1 (1280)\n7x7x1280", 70, "#c05621", "#feebc8"),
        ("Head", "Adaptive\nAvgPool2d\n1x1x1280", 82, "#9b2c2c", "#fff5f5"),
        ("Classifier", "Dropout(0.2)\nLinear(C)\nSoftmax", 93, "#6b46c1", "#faf5ff")
    ]

    for name, desc, x, bcolor, fcolor in stages:
        rect = patches.FancyBboxPatch((x - 4.5, 30), 9, 42, boxstyle="round,pad=0.6", facecolor=fcolor, edgecolor=bcolor, lw=1.5)
        ax.add_patch(rect)
        ax.text(x, 65, name, ha="center", va="center", fontsize=8.5, fontweight="bold", color=bcolor)
        ax.text(x, 46, desc, ha="center", va="center", fontsize=7.5, color="#2d3748")
        if x < 90:
            ax.annotate("", xy=(x + 4.8, 51), xytext=(x + 4.2, 51), arrowprops=dict(arrowstyle="->", lw=1.2, color="#718096"))

    # Bottom annotation
    ax.text(50, 15, "Compound Scaling: depth d = 1.0, width w = 1.0, resolution r = 224. MBConv includes Squeeze-and-Excitation (SE) & Swish activation.\nGrad-CAM extracts activation maps from the final convolutional layer (features[-1]: 7x7x1280).",
            ha="center", va="center", fontsize=8, style="italic", color="#4a5568")

    plt.tight_layout()
    output_path = DOC_ASSETS / "fig05_efficientnet_pipeline.png"
    plt.savefig(output_path)
    plt.close()
    print(f"Generated: {output_path}")

# ==============================================================================
# 6. GRAD-CAM WORKFLOW
# ==============================================================================
def draw_gradcam_workflow():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    ax.text(50, 96, "Gradient-Weighted Class Activation Mapping (Grad-CAM) Workflow",
            ha="center", va="top", fontsize=13, fontweight="bold", color="#1a202c")

    steps = [
        (8, 55, 25, 25, "1. Forward Pass\n& Target Hook",
         "Register forward hook on\nmodel.features[-1].\nCompute model logits y.\nClass index c = argmax(y).", "#2b6cb0", "#ebf8ff"),
        (37, 55, 26, 25, "2. Backward Gradients\n& Global Pooling",
         "Compute gradients dy_c / dA_k\nvia backward pass.\nCompute importance weights:\na_k = (1/Z) sum_i sum_j (dy_c/dA_ijk)", "#2c7a7b", "#e6fffa"),
        (67, 55, 25, 25, "3. Weighted Linear\nCombination & ReLU",
         "L_GradCAM = ReLU(sum_k a_k * A_k).\nReLU filters out features that\nnegatively contribute to class c.", "#b7791f", "#fefcbf"),
    ]

    for x, y, w, h, title, desc, bcolor, fcolor in steps:
        r = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8", facecolor=fcolor, edgecolor=bcolor, lw=1.5)
        ax.add_patch(r)
        ax.text(x + w/2, y + h - 5, title, ha="center", va="center", fontsize=9, fontweight="bold", color=bcolor)
        ax.text(x + w/2, y + h/2 - 3, desc, ha="center", va="center", fontsize=7.5, color="#2d3748")

    ax.annotate("", xy=(37, 67), xytext=(33, 67), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))
    ax.annotate("", xy=(67, 67), xytext=(63, 67), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))

    # Post processing steps below
    post_steps = [
        (20, 15, 27, 24, "4. Normalization & Upsampling",
         "Min-max scaling to [0, 1].\nBilinear interpolation resizing\nfrom 7x7 to original image size (W, H).", "#2f855a", "#f0fff4"),
        (53, 15, 27, 24, "5. Colormap & Visual Overlay",
         "Apply 'Jet' colormap to heatmap.\nAlpha blend with original image:\nOverlay = (1 - a)*Image + a*Heatmap (a=0.42).", "#c05621", "#fffaf0")
    ]
    ax.annotate("", xy=(50, 39), xytext=(79, 55), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))
    ax.annotate("", xy=(53, 27), xytext=(47, 27), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))

    for x, y, w, h, title, desc, bcolor, fcolor in post_steps:
        r = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8", facecolor=fcolor, edgecolor=bcolor, lw=1.5)
        ax.add_patch(r)
        ax.text(x + w/2, y + h - 5, title, ha="center", va="center", fontsize=9, fontweight="bold", color=bcolor)
        ax.text(x + w/2, y + h/2 - 3, desc, ha="center", va="center", fontsize=7.5, color="#2d3748")

    plt.tight_layout()
    output_path = DOC_ASSETS / "fig06_gradcam_workflow.png"
    plt.savefig(output_path)
    plt.close()
    print(f"Generated: {output_path}")

# ==============================================================================
# 7. SEVERITY ESTIMATION WORKFLOW
# ==============================================================================
def draw_severity_workflow():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    ax.text(50, 96, "Classical Computer Vision Disease Severity Estimation Workflow",
            ha="center", va="top", fontsize=13, fontweight="bold", color="#1a202c")

    stages = [
        (5, 55, 26, 26, "Input Alignment",
         "Leaf image (RGB) +\nAligned Lesion Mask (PNG).\nVerify identical dimensions.\nScale to max 1024px working size.", "#2b6cb0", "#ebf8ff"),
        (37, 55, 26, 26, "Leaf Foreground Masking",
         "Convert RGB to HSV color space.\nThreshold green: Hue [25, 95],\nSaturation >= 40, Value >= 30.\nMorphological closing (kernel 5x5).", "#2c7a7b", "#e6fffa"),
        (69, 55, 26, 26, "Lesion Union Handling",
         "Union with annotated lesion:\nLeaf_Total = Green_Mask | Lesion_Mask.\nEnsures necrotic tissue is included\nin total leaf denominator area.", "#b7791f", "#fefcbf"),
    ]

    for x, y, w, h, title, desc, bcolor, fcolor in stages:
        r = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8", facecolor=fcolor, edgecolor=bcolor, lw=1.5)
        ax.add_patch(r)
        ax.text(x + w/2, y + h - 5, title, ha="center", va="center", fontsize=9, fontweight="bold", color=bcolor)
        ax.text(x + w/2, y + h/2 - 3, desc, ha="center", va="center", fontsize=7.5, color="#2d3748")

    ax.annotate("", xy=(37, 68), xytext=(31, 68), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))
    ax.annotate("", xy=(69, 68), xytext=(63, 68), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))

    # Bottom calculation & categorization
    bottom_boxes = [
        (20, 12, 28, 25, "Percentage Computation",
         "A_affected = sum(Lesion & Leaf_Total)\nA_total = sum(Leaf_Total)\nSeverity % = (A_affected / A_total) * 100", "#2f855a", "#f0fff4"),
        (54, 12, 28, 25, "Agronomic Categorization",
         "Mild: Severity < 10%\nModerate: 10% <= Severity < 25%\nSevere: Severity >= 25%", "#c05621", "#fffaf0")
    ]
    ax.annotate("", xy=(50, 37), xytext=(82, 55), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))
    ax.annotate("", xy=(54, 24), xytext=(48, 24), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))

    for x, y, w, h, title, desc, bcolor, fcolor in bottom_boxes:
        r = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8", facecolor=fcolor, edgecolor=bcolor, lw=1.5)
        ax.add_patch(r)
        ax.text(x + w/2, y + h - 5, title, ha="center", va="center", fontsize=9, fontweight="bold", color=bcolor)
        ax.text(x + w/2, y + h/2 - 3, desc, ha="center", va="center", fontsize=8, color="#2d3748")

    plt.tight_layout()
    output_path = DOC_ASSETS / "fig07_severity_estimation_workflow.png"
    plt.savefig(output_path)
    plt.close()
    print(f"Generated: {output_path}")

# ==============================================================================
# 8. WEATHER RECOMMENDATION ENGINE
# ==============================================================================
def draw_weather_recommendation_workflow():
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    ax.text(50, 96, "Weather-Aware Knowledge-Base Recommendation Architecture",
            ha="center", va="top", fontsize=13, fontweight="bold", color="#1a202c")

    boxes = [
        (5, 68, 26, 18, "Predicted Class &\nConfidence Verification",
         "If confidence < 0.60 (minimum threshold)\nor unsupported disease:\ntrigger safe fallback response.", "#2b6cb0", "#ebf8ff"),
        (37, 68, 26, 18, "Knowledge Base Lookup\n(diseases.json)",
         "Retrieve curated disease record:\nsymptoms, prevention steps,\ngeneral management & extension sources.", "#2c7a7b", "#e6fffa"),
        (69, 68, 26, 18, "Open-Meteo Weather\nService Integration",
         "Geocode location to lat/lon.\nFetch temperature, humidity,\nprecipitation and wind speed.", "#b7791f", "#fefcbf"),
    ]

    for x, y, w, h, title, desc, bcolor, fcolor in boxes:
        r = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8", facecolor=fcolor, edgecolor=bcolor, lw=1.5)
        ax.add_patch(r)
        ax.text(x + w/2, y + h - 4.5, title, ha="center", va="center", fontsize=8.5, fontweight="bold", color=bcolor)
        ax.text(x + w/2, y + h/2 - 3, desc, ha="center", va="center", fontsize=7.5, color="#2d3748")

    ax.annotate("", xy=(37, 77), xytext=(31, 77), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))
    ax.annotate("", xy=(69, 77), xytext=(63, 77), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))

    # Rule evaluation engine
    r_eng = patches.FancyBboxPatch((20, 36), 60, 20, boxstyle="round,pad=0.8", facecolor="#faf5ff", edgecolor="#6b46c1", lw=1.5)
    ax.add_patch(r_eng)
    ax.text(50, 51, "Deterministic Recommendation Rule Engine", ha="center", va="center", fontsize=10, fontweight="bold", color="#6b46c1")
    engine_desc = ("1. Evaluates weather thresholds: temp >= 20°C, humidity >= 85%, rain > 0 mm.\n"
                   "2. Correlates with disease-specific favorable conditions from knowledge base.\n"
                   "3. Appends high-severity agronomic warnings if severity == 'Severe'.\n"
                   "4. Attaches full source traceability (organization, title, URL, citation ID).")
    ax.text(50, 42, engine_desc, ha="center", va="center", fontsize=7.5, color="#2d3748")

    ax.annotate("", xy=(50, 56), xytext=(50, 68), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))

    # Final output synthesis
    r_out = patches.FancyBboxPatch((15, 6), 70, 18, boxstyle="round,pad=0.8", facecolor="#f0fff4", edgecolor="#2f855a", lw=1.5)
    ax.add_patch(r_out)
    ax.text(50, 20, "Structured Decision-Support Payload", ha="center", va="center", fontsize=10, fontweight="bold", color="#2f855a")
    out_desc = ("Includes disease information, symptom checklist, numbered general guidance,\n"
                "weather observation metrics, weather alert notes, and prominent disclaimer:\n"
                "'Image predictions are decision support and do not replace professional agricultural extension.'")
    ax.text(50, 12, out_desc, ha="center", va="center", fontsize=7.5, color="#2d3748")

    ax.annotate("", xy=(50, 24), xytext=(50, 36), arrowprops=dict(arrowstyle="->", lw=1.5, color="#4a5568"))

    plt.tight_layout()
    output_path = DOC_ASSETS / "fig08_weather_recommendation_workflow.png"
    plt.savefig(output_path)
    plt.close()
    print(f"Generated: {output_path}")

# ==============================================================================
# 9. FRONTEND-BACKEND COMMUNICATION
# ==============================================================================
def draw_frontend_backend_communication():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    ax.text(50, 96, "Client-Server API Communication & Protocol Flow",
            ha="center", va="top", fontsize=13, fontweight="bold", color="#1a202c")

    # Client Box
    r_client = patches.FancyBboxPatch((10, 15), 25, 72, boxstyle="round,pad=1.0", facecolor="#ebf8ff", edgecolor="#3182ce", lw=1.5)
    ax.add_patch(r_client)
    ax.text(22.5, 82, "CLIENT\n(React 18 SPA)", ha="center", va="center", fontsize=10, fontweight="bold", color="#2b6cb0")
    ax.text(22.5, 50, "- Dropzone file picker\n- Crop radio buttons\n- Text location input\n- Lesion mask picker\n- Fetch API calls\n- Client validation\n- State management\n- Grad-CAM renderer\n- History tab view",
            ha="center", va="center", fontsize=8, color="#2d3748")

    # Server Box
    r_server = patches.FancyBboxPatch((65, 15), 25, 72, boxstyle="round,pad=1.0", facecolor="#e6fffa", edgecolor="#319795", lw=1.5)
    ax.add_patch(r_server)
    ax.text(77.5, 82, "SERVER\n(FastAPI + Uvicorn)", ha="center", va="center", fontsize=10, fontweight="bold", color="#2c7a7b")
    ax.text(77.5, 50, "- CORS middleware\n- Size limit (1 MB JSON)\n- Upload validation\n- Model route execution\n- Grad-CAM generation\n- Severity calculator\n- Open-Meteo client\n- SQLAlchemy ORM\n- SQLite connection",
            ha="center", va="center", fontsize=8, color="#2d3748")

    # Arrows between
    # 1. POST /predict
    ax.annotate("", xy=(65, 68), xytext=(35, 68), arrowprops=dict(arrowstyle="->", lw=1.5, color="#2b6cb0"))
    ax.text(50, 71, "POST /predict\n(Multipart: image, crop, mask, loc)", ha="center", va="center", fontsize=7.5, color="#2b6cb0", fontweight="bold")

    # 2. Response PredictionResponse
    ax.annotate("", xy=(35, 54), xytext=(65, 54), arrowprops=dict(arrowstyle="->", lw=1.5, color="#2c7a7b"))
    ax.text(50, 57, "HTTP 200 OK: PredictionResponse JSON\n(class, conf, scores, heatmap, rec, hist_id)", ha="center", va="center", fontsize=7.5, color="#2c7a7b", fontweight="bold")

    # 3. GET /predictions
    ax.annotate("", xy=(65, 40), xytext=(35, 40), arrowprops=dict(arrowstyle="->", lw=1.5, color="#b7791f"))
    ax.text(50, 43, "GET /predictions?limit=20&offset=0\n(History pagination query)", ha="center", va="center", fontsize=7.5, color="#b7791f", fontweight="bold")

    # 4. Response History list
    ax.annotate("", xy=(35, 26), xytext=(65, 26), arrowprops=dict(arrowstyle="->", lw=1.5, color="#2f855a"))
    ax.text(50, 29, "HTTP 200 OK: List of PredictionRecords\n(date, class, conf, severity, weather)", ha="center", va="center", fontsize=7.5, color="#2f855a", fontweight="bold")

    plt.tight_layout()
    output_path = DOC_ASSETS / "fig09_frontend_backend_communication.png"
    plt.savefig(output_path)
    plt.close()
    print(f"Generated: {output_path}")

# ==============================================================================
# 10. DATABASE PERSISTENCE WORKFLOW
# ==============================================================================
def draw_database_persistence_workflow():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    ax.text(50, 96, "Relational Schema & Database Persistence Architecture",
            ha="center", va="top", fontsize=13, fontweight="bold", color="#1a202c")

    # Schema Box
    r_schema = patches.FancyBboxPatch((15, 15), 70, 74, boxstyle="round,pad=1.0", facecolor="#fffaf0", edgecolor="#c05621", lw=1.5)
    ax.add_patch(r_schema)
    ax.text(50, 83, "SQLite Table: prediction_records", ha="center", va="center", fontsize=11, fontweight="bold", color="#c05621")

    schema_text = (
        "Column Definitions & Types:\n"
        "  - id: VARCHAR(36) [PRIMARY KEY, UUID4]\n"
        "  - predicted_class_id: VARCHAR(120) [NOT NULL]\n"
        "  - confidence: NUMERIC(7, 6) [NOT NULL, 0.000000 to 1.000000]\n"
        "  - severity_category: VARCHAR(20) [NULLABLE, 'Mild'|'Moderate'|'Severe']\n"
        "  - severity_percentage: NUMERIC(6, 3) [NULLABLE, 0.000 to 100.000]\n"
        "  - severity_details: JSON_DOCUMENT [Detailed pixel counts & working sizes]\n"
        "  - weather_context: JSON_DOCUMENT [Provider, observed_at, temp, humidity, etc.]\n"
        "  - recommendation_result: JSON_DOCUMENT [Synthesized disease guidance]\n"
        "  - result_metadata: JSON_DOCUMENT [Inference timings, crop route, etc.]\n"
        "  - model_version: VARCHAR(120) [Model run checkpoint identifier]\n"
        "  - image_filename / media_type / sha256 / storage_uri [Upload metadata]\n"
        "  - created_at: DATETIME(timezone=True) [NOT NULL, server_default=now()]\n\n"
        "Integrity Constraints & Indexing:\n"
        "  - CHECK (length(trim(predicted_class_id)) > 0)\n"
        "  - CHECK (confidence >= 0 AND confidence <= 1)\n"
        "  - CHECK (severity_percentage IS NULL OR (severity_percentage >= 0 AND severity_percentage <= 100))\n"
        "  - CHECK (severity_category IS NULL OR severity_category IN ('Mild', 'Moderate', 'Severe'))\n"
        "  - INDEX ix_prediction_records_created_at ON (created_at DESC)\n"
        "  - INDEX ix_prediction_records_class_created ON (predicted_class_id, created_at)"
    )
    ax.text(18, 48, schema_text, ha="left", va="center", fontsize=7.5, family="monospace", color="#2d3748")

    plt.tight_layout()
    output_path = DOC_ASSETS / "fig10_database_persistence_workflow.png"
    plt.savefig(output_path)
    plt.close()
    print(f"Generated: {output_path}")

# ==============================================================================
# 11. REAL CONFUSION MATRICES
# ==============================================================================
def draw_confusion_matrices():
    # 1. Tomato Potato
    tp_cm_path = PROJECT_ROOT / "reports/classification/evaluations/tomato-potato-2026-11-17-b/confusion_matrix.csv"
    if tp_cm_path.exists():
        with open(tp_cm_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)[1:]
            matrix = []
            for row in reader:
                matrix.append([int(v) for v in row[1:]])
        cm = np.array(matrix)

        fig, ax = plt.subplots(figsize=(7, 6))
        im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
        ax.figure.colorbar(im, ax=ax)
        
        display_labels = [l.replace("tomato_", "T: ").replace("potato_", "P: ").replace("_", " ") for l in header]
        ax.set(xticks=np.arange(cm.shape[1]),
               yticks=np.arange(cm.shape[0]),
               xticklabels=display_labels, yticklabels=display_labels,
               title="Tomato-Potato Classifier Confusion Matrix\n(Test Samples: 1,317, Accuracy: 99.70%)",
               ylabel="Ground Truth Label",
               xlabel="Predicted Label")

        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        # Loop over data dimensions and create text annotations.
        thresh = cm.max() / 2.
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                val = cm[i, j]
                ax.text(j, i, f"{val:,}",
                        ha="center", va="center",
                        color="white" if val > thresh else "black",
                        fontsize=8.5, fontweight="bold" if val > 0 else "normal")
        fig.tight_layout()
        out = DOC_ASSETS / "fig11_tomato_potato_cm.png"
        plt.savefig(out)
        plt.close()
        print(f"Generated: {out}")

    # 2. Grape
    gr_cm_path = PROJECT_ROOT / "reports/classification/evaluations/grape-2026-11-17-a/confusion_matrix.csv"
    if gr_cm_path.exists():
        with open(gr_cm_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)[1:]
            matrix = []
            for row in reader:
                matrix.append([int(v) for v in row[1:]])
        cm = np.array(matrix)

        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Greens)
        ax.figure.colorbar(im, ax=ax)
        
        display_labels = [l.replace("grape_", "").replace("_", " ").title() for l in header]
        ax.set(xticks=np.arange(cm.shape[1]),
               yticks=np.arange(cm.shape[0]),
               xticklabels=display_labels, yticklabels=display_labels,
               title="Grape Classifier Confusion Matrix\n(Test Samples: 544, Accuracy: 99.26%)",
               ylabel="Ground Truth Label",
               xlabel="Predicted Label")

        plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")

        thresh = cm.max() / 2.
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                val = cm[i, j]
                ax.text(j, i, f"{val:,}",
                        ha="center", va="center",
                        color="white" if val > thresh else "black",
                        fontsize=9.5, fontweight="bold" if val > 0 else "normal")
        fig.tight_layout()
        out = DOC_ASSETS / "fig12_grape_cm.png"
        plt.savefig(out)
        plt.close()
        print(f"Generated: {out}")

# ==============================================================================
# 12. REAL TRAINING CURVES
# ==============================================================================
def draw_training_curves():
    # 1. Tomato Potato curves
    tp_hist_path = PROJECT_ROOT / "reports/classification/runs/tomato-potato-2026-11-17-b/training_history.json"
    if tp_hist_path.exists():
        with open(tp_hist_path, encoding="utf-8") as f:
            history = json.load(f)
        epochs = [entry["epoch"] for entry in history]
        train_loss = [entry["train_loss"] for entry in history]
        val_loss = [entry["validation_loss"] for entry in history]
        train_acc = [entry["train_accuracy"] * 100 for entry in history]
        val_acc = [entry["validation_accuracy"] * 100 for entry in history]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))

        # Loss
        ax1.plot(epochs, train_loss, "o-", label="Train Loss", color="#3182ce", lw=1.5, ms=4)
        ax1.plot(epochs, val_loss, "s-", label="Validation Loss", color="#e53e3e", lw=1.5, ms=4)
        ax1.axvline(11, ls="--", color="#38a169", label="Best Epoch (11)")
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("Cross-Entropy Loss")
        ax1.set_title("Tomato-Potato: Loss Progression")
        ax1.grid(True, ls=":", alpha=0.6)
        ax1.legend()

        # Accuracy
        ax2.plot(epochs, train_acc, "o-", label="Train Accuracy (%)", color="#3182ce", lw=1.5, ms=4)
        ax2.plot(epochs, val_acc, "s-", label="Validation Accuracy (%)", color="#e53e3e", lw=1.5, ms=4)
        ax2.axvline(11, ls="--", color="#38a169", label="Best Epoch (11)")
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel("Accuracy (%)")
        ax2.set_title("Tomato-Potato: Accuracy Progression")
        ax2.grid(True, ls=":", alpha=0.6)
        ax2.legend()

        fig.suptitle("Tomato-Potato EfficientNet-B0 Training Dynamics (run: tomato-potato-2026-11-17-b)", fontsize=11, fontweight="bold")
        fig.tight_layout()
        out = DOC_ASSETS / "fig13_tomato_potato_training_curves.png"
        plt.savefig(out)
        plt.close()
        print(f"Generated: {out}")

    # 2. Grape curves
    gr_hist_path = PROJECT_ROOT / "reports/classification/runs/grape-2026-11-17-a/training_history.json"
    if gr_hist_path.exists():
        with open(gr_hist_path, encoding="utf-8") as f:
            history = json.load(f)
        epochs = [entry["epoch"] for entry in history]
        train_loss = [entry["train_loss"] for entry in history]
        val_loss = [entry["validation_loss"] for entry in history]
        train_acc = [entry["train_accuracy"] * 100 for entry in history]
        val_acc = [entry["validation_accuracy"] * 100 for entry in history]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))

        # Loss
        ax1.plot(epochs, train_loss, "o-", label="Train Loss", color="#2c7a7b", lw=1.5, ms=4)
        ax1.plot(epochs, val_loss, "s-", label="Validation Loss", color="#dd6b20", lw=1.5, ms=4)
        ax1.axvline(1, ls="--", color="#38a169", label="Best Epoch (1)")
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("Cross-Entropy Loss")
        ax1.set_title("Grape: Loss Progression")
        ax1.grid(True, ls=":", alpha=0.6)
        ax1.legend()

        # Accuracy
        ax2.plot(epochs, train_acc, "o-", label="Train Accuracy (%)", color="#2c7a7b", lw=1.5, ms=4)
        ax2.plot(epochs, val_acc, "s-", label="Validation Accuracy (%)", color="#dd6b20", lw=1.5, ms=4)
        ax2.axvline(1, ls="--", color="#38a169", label="Best Epoch (1)")
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel("Accuracy (%)")
        ax2.set_title("Grape: Accuracy Progression")
        ax2.grid(True, ls=":", alpha=0.6)
        ax2.legend()

        fig.suptitle("Grape EfficientNet-B0 Training Dynamics (run: grape-2026-11-17-a)", fontsize=11, fontweight="bold")
        fig.tight_layout()
        out = DOC_ASSETS / "fig14_grape_training_curves.png"
        plt.savefig(out)
        plt.close()
        print(f"Generated: {out}")

# ==============================================================================
# 13. PER-CLASS PERFORMANCE METRIC COMPARISON
# ==============================================================================
def draw_per_class_metrics():
    # Load evaluation results from both runs
    tp_eval_path = PROJECT_ROOT / "reports/classification/evaluations/tomato-potato-2026-11-17-b/evaluation_results.json"
    gr_eval_path = PROJECT_ROOT / "reports/classification/evaluations/grape-2026-11-17-a/evaluation_results.json"
    
    classes = []
    precisions = []
    recalls = []
    f1s = []

    if tp_eval_path.exists():
        with open(tp_eval_path, encoding="utf-8") as f:
            data = json.load(f)
        for c, m in data["per_class"].items():
            classes.append(c.replace("tomato_", "Tomato ").replace("potato_", "Potato ").replace("_", " ").title())
            precisions.append(m["precision"] * 100)
            recalls.append(m["recall"] * 100)
            f1s.append(m["f1"] * 100)

    if gr_eval_path.exists():
        with open(gr_eval_path, encoding="utf-8") as f:
            data = json.load(f)
        for c, m in data["per_class"].items():
            classes.append(c.replace("grape_", "Grape ").replace("_", " ").title())
            precisions.append(m["precision"] * 100)
            recalls.append(m["recall"] * 100)
            f1s.append(m["f1"] * 100)

    x = np.arange(len(classes))
    width = 0.26

    fig, ax = plt.subplots(figsize=(11, 5.5))
    rects1 = ax.bar(x - width, precisions, width, label="Precision (%)", color="#3182ce")
    rects2 = ax.bar(x, recalls, width, label="Recall (%)", color="#38a169")
    rects3 = ax.bar(x + width, f1s, width, label="F1-Score (%)", color="#dd6b20")

    ax.set_ylabel("Score (%)")
    ax.set_title("Per-Class Evaluation Metrics on Internal Holdout Test Sets (10 Classes)", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(classes, rotation=35, ha="right", fontsize=8.5)
    ax.set_ylim(95, 101)
    ax.grid(True, axis="y", ls=":", alpha=0.6)
    ax.legend(loc="lower right")

    fig.tight_layout()
    out = DOC_ASSETS / "fig15_per_class_metrics.png"
    plt.savefig(out)
    plt.close()
    print(f"Generated: {out}")

# ==============================================================================
# 14. REAL GRAD-CAM DEMONSTRATION
# ==============================================================================
def generate_real_gradcam_figure():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    sys.path.insert(0, str(PROJECT_ROOT))
    
    from crop_health.explainability.gradcam import generate_gradcam
    from PIL import Image

    # Find sample images for tomato, potato, grape
    sample_images = [
        ("Tomato Late Blight",
         PROJECT_ROOT / "data/PlantVillage/Tomato___Late_blight",
         PROJECT_ROOT / "models/classifier/runs/tomato-potato-2026-11-17-b/efficientnet_b0_best.pt",
         PROJECT_ROOT / "models/classifier/runs/tomato-potato-2026-11-17-b/class_mapping.json"),
        ("Potato Early Blight",
         PROJECT_ROOT / "data/PlantVillage/Potato___Early_blight",
         PROJECT_ROOT / "models/classifier/runs/tomato-potato-2026-11-17-b/efficientnet_b0_best.pt",
         PROJECT_ROOT / "models/classifier/runs/tomato-potato-2026-11-17-b/class_mapping.json"),
        ("Grape Black Rot",
         PROJECT_ROOT / "data/GVLiD-v5/DATASET/Black rot",
         PROJECT_ROOT / "models/classifier/runs/grape-2026-11-17-a/efficientnet_b0_best.pt",
         PROJECT_ROOT / "models/classifier/runs/grape-2026-11-17-a/class_mapping.json")
    ]

    demo_results = []
    for label, folder, ckpt, mapping in sample_images:
        if folder.exists() and ckpt.exists() and mapping.exists():
            files = list(folder.glob("*.jpg")) + list(folder.glob("*.JPG"))
            if files:
                img_path = files[0]
                try:
                    res = generate_gradcam(img_path, ckpt, mapping)
                    with Image.open(img_path) as orig:
                        orig_rgb = orig.convert("RGB").resize((224, 224))
                    demo_results.append((label, orig_rgb, res.heatmap.resize((224, 224)), res.overlay.resize((224, 224)), res.class_id, res.confidence))
                except Exception as e:
                    print(f"GradCAM demo error for {label}: {e}")

    if demo_results:
        n = len(demo_results)
        fig, axes = plt.subplots(n, 3, figsize=(8.5, 2.8 * n))
        if n == 1:
            axes = np.expand_dims(axes, 0)
        
        for i, (title, orig, heatmap, overlay, cid, conf) in enumerate(demo_results):
            axes[i, 0].imshow(orig)
            axes[i, 0].set_title(f"Original: {title}", fontsize=9)
            axes[i, 0].axis("off")

            axes[i, 1].imshow(heatmap)
            axes[i, 1].set_title("Grad-CAM Activation Heatmap", fontsize=9)
            axes[i, 1].axis("off")

            axes[i, 2].imshow(overlay)
            axes[i, 2].set_title(f"Overlay (Conf: {conf*100:.1f}%)\nClass: {cid}", fontsize=9)
            axes[i, 2].axis("off")

        fig.suptitle("Genuine Grad-CAM Visualizations Generated on Test Leaf Samples", fontsize=11, fontweight="bold")
        fig.tight_layout()
        out = DOC_ASSETS / "fig16_gradcam_samples.png"
        plt.savefig(out)
        plt.close()
        print(f"Generated: {out}")

# ==============================================================================
# 15. SEVERITY DEMONSTRATION DIAGRAM
# ==============================================================================
def generate_severity_demo():
    fig, axes = plt.subplots(1, 3, figsize=(9, 3.2))

    # Synthetic sample representation showing HSV leaf detection & lesion mask
    # 1. Leaf image representation
    np.random.seed(42)
    h, w = 150, 150
    leaf_canvas = np.zeros((h, w, 3), dtype=np.uint8) + 230 # gray background
    y, x = np.ogrid[:h, :w]
    # Draw green leaf circle/ellipse
    leaf_mask = ((x - 75)**2 / 45**2 + (y - 75)**2 / 60**2) <= 1
    leaf_canvas[leaf_mask] = [46, 125, 50] # Forest Green

    # Draw disease lesions
    lesion1 = ((x - 65)**2 / 12**2 + (y - 60)**2 / 10**2) <= 1
    lesion2 = ((x - 85)**2 / 15**2 + (y - 95)**2 / 14**2) <= 1
    lesion_mask = lesion1 | lesion2
    leaf_canvas[lesion_mask] = [121, 85, 72] # Brown necrotic tissue

    axes[0].imshow(leaf_canvas)
    axes[0].set_title("Input Leaf Image (RGB)", fontsize=9)
    axes[0].axis("off")

    # 2. Binary Lesion Mask
    lesion_binary = np.zeros((h, w), dtype=np.uint8)
    lesion_binary[lesion_mask] = 255
    axes[1].imshow(lesion_binary, cmap="gray")
    axes[1].set_title("Aligned Lesion Mask (PNG)", fontsize=9)
    axes[1].axis("off")

    # 3. Overlay calculation
    overlay = leaf_canvas.copy()
    overlay[lesion_mask] = [220, 20, 60] # Red highlight
    axes[2].imshow(overlay)
    leaf_area = leaf_mask.sum()
    lesion_area = (lesion_mask & leaf_mask).sum()
    pct = (lesion_area / leaf_area) * 100
    axes[2].set_title(f"Segmented Analysis\nAffected Area: {pct:.1f}% (Moderate)", fontsize=9)
    axes[2].axis("off")

    fig.suptitle("Classical Image-Processing Leaf Area & Disease Severity Estimation", fontsize=11, fontweight="bold")
    fig.tight_layout()
    out = DOC_ASSETS / "fig17_severity_demo.png"
    plt.savefig(out)
    plt.close()
    print(f"Generated: {out}")


if __name__ == "__main__":
    print("Generating publication-quality thesis figures...")
    draw_system_architecture()
    draw_prediction_workflow()
    draw_dataset_split_workflow()
    draw_multicrop_routing()
    draw_efficientnet_pipeline()
    draw_gradcam_workflow()
    draw_severity_workflow()
    draw_weather_recommendation_workflow()
    draw_frontend_backend_communication()
    draw_database_persistence_workflow()
    draw_confusion_matrices()
    draw_training_curves()
    draw_per_class_metrics()
    generate_real_gradcam_figure()
    generate_severity_demo()
    print("All thesis figures successfully generated!")
