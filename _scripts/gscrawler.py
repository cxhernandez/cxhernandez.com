#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import argparse
import pandas as pd
from pandas import io
from urllib import urlopen
from contextlib import closing
from BeautifulSoup import BeautifulSoup

pd.options.display.max_colwidth = 500


def get_soup(user):
    url = u'https://scholar.google.com/citations?' \
        'hl=en&user=%s&pagesize=100' % user
    with closing(urlopen(url)) as pageFile:
        soup = BeautifulSoup("".join(pageFile.read())
                               .decode('utf-8', 'ignore'))
    return soup


def get_table(soup):
    table_data = soup.findAll("table", {"id": "gsc_a_t"})
    table = io.html.read_html(str(table_data[0])
                              .replace('<div', '<td')
                              .replace('class="gsc_a_t"><a href="',
                                       'class="gsc_a_t">'
                                       'https://scholar.google.com')
                              .replace('" class="gsc_a_at">', '</td><td>')
                              .replace('</a>', '</td>'),
                              header=0,
                              flavor='html5lib')[0]
    table.columns = ['Link',
                     'Title',
                     'Author(s)',
                     'Journal',
                     'Citations',
                     'Year']
    table.index += 1
    return table


def get_html(table):
    links = dict(zip(table.Title.to_dense(),
                     table.Link.to_dense()))
    table.drop('Link', inplace=True, axis=1)
    return table.to_html(formatters={"Title": lambda x: u'<a href="%s">%s</a>'
                                     % (links[x], x)}, escape=False,
                         na_rep='-', justify='center').replace('\n', '')


def get_tab(table):
    return table.drop('Link', axis=1).to_string(na_rep='0')


def get_json(table):
    return table.drop('Link', axis=1).to_json()


def get_latex(table):
    return table.drop('Link', axis=1).to_latex(na_rep='0')


def parse_cmdln():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-u', '--user', dest='user',
                        help='Google Scholar ID', type=str, required=True)
    parser.add_argument('-o', '--output', dest='out',
                        help='Outfile path', type=str,
                        default='./gscholar.txt')
    parser.add_argument('-f', '--format', dest='format',
                        help='Output Format', type=str, default='html',
                        choices=['html', 'json', 'latex', 'tab'])
    args = parser.parse_args()
    return args

output = {'html': get_html,
          'json': get_json,
          'latex': get_latex,
          'tab': get_tab}

if __name__ == "__main__":
    options = parse_cmdln()
    soup = get_soup(options.user)
    table = get_table(soup)
    with codecs.open(options.out, 'w', 'utf-8') as file:
        file.write(output[options.format](table))
