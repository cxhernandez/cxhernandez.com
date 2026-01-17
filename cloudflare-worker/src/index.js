/**
 * Cloudflare Worker for Square Photography Store
 *
 * This worker provides:
 * - /catalog - Fetch items from Square catalog
 * - /checkout - Create a Square hosted checkout link
 *
 * Required secrets (set via `wrangler secret put`):
 * - SQUARE_ACCESS_TOKEN: Your Square API access token
 * - SQUARE_LOCATION_ID: Your Square location ID
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': 'https://www.cxhernandez.com',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// For local development, allow localhost
const DEV_CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// Square API base URLs
const SQUARE_API = {
  sandbox: 'https://connect.squareupsandbox.com/v2',
  production: 'https://connect.squareup.com/v2',
};

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const corsHeaders = origin.includes('localhost') || origin.includes('127.0.0.1')
      ? DEV_CORS_HEADERS
      : CORS_HEADERS;

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);

    if (url.pathname === '/catalog' && request.method === 'GET') {
      return handleGetCatalog(env, corsHeaders);
    }

    if (url.pathname === '/checkout' && request.method === 'POST') {
      return handleCreateCheckout(request, env, corsHeaders);
    }

    if (url.pathname === '/payment-link-details' && request.method === 'GET') {
      return handleGetPaymentLinkDetails(url, env, corsHeaders);
    }

    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({ error: 'Not found' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  },
};

async function handleGetCatalog(env, corsHeaders) {
  try {
    const apiBase = env.SQUARE_ENVIRONMENT === 'production'
      ? SQUARE_API.production
      : SQUARE_API.sandbox;

    const catalogResponse = await fetch(`${apiBase}/catalog/list?types=ITEM,IMAGE`, {
      method: 'GET',
      headers: {
        'Square-Version': '2024-01-18',
        'Authorization': `Bearer ${env.SQUARE_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
    });

    const catalogResult = await catalogResponse.json();

    if (!catalogResponse.ok) {
      const errorMessage = catalogResult.errors?.[0]?.detail || 'Failed to fetch catalog';
      console.error('Square catalog error:', JSON.stringify(catalogResult.errors));
      return errorResponse(errorMessage, 400, corsHeaders);
    }

    // Build image map
    const imageMap = {};
    for (const obj of catalogResult.objects || []) {
      if (obj.type === 'IMAGE' && obj.image_data) {
        imageMap[obj.id] = obj.image_data.url;
      }
    }

    // Process items
    const items = [];
    for (const obj of catalogResult.objects || []) {
      if (obj.type === 'ITEM' && obj.item_data) {
        const item = {
          id: obj.id,
          name: obj.item_data.name,
          description: obj.item_data.description || '',
          variations: (obj.item_data.variations || []).map(v => ({
            id: v.id,
            name: v.item_variation_data?.name || '',
            price: v.item_variation_data?.price_money?.amount || 0,
            currency: v.item_variation_data?.price_money?.currency || 'USD',
          })),
          images: (obj.item_data.image_ids || []).map(id => imageMap[id]).filter(Boolean),
        };
        items.push(item);
      }
    }

    return new Response(
      JSON.stringify({ success: true, items }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    console.error('Catalog fetch error:', error);
    return errorResponse('Internal server error', 500, corsHeaders);
  }
}

async function handleCreateCheckout(request, env, corsHeaders) {
  try {
    const body = await request.json();
    const { name, price, redirectUrl } = body;

    // Validate required fields
    if (!name || !price) {
      return errorResponse('Missing required fields: name and price', 400, corsHeaders);
    }

    if (!Number.isInteger(price) || price <= 0) {
      return errorResponse('Invalid price', 400, corsHeaders);
    }

    const apiBase = env.SQUARE_ENVIRONMENT === 'production'
      ? SQUARE_API.production
      : SQUARE_API.sandbox;

    const idempotencyKey = crypto.randomUUID();

    // Create payment link using Square's Checkout API
    const checkoutResponse = await fetch(`${apiBase}/online-checkout/payment-links`, {
      method: 'POST',
      headers: {
        'Square-Version': '2024-01-18',
        'Authorization': `Bearer ${env.SQUARE_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        idempotency_key: idempotencyKey,
        quick_pay: {
          name: name,
          price_money: {
            amount: price,
            currency: 'USD',
          },
          location_id: env.SQUARE_LOCATION_ID,
        },
        checkout_options: {
          redirect_url: redirectUrl || 'https://www.cxhernandez.com/store?success=true',
        },
      }),
    });

    const checkoutResult = await checkoutResponse.json();

    if (checkoutResponse.ok && checkoutResult.payment_link) {
      return new Response(
        JSON.stringify({
          success: true,
          checkoutUrl: checkoutResult.payment_link.url,
          orderId: checkoutResult.payment_link.order_id,
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    } else {
      const errorMessage = checkoutResult.errors?.[0]?.detail || 'Failed to create checkout';
      console.error('Square checkout error:', JSON.stringify(checkoutResult.errors));
      return errorResponse(errorMessage, 400, corsHeaders);
    }
  } catch (error) {
    console.error('Checkout creation error:', error);
    return errorResponse('Internal server error', 500, corsHeaders);
  }
}

function errorResponse(message, status, corsHeaders = CORS_HEADERS) {
  return new Response(
    JSON.stringify({ success: false, error: message }),
    { status, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  );
}

// Fetch payment link details by matching a provided square.link URL.
// Uses Square's Payment Links list endpoint server-side and returns the first match.
async function handleGetPaymentLinkDetails(urlObj, env, corsHeaders) {
  try {
    const linkParam = urlObj.searchParams.get('link');
    if (!linkParam) return errorResponse('Missing query parameter: link', 400, corsHeaders);

    const apiBase = env.SQUARE_ENVIRONMENT === 'production'
      ? SQUARE_API.production
      : SQUARE_API.sandbox;

    // List payment links (paginated). We'll fetch up to a reasonable limit and search.
    const listResponse = await fetch(`${apiBase}/online-checkout/payment-links?limit=100`, {
      method: 'GET',
      headers: {
        'Square-Version': '2024-01-18',
        'Authorization': `Bearer ${env.SQUARE_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
    });

    const listResult = await listResponse.json();
    if (!listResponse.ok) {
      const errorMessage = listResult.errors?.[0]?.detail || 'Failed to list payment links';
      console.error('Square payment-links list error:', JSON.stringify(listResult.errors));
      return errorResponse(errorMessage, 400, corsHeaders);
    }

    const links = listResult.payment_links || [];

    // Normalize the incoming link (compare by pathname or full URL)
    const target = linkParam.trim();

    const match = links.find(pl => {
      if (!pl || !pl.url) return false;
      try {
        // Compare by full URL, and also by ending segment (short id)
        const plUrl = pl.url;
        if (plUrl === target) return true;
        if (plUrl.endsWith(target)) return true;
        const t = new URL(target, 'https://example.com');
        const plPath = new URL(plUrl).pathname;
        if (t.pathname && plPath && plPath.endsWith(t.pathname)) return true;
      } catch (e) {
        // ignore URL parse errors
      }
      return false;
    });

    if (!match) {
      return errorResponse('Payment link not found', 404, corsHeaders);
    }

    // Return the payment link object as-is (front-end can read quick_pay, price, url, etc.)
    return new Response(JSON.stringify({ success: true, payment_link: match }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('Payment link details error:', error);
    return errorResponse('Internal server error', 500, corsHeaders);
  }
}
