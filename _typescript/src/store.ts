/**
 * Store functionality
 * Handles inventory loading, product card rendering, and checkout modal.
 * Listens for 'storeContentLoaded' event dispatched by password-verification.ts.
 */

// Inventory version for cache control (update when inventory changes)
const INVENTORY_VERSION = '1';

// Allowed domains for checkout iframe
const ALLOWED_CHECKOUT_DOMAINS = ['square.link'];

// HTML escaping to prevent XSS
function escapeHtml(str: string | null | undefined): string {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Validate checkout URL before loading in iframe
function isValidCheckoutUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ALLOWED_CHECKOUT_DOMAINS.some(
      (domain) => parsed.hostname === domain || parsed.hostname.endsWith('.' + domain)
    );
  } catch {
    return false;
  }
}

function openCheckoutModal(url: string): void {
  if (!isValidCheckoutUrl(url)) {
    console.error('Blocked checkout URL from untrusted domain:', url);
    return;
  }

  const modal = document.getElementById('checkout-modal');
  const iframe = document.getElementById('checkout-iframe') as HTMLIFrameElement | null;
  const loading = document.getElementById('checkout-loading');

  if (!modal || !iframe || !loading) return;

  loading.classList.remove('is-hidden');
  iframe.classList.add('is-hidden');

  iframe.src = url;
  modal.classList.remove('is-hidden');
  document.body.style.overflow = 'hidden';

  iframe.onload = function () {
    loading.classList.add('is-hidden');
    iframe.classList.remove('is-hidden');
  };
}

function closeCheckoutModal(): void {
  const modal = document.getElementById('checkout-modal');
  const iframe = document.getElementById('checkout-iframe') as HTMLIFrameElement | null;
  const loading = document.getElementById('checkout-loading');

  if (!modal || !iframe || !loading) return;

  modal.classList.add('is-hidden');
  iframe.src = '';
  iframe.classList.add('is-hidden');
  loading.classList.remove('is-hidden');
  document.body.style.overflow = '';
}

function checkForSuccess(): void {
  const params = new URLSearchParams(window.location.search);
  if (params.get('success') === 'true') {
    const msg = document.getElementById('success-message');
    if (msg) msg.style.display = 'block';
    window.history.replaceState({}, '', window.location.pathname);
  }
}

interface InventoryEntry {
  url?: string;
  name?: string;
  description?: string;
  image?: string;
  emoji?: string;
  icon?: string;
  price_display?: string;
  price_min?: number;
  price_max?: number;
}

function formatPrice(entry: InventoryEntry): string {
  const priceMin = entry.price_min;
  const priceMax = entry.price_max;

  if (priceMin != null && priceMax != null) {
    if (priceMin === priceMax) {
      return `$${priceMin.toFixed(2)}`;
    } else {
      return `$${priceMin.toFixed(2)} – $${priceMax.toFixed(2)}`;
    }
  }

  return entry.price_display || '';
}

function handleImageError(img: HTMLImageElement): void {
  const placeholder = document.createElement('div');
  placeholder.className = 'product-card-image-placeholder';
  placeholder.innerHTML =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>';
  img.parentNode?.replaceChild(placeholder, img);
}

function renderImageArea(entry: InventoryEntry, altText: string): string {
  if (entry.emoji) {
    return `<div class="product-card-emoji" aria-hidden="true">${entry.emoji}</div>`;
  }
  if (entry.image) {
    return `<img src="${escapeHtml(entry.image)}" alt="${escapeHtml(altText)}" class="product-card-image" loading="lazy">`;
  }
  return '<div class="product-card-image-placeholder"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg></div>';
}

function renderProductCard(entry: InventoryEntry, index: number, type: string): string {
  const url = escapeHtml(entry.url) || '#';
  const name = escapeHtml(entry.name) || `${type} ${index + 1}`;
  const price = escapeHtml(formatPrice(entry));
  const description = escapeHtml(entry.description) || '';
  const icon = escapeHtml(entry.icon) || '';

  const altText =
    type === 'Print' ? `${name} - photography print` : `${name} - photography service`;

  const priceMin = entry.price_min;
  const priceMax = entry.price_max;
  const hasSizeOptions =
    type === 'Print' && priceMin != null && priceMax != null && priceMin !== priceMax;
  const sizeHint = hasSizeOptions
    ? '<span class="product-card-size-hint">Multiple sizes available</span>'
    : '';

  return `
    <a href="${url}" class="product-card">
        ${renderImageArea(entry, altText)}
        <div class="product-card-body">
            ${icon ? `<div class="product-card-icon" aria-hidden="true">${icon}</div>` : ''}
            <p class="product-card-name">${name}</p>
            ${price ? `<p class="product-card-price">${sizeHint}${price}</p>` : ''}
            ${description ? `<p class="product-card-description">${description}</p>` : ''}
        </div>
    </a>
  `;
}

