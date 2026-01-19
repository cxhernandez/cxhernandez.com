# GitHub Actions CI/CD Pipeline

This directory contains the automated build and deployment workflow for cxhernandez.com.

## Workflow: jekyll-docker.yml

Main CI/CD pipeline that builds and deploys the site.

### Triggers

```yaml
on:
  push:
    branches: [ "master" ]
  pull_request:
    branches: [ "master" ]
  schedule:
    # Run at 00:00 UTC daily to update publication data
    - cron: '0 0 * * *'
```

**When it runs:**
- Every push to `master` branch → Build + Deploy
- Every pull request to `master` → Build only (no deploy)
- Daily at midnight UTC → Update publications, rebuild, deploy

### Permissions

```yaml
permissions:
  contents: read      # Read repository contents
  pages: write        # Deploy to GitHub Pages
  id-token: write     # OIDC token for Pages deployment
```

### Concurrency

```yaml
concurrency:
  group: "pages"
  cancel-in-progress: false
```

Only one deployment runs at a time. New deployments wait for current one to complete.

## Build Steps

### 1. Setup Conda Environment

```yaml
- name: Set up Conda
  uses: conda-incubator/setup-miniconda@v3
  with:
    environment-file: _scripts/environment.yml
    activate-environment: cv_pdf
    auto-activate-base: false
```

Creates Python environment with dependencies:
- Python 3.10
- pandas
- requests
- weasyprint
- markdown

### 2. Fetch Publications

```yaml
- name: Fetch publications from Semantic Scholar
  shell: bash -el {0}
  run: python ./_scripts/cli.py scrape-pubs -a 39400763 -o ./_includes/publications.md
```

Fetches latest publications from Semantic Scholar API:
- Author ID: 39400763
- Filters out abstracts and Zenodo releases
- Sorts by citation count and year
- Outputs HTML table to `_includes/publications.md`

### 3. Update CV Stats

```yaml
- name: Update CV with citations and GitHub stats
  shell: bash -el {0}
  run: python ./_scripts/cli.py update-cv -c ./_includes/cv.md
```

Updates CV with latest metrics:
- Citation counts from Semantic Scholar (DOI and arXiv papers)
- GitHub repository stats (stars, forks)
- Updates `_includes/cv.md` in-place

### 4. Generate CV PDF

```yaml
- name: Generate CV PDF
  shell: bash -el {0}
  run: python ./_scripts/cli.py generate-pdf
```

Converts CV markdown to PDF:
- Input: `_includes/cv.md`
- Output: `static/files/CXHernandez_CV.pdf`
- Uses WeasyPrint for rendering

### 5. Enrich Store Inventory

```yaml
- name: Enrich store inventory
  shell: bash -el {0}
  run: python ./_scripts/cli.py enrich-inventory static/files/store/inventory.json
```

Updates store inventory with Square data:
- Queries Square API (if `SQUARE_ACCESS_TOKEN` set)
- Falls back to web scraping checkout pages
- Updates `static/files/store/inventory.json`

### 6. Setup Node.js

```yaml
- name: Set up Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '25'
    cache: 'npm'
```

Installs Node.js 25 with npm cache.

### 7. Install Node Dependencies

```yaml
- name: Install Node.js dependencies
  run: npm ci
```

Installs TypeScript, Webpack, and build tools from `package.json`.

### 8. Build TypeScript

```yaml
- name: Build TypeScript bundles
  run: npm run build
  env:
    STORE_PASSWORD: ${{ secrets.STORE_PASSWORD }}
```

Compiles TypeScript to JavaScript bundles:
- `main.bundle.js` - Core site functionality
- `password-verification.bundle.js` - Store password protection

Password hash is injected at build time from GitHub Secret.

### 9. Setup Ruby

```yaml
- name: Set up Ruby
  uses: ruby/setup-ruby@v1
  with:
    ruby-version: '3.3'
    bundler-cache: true
```

Installs Ruby 3.3 and caches bundler dependencies.

### 10. Build Jekyll Site

```yaml
- name: Build Jekyll site
  run: bundle exec jekyll build --future
  env:
    LANG: en_US.UTF-8
    LC_ALL: en_US.UTF-8
```

Builds static site with Jekyll:
- `--future` flag includes future-dated posts
- UTF-8 encoding for emoji support
- Output to `_site/` directory

### 11. Deploy to GitHub Pages

```yaml
- name: Setup Pages
  if: env.SHOULD_DEPLOY == 'true'
  uses: actions/configure-pages@v5

- name: Upload artifact
  if: env.SHOULD_DEPLOY == 'true'
  uses: actions/upload-pages-artifact@v3
  with:
    path: '_site'

- name: Deploy to GitHub Pages
  if: env.SHOULD_DEPLOY == 'true'
  id: deployment
  uses: actions/deploy-pages@v4
```

