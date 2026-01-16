#!/usr/bin/env python3
"""
Generate PDF version of CV from markdown using WeasyPrint.

Usage:
    conda env create -f environment.yml
    conda activate cv_pdf
    python generate_cv_pdf.py

Output:
    ../static/files/CXHernandez_CV.pdf
"""

import logging
import sys
from pathlib import Path

import markdown
from weasyprint import CSS, HTML

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent.resolve()
CV_MD_PATH = SCRIPT_DIR / ".." / "_includes" / "cv.md"
OUTPUT_PATH = SCRIPT_DIR / ".." / "static" / "files" / "CXHernandez_CV.pdf"

CSS_STYLES = """
@page {
    size: letter;
    margin: 0.5in 0.6in;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 9pt;
    line-height: 1.45;
    color: #333;
}

/* Name */
h1 {
    font-size: 18pt;
    font-weight: 600;
    margin-bottom: 3pt;
    color: #000;
}

/* Section headers */
h2 {
    font-size: 10pt;
    font-weight: 600;
    color: #000;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1.5pt solid #000;
    padding-bottom: 3pt;
    margin-top: 12pt;
    margin-bottom: 6pt;
    page-break-after: avoid;
}

/* Company/school names */
h3 {
    font-size: 9.5pt;
    font-weight: 600;
    color: #000;
    margin-top: 8pt;
    margin-bottom: 1pt;
    page-break-after: avoid;
}

/* Subsection headers */
h4 {
    font-size: 8.5pt;
    font-weight: 600;
    color: #333;
    margin-top: 6pt;
    margin-bottom: 1pt;
    page-break-after: avoid;
}

p {
    font-size: 8.5pt;
    margin-bottom: 3pt;
    color: #333;
}

/* Role/degree styling */
p strong {
    font-weight: 600;
}

p em {
    font-style: italic;
    color: #555;
}

ul {
    margin: 3pt 0;
    padding-left: 14pt;
}

li {
    font-size: 8.5pt;
    margin-bottom: 2pt;
    color: #333;
}

a {
    color: #2a7ae2;
    text-decoration: none;
}

code {
    background-color: #f0f0f0;
    padding: 0 3pt;
    border-radius: 2pt;
    font-size: 7.5pt;
    color: #555;
    font-family: "SF Mono", Menlo, Monaco, monospace;
}

hr {
    border: none;
    border-top: 0.5pt solid #ccc;
    margin: 10pt 0;
}

/* Avoid page breaks inside list items and paragraphs */
li, p {
    page-break-inside: avoid;
}

/* Keep headers with following content */
h2, h3, h4 {
    page-break-after: avoid;
}
"""


def main():
    """Generate CV PDF from markdown source."""
    try:
        # Validate input file exists
        if not CV_MD_PATH.exists():
            logger.error(f"CV markdown file not found: {CV_MD_PATH}")
            sys.exit(1)

        logger.info(f"Reading CV from {CV_MD_PATH}")
        md_content = CV_MD_PATH.read_text(encoding="utf-8")

        if not md_content.strip():
            logger.error("CV markdown file is empty")
            sys.exit(1)

        # Convert markdown to HTML
        logger.info("Converting markdown to HTML")
        html_content = markdown.markdown(
            md_content,
            extensions=["extra", "smarty"],
        )

        # Wrap in full HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # Ensure output directory exists
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Generate PDF
        logger.info(f"Generating PDF at {OUTPUT_PATH}")
        html_doc = HTML(string=full_html)
        css = CSS(string=CSS_STYLES)
        html_doc.write_pdf(OUTPUT_PATH, stylesheets=[css])

        logger.info(f"Successfully generated PDF: {OUTPUT_PATH}")
        logger.info(f"PDF size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")

    except Exception as e:
        logger.error(f"Failed to generate CV PDF: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
