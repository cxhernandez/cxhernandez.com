# TypeScript Build System

This directory contains the TypeScript source code and build configuration for the cxhernandez.com frontend.

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

## Directory Structure

```
_typescript/
├── src/
│   ├── main.ts                      # Core site interactivity
│   ├── password-verification.ts     # Store password protection
│   ├── generate-password-hash.ts    # Password hash generator (build script)
│   ├── encode-store-content.ts      # Store content encoder (build script)
│   └── types/
│       └── jquery-plugins.d.ts     # Type definitions for jQuery plugins
├── tsconfig.json                    # TypeScript compiler configuration (for src/)
├── tsconfig.scripts.json            # TypeScript config for build scripts
└── webpack.config.js                # Webpack bundler configuration

static/js/dist/                      # Build output (not in git)
├── main.bundle.js
├── main.bundle.js.map
├── password-verification.bundle.js
└── password-verification.bundle.js.map
```

## Build System

### Webpack Configuration

Entry points:
- `main.ts` → `static/js/dist/main.bundle.js`
- `password-verification.ts` → `static/js/dist/password-verification.bundle.js`

Build modes:
- **Production**: Minified bundles with tree shaking
- **Development**: Source maps enabled for debugging
- **Watch**: Auto-rebuild on file changes

### Webpack Plugins

- **ts-loader**: TypeScript compilation
- **DefinePlugin**: Inject environment variables (password hash)
- **TerserPlugin**: Minification for production
- **SourceMapDevToolPlugin**: Source maps for development

## Source Files

### main.ts

Core site interactivity module.

**Features:**
- Smooth scroll navigation with navbar offset calculation
- Mobile navigation toggle with hamburger menu
- CV modal display with scroll locking
- Portfolio carousel with AJAX loading
- DataTables integration for publications
- Responsive design with touch event handling

**Key Functions:**
- `setupSmoothScroll()` - Handles navigation link clicks and scrolling
- `setupMobileNavigation()` - Mobile menu toggle
- `setupCVModal()` - CV modal open/close with body scroll lock
- `setupCarousel()` - Portfolio image carousel
- `initializeDataTables()` - Publications table with search/sort

**Dependencies:**
- jQuery 3.7.1 (CDN)
- Bootstrap 3.4.1 (CDN)
- DataTables 1.10.6 (CDN)

### password-verification.ts

Store password protection with client-side verification.

**Features:**
- SHA-256 password hashing via Web Crypto API
- SessionStorage persistence (not localStorage)
- XSS prevention via HTML escaping
- Animated transitions between password gate and store
- Open access mode for development (when no password set)

**Security:**
- Password hash injected at build time from `STORE_PASSWORD` env var
- Zero plain-text passwords in source code
- Hash comparison happens client-side
- Session-based authentication (cleared on browser close)

**Key Functions:**
- `hashPassword(password: string)` - SHA-256 hashing
- `verifyPassword()` - Password check and session management
- `showStore()` / `showPasswordGate()` - UI transitions

## Password Hash System

The store password is managed securely through environment variables:

1. **Set environment variable** (build time):
   ```bash
   export STORE_PASSWORD="your_password_here"
   ```

2. **Password is hashed** by `generate-password-hash.ts`:
   - Reads `STORE_PASSWORD` from environment
   - Generates SHA-256 hash
   - Returns hash or null if not set
   - Executed via `ts-node` during webpack build

3. **Hash injected into bundle** via webpack DefinePlugin:
   ```javascript
   // webpack.config.js
   new webpack.DefinePlugin({
     PASSWORD_HASH: JSON.stringify(passwordHash)
   })
   ```

4. **Client-side verification**:
   - User enters password
   - Password hashed client-side
   - Hash compared against injected hash
   - Session stored in SessionStorage on success

### Missing Password Behavior

If `STORE_PASSWORD` is not set during build:
- Build succeeds with warning: `⚠️ WARNING: STORE_PASSWORD environment variable is not set`
- Store runs in **OPEN ACCESS mode** (no password protection)
- Console shows: `Store is running in OPEN ACCESS mode (no password protection)`
- Useful for local development

**⚠️ Never commit passwords or hashes to the repository!**

## TypeScript Configuration

### tsconfig.json

