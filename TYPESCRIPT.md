# TypeScript Build Setup

This project uses TypeScript with Webpack to build JavaScript bundles for the Jekyll site.

## Development Setup

### Prerequisites
- Node.js 25.x or later
- npm 11.x or later

### Installation
```bash
npm install
```

## Build Commands

### Production Build
```bash
npm run build
```
Compiles TypeScript to optimized, minified JavaScript bundles in `static/js/dist/`.

### Development Build
```bash
npm run build:dev
```
Compiles TypeScript with source maps and no minification for easier debugging.

### Watch Mode
```bash
npm run watch
```
Automatically rebuilds on file changes during development.

## Project Structure

```
src/
├── main.ts                          # Main site JavaScript
├── password-verification.ts         # Password protection for store
└── types/
    └── jquery-plugins.d.ts         # Type definitions for jQuery plugins

static/js/dist/                      # Build output (gitignored)
├── main.bundle.js
├── main.bundle.js.map
├── password-verification.bundle.js
└── password-verification.bundle.js.map
```

## TypeScript Configuration

- **Target**: ES2017 (supports modern features like async/await, padStart)
- **Module System**: ESNext
- **Type Checking**: Strict mode enabled
- **External Dependencies**: jQuery, Bootstrap, and Bootbox are loaded from CDN and marked as externals

## Workflow

1. Edit TypeScript files in `src/`
2. Run `npm run build` to compile
3. Build Jekyll site: `LANG=en_US.UTF-8 bundle exec jekyll build`
4. The bundled JavaScript is automatically referenced in the site

## Notes

- Source maps are generated for debugging
- The build output is excluded from version control
- Jekyll must be run with UTF-8 encoding to handle emoji characters
- Original JavaScript files in `static/js/` are kept for reference but not used