Deploys to GitHub Pages (only on master push):
- Condition: `github.ref == 'refs/heads/master' && github.event_name == 'push'`
- Uploads `_site/` directory
- Deploys to https://cxhernandez.com

## Environment Variables

### Secrets (GitHub)

Configure in: Repository Settings → Secrets and variables → Actions

**STORE_PASSWORD** (optional)
- Plain-text password for photography store
- Hashed at build time and injected into bundle
- If not set, store runs in open access mode

**SQUARE_ACCESS_TOKEN** (optional)
- Square API token for inventory enrichment
- If not set, falls back to web scraping
- Not required for site to build/deploy

### Runtime Variables

**SHOULD_DEPLOY**
```yaml
env:
  SHOULD_DEPLOY: ${{ github.ref == 'refs/heads/master' && github.event_name == 'push' }}
```

Boolean flag that determines if deployment should happen:
- `true` - Push to master (deploy)
- `false` - Pull request or other branch (skip deploy)

**LANG and LC_ALL**
```yaml
env:
  LANG: en_US.UTF-8
  LC_ALL: en_US.UTF-8
```

UTF-8 encoding for Jekyll build (supports emoji in CV).

## Workflow Behavior

### Pull Request

1. ✅ Run all build steps
2. ✅ Generate fresh publications, CV, PDF
3. ✅ Build TypeScript and Jekyll
4. ❌ Skip deployment
5. 💬 Comment on PR with build status

### Master Push

1. ✅ Run all build steps
2. ✅ Generate fresh data
3. ✅ Build site
4. ✅ Deploy to GitHub Pages
5. 🌐 Live at https://cxhernandez.com

### Daily Schedule (Cron)

1. ✅ Run at 00:00 UTC
2. ✅ Update publications from Semantic Scholar
3. ✅ Update CV citation counts
4. ✅ Rebuild and deploy
5. 🔄 Site stays fresh with latest data

### Failed Build

If any step fails:
- ❌ Workflow marked as failed
- 📧 Email notification to repository owner
- 🚫 No deployment happens
- 💡 Check logs in Actions tab

## Debugging

### View Workflow Runs

1. Go to repository on GitHub
2. Click "Actions" tab
3. Select workflow run
4. View logs for each step

### Common Issues

**Semantic Scholar API fails**
- Workflow continues on error
- Check logs for warnings
- Publications may be stale until next run

**TypeScript build fails**
- Check for TypeScript syntax errors
- Verify `STORE_PASSWORD` secret is set (optional)
- Check npm dependencies in `package.json`

**Jekyll build fails**
- Check for YAML front matter errors
- Verify UTF-8 encoding is set
- Check Ruby/gem versions

**Deployment fails**
- Verify GitHub Pages is enabled in repository settings
- Check Pages permissions in workflow
- Ensure `GITHUB_TOKEN` has correct permissions

### Manual Trigger

To manually trigger the workflow:

1. Go to Actions tab
2. Select "Jekyll site CI" workflow
3. Click "Run workflow"
4. Select branch (usually master)
5. Click "Run workflow" button

## Performance

Typical build time: 3-5 minutes

**Breakdown:**
- Conda setup: 30s
- Python scripts: 1-2 min (API calls)
- Node.js setup: 20s
- TypeScript build: 30s
- Ruby setup: 20s
- Jekyll build: 1 min
- Deployment: 30s

## Caching

Caches used to speed up builds:

- **npm cache**: Node.js dependencies
- **bundler cache**: Ruby gems
- **Conda cache**: Python environment (implicit)

Caches expire after 7 days of no use.

## Cost

GitHub Actions for public repositories: **FREE**

Usage limits:
- ✅ Unlimited minutes for public repos
- ✅ Unlimited storage for artifacts
- ✅ Unlimited deployments

## Monitoring

Check build status:
- [![Build Status](https://github.com/cxhernandez/cxhernandez.com/actions/workflows/jekyll-docker.yml/badge.svg)](https://github.com/cxhernandez/cxhernandez.com/actions/workflows/jekyll-docker.yml)

Monitor via:
- GitHub Actions tab
- Email notifications (if enabled)
- Status badge in README

## Security

**Secrets handling:**
- Secrets never logged or printed
- Secrets injected as environment variables
- Secrets not accessible in pull requests from forks

**Permissions:**
- Minimal permissions (read contents, write pages)
- No access to other repository resources
- Token expires after workflow completes

## Extending the Workflow

To add new steps:

1. Edit `.github/workflows/jekyll-docker.yml`
2. Add step in appropriate section:
   ```yaml
   - name: My new step
     run: |
       echo "Doing something..."
   ```
3. Commit and push to test
4. Check Actions tab for results

Common additions:
- Linting (eslint, rubocop, black)
- Testing (jest, rspec, pytest)
- Notifications (Slack, Discord)
- Artifact uploads (reports, logs)

## Related Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [jekyll-docker action](https://github.com/marketplace/actions/jekyll-actions)
