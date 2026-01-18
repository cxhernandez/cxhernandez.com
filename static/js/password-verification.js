// Password protection (SHA-256 hash)
const STORE_PASSWORD_HASH = '83006a438f94daf3a7dd9c7b27f70c15e443c0ca55d58fcdfa76899ae466b455';

// HTML escaping to prevent XSS
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

async function hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Animate transition from password gate to store
function unlockStore() {
    const gate = document.getElementById('password-gate');
    const store = document.getElementById('store-main');
    const gateContent = gate.querySelector('.password-gate-content');
    const gateBack = gate.querySelector('.password-gate-back');

    // Show welcome message
    if (gateContent) {
        gateContent.innerHTML = '<h2>Welcome, friend<br>(˶ᵔ ᵕ ᵔ˶)</h2>';
        gateBack.style.display = 'none';
    }

    // Brief pause to show welcome, then fade out
    setTimeout(() => {
        gate.style.transition = 'opacity 0.4s ease';
        gate.style.opacity = '0';

        setTimeout(() => {
            gate.style.display = 'none';

            // Prepare store for fade in
            store.style.opacity = '0';
            store.style.display = 'block';
            store.style.transition = 'opacity 0.4s ease';

            // Trigger reflow, then fade in
            store.offsetHeight;
            store.style.opacity = '1';
        }, 400);
    }, 600);
}

async function checkPassword(e) {
    e.preventDefault();
    const input = document.getElementById('password-input');
    const error = document.getElementById('password-error');

    const inputHash = await hashPassword(input.value);
    if (inputHash === STORE_PASSWORD_HASH) {
        sessionStorage.setItem('store_access', 'granted');
        unlockStore();
    } else {
        error.style.display = 'block';
        input.value = '';
        input.focus();
    }
    return false;
}

// Check password on each keystroke for instant unlock
function setupPasswordInputListener() {
    const input = document.getElementById('password-input');
    const error = document.getElementById('password-error');
    if (input && error) {
        input.addEventListener('input', async function() {
            // Clear any previous error
            if (error.style.display !== 'none') {
                error.style.display = 'none';
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
}

function checkAccess() {
    if (sessionStorage.getItem('store_access') === 'granted') {
        document.getElementById('password-gate').style.display = 'none';
        document.getElementById('store-main').style.display = 'block';
    }
}

// Initialize password input listener when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupPasswordInputListener);
} else {
    setupPasswordInputListener();
}
