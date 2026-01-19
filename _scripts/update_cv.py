#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Update CV with latest citation counts and GitHub repository stats.

This script:
1. Fetches citation counts for papers from Semantic Scholar API
2. Fetches GitHub repository stats (stars, forks) from GitHub API
3. Updates cv.md with the latest data
"""

import argparse
import logging
import re
import time
from pathlib import Path

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SemanticScholarAPI:
    """Interface for Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper"

    def __init__(self, max_retries=3, backoff_factor=2):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def get_citation_count(self, doi=None, arxiv_id=None):
        """
        Get citation count for a paper.

        Args:
            doi: DOI of the paper (e.g., "10.1103/PhysRevE.97.062412")
            arxiv_id: ArXiv ID (e.g., "1802.10548")

        Returns:
            int: Citation count, or None if not found
        """
        if doi:
            paper_id = f"DOI:{doi}"
        elif arxiv_id:
            paper_id = f"ARXIV:{arxiv_id}"
        else:
            logger.warning("No DOI or ArXiv ID provided")
            return None

        url = f"{self.BASE_URL}/{paper_id}"
        params = {"fields": "citationCount"}

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching citation count for {paper_id} (attempt {attempt + 1}/{self.max_retries})")
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
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def get_repo_stats(self, owner, repo):
        """
        Get repository statistics (stars, forks).

        Args:
            owner: Repository owner (e.g., "msmbuilder")
            repo: Repository name (e.g., "vde")

        Returns:
            dict: {"stars": int, "forks": int}, or None if not found
        """
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

    def __init__(self, cv_path):
        self.cv_path = Path(cv_path)
        self.semantic_scholar = SemanticScholarAPI()
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
        """
        Update citation counts for publications in Selected Publications section.

        Looks for DOI links like [DOI](https://doi.org/10.1103/PhysRevE.97.062412)
        or arXiv links like [arXiv](https://arxiv.org/abs/1802.10548)
        and adds citation count before the year.
        """
        logger.info("Updating publication citation counts...")

        # Pattern to match publication entries in Selected Publications
        # Format: Title \n Authors \n *Journal* · [DOI](link) · Year
        # or: Title \n Authors \n *Journal* · [arXiv](link) · Year

        # Find all DOI patterns
        doi_pattern = r'\[DOI\]\(https://doi\.org/([\w\.\-/]+)\)'
        arxiv_pattern = r'\[arXiv\]\(https://arxiv\.org/abs/([\w\.]+)\)'

        # Find entries and update them
        lines = content.split('\n')
        updated_lines = []

        for i, line in enumerate(lines):
            # Check if this line contains a DOI or arXiv link
            doi_match = re.search(doi_pattern, line)
            arxiv_match = re.search(arxiv_pattern, line)

            if doi_match or arxiv_match:
                # Extract DOI or arXiv ID
                if doi_match:
                    identifier = doi_match.group(1)
                    citation_count = self.semantic_scholar.get_citation_count(doi=identifier)
                else:
                    identifier = arxiv_match.group(1)
                    citation_count = self.semantic_scholar.get_citation_count(arxiv_id=identifier)

                if citation_count is not None:
                    # Check if citation count already exists in the line
                    # Pattern: · 📚 CITATIONS ·
                    citation_text_pattern = r' · 📚 \d+ ·'

                    if re.search(citation_text_pattern, line):
                        # Replace existing citation count
                        updated_line = re.sub(
                            citation_text_pattern,
                            f' · 📚 {citation_count} ·',
                            line
                        )
                    else:
                        # Add citation count before the year
                        # Pattern: · Year
                        year_pattern = r'( · \d{4})$'
                        if re.search(year_pattern, line):
                            updated_line = re.sub(
                                year_pattern,
                                f' · 📚 {citation_count}\\1',
                                line
                            )
                        else:
                            # If no year pattern found, append at end
                            updated_line = line + f' · 📚 {citation_count}'

                    updated_lines.append(updated_line)
                    logger.info(f"Updated citation count to 📚 {citation_count} for {identifier}")
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        return '\n'.join(updated_lines)

    def update_github_stats(self, content):
        """
        Update GitHub repository statistics in Selected Software section.

        Looks for GitHub links like [owner/repo](https://github.com/owner/repo)
        and updates star/fork counts like ⭐ 683 🍴 290
        """
        logger.info("Updating GitHub repository stats...")

        # Pattern to match GitHub repository links
        # Format: [owner/repo](https://github.com/owner/repo)
        github_pattern = r'\[([\w\-]+)/([\w\-]+)\]\(https://github\.com/\1/\2\)'

        lines = content.split('\n')
        updated_lines = []

        for line in lines:
            # Check if this line contains a GitHub link
            github_match = re.search(github_pattern, line)

            if github_match:
                owner = github_match.group(1)
                repo = github_match.group(2)

                stats = self.github.get_repo_stats(owner, repo)

                if stats:
                    # Check if stats already exist in the line
                    # Pattern: ⭐ ### 🍴 ###
                    stats_pattern = r' · ⭐ \d+ 🍴 \d+'

                    if re.search(stats_pattern, line):
                        # Replace existing stats
                        updated_line = re.sub(
                            stats_pattern,
                            f' · ⭐ {stats["stars"]} 🍴 {stats["forks"]}',
                            line
                        )
                    else:
                        # Add stats at the end
                        updated_line = line + f' · ⭐ {stats["stars"]} 🍴 {stats["forks"]}'

                    updated_lines.append(updated_line)
                    logger.info(f"Updated stats to ⭐ {stats['stars']} 🍴 {stats['forks']} for {owner}/{repo}")
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

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


def parse_cmdln():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-c", "--cv",
        dest="cv_path",
        help="Path to CV markdown file",
        type=str,
        default="_includes/cv.md"
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    options = parse_cmdln()

    try:
        updater = CVUpdater(options.cv_path)
        updater.update()
    except Exception as e:
        logger.error(f"Failed to update CV: {e}")
        raise
