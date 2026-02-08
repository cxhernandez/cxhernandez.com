#!/usr/bin/env python3
"""
Consolidated CLI tool for cxhernandez.com scripts.

Available commands:
  enrich-inventory  Enrich inventory.json with Square payment data
  scrape-pubs       Fetch publication data from Semantic Scholar
  update-cv         Update CV with citation counts and GitHub stats
  generate-pdf      Generate PDF version of CV from markdown

Usage:
  python cli.py <command> [options]
  python cli.py enrich-inventory path/to/inventory.json
  python cli.py scrape-pubs -a <author-id> -o publications.txt
  python cli.py update-cv -c _includes/cv.md -a <author-id>
  python cli.py generate-pdf
"""

import argparse
import codecs
import html
import json
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Optional dependencies with graceful fallback
try:
    import pandas as pd
    pd.options.display.max_colwidth = 500
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False

try:
    import markdown
    from weasyprint import CSS, HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENRICH INVENTORY - Square payment link enrichment
# ============================================================================

def api_base():
    """Get Square API base URL based on environment."""
    env = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')
    if env == 'production':
        return 'https://connect.squareup.com/v2'
    return 'https://connect.squareupsandbox.com/v2'


def format_price_display(price_min, price_max):
    """Format price range for display."""
    if price_min == price_max:
        return f"${price_min:.2f}"
    else:
        return f"${price_min:.2f} - ${price_max:.2f}"


def fetch_payment_links(token, limit=100):
    """Fetch payment links from Square API."""
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
    """Match a target URL against payment links."""
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
    """Scrape a Square checkout page to extract product details."""
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
            # Filter out likely non-prices (less than $1 or more than $10000)
            prices_cents = [int(a) for a in amount_matches if 100 <= int(a) <= 1000000]
            if prices_cents:
                unique_prices = sorted(set(p / 100 for p in prices_cents))
                result['price_min'] = unique_prices[0]
                result['price_max'] = unique_prices[-1]
                result['price_display'] = format_price_display(unique_prices[0], unique_prices[-1])

        # Fallback: look for dollar amounts in content
        if not result.get('price_min'):
            all_prices = re.findall(r'\$(\d+(?:\.\d{2})?)', content)
            if all_prices:
                unique_prices = sorted(set(float(p) for p in all_prices if 1 <= float(p) <= 10000))
                if unique_prices:
                    result['price_min'] = unique_prices[0]
                    result['price_max'] = unique_prices[-1]
                    result['price_display'] = format_price_display(unique_prices[0], unique_prices[-1])

        return result if result.get('name') else None

    except Exception as e:
        print(f'  Scrape error: {e}', file=sys.stderr)
        return None


def enrich_entry(entry, links, index, entry_type='print'):
    """Enrich a single entry using API matching or scraping."""
    url = entry.get('url')
    if not url:
        return entry

    enriched = dict(entry)
    updates = {}

    # First try API matching if we have links
    if links:
        pl = match_payment_link(links, url)
        if pl:
            qp = pl.get('quick_pay') or {}
            price_money = qp.get('price_money') or {}
            amount = price_money.get('amount')
            price_dollars = amount / 100 if isinstance(amount, int) else None

            if name := (qp.get('name') or pl.get('description')):
                updates['name'] = name
            if price_dollars is not None:
                updates['price_min'] = price_dollars
                updates['price_max'] = price_dollars
                updates['price_display'] = f"${price_dollars:.2f}"
            if desc := pl.get('description'):
                updates['description'] = desc

            enriched.update(updates)
            print(f'[{entry_type} {index+1}] API matched: {enriched.get("name")}')
            return enriched

    # Fallback: scrape the checkout page
    print(f'[{entry_type} {index+1}] Scraping {url}...')
    if scraped := scrape_checkout_page(url):
        for key in ('name', 'price_min', 'price_max', 'price_display', 'description'):
            if scraped.get(key) is not None:
                updates[key] = scraped[key]
        # Only update image if entry doesn't already have one
        if scraped.get('image') and not entry.get('image'):
            updates['image'] = scraped['image']

        enriched.update(updates)
        print(f'[{entry_type} {index+1}] Scraped: {enriched.get("name")}')
        return enriched

    print(f'[{entry_type} {index+1}] Could not enrich {url}')
    return entry


def cmd_enrich_inventory(args):
    """Enrich inventory.json entries by querying Square payment links."""
    token = os.environ.get('SQUARE_ACCESS_TOKEN')

    with open(args.inventory, 'r') as f:
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
    with open(args.inventory, 'w') as f:
        json.dump(out, f, indent=4)

    print(f'Wrote enriched inventory to {args.inventory}')


# ============================================================================
# SEMANTIC SCHOLAR SCRAPER - Publication scraper
# ============================================================================

def title_case(text):
    """Convert text to title case, keeping small words lowercase."""
    small_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'in',
                   'nor', 'of', 'on', 'or', 'so', 'the', 'to', 'up', 'yet'}
    words = text.split()
    result = []
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in small_words:
            result.append(word.capitalize())
        else:
            result.append(word.lower())
    return ' '.join(result)


def is_preprint_doi(doi):
    """Check if a DOI points to a preprint server rather than a published journal."""
    if not doi:
        return False
    doi_lower = doi.lower()
    # Common preprint server DOI patterns
    preprint_patterns = [
        'arxiv',
        'biorxiv',
        'medrxiv',
        'chemrxiv',
        '10.1101/',  # bioRxiv/medRxiv DOI prefix
        '10.26434/',  # ChemRxiv DOI prefix
    ]
    return any(pattern in doi_lower for pattern in preprint_patterns)


