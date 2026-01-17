#!/usr/bin/env python3
"""
Enrich inventory.json entries by querying Square payment links.

Usage:
  python3 scripts/enrich_inventory.py static/files/store/inventory.json

Optional environment variables:
  SQUARE_ACCESS_TOKEN      - If set, will try to match against API payment links
  SQUARE_ENVIRONMENT       - sandbox|production (default: sandbox)

If API matching fails or no token is provided, the script will scrape the
checkout page directly to extract product details.
"""
import sys
import json
import os
import re
import html
import urllib.request
import urllib.parse


def api_base():
    env = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')
    if env == 'production':
        return 'https://connect.squareup.com/v2'
    return 'https://connect.squareupsandbox.com/v2'


def fetch_payment_links(token, limit=100):
    base = api_base()
    headers = {
        'Square-Version': '2024-01-18',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    results = []
    cursor = None
    while True:
        qs = {'limit': str(limit)}
        if cursor:
            qs['cursor'] = cursor
        url = f"{base}/online-checkout/payment-links?" + urllib.parse.urlencode(qs)
        req = urllib.request.Request(url, headers=headers, method='GET')
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as e:
            print('HTTP error while listing payment links:', e.read().decode(), file=sys.stderr)
            break
        except Exception as e:
            print('Error while listing payment links:', e, file=sys.stderr)
            break

        items = data.get('payment_links', [])
        results.extend(items)
        cursor = data.get('cursor')
        if not cursor:
            break
    return results


def match_payment_link(links, target_url):
    t = target_url.strip()
    resolved_t = None

    # Try to resolve short/redirecting URLs (e.g., square.link) to their final destination
    try:
        resolved_t = resolve_url(t)
    except Exception:
        pass

    for pl in links:
        url = pl.get('url')
        long_url = pl.get('long_url')
        if not url:
            continue

        # Direct match
        if url == t or long_url == t:
            return pl

        # Match resolved URL against payment link URL or long_url
        if resolved_t:
            if url == resolved_t or long_url == resolved_t:
                return pl
            # Also try matching by path (checkout IDs)
            try:
                resolved_path = urllib.parse.urlparse(resolved_t).path
                pl_path = urllib.parse.urlparse(url).path
                if resolved_path and pl_path and resolved_path == pl_path:
                    return pl
                if long_url:
                    long_path = urllib.parse.urlparse(long_url).path
                    if resolved_path and long_path and resolved_path == long_path:
                        return pl
            except Exception:
                pass

        # Fallback: partial path matching
        try:
            up = urllib.parse.urlparse(url)
            tp = urllib.parse.urlparse(t)
            if up.path and tp.path and up.path.endswith(tp.path):
                return pl
        except Exception:
            pass
    return None


def resolve_url(url):
    """Follow redirects and return the final URL (or None on error)."""
    try:
        req = urllib.request.Request(url, method='GET', headers={'User-Agent': 'enrich-inventory-script/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.geturl()
    except Exception:
        return None


def scrape_checkout_page(url):
    """
    Scrape a Square checkout page to extract product details.
    Works for both short square.link URLs and full checkout.square.site URLs.
    Returns a dict with name, description, price_display, image or None on failure.
    """
    try:
        # Resolve short URLs first
        if 'square.link' in url:
            resolved = resolve_url(url)
            if resolved:
                url = resolved

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode('utf-8', errors='ignore')

        result = {}

        # Extract title from og:title or <title>
        og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', content, re.I)
        if not og_title:
            og_title = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']', content, re.I)
        if og_title:
            name = html.unescape(og_title.group(1))
            # Clean up common suffixes like " - Business Name"
            name = re.sub(r'\s*[-–|]\s*[^-–|]+$', '', name).strip()
            result['name'] = name
        else:
            title = re.search(r'<title>([^<]+)</title>', content, re.I)
            if title:
                name = html.unescape(title.group(1).split('|')[0].strip())
                name = re.sub(r'\s*[-–|]\s*[^-–|]+$', '', name).strip()
                result['name'] = name

        # Extract description from og:description
        og_desc = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', content, re.I)
        if not og_desc:
            og_desc = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']', content, re.I)
        if og_desc:
            desc = html.unescape(og_desc.group(1))
            # Skip placeholder values
            if desc.lower() not in ('description', 'desc', ''):
                result['description'] = desc

        # Extract image from og:image
        og_image = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', content, re.I)
        if not og_image:
            og_image = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', content, re.I)
        if og_image:
            img_url = html.unescape(og_image.group(1))
            # Try to get original quality by removing resize params
            img_url = re.sub(r'\?.*$', '', img_url)
            # Also look for original.jpeg in the page for higher quality
            orig_match = re.search(r'(https://items-images-production[^"\']+/original\.jpeg)', content)
            if orig_match:
                img_url = html.unescape(orig_match.group(1))
            result['image'] = img_url

        # Try to extract price from page content
        # Look for "amount" fields in JSON data embedded in page
        amount_matches = re.findall(r'"amount"\s*:\s*(\d+)', content)
        if amount_matches:
            # Convert cents to dollars and find unique prices
            prices_cents = [int(a) for a in amount_matches if int(a) > 100]  # Filter out likely non-prices
            if prices_cents:
                unique_prices = sorted(set(p / 100 for p in prices_cents))
                if len(unique_prices) > 1:
                    result['price_display'] = f"From ${unique_prices[0]:.2f}"
                else:
                    result['price_display'] = f"${unique_prices[0]:.2f}"

        # Fallback: look for dollar amounts in content
        if not result.get('price_display'):
            all_prices = re.findall(r'\$(\d+(?:\.\d{2})?)', content)
            if all_prices:
                unique_prices = sorted(set(float(p) for p in all_prices))
                if len(unique_prices) > 1:
                    result['price_display'] = f"From ${unique_prices[0]:.2f}"
                elif unique_prices:
                    result['price_display'] = f"${unique_prices[0]:.2f}"

        return result if result.get('name') else None

    except Exception as e:
        print(f'  Scrape error: {e}', file=sys.stderr)
        return None


def enrich_entry(entry, links, index, entry_type='print'):
    """Enrich a single entry using API matching or scraping."""
    url = entry.get('url')
    if not url:
        return entry

    # First try API matching if we have links
    if links:
        pl = match_payment_link(links, url)
        if pl:
            qp = pl.get('quick_pay') or {}
            name = qp.get('name') or entry.get('name') or pl.get('description')
            price_money = qp.get('price_money') or {}
            amount = price_money.get('amount')
            price_display = f"${amount/100:.2f}" if isinstance(amount, int) else None

            enriched_entry = {
                'url': url,  # Keep original short URL
                'name': name,
                'price': amount if isinstance(amount, int) else None,
                'price_display': price_display,
                'description': pl.get('description') or entry.get('description'),
            }
            if entry.get('image'):
                enriched_entry['image'] = entry.get('image')
            if entry.get('icon'):
                enriched_entry['icon'] = entry.get('icon')

            print(f'[{entry_type} {index+1}] API matched: {name}')
            return enriched_entry

    # Fallback: scrape the checkout page
    print(f'[{entry_type} {index+1}] Scraping {url}...')
    scraped = scrape_checkout_page(url)
    if scraped:
        enriched_entry = {
            'url': url,
            'name': scraped.get('name') or entry.get('name'),
            'price_display': scraped.get('price_display') or entry.get('price_display'),
            'description': scraped.get('description') or entry.get('description'),
            'image': entry.get('image') or scraped.get('image'),
        }
        if entry.get('icon'):
            enriched_entry['icon'] = entry.get('icon')

        print(f'[{entry_type} {index+1}] Scraped: {enriched_entry.get("name")}')
        return enriched_entry

    print(f'[{entry_type} {index+1}] Could not enrich {url}')
    return entry


def enrich_inventory(input_path):
    token = os.environ.get('SQUARE_ACCESS_TOKEN')

    with open(input_path, 'r') as f:
        data = json.load(f)

    prints = data.get('prints', [])
    services = data.get('services', [])

    # Try to fetch payment links from API if token provided
    links = []
    if token:
        print('Fetching payment links from Square API...')
        links = fetch_payment_links(token)
        print(f'Loaded {len(links)} payment links')
    else:
        print('No SQUARE_ACCESS_TOKEN set, will scrape checkout pages directly')

    # Enrich prints
    enriched = []
    for i, p in enumerate(prints):
        entry = p if isinstance(p, dict) else {'url': p}
        enriched.append(enrich_entry(entry, links, i, 'print'))

    # Enrich services
    enriched_services = []
    for i, s in enumerate(services):
        entry = s if isinstance(s, dict) else {'url': s}
        enriched_services.append(enrich_entry(entry, links, i, 'service'))

    out = dict(data)
    out['prints'] = enriched
    out['services'] = enriched_services

    # Write back to the original file (overwrite)
    with open(input_path, 'w') as f:
        json.dump(out, f, indent=4)

    print(f'Wrote enriched inventory to {input_path}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: enrich_inventory.py path/to/inventory.json', file=sys.stderr)
        sys.exit(2)
    enrich_inventory(sys.argv[1])