function showStoreError(message: string): void {
  const storeSections = document.querySelector('.store-sections');
  if (storeSections) {
    storeSections.innerHTML = `
      <div class="store-error">
          <p>${escapeHtml(message)}</p>
          <button class="retry-button">Try Again</button>
          <p class="store-error-fallback">Or <a href="/#Photography">&larr; return to Photography</a></p>
      </div>
    `;
  }
}

function renderSkeletonCards(count: number): string {
  const skeletonCard = `
    <div class="skeleton-card" aria-hidden="true">
        <div class="skeleton-image"></div>
        <div class="skeleton-body">
            <div class="skeleton-text skeleton-title"></div>
            <div class="skeleton-text skeleton-price"></div>
            <div class="skeleton-text skeleton-button"></div>
        </div>
    </div>
  `;
  return `<div class="skeleton-grid">${skeletonCard.repeat(count)}</div>`;
}

async function loadInventory(): Promise<void> {
  const printsGrid = document.getElementById('prints-grid');
  const servicesGrid = document.getElementById('services-grid');

  if (printsGrid) printsGrid.innerHTML = renderSkeletonCards(3);
  if (servicesGrid) servicesGrid.innerHTML = renderSkeletonCards(2);

  try {
    const response = await fetch('/static/files/store/inventory.json?v=' + INVENTORY_VERSION);
    if (!response.ok) {
      showStoreError('Unable to load store inventory. Please try again.');
      return;
    }

    const data = await response.json();

    const hasPrints = data.prints && data.prints.length > 0;
    const hasServices = data.services && data.services.length > 0;

    if (!hasPrints && !hasServices) {
      showStoreError('No products are currently available.');
      return;
    }

    if (hasPrints && printsGrid) {
      printsGrid.innerHTML = data.prints
        .map((p: InventoryEntry | string, i: number) => {
          const entry: InventoryEntry = typeof p === 'string' ? { url: p } : p || {};
          return renderProductCard(entry, i, 'Print');
        })
        .join('');
    } else if (printsGrid) {
      printsGrid.innerHTML = '<p class="no-prints">No prints available at this time.</p>';
    }

    if (hasServices && servicesGrid) {
      servicesGrid.innerHTML = data.services
        .map((s: InventoryEntry | string, i: number) => {
          const entry: InventoryEntry = typeof s === 'string' ? { url: s } : s || {};
          return renderProductCard(entry, i, 'Service');
        })
        .join('');
    } else if (servicesGrid) {
      servicesGrid.innerHTML =
        '<p class="no-services">No services available at this time.</p>';
    }
  } catch (error) {
    console.error('Failed to load inventory:', error);
    showStoreError('Failed to load store. Please check your connection and try again.');
  }
}

function initializeStore(): void {
  checkForSuccess();
  loadInventory();

  // Modal close handlers
  const closeBtn = document.querySelector('.checkout-modal-close');
  const backdrop = document.querySelector('.checkout-modal-backdrop');

  if (closeBtn) closeBtn.addEventListener('click', closeCheckoutModal);
  if (backdrop) backdrop.addEventListener('click', closeCheckoutModal);

  document.addEventListener('keydown', function (e: KeyboardEvent) {
    if (e.key === 'Escape') {
      closeCheckoutModal();
    }
  });

  // Event delegation for product cards (checkout modal)
  const storeSections = document.querySelector('.store-sections');
  if (storeSections) {
    storeSections.addEventListener('click', function (e: Event) {
      const target = e.target as HTMLElement;
      const card = target.closest('.product-card') as HTMLAnchorElement | null;
      if (card) {
        e.preventDefault();
        const url = card.href;
        openCheckoutModal(url);
      }

      const retryBtn = target.closest('.retry-button');
      if (retryBtn) {
        loadInventory();
      }
    });

    // Event delegation for image errors
    storeSections.addEventListener(
      'error',
      function (e: Event) {
        const target = e.target as HTMLElement;
        if (target.tagName === 'IMG' && target.classList.contains('product-card-image')) {
          handleImageError(target as HTMLImageElement);
        }
      },
      true // capture phase since error doesn't bubble
    );
  }
}

// Listen for store content to be injected by password-verification.ts
document.addEventListener('storeContentLoaded', initializeStore);

export {};
