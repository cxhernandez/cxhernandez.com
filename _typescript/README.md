# TypeScript Build System

This directory contains the TypeScript source code and build configuration for the cxhernandez.com frontend.

## Directory Structure

```
_typescript/
├── src/
│   ├── main.ts                    # Core site interactivity
│   └── password-verification.ts   # Store password protection
├── webpack.config.js              # Webpack build configuration
├── tsconfig.json                  # TypeScript compiler configuration
├── generate-password-hash.js      # Password hash generator
└── package.json                   # Node.js dependencies (in root)
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

### Build Commands

```bash
# Production build (minified)
npm run build

# Development build (with source maps)
npm run build:dev

# Watch mode (auto-rebuild)
npm run watch
```

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
- jQuery (CDN)
- Bootstrap 3 (CDN)
- DataTables (CDN)

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

2. **Password is hashed** by `generate-password-hash.js`:
   - Reads `STORE_PASSWORD` from environment
   - Generates SHA-256 hash
   - Returns hash or null if not set

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

```json
{
  "compilerOptions": {
    "target": "ES2015",
    "module": "ES2015",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "node"
  }
}
```

### Webpack Plugins

- **ts-loader**: TypeScript compilation
- **DefinePlugin**: Inject environment variables (password hash)
- **TerserPlugin**: Minification for production
- **SourceMapDevToolPlugin**: Source maps for development

## Output Files

Built bundles are output to `static/js/dist/`:
- `main.bundle.js` - Core site functionality
- `password-verification.bundle.js` - Store password protection

These are loaded in Jekyll templates:
- `main.bundle.js` → `_layouts/default.html`
- `password-verification.bundle.js` → Store page

## Development Workflow

1. **Make changes** to TypeScript files in `src/`
2. **Run build** (or use watch mode):
   ```bash
   npm run watch
   ```
3. **Test in browser** (Jekyll must be running):
   ```bash
   bundle exec jekyll serve
   ```
4. **Check console** for any TypeScript errors
5. **Commit changes** to both `.ts` and `.bundle.js` files

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
