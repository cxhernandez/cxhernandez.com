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


def clean_journal_name(venue, external_ids=None, doi=None):
    """Clean and format venue/journal names."""
    # Check external IDs for better venue detection
    if external_ids:
        # Check for arXiv
        if 'ArXiv' in external_ids:
            return 'arXiv'

        # Check for Zenodo (software releases)
        if doi and 'zenodo' in doi.lower():
            return 'Zenodo'

    # Check DOI patterns for conference abstracts
    if doi:
        # Biophysical Journal abstracts have pattern like "10.1016/j.bpj.YYYY.MM.XXXX"
        if 'j.bpj.' in doi.lower() and len(doi.split('.')) >= 5:
            return 'Biophysical Journal (Abstract)'

    if not venue:
        return ""

    # Special case for arXiv in venue name
    if venue.lower().startswith('arxiv'):
        return 'arXiv'

    # Apply title case
    return title_case(venue.strip())


def get_author_publications(author_id, max_retries=3, backoff_factor=2):
    """Fetch author publications from Semantic Scholar API."""
    if not REQUESTS_AVAILABLE:
        logger.error("requests library is required for this command. Install with: pip install requests")
        sys.exit(1)

    base_url = "https://api.semanticscholar.org/graph/v1/author"
    url = f"{base_url}/{author_id}"

    params = {
        "fields": "authorId,name,papers.title,papers.paperId,papers.year,"
                 "papers.citationCount,papers.authors,papers.venue,"
                 "papers.externalIds"
    }

    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching publications for author {author_id} (attempt {attempt + 1}/{max_retries})")

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            logger.info("Successfully fetched publication data from Semantic Scholar")
            return response.json()

        except Exception as e:
            wait_time = backoff_factor ** attempt
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch publications after {max_retries} attempts: {e}")
                raise


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


def get_table(author_data, bold_author_name=None):
    """Parse author data and create publication table.

    Args:
        author_data: Author data from Semantic Scholar API
        bold_author_name: Optional author name to bold in the output (for HTML/markdown)
    """
    if not PANDAS_AVAILABLE:
        logger.error("pandas library is required for this command. Install with: pip install pandas")
        sys.exit(1)

    papers = author_data.get('papers', [])

    if not papers:
        logger.warning("No papers found for this author")
        return pd.DataFrame()

    # Group papers by normalized title to detect duplicates (preprint + published)
    papers_by_title = {}

    for paper in papers:
        # Skip papers without basic info
        if not paper.get('title') or not paper.get('paperId'):
            continue

        # Filter out conference abstracts and Zenodo releases
        external_ids = paper.get('externalIds', {})
        doi = external_ids.get('DOI') if external_ids else None

        # Skip Zenodo software releases
        if doi and 'zenodo' in doi.lower():
            continue

        # Skip Biophysical Journal conference abstracts
        if doi and 'j.bpj.' in doi.lower() and len(doi.split('.')) >= 5:
            continue

        normalized_title = normalize_title(paper['title'])

        if normalized_title not in papers_by_title:
            papers_by_title[normalized_title] = []

        papers_by_title[normalized_title].append(paper)

    # Process grouped papers: consolidate preprints with published versions
    consolidated_papers = []

    for normalized_title, paper_group in papers_by_title.items():
        if len(paper_group) == 1:
            # Single paper, use as-is
            consolidated_papers.append(paper_group[0])
        else:
            # Multiple papers with same title - likely preprint + published
            preprints = []
            published = []

            for paper in paper_group:
                external_ids = paper.get('externalIds', {})
                venue = paper.get('venue', '')

                if is_preprint(external_ids, venue):
                    preprints.append(paper)
                else:
                    published.append(paper)

            # Prefer published version for metadata, sum citations
            if published:
                # Use the first published version as base
                base_paper = published[0]
            else:
                # All are preprints, use the first one
                base_paper = paper_group[0]

            # Sum citations from all versions
            total_citations = sum(p.get('citationCount', 0) for p in paper_group)

            # Create consolidated paper with summed citations
            consolidated = dict(base_paper)
            consolidated['citationCount'] = total_citations

            consolidated_papers.append(consolidated)

            # Log consolidation
            if len(paper_group) > 1:
                logger.info(f"Consolidated {len(paper_group)} versions of '{base_paper.get('title', '')[:50]}...' "
                           f"(total citations: {total_citations})")

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

            # Bold the specified author name if provided
            if bold_author_name:
                author_names = [
                    f'**{name}**' if name == bold_author_name else name
                    for name in author_names
                ]

            if len(author_names) > 3:
                authors_str = ', '.join(author_names[:3]) + ', ...'
            else:
                authors_str = ', '.join(author_names)
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


def get_json(table):
    """Convert table to JSON format."""
    return table.drop("Link", axis=1).to_json()


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
        # Fetch publications from Semantic Scholar
        author_data = get_author_publications(args.author)

        # Extract author name from the data
        author_name = author_data.get('name')
        logger.info(f"Fetched publications for author: {author_name}")

        # Generate table with author name bolded
        table = get_table(author_data, bold_author_name=author_name)

        output_formats = {"html": get_html, "json": get_json, "latex": get_latex, "tab": get_tab}

        logger.info(f"Writing {len(table)} publications to {output_path}")
        with codecs.open(output_path, "w", "utf-8") as file:
            file.write(output_formats[args.format](table))

        logger.info(f"Successfully wrote publications to {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate publication list: {e}")
        raise


# ============================================================================
# UPDATE CV - Citation counts and GitHub stats
# ============================================================================

class SemanticScholarAPI:
    """Interface for Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper"

    def __init__(self, max_retries=3, backoff_factor=2, author_id=None):
        if not REQUESTS_AVAILABLE:
            logger.error("requests library is required for this command. Install with: pip install requests")
            sys.exit(1)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.author_id = author_id
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

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()
                citation_count = data.get('citationCount', 0)
                logger.info(f"Found {citation_count} citations for {paper_id}")
                return citation_count

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Paper not found: {paper_id}")
                    return None
                wait_time = self.backoff_factor ** attempt
                if attempt < self.max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch citation count after {self.max_retries} attempts: {e}")
                    return None
            except Exception as e:
                wait_time = self.backoff_factor ** attempt
                if attempt < self.max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch citation count after {self.max_retries} attempts: {e}")
                    return None


class GitHubAPI:
    """Interface for GitHub API."""

    BASE_URL = "https://api.github.com/repos"

    def __init__(self, max_retries=3, backoff_factor=2):
        if not REQUESTS_AVAILABLE:
            logger.error("requests library is required for this command. Install with: pip install requests")
            sys.exit(1)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def get_repo_stats(self, owner, repo):
        """Get repository statistics (stars, forks)."""
        url = f"{self.BASE_URL}/{owner}/{repo}"

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching stats for {owner}/{repo} (attempt {attempt + 1}/{self.max_retries})")
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()
                stars = data.get('stargazers_count', 0)
                forks = data.get('forks_count', 0)
                logger.info(f"Found {stars} stars and {forks} forks for {owner}/{repo}")
                return {"stars": stars, "forks": forks}

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Repository not found: {owner}/{repo}")
                    return None
                wait_time = self.backoff_factor ** attempt
                if attempt < self.max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch repo stats after {self.max_retries} attempts: {e}")
                    return None
            except Exception as e:
                wait_time = self.backoff_factor ** attempt
                if attempt < self.max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch repo stats after {self.max_retries} attempts: {e}")
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
        logger.error("Install with: pip install weasyprint markdown")
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
