/**
 * Cloudflare Worker for Square Payments
 *
 * This worker handles payment processing for the photography store.
 * It acts as a secure backend to process Square payments.
 *
 * Required secrets (set via `wrangler secret put`):
 * - SQUARE_ACCESS_TOKEN: Your Square API access token
 * - SQUARE_LOCATION_ID: Your Square location ID
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': 'https://www.cxhernandez.com', // Update with your domain
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
    // Use permissive CORS for local dev, strict for production
    const origin = request.headers.get('Origin') || '';
    const corsHeaders = origin.includes('localhost') || origin.includes('127.0.0.1')
      ? DEV_CORS_HEADERS
      : CORS_HEADERS;

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);

    // Route handling
    if (url.pathname === '/create-payment' && request.method === 'POST') {
      return handleCreatePayment(request, env, corsHeaders);
    }

    if (url.pathname === '/catalog' && request.method === 'GET') {
      return handleGetCatalog(env, corsHeaders);
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

async function handleCreatePayment(request, env, corsHeaders) {
  try {
    const body = await request.json();
    const { sourceId, amount, item, title, email } = body;

    // Validate required fields
    if (!sourceId || !amount) {
      return errorResponse('Missing required fields: sourceId and amount', 400, corsHeaders);
    }

    // Validate amount is a positive integer (cents)
    if (!Number.isInteger(amount) || amount <= 0) {
      return errorResponse('Invalid amount', 400, corsHeaders);
    }

    // Determine API URL based on environment
    const apiBase = env.SQUARE_ENVIRONMENT === 'production'
      ? SQUARE_API.production
      : SQUARE_API.sandbox;

    // Create idempotency key for this payment
    const idempotencyKey = crypto.randomUUID();

    // Create payment with Square
    const paymentResponse = await fetch(`${apiBase}/payments`, {
      method: 'POST',
      headers: {
        'Square-Version': '2024-01-18',
        'Authorization': `Bearer ${env.SQUARE_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        idempotency_key: idempotencyKey,
        source_id: sourceId,
        amount_money: {
          amount: amount,
          currency: 'USD',
        },
        location_id: env.SQUARE_LOCATION_ID,
        note: `Photography Store: ${title || item || 'Purchase'}`,
        // Optional: Add buyer email for receipts
        ...(email && { buyer_email_address: email }),
      }),
    });

    const paymentResult = await paymentResponse.json();

    if (paymentResponse.ok && paymentResult.payment) {
      return new Response(
        JSON.stringify({
          success: true,
          paymentId: paymentResult.payment.id,
          status: paymentResult.payment.status,
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        }
      );
    } else {
      // Extract error message from Square response
      const errorMessage = paymentResult.errors?.[0]?.detail || 'Payment failed';
      console.error('Square payment error:', JSON.stringify(paymentResult.errors));
      return errorResponse(errorMessage, 400, corsHeaders);
    }
  } catch (error) {
    console.error('Payment processing error:', error);
    return errorResponse('Internal server error', 500, corsHeaders);
  }
}

async function handleGetCatalog(env, corsHeaders) {
  try {
    // Determine API URL based on environment
    const apiBase = env.SQUARE_ENVIRONMENT === 'production'
      ? SQUARE_API.production
      : SQUARE_API.sandbox;

    // Fetch catalog items and images from Square
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

    // Build a map of image IDs to URLs
    const imageMap = {};
    const items = [];

    for (const obj of catalogResult.objects || []) {
      if (obj.type === 'IMAGE' && obj.image_data) {
        imageMap[obj.id] = obj.image_data.url;
      }
    }

    // Process items and attach image URLs
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
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  } catch (error) {
    console.error('Catalog fetch error:', error);
    return errorResponse('Internal server error', 500, corsHeaders);
  }
}

function errorResponse(message, status, corsHeaders = CORS_HEADERS) {
  return new Response(
    JSON.stringify({ success: false, error: message }),
    {
      status,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    }
  );
}
