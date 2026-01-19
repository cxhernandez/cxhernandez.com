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

        New format:
        #### Title
        Authors · *[Journal](https://doi.org/...)* · Year<br>
        📚 COUNT

        Looks for DOI/arXiv links embedded in journal names and updates the
        citation count on the line after the <br> tag.
        """
        logger.info("Updating publication citation counts...")

        # Pattern to match DOI/arXiv URLs in markdown links
        # Format: *[Journal](https://doi.org/10.xxxx/xxxx)* or *[Journal](https://arxiv.org/abs/xxxx)*
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
        """
        Update GitHub repository statistics in Selected Software section.

        New format:
        #### Title
        Authors · [owner/repo](https://github.com/owner/repo)<br>
        `Language` · ⭐ STARS 🍴 FORKS

        Looks for GitHub repo links and updates stats on the line after <br>.
        """
        logger.info("Updating GitHub repository stats...")

        # Pattern to match GitHub repository links
        # Format: [owner/repo](https://github.com/owner/repo)
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
                            # Check if next line starts with language tag
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
