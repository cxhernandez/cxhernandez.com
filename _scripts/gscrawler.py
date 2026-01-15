#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import codecs
import re
from contextlib import closing
from urllib.request import Request, urlopen

import pandas as pd
from bs4 import BeautifulSoup

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


def clean_journal_name(journal):
    """Remove trailing volume/issue numbers from journal names and apply title case.
    
    Examples:
        'Biophysical Journal 109' -> 'Biophysical Journal'
        'Accounts of chemical research 48 (2)' -> 'Accounts of Chemical Research'
        'Physical Review E 97 (6)' -> 'Physical Review E'
        'The Journal of Open Source Software 2 (12)' -> 'The Journal of Open Source Software'
        'arXiv preprint arXiv:1802.10548' -> 'arXiv'
    """
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


def get_soup(user):
    url = "https://scholar.google.com/citations?" "hl=en&user=%s&pagesize=100" % user
    user_agent = (
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7)"
        " Gecko/2009021910 Firefox/3.0.7"
    )
    req = Request(url, None, headers={"User-Agent": user_agent})
    with closing(urlopen(req)) as r:
        soup = BeautifulSoup(r.read(), "html5lib")
    return soup


def get_table(soup):
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
    soup = get_soup(options.user)
    table = get_table(soup)
    with codecs.open(options.out, "w", "utf-8") as file:
        file.write(output[options.format](table))
