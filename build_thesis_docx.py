"""
build_thesis_docx.py
Compile CAPSTONE_THESIS_REPORT.md into a formatted DOCX.

Requirements:
    python-docx 1.2.0+   (pip install python-docx)
    lxml                  (installed as dependency)

Usage:
    C:\\Users\\ASUS\\miniconda3\\envs\\retail-forecast\\python.exe build_thesis_docx.py

Output:
    CROP_HEALTH_INTELLIGENCE_CAPSTONE_REPORT.docx
"""

from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    from docx.shared import Inches, Pt, RGBColor, Cm
except ImportError:
    print("ERROR: python-docx is not installed. Run: pip install python-docx", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent
MD_FILE = PROJECT_ROOT / "CAPSTONE_THESIS_REPORT.md"
OUT_FILE = PROJECT_ROOT / "CROP_HEALTH_INTELLIGENCE_CAPSTONE_REPORT.docx"
DOC_ASSETS = PROJECT_ROOT / "doc_assets"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def set_margins(doc: Document,
                top: float = 2.54, bottom: float = 2.54,
                left: float = 3.17, right: float = 2.54) -> None:
    """Set A4 page size (21.0 x 29.7 cm) and margins in centimetres. Left=1.25in≈3.17cm per VIT-AP template."""
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(top)
        section.bottom_margin = Cm(bottom)
        section.left_margin = Cm(left)
        section.right_margin = Cm(right)


def apply_body_style(paragraph, bold: bool = False, italic: bool = False,
                     font_size: int = 12, color: RGBColor | None = None) -> None:
    """Apply Times New Roman 12pt body formatting to a paragraph's runs."""
    for run in paragraph.runs:
        run.font.name = "Times New Roman"
        run.font.size = Pt(font_size)
        if bold:
            run.font.bold = True
        if italic:
            run.font.italic = True
        if color:
            run.font.color.rgb = color


def add_heading(doc: Document, text: str, level: int) -> None:
    """Add a heading with Times New Roman styling."""
    sizes = {1: 16, 2: 14, 3: 13, 4: 12}
    p = doc.add_heading(text, level=level)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in p.runs:
        run.font.name = "Times New Roman"
        run.font.size = Pt(sizes.get(level, 12))
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)


def add_body_paragraph(doc: Document, text: str,
                       bold: bool = False, italic: bool = False,
                       alignment: WD_ALIGN_PARAGRAPH = WD_ALIGN_PARAGRAPH.JUSTIFY) -> None:
    """Add a body paragraph with Times New Roman 12pt."""
    p = doc.add_paragraph()
    p.alignment = alignment
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    run.font.bold = bold
    run.font.italic = italic


def add_figure(doc: Document, image_path: Path, caption: str) -> None:
    """Add a figure with a centred image and caption."""
    if not image_path.exists():
        add_body_paragraph(doc, f"[Figure not found: {image_path.name}]", italic=True)
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p_img.add_run()
    # Fit within 15cm width (stays within margins on A4)
    run.add_picture(str(image_path), width=Cm(14))
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_cap = p_cap.add_run(caption)
    run_cap.font.name = "Times New Roman"
    run_cap.font.size = Pt(10)
    run_cap.font.italic = True


def add_table_from_rows(doc: Document, headers: list[str],
                        rows: list[list[str]]) -> None:
    """Add a simple bordered table."""
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    hdr_row = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.text = h
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(10)
    for row_data in rows:
        row = table.add_row()
        for i, val in enumerate(row_data):
            cell = row.cells[i]
            cell.text = val
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(10)
    doc.add_paragraph()  # spacing


def add_code_block(doc: Document, code: str) -> None:
    """Add a code block in Courier New 9pt."""
    for line in code.split("\n"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(line or " ")
        run.font.name = "Courier New"
        run.font.size = Pt(9)
        # Light grey background via paragraph shading
        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "F5F5F5")
        pPr.append(shd)


def add_page_break(doc: Document) -> None:
    doc.add_page_break()


# ---------------------------------------------------------------------------
# Figure reference map
# ---------------------------------------------------------------------------

