# cxhernandez.com

[![Build Status](https://github.com/cxhernandez/cxhernandez.com/actions/workflows/jekyll-docker.yml/badge.svg)](https://github.com/cxhernandez/cxhernandez.com/actions/workflows/jekyll-docker.yml)

Personal portfolio website for Carlos Xavier Hernández, featuring automated publication tracking, CV generation, and an integrated e-commerce store.

**Live Site**: https://cxhernandez.com

## Features

- 📄 **Publications**: Auto-synced from Semantic Scholar API with searchable tables
- 💼 **CV**: Markdown-to-PDF generation with automated citation counts
- 💻 **Software**: Project showcase with GitHub stats
- 📸 **Photography**: Portfolio gallery with password-protected store
- 🤖 **Automation**: Daily updates via GitHub Actions

## Quick Start

### Prerequisites

- Ruby 3.3+ (with Bundler)
- Node.js 25+ (with npm)
- Python 3.10+ (with Conda)

### Local Development

```bash
# 1. Install dependencies
bundle install                              # Jekyll
npm ci                                      # TypeScript/Webpack
conda env create -f _scripts/environment.yml  # Python scripts

# 2. Build TypeScript (required before Jekyll)
npm run build

# 3. Run Jekyll development server
LANG=en_US.UTF-8 bundle exec jekyll serve

# Site will be available at http://localhost:4000
```

### Optional: Run Automation Scripts

```bash
conda activate cxhernandez.com

# Fetch publications from Semantic Scholar
python _scripts/cli.py scrape-pubs -a 39400763 -o _includes/publications.md

# Update CV with citations and GitHub stats
python _scripts/cli.py update-cv -c _includes/cv.md

# Generate CV PDF
python _scripts/cli.py generate-pdf

# Enrich store inventory
python _scripts/cli.py enrich-inventory static/files/store/inventory.json
```

See [_scripts/README.md](_scripts/README.md) for detailed CLI documentation.

## Architecture

### Technology Stack

- **Static Site**: Jekyll (Ruby) with custom plugins
- **Frontend**: TypeScript + Webpack
- **Styling**: SCSS with Bootstrap 3
- **Automation**: Python CLI tool
- **CI/CD**: GitHub Actions → GitHub Pages
- **APIs**: Semantic Scholar, GitHub, Square

### Project Structure

```
cxhernandez.com/
├── _includes/          # Content sections (About, Publications, CV)
├── _layouts/           # HTML templates
├── _typescript/        # TypeScript source (see _typescript/README.md)
├── _sass/             # SCSS stylesheets
├── _scripts/          # Python automation CLI (see _scripts/README.md)
├── _plugins/          # Jekyll custom plugins
├── .github/workflows/ # CI/CD pipeline (see .github/workflows/README.md)
├── static/
│   ├── css/          # Compiled CSS
│   ├── js/dist/      # Compiled JavaScript bundles
│   ├── files/        # CV PDF, inventory JSON
│   └── images/       # Static assets
└── _site/            # Generated site (build output)
```

## Documentation

- **[_scripts/README.md](_scripts/README.md)** - Python automation CLI (publications, CV, PDF generation)
- **[_typescript/README.md](_typescript/README.md)** - TypeScript build system and frontend code
- **[.github/workflows/README.md](.github/workflows/README.md)** - CI/CD pipeline and deployment

## Deployment

### Automated Deployment

The site automatically deploys via GitHub Actions:

- **On push to master**: Build and deploy to https://cxhernandez.com
- **Daily at midnight**: Update publications and redeploy
- **On pull requests**: Build only (no deploy)

See [.github/workflows/README.md](.github/workflows/README.md) for details.

### Manual Build

```bash
# Full production build
LANG=en_US.UTF-8 bundle exec jekyll build --future

# Output in _site/ directory
```

## Configuration

### GitHub Secrets

Configure in: **Repository Settings → Secrets and variables → Actions**

**STORE_PASSWORD** (optional)
- Password for photography store
- If not set, store runs in open access mode
- See [_typescript/README.md](_typescript/README.md) for password system details

**SQUARE_ACCESS_TOKEN** (optional)
- Square API token for inventory enrichment
- Falls back to web scraping if not set

### Jekyll Configuration

Edit `_config.yml` for:
- Site metadata (title, description, author)
- Navigation sections
- Build settings and plugins

### TypeScript Build

Edit `_typescript/webpack.config.js` for:
- Entry points and output paths
- Production/development modes
- Source maps and minification

See [_typescript/README.md](_typescript/README.md) for build system details.

## Development Workflow

### Making Changes

1. **Content changes** (markdown files in `_includes/`):
   ```bash
   # Edit content, then rebuild Jekyll
   bundle exec jekyll serve
   ```

2. **TypeScript changes** (files in `_typescript/src/`):
   ```bash
   # Watch mode rebuilds automatically
   npm run watch
   ```

3. **Style changes** (SCSS files in `_sass/`):
   ```bash
   # Jekyll watches SCSS automatically
   bundle exec jekyll serve
   ```

4. **Automation scripts** (Python in `_scripts/`):
   ```bash
   # Test locally before pushing
   python _scripts/cli.py <command> [options]
   ```

### Testing Changes

```bash
# Build everything
npm run build                           # TypeScript
LANG=en_US.UTF-8 bundle exec jekyll build  # Jekyll

# Test locally
bundle exec jekyll serve
# Visit http://localhost:4000
```

### Committing Changes

```bash
git add .
git commit -m "Description of changes"
git push origin <branch>

# Create PR for review
# Or push to master to deploy
```

## Key Features

### Auto-Updating Publications

- Fetches from Semantic Scholar API daily
- Filters and sorts by citations
- Rendered as searchable DataTable
- Updated in `_includes/publications.md`

### Dynamic CV with Metrics

- Citation counts from Semantic Scholar
- GitHub stats (stars, forks)
- Automatically updated daily
- PDF generated from markdown source

### Password-Protected Store

- SHA-256 password hashing
- Client-side verification
- Session-based authentication
- Square Checkout integration

### Responsive Design

- Mobile-first with Bootstrap 3
- Touch-friendly navigation
- Optimized for all screen sizes
- Fast page loads via static generation

## Troubleshooting

### TypeScript Build Errors

```bash
# Clean rebuild
rm -rf static/js/dist/*
npm run build
```

See [_typescript/README.md](_typescript/README.md) for detailed troubleshooting.

### Jekyll UTF-8 Issues

Always use `LANG=en_US.UTF-8` when building:
```bash
LANG=en_US.UTF-8 bundle exec jekyll serve
```

### Python Script Failures

Check logs for API rate limits:
```bash
python _scripts/cli.py <command> --help
```

See [_scripts/README.md](_scripts/README.md) for CLI documentation.

### GitHub Actions Failures

Check build logs in the Actions tab:
1. Go to https://github.com/cxhernandez/cxhernandez.com/actions
2. Click on failed workflow run
3. View logs for each step

See [.github/workflows/README.md](.github/workflows/README.md) for CI/CD details.

## Dependencies

### Core Technologies

- **Jekyll** 4.4.1+ - Static site generator
- **Ruby** 3.3+ - Jekyll runtime
- **Node.js** 25+ - TypeScript build system
- **Python** 3.10+ - Automation scripts

### Frontend Libraries (CDN)

- jQuery 3.7.1
- Bootstrap 3.4.1
- DataTables 1.10.6
- Lightbox2 2.11.4
- Font Awesome 7.0.1

### Python Packages

- pandas - Data processing
- requests - API calls
- markdown - CV conversion
- weasyprint - PDF generation

See `_scripts/environment.yml` for full Python dependencies.

### Node.js Packages

- TypeScript 5.9.3+
- Webpack 5.104.1+
- ts-loader 9.5.4+

See `package.json` for full Node.js dependencies.

## Performance

- **Build time**: 3-5 minutes (GitHub Actions)
- **Page load**: < 2 seconds (static site)
- **Lighthouse score**: 95+ (Performance, Accessibility, Best Practices, SEO)

Optimizations:
- Webpack minification and tree shaking
- Lazy image loading
- Deferred script loading
- CDN for common libraries
- Static site generation (no server-side rendering)

## Security

- Password-protected store with SHA-256 hashing
- XSS prevention via HTML escaping
- Square Checkout iframe sandboxing
- Session-only storage (not localStorage)
- No plain-text passwords in source code
- Regular dependency audits (`npm audit`, `bundle audit`)

## License

Personal website - All rights reserved.

## Contact

Carlos Xavier Hernández
- Website: https://cxhernandez.com
- GitHub: https://github.com/cxhernandez