- **Target**: ES2017 (supports modern features like async/await, padStart)
- **Module System**: ESNext
- **Type Checking**: Strict mode enabled
- **Module Resolution**: Node
- **External Dependencies**: jQuery, Bootstrap, and Bootbox are loaded from CDN and marked as externals

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "module": "ESNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "node"
  }
}
```

## Output Files

Built bundles are output to `static/js/dist/`:
- `main.bundle.js` - Core site functionality
- `main.bundle.js.map` - Source map for debugging
- `password-verification.bundle.js` - Store password protection
- `password-verification.bundle.js.map` - Source map for debugging

These are loaded in Jekyll templates:
- `main.bundle.js` → `_layouts/default.html`
- `password-verification.bundle.js` → Store page

**Note:** Build output is excluded from version control (`.gitignore`).

## Development Workflow

1. Edit TypeScript files in `_typescript/src/`
2. Run `npm run watch` for auto-rebuild
3. Build Jekyll site: `LANG=en_US.UTF-8 bundle exec jekyll build`
4. Test in browser at http://localhost:4000
5. Check console for TypeScript errors
6. The bundled JavaScript is automatically referenced in the site

## Build Integration

### GitHub Actions

The TypeScript build is integrated into the CI/CD pipeline:

```yaml
- name: Set up Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '25'
    cache: 'npm'

- name: Install Node.js dependencies
  run: npm ci

- name: Build TypeScript bundles
  run: npm run build
  env:
    STORE_PASSWORD: ${{ secrets.STORE_PASSWORD }}
```

### Local Development

```bash
# Install dependencies
npm ci

# Set password (optional)
export STORE_PASSWORD="dev_password"

# Build
npm run build

# Or use watch mode
npm run watch
```

## Troubleshooting

### TypeScript Build Errors

**Issue**: Build fails with type errors
```bash
npm run build
# ERROR in src/main.ts:42:5
```

**Solution**: Check TypeScript syntax and type annotations
```bash
# Clean rebuild
rm -rf static/js/dist/*
npm run build
```

### Password Not Working

**Issue**: Store password doesn't work after build

**Solution**: Verify password hash was injected
1. Check build output for password warning
2. Set `STORE_PASSWORD` environment variable
3. Rebuild TypeScript bundles
4. Clear browser SessionStorage

### Source Maps Missing

**Issue**: Can't debug TypeScript in browser DevTools

**Solution**: Use development build
```bash
npm run build:dev
```

### Bundle Size Too Large

**Issue**: Bundle files are very large

**Solution**: Use production build (minified)
```bash
NODE_ENV=production npm run build
```

## Dependencies

### Runtime (CDN)
- jQuery 3.7.1
- Bootstrap 3.4.1
- DataTables 1.10.6
- Bootbox.js (for modals)

### Build Time (npm)
- TypeScript ^5.9.3
- Webpack ^5.104.1
- ts-loader ^9.5.4
- terser-webpack-plugin ^5.3.11

## Performance Optimizations

- **Tree shaking**: Unused code eliminated in production
- **Minification**: Terser plugin reduces bundle size
- **Code splitting**: Separate bundles for main and password verification
- **Lazy loading**: Images loaded on demand
- **Deferred script loading**: Non-critical scripts load after page render

## Security Considerations

- **No plain-text passwords**: Only hashes in bundles
- **XSS prevention**: HTML escaping for user inputs
- **Session-only storage**: SessionStorage (not localStorage)
- **CSP compliance**: No inline scripts or eval()
- **Dependency auditing**: Regular `npm audit` checks

## Testing

While there are no formal unit tests, manual testing checklist:

- [ ] Smooth scroll navigation works on all sections
- [ ] Mobile menu opens and closes
- [ ] CV modal opens and closes without scroll issues
- [ ] Portfolio carousel advances images
- [ ] Publications table sorts and searches
- [ ] Store password verification works
- [ ] Store shows after correct password
- [ ] Wrong password shows error message
- [ ] Session persists across page refreshes

## Notes

- Source maps are generated for debugging
- Jekyll must be run with UTF-8 encoding to handle emoji characters: `LANG=en_US.UTF-8`
- Original JavaScript files in `static/js/` are kept for reference but not used
- Always rebuild TypeScript before running Jekyll in production