def get_journal_from_pubmed(pubmed_id):
    """Look up journal name from PubMed ID using NCBI E-utilities API."""
    if not REQUESTS_AVAILABLE:
        return None
    
    try:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params = {
            "db": "pubmed",
            "id": pubmed_id,
            "retmode": "json"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract journal name from the result
        result = data.get("result", {}).get(str(pubmed_id), {})
        journal = result.get("fulljournalname") or result.get("source")
        if journal:
            return title_case(journal)
    except Exception as e:
        logger.debug(f"Failed to fetch journal from PubMed {pubmed_id}: {e}")
    
    return None


def clean_journal_name(venue, external_ids=None, doi=None):
    """Clean and format venue/journal names.
    
    Priority order:
    1. If there's a published DOI (not preprint), use the venue from API
    2. If there's a PubMed ID and venue is a preprint server, look up actual journal
    3. If Zenodo DOI, return 'Zenodo'
    4. If only preprint IDs exist (ArXiv, bioRxiv, etc.), return the preprint server name
    5. Fall back to cleaned venue name
    """
    # Check for Zenodo first (software releases)
    if doi and 'zenodo' in doi.lower():
        return 'Zenodo'

    # Check DOI patterns for conference abstracts
    if doi:
        # Biophysical Journal abstracts have pattern like "10.1016/j.bpj.YYYY.MM.XXXX"
        if 'j.bpj.' in doi.lower() and len(doi.split('.')) >= 5:
            return 'Biophysical Journal (Abstract)'

    # Check if we have a published DOI (not from a preprint server)
    has_published_doi = doi and not is_preprint_doi(doi)
    
    # If we have a published DOI and a venue, use the venue (it's the real journal)
    if has_published_doi and venue:
        venue_cleaned = venue.strip()
        # Don't return preprint venue names if we have a published DOI
        if venue_cleaned.lower() not in ['arxiv', 'biorxiv', 'medrxiv', 'chemrxiv']:
            return title_case(venue_cleaned)
    
    # Check if we have a PubMed ID - indicates the paper was published
    # Even if the DOI is a preprint DOI, having a PubMed ID means it was published
    if external_ids and 'PubMed' in external_ids:
        pubmed_id = external_ids['PubMed']
        # If venue is a preprint server name, look up the real journal from PubMed
        venue_lower = (venue or '').lower()
        if venue_lower in ['arxiv', 'biorxiv', 'medrxiv', 'chemrxiv', '']:
            journal = get_journal_from_pubmed(pubmed_id)
            if journal:
                return journal
    
    # If we have external IDs, check for preprint IDs
    if external_ids:
        has_pubmed = 'PubMed' in external_ids
        has_arxiv = 'ArXiv' in external_ids
        venue_is_empty = not venue or not venue.strip()
        
        # Return preprint server name if:
        # - We have an ArXiv ID AND no PubMed ID AND (no venue OR venue is a preprint server)
        # - This handles cases like institutional repository DOIs that aren't journals
        if has_arxiv and not has_pubmed:
            venue_lower = (venue or '').lower().strip()
            if venue_is_empty or venue_lower in ['arxiv', 'biorxiv', 'medrxiv', 'chemrxiv']:
                return 'arXiv'

    if not venue:
        return ""

    # Special case for arXiv in venue name (only if no published DOI)
    if venue.lower().startswith('arxiv') and not has_published_doi:
        return 'arXiv'

    # Apply title case
    return title_case(venue.strip())


def _get_semantic_scholar_headers():
    """Get headers for Semantic Scholar API, including API key if available."""
    headers = {}
    api_key = os.environ.get('SEMANTIC_SCHOLAR_API_KEY')
    if api_key:
        headers['x-api-key'] = api_key
    return headers


def get_author_publications(author_id, max_retries=5, backoff_factor=4):
    """Fetch author publications from Semantic Scholar API."""
    if not REQUESTS_AVAILABLE:
        logger.error("requests library is required for this command. Install with: conda install requests")
        sys.exit(1)
    if not TENACITY_AVAILABLE:
        logger.error("tenacity library is required for this command. Install with: conda install tenacity")
        sys.exit(1)

    base_url = "https://api.semanticscholar.org/graph/v1/author"
    url = f"{base_url}/{author_id}"
    headers = _get_semantic_scholar_headers()

    params = {
        "fields": "authorId,name,papers.title,papers.paperId,papers.year,"
                 "papers.citationCount,papers.authors,papers.venue,"
                 "papers.externalIds,papers.openAccessPdf"
    }

    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=1, min=backoff_factor, max=60),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _fetch():
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                wait_time = int(retry_after)
                logger.warning(f"Rate limited, Retry-After: {wait_time}s")
                time.sleep(wait_time)
        response.raise_for_status()
        return response.json()

    logger.info(f"Fetching publications for author {author_id}")
    result = _fetch()
    logger.info("Successfully fetched publication data from Semantic Scholar")
    return result


def normalize_title(title):
    """Normalize title for comparison (lowercase, no punctuation)."""
    import string
    # Remove punctuation and convert to lowercase
    normalized = title.lower()
    normalized = normalized.translate(str.maketrans('', '', string.punctuation))
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    return normalized


def is_preprint(external_ids, venue):
    """Check if a paper is a preprint."""
    if not external_ids:
        return False

    # Check for preprint identifiers in external IDs
    preprint_ids = ['ArXiv', 'bioRxiv', 'medRxiv', 'ChemRxiv']
    if any(pid in external_ids for pid in preprint_ids):
        return True

    # Check venue name for preprint indicators
    if venue:
        venue_lower = venue.lower()
        if any(preprint in venue_lower for preprint in ['arxiv', 'biorxiv', 'medrxiv', 'chemrxiv']):
            return True

    return False


def consolidate_papers(papers, merge_external_ids=False):
    """Group papers by normalized title and consolidate preprint + published versions.

    Args:
        papers: List of paper dicts from Semantic Scholar API.
        merge_external_ids: If True, merge externalIds from all versions into the
            consolidated paper (useful for lookups by DOI/ArXiv).

    Returns:
        List of consolidated paper dicts with summed citation counts.
    """
    papers_by_title = {}

    for paper in papers:
        if not paper.get('title') or not paper.get('paperId'):
            continue

        external_ids = paper.get('externalIds', {})
        doi = external_ids.get('DOI') if external_ids else None

        if doi and 'zenodo' in doi.lower():
            continue
        if doi and 'j.bpj.' in doi.lower() and len(doi.split('.')) >= 5:
            continue

        normalized_title = normalize_title(paper['title'])

        if normalized_title not in papers_by_title:
            papers_by_title[normalized_title] = []

        papers_by_title[normalized_title].append(paper)

    consolidated_papers = []

    for normalized_title, paper_group in papers_by_title.items():
        if len(paper_group) == 1:
            consolidated_papers.append(paper_group[0])
        else:
            preprints = []
            published = []

            for paper in paper_group:
                external_ids = paper.get('externalIds', {})
                venue = paper.get('venue', '')

                if is_preprint(external_ids, venue):
                    preprints.append(paper)
                else:
                    published.append(paper)

            base_paper = published[0] if published else paper_group[0]

            total_citations = sum(p.get('citationCount', 0) for p in paper_group)

            consolidated = dict(base_paper)
            consolidated['citationCount'] = total_citations

            if merge_external_ids:
                all_external_ids = {}
                for p in paper_group:
                    if p.get('externalIds'):
                        all_external_ids.update(p['externalIds'])
                consolidated['externalIds'] = all_external_ids

            consolidated_papers.append(consolidated)

            if len(paper_group) > 1:
                logger.info(f"Consolidated {len(paper_group)} versions of '{base_paper.get('title', '')[:50]}...' "
                           f"(total citations: {total_citations})")

    return consolidated_papers


def get_table(author_data, bold_author_name=None):
    """Parse author data and create publication table.

    Args:
        author_data: Author data from Semantic Scholar API
        bold_author_name: Optional author name to bold in the output (for HTML/markdown)
    """
    if not PANDAS_AVAILABLE:
        logger.error("pandas library is required for this command. Install with: conda install pandas")
        sys.exit(1)

    papers = author_data.get('papers', [])

    if not papers:
        logger.warning("No papers found for this author")
        return pd.DataFrame()

    consolidated_papers = consolidate_papers(papers)

    # Build lists for DataFrame
    titles = []
    links = []
    authors_list = []
    journals = []
    citations = []
    years = []

    for paper in consolidated_papers:
        titles.append(paper['title'])
        links.append(f"https://www.semanticscholar.org/paper/{paper['paperId']}")

        # Format authors
        paper_authors = paper.get('authors', [])
        if paper_authors:
            author_names = [a.get('name', '') for a in paper_authors if a.get('name')]

            # Convert to initials + last name format
            formatted_names = []
            for name in author_names:
                parts = name.split()
                if len(parts) > 1:
                    # Get initials from all parts except last
                    initials = ''.join([p[0].upper() for p in parts[:-1]])
                    # Get last name
                    last_name = parts[-1]
                    formatted = f"{initials} {last_name}"
                else:
                    # Single name, keep as is
                    formatted = name
                formatted_names.append(formatted)

            # Bold the specified author name if provided
            if bold_author_name:
                formatted_names = [
                    f'<strong>{name}</strong>' if any(part in bold_author_name.split() for part in name.split()) else name
                    for name in formatted_names
                ]

            if len(formatted_names) > 3:
                authors_str = ', '.join(formatted_names[:3]) + ', ...'
            else:
                authors_str = ', '.join(formatted_names)
        else:
            authors_str = ""
        authors_list.append(authors_str)

        # Journal/Venue - use external IDs to improve venue detection
        venue = paper.get('venue', '')
        external_ids = paper.get('externalIds', {})
        doi = external_ids.get('DOI') if external_ids else None
        journals.append(clean_journal_name(venue, external_ids, doi))

        # Citations (now potentially summed from multiple versions)
        cite_count = paper.get('citationCount', 0)
        citations.append(str(cite_count) if cite_count else "-")

        # Year
        year = paper.get('year', '')
        years.append(str(year) if year else "")

    # Create DataFrame
    data = {
        "Title": titles,
        "Link": links,
        "Author(s)": authors_list,
        "Journal": journals,
        "Citations": citations,
        "Year": years,
    }

    table = pd.DataFrame(data)

    # Sort by citation count (descending), then year (descending)
    table['_cite_count'] = pd.to_numeric(
        table['Citations'].replace('-', '0').str.replace('*', ''),
        errors='coerce'
    ).fillna(0).astype(int)
    table['_year'] = pd.to_numeric(table['Year'], errors='coerce').fillna(0).astype(int)
    table = table.sort_values(by=['_cite_count', '_year'], ascending=[False, False])
    table = table.drop(columns=['_cite_count', '_year'])

    # Reset index starting from 1
    table.index = range(1, len(table) + 1)

    return table[["Title", "Link", "Author(s)", "Journal", "Citations", "Year"]]


