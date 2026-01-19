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
│   ├── cli.py          # Consolidated CLI tool
│   ├── environment.yml # Conda environment config
│   └── README.md       # Scripts documentation
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
  → cli.py scrape-pubs (fetches from Semantic Scholar API)
    → Filters and sorts by citations and year
    → Outputs to _includes/publications.md
      → Rendered in Publications section via custom markdown tag
        → DataTables.js provides interactive table
```

### CV Pipeline

```
_includes/cv.md (markdown source)
  → cli.py update-cv (updates citations and GitHub stats)
    → Fetches citation counts from Semantic Scholar API
    → Fetches repository stats from GitHub API
    → Updates cv.md with latest data
  → cli.py generate-pdf (Python + WeasyPrint)
    → Converts markdown → HTML → PDF
      → static/files/CXHernandez_CV.pdf
        → Accessible via modal in navigation
```

### Store Pipeline

```
inventory.json
  → cli.py enrich-inventory (optional: fetches from Square API)
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
   python _scripts/cli.py scrape-pubs -a 39400763 -o _includes/publications.md

   # Update CV with latest citations and GitHub stats
   python _scripts/cli.py update-cv -c _includes/cv.md

   # Generate CV PDF
   python _scripts/cli.py generate-pdf

   # Enrich store inventory (requires Square credentials)
   python _scripts/cli.py enrich-inventory static/files/store/inventory.json
   ```

   See [_scripts/README.md](_scripts/README.md) for detailed documentation on all CLI commands.

3. **Build TypeScript**:
   ```bash
   # Set store password (optional - if not set, store will have open access)
   export STORE_PASSWORD="your_password_here"

   # Production build
   npm run build

   # Development build with source maps
   npm run build:dev

   # Watch mode for development
   npm run watch
   ```

   **Notes**:
   - The `STORE_PASSWORD` environment variable is hashed at build time and injected into the bundle
   - If `STORE_PASSWORD` is not set, the build will succeed with a warning and the store will be accessible without password protection (useful for local development)
   - Never commit the plain password to the repository

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
2. Fetch publications from Semantic Scholar API
3. Update CV with citation counts and GitHub repository stats
4. Generate CV PDF from markdown
5. Enrich store inventory (optional)
6. Install npm dependencies and build TypeScript
7. Build Jekyll site with UTF-8 support
8. Deploy to GitHub Pages (on master push only)

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

All automation is handled through a unified CLI tool: [_scripts/cli.py](_scripts/cli.py)

See [_scripts/README.md](_scripts/README.md) for complete documentation.

### Quick Reference

```bash
# Fetch publications from Semantic Scholar
python _scripts/cli.py scrape-pubs -a 39400763 -o _includes/publications.md

# Update CV with citations and GitHub stats
python _scripts/cli.py update-cv -c _includes/cv.md

# Generate CV PDF
python _scripts/cli.py generate-pdf

# Enrich store inventory
python _scripts/cli.py enrich-inventory static/files/store/inventory.json
```

**Features**:
- **scrape-pubs**: Fetches publications from Semantic Scholar API
  - Automatic venue detection and filtering
  - Sorts by citation count and year
  - Multiple output formats (HTML, JSON, LaTeX, tab-separated)

- **update-cv**: Updates CV with latest metrics
  - Fetches citation counts from Semantic Scholar API
  - Fetches repository stats (stars, forks) from GitHub API
  - Updates in-place while preserving formatting

- **generate-pdf**: Converts CV to PDF
  - Markdown → HTML → PDF pipeline via WeasyPrint
  - Professional styling with page break optimization

- **enrich-inventory**: Enriches store inventory
  - Queries Square Checkout links or scrapes checkout pages
  - Updates pricing and product details
  - Graceful error handling

## Configuration

### GitHub Secrets

The following secrets should be configured in your GitHub repository for production deployment:

**Optional Secrets:**
- `STORE_PASSWORD`: The plain-text password for the photography store. This is hashed at build time and injected into the password-verification bundle.

**How to add secrets:**
1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add `STORE_PASSWORD` with your chosen password value

The secret is automatically used in the GitHub Actions workflow during the TypeScript build step.

**⚠️ Important**: If `STORE_PASSWORD` is not set, the build will succeed with a warning, but the store will be accessible **without password protection**. This is useful for local development but should be avoided in production.

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

- **Password-protected store** with SHA-256 hashing
  - Plain password stored in GitHub Secrets (never committed to repository)
  - Hashed at build time and injected into bundle via webpack DefinePlugin
  - Zero plain-text passwords in source code or version control
- **XSS prevention** via HTML escaping
- **Square Checkout iframe sandboxing** with CSP-style domain whitelisting
- **SessionStorage** (not localStorage) for temporary access tokens
- **Input validation and sanitization** throughout forms

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

The store password is managed securely through environment variables:

1. **For GitHub Actions**: Set the `STORE_PASSWORD` secret in your repository settings (Settings → Secrets and variables → Actions → New repository secret)
2. **For local development**: Set `export STORE_PASSWORD="your_password"` before building TypeScript
3. The password is SHA-256 hashed at build time by [generate-password-hash.js](_typescript/generate-password-hash.js)
4. The hash is injected into the bundle via webpack's DefinePlugin (see [webpack.config.js](_typescript/webpack.config.js))

**Never commit the plain password or hash to the repository.** The password is injected at build time from the environment.

**Missing Password Behavior:**
- If `STORE_PASSWORD` is not set during build, you'll see a warning: `⚠️ WARNING: STORE_PASSWORD environment variable is not set`
- The build will succeed, but the store will be in **OPEN ACCESS mode** (no password protection)
- The browser console will show: `Store is running in OPEN ACCESS mode (no password protection)`
- This is useful for local development but should be avoided in production deployments

## License

Personal website - All rights reserved.
