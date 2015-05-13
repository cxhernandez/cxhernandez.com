#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
from urllib import request
import argparse
import pandas as pd
from bs4 import BeautifulSoup
from contextlib import closing

pd.options.display.max_colwidth = 500


def get_soup(user):
    url = 'https://scholar.google.com/citations?'\
          'hl=en&user=%s&pagesize=100' % user
    with closing(request.urlopen(url)) as req:
        soup = BeautifulSoup(req.read())
    return soup


def get_table(soup):
    table_data = soup.findAll("table", {"id": "gsc_a_t"})[0]
    links = ['https://scholar.google.com/' + item.attrs['href']
             for item in table_data.findAll('a', {'class': 'gsc_a_at'})]
    titles = [item.text
              for item in table_data.findAll('a', {'class': 'gsc_a_at'})]
    authors = [item.text
               for i, item in enumerate(
                   table_data.findAll('div', {'class': 'gs_gray'}))
               if not (i % 2)]
    journals = [item.text.split(',')[0]
                for i, item in enumerate(
                    table_data.findAll('div', {'class': 'gs_gray'}))
                if i % 2]
    citations = [item.text.replace(u'\xa0', u'-')
                 for item in table_data.findAll('td', {'class': 'gsc_a_c'})]
    years = [item.text.split(',')[1]
             for i, item in enumerate(table_data.findAll('div',
                                                         {'class': 'gs_gray'}))
             if (i % 2)]

    data = {'Link': links,
            'Title': titles,
            'Author(s)': authors,
            'Journal': journals,
            'Citations': citations,
            'Year': years}

    table = pd.DataFrame(data)

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
