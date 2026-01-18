/**
 * Cloudflare Worker for Square Photography Store
 *
 * This worker provides a health check endpoint.
 * The storefront currently uses pre-built Square payment links
 * and static inventory.json, so no dynamic API calls are needed.
 *
 * If dynamic catalog/checkout functionality is needed in the future,
 * add SQUARE_ACCESS_TOKEN and SQUARE_LOCATION_ID secrets via:
 *   wrangler secret put SQUARE_ACCESS_TOKEN
 *   wrangler secret put SQUARE_LOCATION_ID
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': 'https://www.cxhernandez.com',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// For local development, allow localhost
const DEV_CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
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
