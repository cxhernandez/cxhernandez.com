#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import codecs
import logging
import time
from pathlib import Path

import pandas as pd
import requests

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


def clean_journal_name(venue, external_ids=None, doi=None):
    """Clean and format venue/journal names.

    Args:
        venue: Venue name from Semantic Scholar
        external_ids: Dictionary of external IDs (ArXiv, DOI, etc.)
        doi: DOI string if available

    Returns:
        Cleaned venue/journal name
    """
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
    """Fetch author publications from Semantic Scholar API.

    Args:
        author_id: Semantic Scholar author ID
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Exponential backoff multiplier (default: 2)

    Returns:
        dict: Author data including papers

    Raises:
        Exception: If fetching data fails after all retries
    """
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


def get_table(author_data):
    """Parse author data and create publication table.

    Args:
        author_data: JSON response from Semantic Scholar API

    Returns:
        pandas DataFrame with publication data
    """
    papers = author_data.get('papers', [])

    if not papers:
        logger.warning("No papers found for this author")
        return pd.DataFrame()

    # Build lists for DataFrame
    titles = []
    links = []
    authors_list = []
    journals = []
    citations = []
    years = []

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

        titles.append(paper['title'])
        links.append(f"https://www.semanticscholar.org/paper/{paper['paperId']}")

        # Format authors
        paper_authors = paper.get('authors', [])
        if paper_authors:
            author_names = [a.get('name', '') for a in paper_authors if a.get('name')]
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

        # Citations
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


def parse_cmdln():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-a", "--author", dest="author", help="Semantic Scholar Author ID",
        type=str, required=True
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="out",
        help="Outfile path",
        type=str,
        default="./publications.txt",
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

    # Validate author ID
    if not options.author or len(options.author) < 5:
        logger.error("Invalid Semantic Scholar author ID")
        raise ValueError("Author ID must be at least 5 characters long")

    # Validate output path
    output_path = Path(options.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Fetch publications from Semantic Scholar
        author_data = get_author_publications(options.author)
        table = get_table(author_data)

        logger.info(f"Writing {len(table)} publications to {output_path}")
        with codecs.open(output_path, "w", "utf-8") as file:
            file.write(output[options.format](table))

        logger.info(f"Successfully wrote publications to {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate publication list: {e}")
        raise
