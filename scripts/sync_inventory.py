#!/usr/bin/env python3
"""
Sync inventory from Square Catalog API.

Fetches all items from your Square catalog and creates payment links
for each item to generate checkout URLs.

Usage:
  python3 scripts/sync_inventory.py static/files/store/inventory.json

Required environment variables:
  SQUARE_ACCESS_TOKEN      - Your Square API access token

Optional environment variables:
  SQUARE_ENVIRONMENT       - sandbox|production (default: production)
"""
import sys
import json
import os
import urllib.request
import urllib.parse
import uuid


def api_base():
    env = os.environ.get('SQUARE_ENVIRONMENT', 'production')
    if env == 'production':
        return 'https://connect.squareup.com/v2'
    return 'https://connect.squareupsandbox.com/v2'


def api_headers(token):
    return {
        'Square-Version': '2024-01-18',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }


def fetch_catalog_items(token):
    """Fetch all ITEM objects from the catalog."""
    base = api_base()
    headers = api_headers(token)

    results = []
    cursor = None
    while True:
        qs = {'types': 'ITEM'}
        if cursor:
            qs['cursor'] = cursor
        url = f"{base}/catalog/list?" + urllib.parse.urlencode(qs)
        req = urllib.request.Request(url, headers=headers, method='GET')
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as e:
            print('HTTP error listing catalog:', e.read().decode(), file=sys.stderr)
            break
        except Exception as e:
            print('Error listing catalog:', e, file=sys.stderr)
            break

        objects = data.get('objects', [])
        results.extend(objects)
        cursor = data.get('cursor')
        if not cursor:
            break
    return results


def fetch_catalog_images(token, image_ids):
    """Batch retrieve image objects by ID."""
    if not image_ids:
        return {}

    base = api_base()
    headers = api_headers(token)

    url = f"{base}/catalog/batch-retrieve"
    body = json.dumps({
        'object_ids': list(image_ids),
        'include_related_objects': False
    }).encode('utf-8')

    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
    except Exception as e:
        print(f'Error fetching images: {e}', file=sys.stderr)
        return {}

    images = {}
    for obj in data.get('objects', []):
        if obj.get('type') == 'IMAGE':
            image_data = obj.get('image_data', {})
            images[obj['id']] = image_data.get('url')
    return images


def create_payment_link(token, item_name, variation_id, price_money):
    """Create a payment link for an item variation."""
    base = api_base()
    headers = api_headers(token)

    url = f"{base}/online-checkout/payment-links"
    body = json.dumps({
        'idempotency_key': str(uuid.uuid4()),
        'quick_pay': {
            'name': item_name,
            'price_money': price_money,
            'location_id': get_location_id(token),
        }
    }).encode('utf-8')

    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
            pl = data.get('payment_link', {})
            return pl.get('url')
    except urllib.error.HTTPError as e:
        error = e.read().decode()
        print(f'  Error creating payment link: {error}', file=sys.stderr)
        return None
    except Exception as e:
        print(f'  Error creating payment link: {e}', file=sys.stderr)
        return None


_location_id_cache = None

def get_location_id(token):
    """Get the main location ID for the merchant."""
    global _location_id_cache
    if _location_id_cache:
        return _location_id_cache

    base = api_base()
    headers = api_headers(token)

    url = f"{base}/locations"
    req = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
            locations = data.get('locations', [])
            if locations:
                _location_id_cache = locations[0]['id']
                return _location_id_cache
    except Exception as e:
        print(f'Error fetching locations: {e}', file=sys.stderr)
    return None


def format_price(variations):
    """Format price display and return lowest price_money from variations."""
    prices = []
    for var in variations:
        var_data = var.get('item_variation_data', {})
        price_money = var_data.get('price_money')
        if price_money and isinstance(price_money.get('amount'), int):
            prices.append((price_money['amount'], price_money))

    if not prices:
        return None, None

    prices.sort(key=lambda x: x[0])
    lowest = prices[0][0] / 100

    if len(prices) > 1:
        return f"From ${lowest:.2f}", prices[0][1]
    return f"${lowest:.2f}", prices[0][1]


def categorize_item(item_data):
    """Determine if item is a 'print' or 'service' based on product_type."""
    product_type = item_data.get('product_type', '')
    if product_type == 'APPOINTMENTS_SERVICE':
        return 'service'
    return 'print'


def sync_inventory(output_path):
    token = os.environ.get('SQUARE_ACCESS_TOKEN')
    if not token:
        print('Error: SQUARE_ACCESS_TOKEN environment variable is required', file=sys.stderr)
        sys.exit(1)

    print('Fetching catalog items from Square API...')
    catalog_items = fetch_catalog_items(token)
    print(f'Found {len(catalog_items)} catalog items')

    # Collect all image IDs
    image_ids = set()
    for item in catalog_items:
        item_data = item.get('item_data', {})
        for img_id in item_data.get('image_ids', []):
            image_ids.add(img_id)

    # Fetch images
    images = {}
    if image_ids:
        print(f'Fetching {len(image_ids)} images...')
        images = fetch_catalog_images(token, image_ids)

    prints = []
    services = []

    for item in catalog_items:
        item_data = item.get('item_data', {})
        name = item_data.get('name')
        if not name:
            continue

        variations = item_data.get('variations', [])
        price_display, price_money = format_price(variations)

        if not price_money:
            print(f'  Skipping {name} (no price)')
            continue

        # Create payment link for this item
        print(f'  Creating payment link for "{name}"...')
        checkout_url = create_payment_link(token, name, None, price_money)

        if not checkout_url:
            print(f'  Failed to create payment link for "{name}"')
            continue

        # Get image
        image_url = None
        img_ids = item_data.get('image_ids', [])
        if img_ids and img_ids[0] in images:
            image_url = images[img_ids[0]]

        entry = {
            'url': checkout_url,
            'name': name,
            'price_display': price_display,
            'description': item_data.get('description'),
            'image': image_url,
        }

        category = categorize_item(item_data)
        if category == 'service':
            print(f'  [service] {name} -> {checkout_url}')
            services.append(entry)
        else:
            print(f'  [print] {name} -> {checkout_url}')
            prints.append(entry)

    inventory = {
        'prints': prints,
        'services': services,
    }

    with open(output_path, 'w') as f:
        json.dump(inventory, f, indent=4)

    print(f'\nWrote {len(prints)} prints and {len(services)} services to {output_path}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Sync inventory from Square Catalog API')
    parser.add_argument('output', help='Path to output inventory.json')
    args = parser.parse_args()
    sync_inventory(args.output)
