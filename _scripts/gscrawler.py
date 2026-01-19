#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import codecs
import logging
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

pd.options.display.max_colwidth = 500


def title_case(text):
    """Convert text to title case, keeping small words lowercase.
    
    Small words (of, the, and, in, for, a, an, etc.) remain lowercase
    unless they're the first word.
    """
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


def extract_domain_name(url):
    """Extract a clean domain name from a URL.
    
    Examples:
        'https://github.com/ParmEd/ParmEd' -> 'GitHub'
        'Url: Https://github. Com/parmed/parmed' -> 'GitHub'
    """
    # Known domain mappings (lowercase domain -> display name)
    domain_names = {
        'github.com': 'GitHub',
        'gitlab.com': 'GitLab',
        'bitbucket.org': 'Bitbucket',
        'zenodo.org': 'Zenodo',
        'figshare.com': 'Figshare',
        'osf.io': 'OSF',
        'sourceforge.net': 'SourceForge',
    }
    
    # Normalize: remove spaces, lowercase
    url_clean = url.lower().replace(' ', '')
    
    for domain, name in domain_names.items():
        if domain.replace('.', '') in url_clean.replace('.', ''):
            return name
    
    # Fallback: try to extract domain from URL pattern
    match = re.search(r'(?:https?://)?(?:www\.)?([a-z0-9-]+)\.[a-z]+', url_clean)
    if match:
        return match.group(1).capitalize()
    
    return None


def clean_journal_name(journal):
    """Remove trailing volume/issue numbers from journal names and apply title case.
    
    Examples:
        'Biophysical Journal 109' -> 'Biophysical Journal'
        'Accounts of chemical research 48 (2)' -> 'Accounts of Chemical Research'
        'Physical Review E 97 (6)' -> 'Physical Review E'
        'The Journal of Open Source Software 2 (12)' -> 'The Journal of Open Source Software'
        'arXiv preprint arXiv:1802.10548' -> 'arXiv'
        'Url: Https://github. Com/parmed/parmed' -> 'GitHub'
    """
    # Check if it's a URL - extract domain name
    if re.search(r'https?:|www\.|\.com|\.org|\.io|\.net', journal, re.IGNORECASE):
        domain = extract_domain_name(journal)
        if domain:
            return domain
    
    # Remove trailing parenthetical content like (1), (2), (12)
    journal = re.sub(r'\s*\([^)]*\)\s*$', '', journal)
    # Remove trailing numbers (volume numbers)
    journal = re.sub(r'\s+\d+\s*$', '', journal)
    # Clean up arXiv format - just use 'arXiv'
    if journal.lower().startswith('arxiv'):
        return 'arXiv'
    # Apply title case
    journal = title_case(journal.strip())
    return journal


def setup_proxy():
    """Setup proxy to avoid Google Scholar blocking.

    Note: Free proxy setup is disabled due to unmerged compatibility fix.
    The scholarly package's built-in session management and user-agent
    handling is sufficient to avoid most blocking.

    See: https://github.com/scholarly-python-package/scholarly/pull/579
    """
    # Proxy setup disabled - PR #579 not yet merged
    logger.info("Using scholarly's default session (proxy disabled - waiting for PR #579)")


def get_author_publications_html(user_id):
    """Fetch author profile HTML using scholarly's session (with proxy support).

    Args:
        user_id: Google Scholar user ID

    Returns:
        BeautifulSoup object of the author profile page

    Raises:
        Exception: If fetching publications fails
    """
    try:
        logger.info(f"Fetching publications for user {user_id}")

        # Import the navigation module which handles HTTP requests with proxy support
        from scholarly import _navigator

        # Create a navigator instance
        nav = _navigator.Navigator()

        # Fetch the author profile page with pagesize=100
        # _get_soup expects a relative URL (it prepends https://scholar.google.com)
        url = f"/citations?hl=en&user={user_id}&pagesize=100"
        soup = nav._get_soup(url)

        logger.info("Successfully fetched publication data via scholarly session")
        return soup

    except Exception as e:
        logger.error(f"Failed to fetch publications: {e}")
        raise


def get_table(soup):
    """Parse BeautifulSoup object and extract publication data.

    Args:
        soup: BeautifulSoup object of Google Scholar author profile page

    Returns:
        pandas DataFrame with publication data
    """
    table_data = soup.find_all("table", {"id": "gsc_a_t"})[0]

    links = [
        "https://scholar.google.com" + item.attrs["href"]
        for item in table_data.find_all("a", {"class": "gsc_a_at"})
    ]

    titles = [item.text for item in table_data.find_all("a", {"class": "gsc_a_at"})]

    authors = [
        item.text
        for i, item in enumerate(table_data.find_all("div", {"class": "gs_gray"}))
        if not (i % 2)
    ]

    journals = [
        clean_journal_name(item.text.split(",")[0])
        for i, item in enumerate(table_data.find_all("div", {"class": "gs_gray"}))
        if i % 2
    ]

    years = [
        item.text.split(",")[-1]
        for i, item in enumerate(table_data.find_all("div", {"class": "gs_gray"}))
        if (i % 2)
    ]

    citations = [
        item.text.replace("\xa0", "-")
        for item in table_data.find_all("td", {"class": "gsc_a_c"})
    ]

    data = {
        "Title": titles,
        "Link": links,
        "Author(s)": authors,
        "Journal": journals,
        "Citations": citations,
        "Year": years,
    }

    table = pd.DataFrame(data)

    table.index += 1

    return table[["Title", "Link", "Author(s)", "Journal", "Citations", "Year"]]


def get_html(table):
    links = dict(zip(table.Title, table.Link))
    table = table.drop("Link", axis=1)
    return table.to_html(
        formatters={"Title": lambda x: '<a href="%s">%s</a>' % (links[x], x)},
        escape=False,
        na_rep="-",
        justify="center",
    ).replace("\n", "")


def get_tab(table):
    return table.drop("Link", axis=1).to_string(na_rep="0")


def get_json(table):
    return table.drop("Link", axis=1).to_json()


def get_latex(table):
    return table.drop("Link", axis=1).to_latex(na_rep="0")


def parse_cmdln():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-u", "--user", dest="user", help="Google Scholar ID", type=str, required=True
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="out",
        help="Outfile path",
        type=str,
        default="./gscholar.txt",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="format",
        help="Output Format",
        type=str,
        default="html",
        choices=["html", "json", "latex", "tab"],
    )
    args = parser.parse_args()
    return args


output = {"html": get_html, "json": get_json, "latex": get_latex, "tab": get_tab}

if __name__ == "__main__":
    options = parse_cmdln()

    # Validate user ID
    if not options.user or len(options.user) < 5:
        logger.error("Invalid Google Scholar user ID")
        raise ValueError("User ID must be at least 5 characters long")

    # Validate output path
    output_path = Path(options.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Setup proxy to avoid being blocked
        setup_proxy()

        # Fetch publications HTML using scholarly's session
        soup = get_author_publications_html(options.user)
        table = get_table(soup)

        logger.info(f"Writing {len(table)} publications to {output_path}")
        with codecs.open(output_path, "w", "utf-8") as file:
            file.write(output[options.format](table))

        logger.info(f"Successfully wrote publications to {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate publication list: {e}")
        raise