FIGURE_MAP: dict[str, str] = {
    "fig01_overall_architecture.png": "Figure 1 — Overall System Architecture",
    "fig02_prediction_workflow.png": "Figure 2 — End-to-End Prediction Workflow",
    "fig03_dataset_split_workflow.png": "Figure 3 — Dataset Split Methodology",
    "fig04_multicrop_routing.png": "Figure 4 — Multi-Crop Routing Logic",
    "fig05_efficientnet_pipeline.png": "Figure 5 — EfficientNet-B0 Inference Pipeline",
    "fig06_gradcam_workflow.png": "Figure 6 — Grad-CAM Generation Workflow",
    "fig07_severity_estimation_workflow.png": "Figure 7 — Severity Estimation Workflow",
    "fig08_weather_recommendation_workflow.png": "Figure 8 — Weather and Recommendation Pipeline",
    "fig09_frontend_backend_communication.png": "Figure 9 — Frontend–Backend Communication",
    "fig10_database_persistence_workflow.png": "Figure 10 — Database Persistence Workflow",
    "fig11_tomato_potato_cm.png": "Figure 11 — Tomato–Potato Confusion Matrix",
    "fig12_grape_cm.png": "Figure 12 — Grape Confusion Matrix",
    "fig13_tomato_potato_training_curves.png": "Figure 13 — Tomato–Potato Training Curves",
    "fig14_grape_training_curves.png": "Figure 14 — Grape Training Curves",
    "fig15_per_class_metrics.png": "Figure 15 — Per-Class Precision, Recall, and F1 Scores",
    "fig16_gradcam_samples.png": "Figure 16 — Grad-CAM Overlay Samples",
    "fig17_severity_demo.png": "Figure 17 — Severity Estimation Demo",
    "screenshots/01_dashboard.png": "Figure 18 — Application Dashboard and Crop Selector",
    "screenshots/02_image_upload.png": "Figure 19 — Leaf Image Upload with Preview",
    "screenshots/03_prediction_results.png": "Figure 20 — Prediction Results",
    "screenshots/04_gradcam_visualization.png": "Figure 21 — Grad-CAM Heatmap and Overlay",
    "screenshots/05_disease_recommendations.png": "Figure 22 — Disease Recommendations and Guidance",
    "screenshots/06_prediction_history.png": "Figure 23 — Prediction History View",
    "01_dashboard.png": "Figure 18 — Application Dashboard and Crop Selector",
    "02_image_upload.png": "Figure 19 — Leaf Image Upload with Preview",
    "03_prediction_results.png": "Figure 20 — Prediction Results",
    "04_gradcam_visualization.png": "Figure 21 — Grad-CAM Heatmap and Overlay",
    "05_disease_recommendations.png": "Figure 22 — Disease Recommendations and Guidance",
    "06_prediction_history.png": "Figure 23 — Prediction History View",
}

# ---------------------------------------------------------------------------
# Markdown parser (line-by-line, good-enough for this document)
# ---------------------------------------------------------------------------