def get_html(table):
    """Convert table to HTML format."""
    links = dict(zip(table.Title, table.Link))
    table = table.drop("Link", axis=1)

    # Create copy to avoid modifying original
    table = table.copy()

    # Convert markdown bold to HTML bold in Author(s) column
    if 'Author(s)' in table.columns:
        table['Author(s)'] = table['Author(s)'].str.replace(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', regex=True)

    return table.to_html(
        formatters={"Title": lambda x: '<a href="%s">%s</a>' % (links[x], x)},
        escape=False,
        na_rep="-",
        justify="center",
    ).replace("\n", "")


def get_tab(table):
    """Convert table to tab-separated format."""
    return table.drop("Link", axis=1).to_string(na_rep="0")


# Publisher-specific gradients for fallback (matching frontend)
PUBLISHER_GRADIENTS = {
    'Nature': 'linear-gradient(135deg, #0d47a1, #1976d2)',
    'Biorxiv': 'linear-gradient(135deg, #ff6f00, #ff8f00)',
    'arXiv': 'linear-gradient(135deg, #b31b1b, #c62828)',
    'Journal of Open Source Software': 'linear-gradient(135deg, #1565c0, #1976d2)',
    'Accounts of Chemical Research': 'linear-gradient(135deg, #2e7d32, #388e3c)',
    'default': 'linear-gradient(135deg, #455a64, #607d8b)'
}


def get_fallback_gradient(journal):
    """Get fallback gradient based on journal/publisher name."""
    return PUBLISHER_GRADIENTS.get(journal, PUBLISHER_GRADIENTS['default'])


def fetch_figure_from_pmc(pmcid, timeout=10):
    """Fetch first figure URL from Europe PMC for a given PMC ID.

    Args:
        pmcid: PubMed Central ID (e.g., 'PMC4567604' or '4567604')
        timeout: Request timeout in seconds

    Returns:
        Figure URL string if found and valid, None otherwise
    """
    if not pmcid:
        return None

    # Ensure PMC prefix is present
    if not str(pmcid).upper().startswith('PMC'):
        pmcid = f"PMC{pmcid}"

    try:
        # Fetch fullTextXML to find actual figure filenames
        xml_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
        response = requests.get(xml_url, timeout=timeout)

        if response.status_code != 200:
            logger.debug(f"Failed to fetch fullTextXML for {pmcid}: HTTP {response.status_code}")
            return None

        # Parse XML to find first graphic element with position="float" (main figures)
        import re
        float_graphics = re.findall(
            r'<graphic[^>]*xlink:href="([^"]+)"[^>]*position="float"',
            response.text
        )

        if not float_graphics:
            # Fallback: try any graphic element
            all_graphics = re.findall(r'<graphic[^>]*xlink:href="([^"]+)"', response.text)
            if not all_graphics:
                logger.debug(f"No graphics found in fullTextXML for {pmcid}")
                return None
            figure_name = all_graphics[0]
        else:
            figure_name = float_graphics[0]

        # Skip if it's an external URL
        if figure_name.startswith('http'):
            logger.debug(f"Skipping external graphic URL for {pmcid}")
            return None

        # Construct the figure URL and verify accessibility
        for ext in ['.jpg', '.png', '.gif', '']:
            figure_url = f"https://europepmc.org/articles/{pmcid}/bin/{figure_name}{ext}"
            try:
                head_response = requests.head(figure_url, timeout=5, allow_redirects=True)
                if head_response.status_code == 200:
                    return figure_url
            except requests.RequestException:
                continue

        logger.debug(f"Figure URL not accessible for {pmcid}")
        return None

    except requests.RequestException as e:
        logger.debug(f"Failed to fetch figure for {pmcid}: {e}")
        return None
    except Exception as e:
        logger.debug(f"Error processing figure for {pmcid}: {e}")
        return None


def lookup_pmc_from_pubmed(pubmed_id, timeout=10):
    """Look up PMC ID from PubMed ID using NCBI elink API.

    Args:
        pubmed_id: PubMed ID (e.g., '26488642')
        timeout: Request timeout in seconds

    Returns:
        PMC ID string (e.g., 'PMC1234567') if found, None otherwise
    """
    if not pubmed_id:
        return None

    try:
        # Use NCBI elink to find PMC ID from PubMed ID
        elink_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&db=pmc&id={pubmed_id}&retmode=json"
        response = requests.get(elink_url, timeout=timeout)

        if response.status_code != 200:
            logger.debug(f"Failed to lookup PMC ID for PubMed {pubmed_id}: HTTP {response.status_code}")
            return None

        data = response.json()

        # Navigate the response structure to find PMC ID
        linksets = data.get('linksets', [])
        for linkset in linksets:
            linksetdbs = linkset.get('linksetdbs', [])
            for linksetdb in linksetdbs:
                if linksetdb.get('linkname') == 'pubmed_pmc':
                    links = linksetdb.get('links', [])
                    if links:
                        # Return first PMC ID with prefix
                        return f"PMC{links[0]}"

        logger.debug(f"No PMC ID found for PubMed {pubmed_id}")
        return None

    except requests.RequestException as e:
        logger.debug(f"Failed to lookup PMC ID for PubMed {pubmed_id}: {e}")
        return None
    except Exception as e:
        logger.debug(f"Error looking up PMC ID for PubMed {pubmed_id}: {e}")
        return None




def check_open_access(pmcid, timeout=10):
    """Check if a PMC article has open access full text available.

    Args:
        pmcid: PubMed Central ID (e.g., 'PMC4567604' or '4567604')
        timeout: Request timeout in seconds

    Returns:
        Boolean indicating if open access full text is available
    """
    if not pmcid:
        return None

    # Ensure PMC prefix is present
    if not str(pmcid).upper().startswith('PMC'):
        pmcid = f"PMC{pmcid}"

    try:
        # Use Europe PMC search API to check open access status
        search_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=PMCID:{pmcid}&resultType=core&format=json"
        response = requests.get(search_url, timeout=timeout)

        if response.status_code != 200:
            logger.debug(f"Failed to check open access for {pmcid}: HTTP {response.status_code}")
            return None

        data = response.json()
        results = data.get('resultList', {}).get('result', [])

        if results:
            # isOpenAccess field indicates if full text is available
            is_open_access = results[0].get('isOpenAccess') == 'Y'
            return is_open_access

        return None

    except requests.RequestException as e:
        logger.debug(f"Failed to check open access for {pmcid}: {e}")
        return None
    except Exception as e:
        logger.debug(f"Error checking open access for {pmcid}: {e}")
        return None



def scrape_pubmed_figure(pubmed_id, timeout=10):
    """Scrape first figure URL from PubMed page.
    
    PubMed pages embed figures using NCBI CDN blob URLs that are publicly accessible.

    Args:
        pubmed_id: PubMed ID (e.g., '30011547')
        timeout: Request timeout in seconds

    Returns:
        Figure URL string if found, None otherwise
    """
    if not pubmed_id:
        return None

    try:
        # Fetch PubMed page
        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/"
        response = requests.get(pubmed_url, timeout=timeout)

        if response.status_code != 200:
            logger.debug(f"Failed to fetch PubMed page for {pubmed_id}: HTTP {response.status_code}")
            return None

        # Extract CDN blob URLs for figures (prefer jpg over gif)
        import re
        jpg_figures = re.findall(
            r'https://cdn\.ncbi\.nlm\.nih\.gov/pmc/blobs/[^"]+\.jpg',
            response.text
        )
        
        if jpg_figures:
            return jpg_figures[0]
        
        # Fallback to gif if no jpg found
        gif_figures = re.findall(
            r'https://cdn\.ncbi\.nlm\.nih\.gov/pmc/blobs/[^"]+\.gif',
            response.text
        )
        
        if gif_figures:
            return gif_figures[0]

        logger.debug(f"No figure URLs found on PubMed page for {pubmed_id}")
        return None

    except requests.RequestException as e:
        logger.debug(f"Failed to scrape PubMed page for {pubmed_id}: {e}")
        return None
    except Exception as e:
        logger.debug(f"Error scraping PubMed page for {pubmed_id}: {e}")
        return None


def fetch_figure_from_semantic_scholar(paper_id, timeout=10):
    """Fetch figure/thumbnail URL from Semantic Scholar API.

    Semantic Scholar provides preview images for many papers on their website.
    This function attempts to extract those image URLs from their API.

    Args:
        paper_id: Semantic Scholar paper ID (e.g., 'e897a9ce6f194f0e420f58c1e7fdb565ee9b98b2')
        timeout: Request timeout in seconds

    Returns:
        Figure URL string if found, None otherwise
    """
    if not paper_id:
        return None

    try:
        # Query Semantic Scholar API for paper details
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
        params = {
            "fields": "openAccessPdf,tldr"
        }

        response = requests.get(url, params=params, timeout=timeout)

        if response.status_code != 200:
            logger.debug(f"Failed to fetch Semantic Scholar data for {paper_id}: HTTP {response.status_code}")
            return None

        data = response.json()

        # Check for openAccessPdf which may contain a URL to the PDF
        # We can potentially extract the first page as an image
        open_access_pdf = data.get('openAccessPdf')
        if open_access_pdf and open_access_pdf.get('url'):
            pdf_url = open_access_pdf['url']
            logger.debug(f"Found open access PDF for {paper_id}: {pdf_url}")
            # Note: We could potentially convert first page of PDF to image here
            # For now, we'll try to scrape the Semantic Scholar page for preview images

        # Try to scrape the Semantic Scholar paper page for preview images
        paper_url = f"https://www.semanticscholar.org/paper/{paper_id}"
        page_response = requests.get(paper_url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        if page_response.status_code == 200:
            # Look for og:image meta tag (preview image)
            import re
            og_image_match = re.search(
                r'<meta\s+property="og:image"\s+content="([^"]+)"',
                page_response.text
            )

            if og_image_match:
                image_url = og_image_match.group(1)
                # Filter out generic Semantic Scholar logo/placeholder images
                if 'semantic-scholar-og.png' not in image_url and image_url.startswith('http'):
                    logger.info(f"Found figure from Semantic Scholar og:image for {paper_id}")
                    return image_url

            # Look for figure thumbnails with multiple patterns
            # Pattern 1: Standard figure/thumb URLs
            figure_patterns = [
                r'https://[^"\']+\.semanticscholar\.org/[^"\']+/(?:figure|thumb)/[^"\']+\.(?:jpg|png|gif|webp)',
                # Pattern 2: ai2-s2-public URLs (common for figures)
                r'https://ai2-s2-public\.s3\.amazonaws\.com/figures/[^"\']+\.(?:jpg|png|gif|webp)',
                # Pattern 3: d3i71xaburhd42 cloudfront URLs (Semantic Scholar CDN)
                r'https://d3i71xaburhd42\.cloudfront\.net/[^"\']+\.(?:jpg|png|gif|webp)',
            ]

            for pattern in figure_patterns:
                figure_matches = re.findall(pattern, page_response.text)
                if figure_matches:
                    logger.info(f"Found figure from Semantic Scholar (pattern match) for {paper_id}: {figure_matches[0][:100]}")
                    return figure_matches[0]

        logger.debug(f"No figure found on Semantic Scholar for {paper_id}")
        return None

    except requests.RequestException as e:
        logger.debug(f"Failed to fetch figure from Semantic Scholar for {paper_id}: {e}")
        return None
    except Exception as e:
        logger.debug(f"Error fetching figure from Semantic Scholar for {paper_id}: {e}")
        return None


def extract_figure_from_pdf(pdf_url, paper_id, output_dir="static/files/publication-figures", timeout=30):
    """Extract first page from PDF as an image and save locally.

    Args:
        pdf_url: URL to PDF file
        paper_id: Semantic Scholar paper ID (used for filename)
        output_dir: Directory to save extracted figures
        timeout: Download timeout in seconds

    Returns:
        Relative URL path to saved figure, or None if extraction fails
    """
    try:
        from pdf2image import convert_from_bytes
        from PIL import Image
        from pathlib import Path
        import tempfile

        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Download PDF
        logger.info(f"Downloading PDF from {pdf_url[:60]}...")
        response = requests.get(pdf_url, timeout=timeout, stream=True)
        response.raise_for_status()

        # Convert first page of PDF to image
        logger.debug("Converting first page of PDF to image...")
        images = convert_from_bytes(
            response.content,
            first_page=1,
            last_page=1,
            dpi=150,  # Good balance between quality and file size
            fmt='jpeg'
        )

        if not images:
            logger.debug("No pages found in PDF")
            return None

        # Get the first page image
        img = images[0]

        # Crop to focus on the content (remove excessive white space)
        # This helps emphasize the paper title and first figure
        width, height = img.size
        # Crop bottom 20% to remove footer/page numbers
        crop_height = int(height * 0.8)
        img = img.crop((0, 0, width, crop_height))

        # Resize if too large (max width 800px to keep file size reasonable)
        max_width = 800
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Save as JPEG
        output_filename = f"{paper_id[:16]}.jpg"
        output_file = output_path / output_filename

        img.save(output_file, "JPEG", quality=85, optimize=True)
        logger.info(f"Extracted first page from PDF: {output_file}")

        # Return relative URL path
        return f"/{output_dir}/{output_filename}"

    except ImportError:
        logger.warning("pdf2image not installed. Cannot extract figures from PDFs. Install with: conda install -c conda-forge pdf2image poppler")
        return None
    except requests.RequestException as e:
        logger.info(f"Failed to download PDF from {pdf_url[:80]}: {e}")
        return None
    except Exception as e:
        logger.info(f"Error extracting figure from PDF {pdf_url[:80]}: {e}")
        return None


def fetch_paper_figure(paper_id=None, pmcid=None, pubmed_id=None, open_access_pdf_url=None, timeout=10):
    """Fetch first figure URL for a paper from multiple sources.

    Tries PDF extraction first for consistent visual style, then falls back to other sources:
    1. If open access PDF available, extract first page from PDF (preferred for consistency)
    2. If no PDF, try Europe PMC via PMC ID
    3. If no PMC ID, try to discover PMC ID from PubMed ID
    4. If Europe PMC fails, scrape figure URL from PubMed page (uses NCBI CDN)

    Args:
        paper_id: Semantic Scholar paper ID (e.g., 'e897a9ce6f194f0e420f58c1e7fdb565ee9b98b2')
        pmcid: PubMed Central ID (e.g., 'PMC4567604' or '4567604')
        pubmed_id: PubMed ID (e.g., '26488642')
        open_access_pdf_url: URL to open access PDF (from Semantic Scholar API)
        timeout: Request timeout in seconds

    Returns:
        Figure URL string if found and valid, None otherwise
    """
    # Strategy 1: Extract figure from open access PDF (preferred for consistent visual style)
    if open_access_pdf_url and paper_id:
        logger.debug(f"Trying PDF extraction for {paper_id}...")
        # Use longer timeout for PDF downloads (60s instead of 10s)
        figure_url = extract_figure_from_pdf(open_access_pdf_url, paper_id, timeout=60)
        if figure_url:
            logger.info(f"Extracted figure from PDF for {paper_id}")
            return figure_url

    # Strategy 2: Try with PMC ID directly via Europe PMC
    if pmcid:
        figure_url = fetch_figure_from_pmc(pmcid, timeout)
        if figure_url:
            return figure_url

    # Strategy 3: Try to find PMC ID from PubMed ID, then fetch from Europe PMC
    discovered_pmcid = None
    if pubmed_id and not pmcid:
        discovered_pmcid = lookup_pmc_from_pubmed(pubmed_id, timeout)
        if discovered_pmcid:
            logger.info(f"Discovered {discovered_pmcid} from PubMed {pubmed_id}")
            figure_url = fetch_figure_from_pmc(discovered_pmcid, timeout)
            if figure_url:
                return figure_url

    # Strategy 4: Scrape PubMed page for CDN figure URL (works for non-open-access PMC articles)
    if pubmed_id:
        logger.debug(f"Trying PubMed page scrape for {pubmed_id}...")
        figure_url = scrape_pubmed_figure(pubmed_id, timeout)
        if figure_url:
            logger.info(f"Found figure via PubMed scrape for {pubmed_id}")
            return figure_url

    return None



def get_json(table):
    """Convert table to JSON format."""
    return table.drop("Link", axis=1).to_json()




def load_figure_cache(cache_file):
    """Load figure URL cache from file."""
    if cache_file and Path(cache_file).exists():
        try:
            return json.loads(Path(cache_file).read_text())
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_figure_cache(cache_file, cache):
    """Save figure URL cache to file."""
    if cache_file:
        Path(cache_file).write_text(json.dumps(cache, indent=2))


def get_publication_list_extended(author_data, bold_author_name=None, with_figures=False, cache_file=None):
    """Generate extended publication list with figure URLs and gradients.

    Args:
        author_data: Author data from Semantic Scholar API
        bold_author_name: Optional author name to bold in the output
        with_figures: Whether to fetch figure URLs from Europe PMC
        cache_file: Optional path to cache file for figure URLs

    Returns:
        List of publication dictionaries with extended metadata
    """
    if not PANDAS_AVAILABLE:
        logger.error("pandas library is required for this command. Install with: conda install pandas")
        sys.exit(1)

    papers = author_data.get('papers', [])

    if not papers:
        logger.warning("No papers found for this author")
        return []

    # Load figure cache
    figure_cache = load_figure_cache(cache_file) if with_figures else {}

    consolidated_papers = consolidate_papers(papers, merge_external_ids=True)

    # Build publication list
    publications = []

    for paper in consolidated_papers:
        paper_id = paper.get('paperId', '')
        semantic_scholar_url = f"https://www.semanticscholar.org/paper/{paper_id}"
        external_ids = paper.get('externalIds', {})

        # Format authors
        paper_authors = paper.get('authors', [])
        if paper_authors:
            author_names = [a.get('name', '') for a in paper_authors if a.get('name')]

            formatted_names = []
            for name in author_names:
                parts = name.split()
                if len(parts) > 1:
                    initials = ''.join([p[0].upper() for p in parts[:-1]])
                    last_name = parts[-1]
                    formatted = f"{initials} {last_name}"
                else:
                    formatted = name
                formatted_names.append(formatted)

            if bold_author_name:
                formatted_names = [
                    f'<strong>{name}</strong>' if any(part in bold_author_name.split() for part in name.split()) else name
                    for name in formatted_names
                ]

            if len(formatted_names) > 3:
                authors_str = ', '.join(formatted_names[:3]) + ', ...'
            else:
                authors_str = ', '.join(formatted_names)
        else:
            authors_str = ""

        # Clean journal name
        venue = paper.get('venue', '')
        doi = external_ids.get('DOI') if external_ids else None
        journal = clean_journal_name(venue, external_ids, doi)

        # Get year and citations
        year = paper.get('year', None)
        cite_count = paper.get('citationCount', 0)

        # Create title HTML with link
        title = paper.get('title', '')
        title_html = f'<a href="{semantic_scholar_url}">{title}</a>'

        # Get figure URL (with caching)
        figure_url = None
        pmcid = external_ids.get('PubMedCentral') if external_ids else None
        pubmed_id = external_ids.get('PubMed') if external_ids else None

        # Extract open access PDF URL if available (but prefer constructing our own)
        open_access_pdf = paper.get('openAccessPdf')
        api_pdf_url = None
        if open_access_pdf and isinstance(open_access_pdf, dict):
            api_pdf_url = open_access_pdf.get('url')
            # Filter out empty strings
            if not api_pdf_url or api_pdf_url.strip() == '':
                api_pdf_url = None

        # Try to construct a PDF URL from external IDs (preferred for reliability)
        open_access_pdf_url = None
        if external_ids:
            # Try ArXiv first
            arxiv_id = external_ids.get('ArXiv')
            if arxiv_id:
                open_access_pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                logger.debug(f"Constructed ArXiv PDF URL: {open_access_pdf_url}")

            # Try DOI for common open access publishers
            elif external_ids.get('DOI'):
                doi = external_ids['DOI']
                # Biorxiv/medRxiv preprints (use DOI prefix 10.1101)
                if doi.startswith('10.1101/'):
                    open_access_pdf_url = f"https://www.biorxiv.org/content/{doi}v1.full.pdf"
                    logger.debug(f"Constructed Biorxiv/medRxiv PDF URL: {open_access_pdf_url}")
                # JOSS papers (case-insensitive DOI handling)
                elif 'joss' in doi.lower():
                    # JOSS DOIs use format 10.21105/JOSS.00188
                    # PDF URLs use format: https://www.theoj.org/joss-papers/joss.00188/10.21105.joss.00188.pdf
                    # Note: DOI has / but PDF URL uses . between 10.21105 and joss
                    doi_lower = doi.lower().replace('/', '.')  # 10.21105/joss.00188 -> 10.21105.joss.00188
                    paper_number = doi_lower.split('.')[-1]  # 00188
                    open_access_pdf_url = f"https://www.theoj.org/joss-papers/joss.{paper_number}/{doi_lower}.pdf"
                    logger.debug(f"Constructed JOSS PDF URL: {open_access_pdf_url}")

        # Fall back to API-provided URL if we couldn't construct one
        if not open_access_pdf_url and api_pdf_url:
            open_access_pdf_url = api_pdf_url
            logger.debug(f"Using API-provided PDF URL: {open_access_pdf_url}")

        if with_figures:
            cache_key = paper_id or pmcid or pubmed_id

            if cache_key in figure_cache:
                figure_url = figure_cache[cache_key]
                logger.debug(f"Using cached figure for {cache_key}")
            else:
                # Always try to fetch (Semantic Scholar will be tried first, then PMC/PubMed, then PDF)
                logger.info(f"Fetching figure for paper {paper_id[:8]}...")
                figure_url = fetch_paper_figure(
                    paper_id=paper_id,
                    pmcid=pmcid,
                    pubmed_id=pubmed_id,
                    open_access_pdf_url=open_access_pdf_url
                )
                figure_cache[cache_key] = figure_url
                # Small delay to avoid rate limiting
                time.sleep(0.5)

        # Get fallback gradient
        fallback_gradient = get_fallback_gradient(journal)

        # Check open access status for PMC articles
        # If no direct PMC ID, try to discover one from PubMed ID
        is_open_access = None
        effective_pmcid = pmcid
        
        if not effective_pmcid and pubmed_id:
            # Try to discover PMC ID from PubMed ID
            effective_pmcid = lookup_pmc_from_pubmed(pubmed_id)
        
        if effective_pmcid:
            is_open_access = check_open_access(effective_pmcid)

        publications.append({
            'paperId': paper_id,
            'title': title,
            'titleHtml': title_html,
            'authors': authors_str,
            'journal': journal,
            'year': year,
            'citations': cite_count,
            'semanticScholarUrl': semantic_scholar_url,
            'figureUrl': figure_url,
            'fallbackGradient': fallback_gradient,
            'externalIds': external_ids,
            'isOpenAccess': is_open_access,
        })

    # Sort by year (descending), then citations (descending)
    publications.sort(key=lambda x: (-(x['year'] or 0), -x['citations']))

    # Add index
    for i, pub in enumerate(publications, 1):
        pub['index'] = i

    # Save figure cache
    if with_figures and cache_file:
        save_figure_cache(cache_file, figure_cache)

    return publications


def get_json_extended(publications):
    """Convert extended publication list to JSON string."""
    return json.dumps(publications, indent=2)

def get_latex(table):
    """Convert table to LaTeX format."""
    return table.drop("Link", axis=1).to_latex(na_rep="0")


def cmd_scrape_pubs(args):
    """Fetch and format publication data from Semantic Scholar."""
    # Validate author ID
    if not args.author or len(args.author) < 5:
        logger.error("Invalid Semantic Scholar author ID")
        raise ValueError("Author ID must be at least 5 characters long")

    # Validate output path
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Fetch publications from Semantic Scholar (fetch once, use for both outputs)
        author_data = get_author_publications(args.author)

        # Extract author name from the data
        author_name = author_data.get('name')
        logger.info(f"Fetched publications for author: {author_name}")

        # Check if we need extended JSON output
        with_figures = getattr(args, 'with_figures', False)
        cache_file = getattr(args, 'cache_file', None)
        also_json = getattr(args, 'also_json', None)

        # If --also-json is specified, it implies --with-figures
        if also_json:
            with_figures = True

        # Generate primary output
        if args.format == 'json' and with_figures:
            # Use extended JSON with figure fetching
            publications = get_publication_list_extended(
                author_data,
                bold_author_name=author_name,
                with_figures=True,
                cache_file=cache_file
            )
            logger.info(f"Writing {len(publications)} publications (with figures) to {output_path}")
            with codecs.open(output_path, "w", "utf-8") as file:
                file.write(get_json_extended(publications))
        else:
            # Use standard table-based output
            table = get_table(author_data, bold_author_name=author_name)
            output_formats = {"html": get_html, "json": get_json, "latex": get_latex, "tab": get_tab}

            logger.info(f"Writing {len(table)} publications to {output_path}")
            with codecs.open(output_path, "w", "utf-8") as file:
                file.write(output_formats[args.format](table))

        logger.info(f"Successfully wrote publications to {output_path}")

        # Generate additional JSON with figures if --also-json is specified
        if also_json:
            json_path = Path(also_json)
            json_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate extended JSON with figures
            publications = get_publication_list_extended(
                author_data,
                bold_author_name=author_name,
                with_figures=True,
                cache_file=cache_file
            )
            logger.info(f"Writing {len(publications)} publications (with figures) to {json_path}")
            with codecs.open(json_path, "w", "utf-8") as file:
                file.write(get_json_extended(publications))

            logger.info(f"Successfully wrote JSON with figures to {json_path}")

    except Exception as e:
        logger.error(f"Failed to generate publication list: {e}")
        raise


# ============================================================================
# UPDATE CV - Citation counts and GitHub stats
# ============================================================================

class SemanticScholarAPI:
    """Interface for Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper"

    def __init__(self, max_retries=5, backoff_factor=4, author_id=None):
        if not REQUESTS_AVAILABLE:
            logger.error("requests library is required for this command. Install with: conda install requests")
            sys.exit(1)
        if not TENACITY_AVAILABLE:
            logger.error("tenacity library is required for this command. Install with: conda install tenacity")
            sys.exit(1)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.author_id = author_id
        self.headers = _get_semantic_scholar_headers()
        self._citation_cache = {}  # Cache for consolidated citation counts

    def _build_citation_cache(self):
        """Build a cache of consolidated citation counts from author's publications."""
        if not self.author_id:
            logger.warning("No author_id provided, citation consolidation will use search fallback")
            return

        logger.info(f"Building citation cache from author publications for {self.author_id}...")

        try:
            # Fetch all author publications with consolidation
            author_data = get_author_publications(self.author_id, self.max_retries, self.backoff_factor)
            papers = author_data.get('papers', [])

            # Group papers by normalized title (same logic as get_table)
            papers_by_title = {}

            for paper in papers:
                if not paper.get('title') or not paper.get('paperId'):
                    continue

                # Skip abstracts and Zenodo releases
                external_ids = paper.get('externalIds', {})
                doi = external_ids.get('DOI') if external_ids else None

                if doi and 'zenodo' in doi.lower():
                    continue
                if doi and 'j.bpj.' in doi.lower() and len(doi.split('.')) >= 5:
                    continue

                normalized_title = normalize_title(paper['title'])

                if normalized_title not in papers_by_title:
                    papers_by_title[normalized_title] = []

                papers_by_title[normalized_title].append(paper)

            # Build cache: map each paper ID to its consolidated citation count
            for normalized_title, paper_group in papers_by_title.items():
                # Sum citations from all versions
                total_citations = sum(p.get('citationCount', 0) for p in paper_group)

                # Store the consolidated count for each paper ID in the group
                for paper in paper_group:
                    paper_id = paper.get('paperId')
                    if paper_id:
                        self._citation_cache[paper_id] = total_citations

                    # Also cache by DOI and ArXiv ID for easy lookup
                    ext_ids = paper.get('externalIds', {})
                    if ext_ids:
                        if ext_ids.get('DOI'):
                            self._citation_cache[f"DOI:{ext_ids['DOI']}"] = total_citations
                        if ext_ids.get('ArXiv'):
                            self._citation_cache[f"ARXIV:{ext_ids['ArXiv']}"] = total_citations

                if len(paper_group) > 1:
                    logger.info(f"Cached {len(paper_group)} versions of '{paper_group[0].get('title', '')[:50]}...' "
                               f"with total citations: {total_citations}")

            logger.info(f"Citation cache built with {len(self._citation_cache)} entries")

        except Exception as e:
            logger.warning(f"Failed to build citation cache: {e}. Will use direct lookup fallback.")

    def get_citation_count(self, doi=None, arxiv_id=None):
        """Get consolidated citation count for a paper, including preprint versions."""
        if doi:
            paper_id = f"DOI:{doi}"
        elif arxiv_id:
            paper_id = f"ARXIV:{arxiv_id}"
        else:
            logger.warning("No DOI or ArXiv ID provided")
            return None

        # Build cache on first use
        if not self._citation_cache and self.author_id:
            self._build_citation_cache()

        # Check cache first
        if paper_id in self._citation_cache:
            citation_count = self._citation_cache[paper_id]
            logger.info(f"Found {citation_count} citations for {paper_id} (from cache)")
            return citation_count

        # Fallback: direct API lookup (without consolidation)
        logger.info(f"Fetching citation count for {paper_id} (not in cache)")
        url = f"{self.BASE_URL}/{paper_id}"
        params = {"fields": "citationCount"}

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=self.backoff_factor, max=60),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            retry=retry_if_exception_type(requests.exceptions.RequestException),
            reraise=True,
        )
        def _fetch():
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    wait_time = int(retry_after)
                    logger.warning(f"Rate limited, Retry-After: {wait_time}s")
                    time.sleep(wait_time)
            response.raise_for_status()
            return response.json()

        try:
            data = _fetch()
            citation_count = data.get('citationCount', 0)
            logger.info(f"Found {citation_count} citations for {paper_id}")
            return citation_count
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Paper not found: {paper_id}")
            else:
                logger.error(f"Failed to fetch citation count: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch citation count: {e}")
            return None


