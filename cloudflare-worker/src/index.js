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
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// Square API base URLs
const SQUARE_API = {
  sandbox: 'https://connect.squareupsandbox.com/v2',
  production: 'https://connect.squareup.com/v2',
};

export default {
  async fetch(request, env, ctx) {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const url = new URL(request.url);

    // Route handling
    if (url.pathname === '/create-payment' && request.method === 'POST') {
      return handleCreatePayment(request, env);
    }

    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok' }), {
        headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({ error: 'Not found' }), {
      status: 404,
      headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
    });
  },
};

async function handleCreatePayment(request, env) {
  try {
    const body = await request.json();
    const { sourceId, amount, item, title, email } = body;

    // Validate required fields
    if (!sourceId || !amount) {
      return errorResponse('Missing required fields: sourceId and amount', 400);
    }

    // Validate amount is a positive integer (cents)
    if (!Number.isInteger(amount) || amount <= 0) {
      return errorResponse('Invalid amount', 400);
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
          headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
        }
      );
    } else {
      // Extract error message from Square response
      const errorMessage = paymentResult.errors?.[0]?.detail || 'Payment failed';
      console.error('Square payment error:', JSON.stringify(paymentResult.errors));
      return errorResponse(errorMessage, 400);
    }
  } catch (error) {
    console.error('Payment processing error:', error);
    return errorResponse('Internal server error', 500);
  }
}

function errorResponse(message, status) {
  return new Response(
    JSON.stringify({ success: false, error: message }),
    {
      status,
      headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
    }
  );
}
