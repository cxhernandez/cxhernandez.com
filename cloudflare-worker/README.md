# Photography Store API (Cloudflare Worker)

This Cloudflare Worker handles Square payment processing for the photography store.

## Setup

### 1. Install Wrangler CLI

```bash
npm install -g wrangler
```

### 2. Login to Cloudflare

```bash
wrangler login
```

### 3. Get Square Credentials

1. Go to [Square Developer Dashboard](https://developer.squareup.com/apps)
2. Create a new application (or use existing)
3. Get your **Application ID** and **Access Token**
4. Get your **Location ID** from the Locations tab

### 4. Set Secrets

```bash
cd cloudflare-worker

# Set your Square access token (keep this secret!)
wrangler secret put SQUARE_ACCESS_TOKEN
# Paste your token when prompted

# Set your Square location ID
wrangler secret put SQUARE_LOCATION_ID
# Paste your location ID when prompted
```

### 5. Update Configuration

Edit `wrangler.toml`:
- Change `SQUARE_ENVIRONMENT` to `"production"` when ready to go live

Edit `src/index.js`:
- Update `CORS_HEADERS['Access-Control-Allow-Origin']` to your actual domain

### 6. Deploy

```bash
# Test locally first
npm run dev

# Deploy to Cloudflare
npm run deploy
```

### 7. Update Frontend

After deploying, update the `WORKER_URL` in `/store.html`:

```javascript
const SQUARE_APP_ID = 'your-square-app-id';
const SQUARE_LOCATION_ID = 'your-location-id';
const WORKER_URL = 'https://photography-store-api.your-subdomain.workers.dev';
```

## API Endpoints

### POST /create-payment

Creates a payment using Square.

**Request:**
```json
{
  "sourceId": "cnon:card-nonce-from-square-sdk",
  "amount": 25000,
  "item": "portrait",
  "title": "Portrait Session",
  "email": "customer@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "paymentId": "payment-id",
  "status": "COMPLETED"
}
```

### GET /health

Health check endpoint.

## Testing

Use Square's sandbox environment for testing:
- Test card number: `4532 0123 4567 8901`
- Any future expiration date
- Any CVV

## Security Notes

- Never commit your `SQUARE_ACCESS_TOKEN` to git
- The worker validates CORS to only allow requests from your domain
- All sensitive credentials are stored as Cloudflare secrets
