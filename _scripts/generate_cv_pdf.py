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

import os

import markdown
from weasyprint import CSS, HTML

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CV_MD_PATH = os.path.join(SCRIPT_DIR, "..", "_includes", "cv.md")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "static", "files", "CXHernandez_CV.pdf")

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
    # Read markdown content
    with open(CV_MD_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Convert markdown to HTML
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
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Generate PDF
    html_doc = HTML(string=full_html)
    css = CSS(string=CSS_STYLES)
    html_doc.write_pdf(OUTPUT_PATH, stylesheets=[css])

    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