def parse_and_build(doc: Document, md_path: Path) -> None:  # noqa: C901
    lines = md_path.read_text(encoding="utf-8").splitlines()

    in_code_block = False
    code_lines: list[str] = []
    in_table = False
    table_rows: list[list[str]] = []
    table_header: list[str] = []
    skip_lines: set[int] = set()

    i = 0
    while i < len(lines):
        line = lines[i]

        # --- Code block fence ---
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                add_code_block(doc, "\n".join(code_lines))
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # --- Table ---
        if line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if not table_header:
                table_header = cells
            elif all(re.match(r"^[-:]+$", c) for c in cells):
                pass  # separator row
            else:
                table_rows.append(cells)
            # Check if next line is still a table
            if i + 1 < len(lines) and lines[i + 1].startswith("|"):
                i += 1
                continue
            else:
                # Flush table
                if table_header and table_rows:
                    add_table_from_rows(doc, table_header, table_rows)
                table_header = []
                table_rows = []
                i += 1
                continue

        # Flush table if we exit
        if table_header and table_rows and not line.startswith("|"):
            add_table_from_rows(doc, table_header, table_rows)
            table_header = []
            table_rows = []

        # --- Horizontal rule ---
        if re.match(r"^-{3,}$", line.strip()):
            doc.add_paragraph("─" * 60)
            i += 1
            continue

        # --- Page break trigger (after major sections) ---
        if re.match(r"^## Chapter \d+", line) or re.match(r"^## Biodata", line):
            add_page_break(doc)

        # --- Redundant figure title preceding an image line ---
        if re.match(r"^\*\*Figure\s+\d+.*?\*\*\s*$", line.strip()):
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and lines[j].strip().startswith("!["):
                i += 1
                continue

        # --- Headings ---
        m_h = re.match(r"^(#{1,4})\s+(.*)", line)
        if m_h:
            level = len(m_h.group(1))
            text = m_h.group(2).strip()
            # Strip markdown links from heading text
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
            add_heading(doc, text, min(level, 4))
            i += 1
            continue

        # --- Figure image lines ---
        m_fig = re.match(r"!\[([^\]]*)\]\(doc_assets/([^)]+)\)", line)
        if m_fig:
            alt_text = m_fig.group(1)
            filename = m_fig.group(2)
            img_path = DOC_ASSETS / filename
            caption = FIGURE_MAP.get(filename, FIGURE_MAP.get(Path(filename).name, alt_text or filename))
            add_figure(doc, img_path, caption)
            i += 1
            continue

        # --- Blank line ---
        if line.strip() == "" or line.strip() == "&nbsp;":
            doc.add_paragraph()
            i += 1
            continue

        # --- LaTeX / math lines (simplify) ---
        line_text = re.sub(r"\$\$(.+?)\$\$", r"[\1]", line)
        line_text = re.sub(r"\$(.+?)\$", r"[\1]", line_text)

        # --- Bullet / list items ---
        m_bullet = re.match(r"^(\s*)[-*]\s+(.*)", line_text)
        if m_bullet:
            indent = len(m_bullet.group(1)) // 2
            text = m_bullet.group(2).strip()
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
            text = re.sub(r"\*(.+?)\*", r"\1", text)
            text = re.sub(r"`(.+?)`", r"\1", text)
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
            p = doc.add_paragraph(style="List Bullet")
            run = p.add_run(text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
            i += 1
            continue

        # --- Numbered list ---
        m_num = re.match(r"^(\s*)\d+\.\s+(.*)", line_text)
        if m_num:
            text = m_num.group(2).strip()
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
            text = re.sub(r"`(.+?)`", r"\1", text)
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
            p = doc.add_paragraph(style="List Number")
            run = p.add_run(text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
            i += 1
            continue

        # --- Block quote ---
        m_bq = re.match(r"^>\s*(.*)", line_text)
        if m_bq:
            text = m_bq.group(1).strip()
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
            text = re.sub(r"`(.+?)`", r"\1", text)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
            i += 1
            continue

        # --- Regular paragraph ---
        # Strip inline markdown
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", line_text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = text.strip()

        if text:
            bold = line.startswith("**") and line.endswith("**")
            add_body_paragraph(doc, text, bold=bold)

        i += 1


# ---------------------------------------------------------------------------
# Title page builder
# ---------------------------------------------------------------------------

def build_title_page(doc: Document) -> None:
    """Add a formatted VIT-AP-style title page."""
    doc.add_paragraph()
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("AI-POWERED CROP HEALTH INTELLIGENCE SYSTEM")
    r.font.name = "Times New Roman"
    r.font.size = Pt(16)
    r.font.bold = True

    doc.add_paragraph()
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = sub.add_run("A Capstone Project Report\nsubmitted in partial fulfillment of the requirements for the degree of")
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)

    doc.add_paragraph()
    deg = doc.add_paragraph()
    deg.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = deg.add_run("Bachelor of Technology\nin\nComputer Science and Engineering")
    r3.font.name = "Times New Roman"
    r3.font.size = Pt(13)
    r3.font.bold = True

    doc.add_paragraph()
    byp = doc.add_paragraph()
    byp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r4 = byp.add_run("by\n\nNayanah Soju\nRegistration Number: [PLACEHOLDER]")
    r4.font.name = "Times New Roman"
    r4.font.size = Pt(12)

    doc.add_paragraph()
    guide = doc.add_paragraph()
    guide.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r5 = guide.add_run(
        "Under the guidance of\n[PLACEHOLDER – Project Guide Name]\n[PLACEHOLDER – Designation, Department]"
    )
    r5.font.name = "Times New Roman"
    r5.font.size = Pt(12)

    doc.add_paragraph()
    uni = doc.add_paragraph()
    uni.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r6 = uni.add_run(
        "SCHOOL OF COMPUTER SCIENCE AND ENGINEERING\n"
        "VIT-AP UNIVERSITY\n"
        "Amaravati, Andhra Pradesh — 522 237\n"
        "November 2026"
    )
    r6.font.name = "Times New Roman"
    r6.font.size = Pt(13)
    r6.font.bold = True

    add_page_break(doc)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not MD_FILE.exists():
        print(f"ERROR: Markdown source not found: {MD_FILE}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading: {MD_FILE}")
    doc = Document()

    # Page setup
    set_margins(doc, top=2.54, bottom=2.54, left=3.17, right=2.54)

    # Default paragraph style
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)

    # Title page (first)
    build_title_page(doc)

    # Parse and add all content from the Markdown file
    parse_and_build(doc, MD_FILE)

    # Add page numbers to footer
    for section in doc.sections:
        footer = section.footer
        p = footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.clear()
        run = p.add_run()
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)
        # Insert page number field
        fldChar1 = OxmlElement("w:fldChar")
        fldChar1.set(qn("w:fldCharType"), "begin")
        instrText = OxmlElement("w:instrText")
        instrText.text = " PAGE "
        fldChar2 = OxmlElement("w:fldChar")
        fldChar2.set(qn("w:fldCharType"), "end")
        run._r.append(fldChar1)
        run._r.append(instrText)
        run._r.append(fldChar2)

    doc.save(str(OUT_FILE))
    print(f"DOCX saved: {OUT_FILE}")
    print(f"File size: {OUT_FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
