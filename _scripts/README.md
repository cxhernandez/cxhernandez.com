# Scripts

Consolidated CLI tool for managing the cxhernandez.com website.

## Installation

Install dependencies:

```bash
conda env create -f environment.yml
conda activate cv_pdf
```

Or using pip:

```bash
pip install pandas requests weasyprint markdown
```

## Usage

The `cli.py` script provides multiple commands via subcommands:

### 1. Enrich Inventory

Enrich inventory.json entries by querying Square payment links.

```bash
python cli.py enrich-inventory static/files/store/inventory.json
```

**Environment variables:**
- `SQUARE_ACCESS_TOKEN` - Square API access token (optional)
- `SQUARE_ENVIRONMENT` - `sandbox` or `production` (default: sandbox)

If no API token is provided, the script will scrape checkout pages directly.

### 2. Scrape Publications

Fetch publication data from Semantic Scholar API.

```bash
python cli.py scrape-pubs -a <author-id> -o publications.txt -f html
```

**Options:**
- `-a, --author` - Semantic Scholar Author ID (required)
- `-o, --output` - Output file path (default: ./publications.txt)
- `-f, --format` - Output format: html, json, latex, or tab (default: html)

**Example:**
```bash
python cli.py scrape-pubs -a 2722763 -o ../static/publications.html -f html
```

### 3. Update CV

Update CV with latest citation counts and GitHub repository stats.

```bash
python cli.py update-cv -c _includes/cv.md
```

**Options:**
- `-c, --cv-path` - Path to CV markdown file (default: _includes/cv.md)

This command:
1. Fetches citation counts for papers from Semantic Scholar API
2. Fetches GitHub repository stats (stars, forks) from GitHub API
3. Updates the CV markdown file with the latest data

### 4. Generate PDF

Generate PDF version of CV from markdown using WeasyPrint.

```bash
python cli.py generate-pdf
```

**Options:**
- `-c, --cv-path` - Path to CV markdown file (default: ../_includes/cv.md)
- `-o, --output` - Output PDF path (default: ../static/files/CXHernandez_CV.pdf)

**Example:**
```bash
python cli.py generate-pdf -c ../_includes/cv.md -o ../static/files/CV.pdf
```

## Dependencies

- **All commands**: Python 3.10+
- **enrich-inventory**: No external dependencies (uses stdlib)
- **scrape-pubs**: pandas, requests
- **update-cv**: requests
- **generate-pdf**: markdown, weasyprint

## Migrating from Old Scripts

The following old scripts have been consolidated into `cli.py`:

| Old Script | New Command |
|------------|-------------|
| `enrich_inventory.py <file>` | `cli.py enrich-inventory <file>` |
| `semantic_scholar_scraper.py -a <id> -o <out>` | `cli.py scrape-pubs -a <id> -o <out>` |
| `update_cv.py -c <cv>` | `cli.py update-cv -c <cv>` |
| `generate_cv_pdf.py` | `cli.py generate-pdf` |

The old scripts can be kept for backward compatibility or removed once you've migrated to the new CLI.