class GitHubAPI:
    """Interface for GitHub API."""

    BASE_URL = "https://api.github.com/repos"

    def __init__(self, max_retries=5, backoff_factor=4):
        if not REQUESTS_AVAILABLE:
            logger.error("requests library is required for this command. Install with: conda install requests")
            sys.exit(1)
        if not TENACITY_AVAILABLE:
            logger.error("tenacity library is required for this command. Install with: conda install tenacity")
            sys.exit(1)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def get_repo_stats(self, owner, repo):
        """Get repository statistics (stars, forks)."""
        url = f"{self.BASE_URL}/{owner}/{repo}"

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=self.backoff_factor, max=60),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            retry=retry_if_exception_type(requests.exceptions.RequestException),
            reraise=True,
        )
        def _fetch():
            response = requests.get(url, timeout=10)
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    wait_time = int(retry_after)
                    logger.warning(f"Rate limited, Retry-After: {wait_time}s")
                    time.sleep(wait_time)
            response.raise_for_status()
            return response.json()

        logger.info(f"Fetching stats for {owner}/{repo}")
        try:
            data = _fetch()
            stars = data.get('stargazers_count', 0)
            forks = data.get('forks_count', 0)
            logger.info(f"Found {stars} stars and {forks} forks for {owner}/{repo}")
            return {"stars": stars, "forks": forks}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Repository not found: {owner}/{repo}")
            else:
                logger.error(f"Failed to fetch repo stats: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch repo stats: {e}")
            return None


