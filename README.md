cxhernandez.com
===
[![Build Status](https://github.com/cxhernandez/cxhernandez.com/actions/workflows/jekyll-docker.yml/badge.svg)](https://github.com/cxhernandez/cxhernandez.com/actions/workflows/jekyll-docker.yml)

Personal Webpage

## Development

This site uses Jekyll for static site generation and TypeScript for client-side JavaScript.

### JavaScript Development
- TypeScript source files are in `src/`
- Build with `npm run build` before running Jekyll
- See [TYPESCRIPT.md](TYPESCRIPT.md) for detailed build documentation

### Jekyll Build
```bash
LANG=en_US.UTF-8 bundle exec jekyll serve
```
