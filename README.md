# cxhernandez.com

[![Build Status](https://github.com/cxhernandez/cxhernandez.com/actions/workflows/jekyll-docker.yml/badge.svg)](https://github.com/cxhernandez/cxhernandez.com/actions/workflows/jekyll-docker.yml)

Personal portfolio website for Carlos Xavier Hernández, featuring automated publication tracking, CV generation, and an integrated e-commerce store.

## Overview

This is a sophisticated personal website that combines static site generation with modern automation and e-commerce capabilities. The site automatically updates publications daily from Semantic Scholar, generates PDFs from markdown, and includes a password-protected photography store with Square payment integration.

### Key Features

- **About Section**: Personal bio and profile
- **Publications**: Automatically synced from Semantic Scholar API with searchable/sortable DataTables
- **Software**: Project showcase and contributions
- **Photography**: Portfolio gallery with integrated e-commerce store
- **Automated CV**: Markdown-to-PDF generation pipeline
- **Password-Protected Store**: Square payment integration with inventory management

## Architecture

### Technology Stack

- **Static Site Generator**: Jekyll (Ruby) with custom plugins
- **Frontend**: TypeScript + Webpack for bundling
- **Styling**: SCSS with Bootstrap 3
- **Backend Automation**: Python scripts for data aggregation and document generation
- **CI/CD**: GitHub Actions with automated deployment to GitHub Pages
- **E-commerce**: Square Checkout iframe integration
- **Data Source**: Semantic Scholar API for publications

### Directory Structure

```
cxhernandez.com/
├── _includes/          # Content sections (About, Publications, CV, etc.)
├── _layouts/           # HTML templates (default.html, main.html)
├── _typescript/        # TypeScript source with webpack config
│   └── src/           # main.ts, password-verification.ts
├── _sass/             # SCSS stylesheets
├── _scripts/          # Python automation scripts
│   ├── semantic_scholar_scraper.py
│   ├── generate_cv_pdf.py
│   └── enrich_inventory.py
├── _plugins/          # Jekyll custom plugins (markdown processor)
├── static/
│   ├── css/           # Compiled CSS output
│   ├── js/dist/       # Webpack bundle output
│   ├── files/         # CV PDF, inventory JSON
│   └── images/        # Static assets
├── .github/workflows/ # CI/CD pipeline
└── _site/             # Generated static site (build output)
```

## Data Flow

### Publication Pipeline

```
GitHub Actions (daily schedule)
  → semantic_scholar_scraper.py (fetches from Semantic Scholar API)
    → Filters and sorts by citations and year
    → Outputs to _includes/publications.md
      → Rendered in Publications section via custom markdown tag
        → DataTables.js provides interactive table
```

### CV Pipeline

```
_includes/cv.md (markdown source)
  → generate_cv_pdf.py (Python + WeasyPrint)
    → Converts markdown → HTML → PDF
      → static/files/CXHernandez_CV.pdf
        → Accessible via modal in navigation
```

### Store Pipeline

```
inventory.json
  → enrich_inventory.py (optional: fetches from Square API)
    → store.html JavaScript renders product cards
      → Square iframe checkout on product click
```

## Development

This site uses Jekyll for static site generation and TypeScript for client-side JavaScript.

### Prerequisites

- Ruby (with Bundler)
- Node.js (with npm)
- Python 3.10+ (with Conda)

### Quick Start

1. **Install dependencies**:
   ```bash
   # Ruby/Jekyll dependencies
   bundle install

   # Node.js dependencies
   npm ci

   # Python dependencies
   conda env create -f _scripts/environment.yml
   conda activate cxhernandez-web
   ```

2. **Run automation scripts** (optional):
   ```bash
   # Update publications from Semantic Scholar
   python _scripts/semantic_scholar_scraper.py -a 39400763 -o _includes/publications.md

   # Generate CV PDF
   python _scripts/generate_cv_pdf.py

   # Enrich store inventory (requires Square credentials)
   python _scripts/enrich_inventory.py static/files/store/inventory.json
   ```

3. **Build TypeScript**:
   ```bash
   # Production build
   npm run build

   # Development build with source maps
   npm run build:dev

   # Watch mode for development
   npm run watch
   ```

4. **Run Jekyll development server**:
   ```bash
   LANG=en_US.UTF-8 bundle exec jekyll serve
   ```

   The site will be available at `http://localhost:4000`

### TypeScript Development

- TypeScript source files are in [_typescript/src/](_typescript/src/)
- Build with `npm run build` before running Jekyll
- See [TYPESCRIPT.md](TYPESCRIPT.md) for detailed build documentation

**Main TypeScript modules**:
- [main.ts](_typescript/src/main.ts): Core site interactivity (navigation, modals, carousel)
- [password-verification.ts](_typescript/src/password-verification.ts): Store password protection

## Build & Deployment

### GitHub Actions Workflow

The site uses automated CI/CD via [.github/workflows/jekyll-docker.yml](.github/workflows/jekyll-docker.yml):

**Triggers**:
- Push to `master` branch
- Pull requests to `master`
- Daily scheduled run at 00:00 UTC (for publication updates)

**Build Steps**:
1. Setup Conda environment
2. Run Python automation scripts (publications, CV, inventory)
3. Install npm dependencies and build TypeScript
4. Build Jekyll site with UTF-8 support
5. Deploy to GitHub Pages (on master push only)

**Deployment URL**: https://cxhernandez.com

### Manual Build

```bash
# Full production build
LANG=en_US.UTF-8 bundle exec jekyll build --future

# Output in _site/ directory
```

## Key Components

### Frontend Interactivity ([main.ts](_typescript/src/main.ts))

- Smooth scroll navigation with navbar offset calculation
- Mobile navigation toggle
- CV modal display with scroll locking
- Portfolio carousel with AJAX loading
- DataTables integration for publications
- Responsive design with touch event handling

### Password Protection ([password-verification.ts](_typescript/src/password-verification.ts))

- SHA-256 password hashing (Web Crypto API)
- SessionStorage persistence
- XSS prevention via HTML escaping
- Animated transitions between password gate and store

### Styling

- SCSS with Bootstrap 3 overrides
- Responsive design with mobile breakpoints
- Dark mode skin support
- Skeleton loading states for async content

## Automation Scripts

### semantic_scholar_scraper.py

Fetches publications from Semantic Scholar API for author ID 39400763.

**Features**:
- Automatic venue detection
- Filters out conference abstracts and Zenodo releases
- Sorts by citation count and year
- Title case conversion
- Generates HTML table in markdown format

**Usage**:
```bash
python _scripts/semantic_scholar_scraper.py -a 39400763 -o _includes/publications.md
```

### generate_cv_pdf.py

Converts CV from markdown to professionally styled PDF.

**Features**:
- Markdown → HTML → PDF pipeline
- WeasyPrint rendering with custom styling
- Single source of truth in [_includes/cv.md](_includes/cv.md)

**Usage**:
```bash
python _scripts/generate_cv_pdf.py
```

### enrich_inventory.py

Enriches store inventory with data from Square API.

**Features**:
- Queries Square Checkout links
- Scrapes pricing and product details
- Updates [inventory.json](static/files/store/inventory.json)
- Graceful error handling

**Usage**:
```bash
python _scripts/enrich_inventory.py static/files/store/inventory.json
```

## Configuration

### Jekyll Configuration ([_config.yml](_config.yml))

- Site metadata (title, description, author)
- Navigation sections: About, Publications, Software, Photography
- Build settings and plugin configuration
- Exclusions for build optimization

### Webpack Configuration ([_typescript/webpack.config.js](_typescript/webpack.config.js))

- Entry points: main.ts, password-verification.ts
- TypeScript compilation via ts-loader
- Production minification
- Source map generation for development

## Dependencies

### Ruby (Jekyll)
- jekyll >= 4.4.1
- rouge (syntax highlighting)
- webrick (development server)

### Node.js (TypeScript/Webpack)
- typescript ^5.9.3
- webpack ^5.104.1
- ts-loader ^9.5.4

### Python (Automation)
- pandas (data processing)
- requests (API calls)
- markdown (CV conversion)
- weasyprint (PDF generation)

### Frontend Libraries (CDN)
- jQuery 3.7.1
- Bootstrap 3.4.1
- DataTables 1.10.6
- Flexslider 2.1
- Lightbox2 2.11.4
- Font Awesome 4.7.0

## Security Features

- Password-protected store with SHA-256 hashing
- XSS prevention via HTML escaping
- Square Checkout iframe sandboxing
- SessionStorage (not localStorage) for temporary access
- Input validation and sanitization

## Performance Optimizations

- Webpack minification for production bundles
- Lazy loading for store images
- Skeleton loading states
- Deferred script loading
- Static site generation for fast page loads

## Troubleshooting

### UTF-8 Encoding Issues
Always use `LANG=en_US.UTF-8` when building Jekyll to support emojis and special characters:
```bash
LANG=en_US.UTF-8 bundle exec jekyll serve
```

### TypeScript Build Errors
Ensure TypeScript is built before running Jekyll:
```bash
npm run build
```

### Publication Fetch Failures
The workflow continues on error if Semantic Scholar API is unavailable. Check logs in GitHub Actions for warnings.

### Store Password Issues
Password is hashed with SHA-256. Update the expected hash in [password-verification.ts](_typescript/src/password-verification.ts) if changing the password.

## License

Personal website - All rights reserved.