class CVUpdater:
    """Update CV markdown file with latest citation and GitHub stats."""

    def __init__(self, cv_path, author_id=None):
        self.cv_path = Path(cv_path)
        self.semantic_scholar = SemanticScholarAPI(author_id=author_id)
        self.github = GitHubAPI()

    def read_cv(self):
        """Read CV markdown file."""
        if not self.cv_path.exists():
            raise FileNotFoundError(f"CV file not found: {self.cv_path}")

        with open(self.cv_path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_cv(self, content):
        """Write updated CV markdown file."""
        with open(self.cv_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Updated CV written to {self.cv_path}")

    def update_publication_citations(self, content):
        """Update citation counts for publications in Selected Publications section."""
        logger.info("Updating publication citation counts...")

        # Pattern to match DOI/arXiv URLs in markdown links
        doi_pattern = r'\*\[[^\]]+\]\(https://doi\.org/([\w\.\-/]+)\)\*'
        arxiv_pattern = r'\*\[[^\]]+\]\(https://arxiv\.org/abs/([\w\.]+)\)\*'

        lines = content.split('\n')
        updated_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this line contains a DOI or arXiv link
            doi_match = re.search(doi_pattern, line)
            arxiv_match = re.search(arxiv_pattern, line)

            if (doi_match or arxiv_match) and line.endswith('<br>'):
                # Extract DOI or arXiv ID
                if doi_match:
                    identifier = doi_match.group(1)
                    citation_count = self.semantic_scholar.get_citation_count(doi=identifier)
                else:
                    identifier = arxiv_match.group(1)
                    citation_count = self.semantic_scholar.get_citation_count(arxiv_id=identifier)

                updated_lines.append(line)

                # Check the next line for existing citation count
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    citation_pattern = r'^(\s*)📚 \d+$'

                    if citation_count is not None:
                        if re.match(citation_pattern, next_line):
                            # Replace existing citation count, preserving whitespace
                            whitespace_match = re.match(r'^(\s*)', next_line)
                            whitespace = whitespace_match.group(1) if whitespace_match else ''
                            updated_lines.append(f'{whitespace}📚 {citation_count}')
                            logger.info(f"Updated citation count to 📚 {citation_count} for {identifier}")
                            i += 2  # Skip the citation line we just updated
                            continue
                        else:
                            # Add new citation count line
                            updated_lines.append(f'📚 {citation_count}')
                            logger.info(f"Added citation count 📚 {citation_count} for {identifier}")
                            i += 1
                            continue
                    else:
                        # No citation count found, skip to next line
                        i += 1
                        continue
                else:
                    # Last line in file
                    if citation_count is not None:
                        updated_lines.append(f'📚 {citation_count}')
                        logger.info(f"Added citation count 📚 {citation_count} for {identifier}")
                    i += 1
                    continue

            updated_lines.append(line)
            i += 1

        return '\n'.join(updated_lines)

    def update_github_stats(self, content):
        """Update GitHub repository statistics in Selected Software section."""
        logger.info("Updating GitHub repository stats...")

        # Pattern to match GitHub repository links
        github_pattern = r'\[([\w\-]+)/([\w\-]+)\]\(https://github\.com/\1/\2\)'

        lines = content.split('\n')
        updated_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this line contains a GitHub link
            github_match = re.search(github_pattern, line)

            if github_match and line.endswith('<br>'):
                owner = github_match.group(1)
                repo = github_match.group(2)

                stats = self.github.get_repo_stats(owner, repo)

                updated_lines.append(line)

                # Check the next line for existing stats
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # Pattern: `Language` · ⭐ ### · 🍴 ###
                    stats_pattern = r'^(`[^`]+`\s+)?· ⭐ \d+\s+· 🍴 \d+'

                    if stats:
                        if re.match(stats_pattern, next_line):
                            # Replace existing stats, preserving language tag
                            lang_match = re.match(r'^(`[^`]+`\s+)', next_line)
                            lang_prefix = lang_match.group(1) if lang_match else ''
                            updated_lines.append(f'{lang_prefix}· ⭐ {stats["stars"]}  · 🍴 {stats["forks"]}')
                            logger.info(f"Updated stats to ⭐ {stats['stars']} 🍴 {stats['forks']} for {owner}/{repo}")
                            i += 2  # Skip the stats line we just updated
                            continue
                        else:
                            # Add new stats line (may or may not have language tag already)
                            if next_line.strip().startswith('`'):
                                # Next line has language, append stats to it
                                updated_lines.append(f'{next_line.rstrip()} · ⭐ {stats["stars"]}  · 🍴 {stats["forks"]}')
                                logger.info(f"Added stats ⭐ {stats['stars']} 🍴 {stats['forks']} for {owner}/{repo}")
                                i += 2
                                continue
                            else:
                                # No language tag, just add stats
                                updated_lines.append(f'· ⭐ {stats["stars"]}  · 🍴 {stats["forks"]}')
                                logger.info(f"Added stats ⭐ {stats['stars']} 🍴 {stats['forks']} for {owner}/{repo}")
                                i += 1
                                continue
                    else:
                        # No stats found, skip to next line
                        i += 1
                        continue
                else:
                    # Last line in file
                    if stats:
                        updated_lines.append(f'· ⭐ {stats["stars"]}  · 🍴 {stats["forks"]}')
                        logger.info(f"Added stats ⭐ {stats['stars']} 🍴 {stats['forks']} for {owner}/{repo}")
                    i += 1
                    continue

            updated_lines.append(line)
            i += 1

        return '\n'.join(updated_lines)

    def update(self):
        """Run full CV update process."""
        logger.info(f"Starting CV update for {self.cv_path}")

        # Read current CV
        content = self.read_cv()

        # Update citations
        content = self.update_publication_citations(content)

        # Rate limit between API sections
        logger.info("Waiting 2 seconds before GitHub API calls...")
        time.sleep(2)

        # Update GitHub stats
        content = self.update_github_stats(content)

        # Write updated CV
        self.write_cv(content)

        logger.info("CV update complete!")


def cmd_update_cv(args):
    """Update CV with latest citation counts and GitHub repository stats."""
    try:
        updater = CVUpdater(args.cv_path, author_id=args.author_id)
        updater.update()
    except Exception as e:
        logger.error(f"Failed to update CV: {e}")
        raise


# ============================================================================
# GENERATE PDF - WeasyPrint PDF generation
# ============================================================================

CSS_STYLES = """
@page {
    size: letter;
    margin: 0.5in 0.6in;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 9pt;
    line-height: 1.45;
    color: #333;
}

/* Name */
h1 {
    font-size: 18pt;
    font-weight: 600;
    margin-bottom: 3pt;
    color: #000;
}

/* Section headers */
h2 {
    font-size: 10pt;
    font-weight: 600;
    color: #000;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1.5pt solid #000;
    padding-bottom: 3pt;
    margin-top: 12pt;
    margin-bottom: 6pt;
    page-break-after: avoid;
}

/* Company/school names */
h3 {
    font-size: 9.5pt;
    font-weight: 600;
    color: #000;
    margin-top: 8pt;
    margin-bottom: 1pt;
    page-break-after: avoid;
}

/* Subsection headers */
h4 {
    font-size: 8.5pt;
    font-weight: 600;
    color: #333;
    margin-top: 6pt;
    margin-bottom: 1pt;
    page-break-after: avoid;
}

p {
    font-size: 8.5pt;
    margin-bottom: 3pt;
    color: #333;
}

/* Role/degree styling */
p strong {
    font-weight: 600;
}

p em {
    font-style: italic;
    color: #555;
}

ul {
    margin: 3pt 0;
    padding-left: 14pt;
}

li {
    font-size: 8.5pt;
    margin-bottom: 2pt;
    color: #333;
}

a {
    color: #2a7ae2;
    text-decoration: none;
}

code {
    background-color: #f0f0f0;
    padding: 0 3pt;
    border-radius: 2pt;
    font-size: 7.5pt;
    color: #555;
    font-family: "SF Mono", Menlo, Monaco, monospace;
}

hr {
    border: none;
    border-top: 0.5pt solid #ccc;
    margin: 10pt 0;
}

/* Avoid page breaks inside list items and paragraphs */
li, p {
    page-break-inside: avoid;
}

/* Keep headers with following content */
h2, h3, h4 {
    page-break-after: avoid;
}
"""


def cmd_generate_pdf(args):
    """Generate PDF version of CV from markdown using WeasyPrint."""
    if not WEASYPRINT_AVAILABLE:
        logger.error("weasyprint and markdown libraries are required for this command.")
        logger.error("Install with: conda install weasyprint markdown")
        sys.exit(1)

    try:
        # Validate input file exists
        if not args.cv_path.exists():
            logger.error(f"CV markdown file not found: {args.cv_path}")
            sys.exit(1)

        logger.info(f"Reading CV from {args.cv_path}")
        md_content = args.cv_path.read_text(encoding="utf-8")

        if not md_content.strip():
            logger.error("CV markdown file is empty")
            sys.exit(1)

        # Convert markdown to HTML
        logger.info("Converting markdown to HTML")
        html_content = markdown.markdown(
            md_content,
            extensions=["extra", "smarty"],
        )

        # Wrap in full HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # Ensure output directory exists
        args.output.parent.mkdir(parents=True, exist_ok=True)

        # Generate PDF
        logger.info(f"Generating PDF at {args.output}")
        html_doc = HTML(string=full_html)
        css = CSS(string=CSS_STYLES)
        html_doc.write_pdf(args.output, stylesheets=[css])

        logger.info(f"Successfully generated PDF: {args.output}")
        logger.info(f"PDF size: {args.output.stat().st_size / 1024:.1f} KB")

    except Exception as e:
        logger.error(f"Failed to generate CV PDF: {e}")
        sys.exit(1)


# ============================================================================
# MAIN CLI ENTRY POINT
# ============================================================================

def main():
    """Main CLI entry point with subcommands."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Enrich Inventory command
    enrich_parser = subparsers.add_parser(
        'enrich-inventory',
        help='Enrich inventory.json with Square payment data'
    )
    enrich_parser.add_argument(
        'inventory',
        help='Path to inventory.json file'
    )

    # Scrape Publications command
    scrape_parser = subparsers.add_parser(
        'scrape-pubs',
        help='Fetch publication data from Semantic Scholar'
    )
    scrape_parser.add_argument(
        '-a', '--author',
        required=True,
        help='Semantic Scholar Author ID'
    )
    scrape_parser.add_argument(
        '-o', '--output',
        default='./publications.txt',
        help='Output file path (default: ./publications.txt)'
    )
    scrape_parser.add_argument(
        '-f', '--format',
        choices=['html', 'json', 'latex', 'tab'],
        default='html',
        help='Output format (default: html)'
    )
    scrape_parser.add_argument(
        '--with-figures',
        action='store_true',
        help='Fetch figure URLs from Europe PMC (slower, requires additional API calls). Only works with JSON format.'
    )
    scrape_parser.add_argument(
        '--cache-file',
        type=str,
        help='Cache file for figure URLs (JSON). Speeds up subsequent runs.'
    )
    scrape_parser.add_argument(
        '--also-json',
        type=str,
        metavar='PATH',
        help='Also generate JSON with figures at this path (implies --with-figures)'
    )

    # Update CV command
    update_parser = subparsers.add_parser(
        'update-cv',
        help='Update CV with citation counts and GitHub stats'
    )
    update_parser.add_argument(
        '-c', '--cv-path',
        default='_includes/cv.md',
        help='Path to CV markdown file (default: _includes/cv.md)'
    )
    update_parser.add_argument(
        '-a', '--author-id',
        help='Semantic Scholar Author ID for citation consolidation (recommended)'
    )

    # Generate PDF command
    pdf_parser = subparsers.add_parser(
        'generate-pdf',
        help='Generate PDF version of CV from markdown'
    )
    pdf_parser.add_argument(
        '-c', '--cv-path',
        type=Path,
        default=Path(__file__).parent / '..' / '_includes' / 'cv.md',
        help='Path to CV markdown file (default: ../_includes/cv.md)'
    )
    pdf_parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path(__file__).parent / '..' / 'static' / 'files' / 'CXHernandez_CV.pdf',
        help='Output PDF path (default: ../static/files/CXHernandez_CV.pdf)'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to appropriate command handler
    if args.command == 'enrich-inventory':
        cmd_enrich_inventory(args)
    elif args.command == 'scrape-pubs':
        cmd_scrape_pubs(args)
    elif args.command == 'update-cv':
        cmd_update_cv(args)
    elif args.command == 'generate-pdf':
        cmd_generate_pdf(args)


if __name__ == '__main__':
    main()
