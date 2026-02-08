// Password protection (SHA-256 hash)
// This hash is injected at build time from the STORE_PASSWORD environment variable
// via webpack DefinePlugin. See webpack.config.js and generate-password-hash.js
// If null, the password gate is automatically bypassed (open access mode)
//
// Store content is Base64 encoded and injected at build time for obfuscation
declare const process: {
  env: {
    STORE_PASSWORD_HASH: string | null;
    STORE_CONTENT_ENCODED: string;
  };
};

const STORE_PASSWORD_HASH = process.env.STORE_PASSWORD_HASH;
const STORE_CONTENT_ENCODED = process.env.STORE_CONTENT_ENCODED;

// HTML escaping to prevent XSS
function escapeHtml(str: string | null | undefined): string {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

// Decode and inject store content from Base64
function injectStoreContent(): void {
  const store = document.getElementById('store-main');
  if (!store) return;

  try {
    // Decode Base64 content
    const decoded = atob(STORE_CONTENT_ENCODED);
    store.innerHTML = decoded;

    // Initialize store functionality after content is injected
    // Trigger custom event that store.html script can listen for
    const event = new CustomEvent('storeContentLoaded');
    document.dispatchEvent(event);
  } catch (error) {
    console.error('Failed to load store content:', error);
    store.innerHTML = '<div style="padding: 2rem; text-align: center;">Failed to load store content. Please refresh the page.</div>';
  }
}

// Animate transition from password gate to store
function unlockStore(): void {
  const gate = document.getElementById('password-gate');
  const store = document.getElementById('store-main');
  const gateContent = gate?.querySelector<HTMLElement>('.password-gate-content');
  const gateBack = gate?.querySelector<HTMLElement>('.password-gate-back');

  if (!gate || !store) return;

  // Inject store content before showing
  injectStoreContent();

  // Show welcome message
  if (gateContent) {
    gateContent.innerHTML = '<h2>Welcome, friend<br>(˶ᵔ ᵕ ᵔ˶)</h2>';
    if (gateBack) {
      gateBack.style.display = 'none';
    }
  }

  // Brief pause to show welcome, then fade out
  setTimeout(() => {
    gate.style.transition = 'opacity 0.4s ease';
    gate.style.opacity = '0';

    setTimeout(() => {
      gate.style.display = 'none';

      // Prepare store for fade in
      store.classList.remove('is-hidden');
      store.style.opacity = '0';
      store.style.transition = 'opacity 0.4s ease';

      // Trigger reflow, then fade in
      store.offsetHeight; // Force reflow
      store.style.opacity = '1';
    }, 400);
  }, 600);
}

async function checkPassword(e: Event): Promise<boolean> {
  e.preventDefault();
  const input = document.getElementById('password-input') as HTMLInputElement | null;
  const error = document.getElementById('password-error');

  if (!input || !error) return false;

  const inputHash = await hashPassword(input.value);
  if (inputHash === STORE_PASSWORD_HASH) {
    sessionStorage.setItem('store_access', 'granted');
    unlockStore();
  } else {
    error.classList.remove('is-hidden');
    input.value = '';
    input.focus();
  }
  return false;
}

// Check password on each keystroke for instant unlock
function setupPasswordInputListener(): void {
  const input = document.getElementById('password-input') as HTMLInputElement | null;
  const error = document.getElementById('password-error');

  if (input && error) {
    input.addEventListener('input', async function () {
      // Clear any previous error
      if (!error.classList.contains('is-hidden')) {
        error.classList.add('is-hidden');
      }
      // Check if password matches
      if (input.value) {
        const inputHash = await hashPassword(input.value);
        if (inputHash === STORE_PASSWORD_HASH) {
          sessionStorage.setItem('store_access', 'granted');
          unlockStore();
        }
      }
    });
  }

  // Form submit handler
  const form = document.getElementById('password-form');
  if (form) {
    form.addEventListener('submit', function (e: Event) {
      checkPassword(e);
    });
  }
}

function checkAccess(): void {
  const gate = document.getElementById('password-gate');
  const store = document.getElementById('store-main');

  if (!gate || !store) return;

  // If no password is set at build time, grant immediate access (open mode)
  if (STORE_PASSWORD_HASH === null) {
    console.warn('Store is running in OPEN ACCESS mode (no password protection)');
    injectStoreContent();
    gate.style.display = 'none';
    store.classList.remove('is-hidden');
    return;
  }

  // Check if user has already been granted access in this session
  if (sessionStorage.getItem('store_access') === 'granted') {
    injectStoreContent();
    gate.style.display = 'none';
    store.classList.remove('is-hidden');
  }
}

// Initialize on DOM ready
function init(): void {
  setupPasswordInputListener();
  checkAccess();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Export to make this a module
export {};
