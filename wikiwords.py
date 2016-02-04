"""
Author: Matt Christie, 2015-2016

Collect and compare word frequencies from Wikipedia pages.
Use those word frequencies to judge similarity between pages.
"""

import re
import os
import time
import math
import json
import random
import argparse
import itertools as it
from collections import Counter

import requests
from bs4 import BeautifulSoup


def preprocessed(parse_words):
    """A decorator that preprocesses text."""
    
    def preprocess(text):
        """Preprocess text."""
        # Potentially, could be more than just this
        text = re.sub("'", '', text).lower()
        return parse_words(text)
    
    return preprocess
 
        
# Comment out decorator if you want the raw output from \w+ groups       
@preprocessed
def parse_words(text):
    """Break up a string of text into words."""
    
    # Did you know that uni.isalpha() is False when uni is a vowel in Devanagari?
    # I was originally overambitious, thinking I could parse words out from any
    # major world language. Also, uni.isalpha() is True when uni is a CJK character,
    # which makes parsing out words an entirely different enterprise for languages
    # whose writing system is logographic (no delimiters between logograms). For
    # now, this should work for a good number of European languages.
    
    return (m.group(0) for m in re.finditer('\w+', text, flags=re.UNICODE))


def words_from_strings(strings):
    """Get words from some strings."""
    for word in it.chain(*(parse_words(string) for string in strings)):
        yield word


def raw_words(html):
    """Get words from raw HTML."""
    for word in parse_words(html):
        yield word


def html_words(html):
    """Get words from inside HTML elements."""
    soup = BeautifulSoup(html, 'lxml')
    for word in words_from_strings(soup.strings):
        yield word


def body_words(html):
    """Get words from inside the body element."""
    soup = BeautifulSoup(html, 'lxml')
    for word in words_from_strings(soup.body.strings):
        yield word


def paragraph_words(html):
    """Get words only from inside paragraph elements."""
    soup = BeautifulSoup(html, 'lxml')
    paragraphs = soup.find_all('p')
    for p in paragraphs:
        for word in words_from_strings(p.strings):
            yield word


def print_comparison(counts, num_words=20):
    """Print lists of the most common words in each of the word counts."""
    for method, counter in counts.iteritems():
        print "Top %d most common words using %s:" % (num_words, method)
        for i, pair in enumerate(counter.most_common(num_words)):
            word, count = pair
            print "%d\t%s, %d" % (i + 1, word, count)


def parser_word_counts(page, parsers):
    """Get the counts of words from a page using different parsers."""
    
    html = get_page(page)
    counts = {parse.__name__: Counter(parse(html)) for parse in parsers}
    
    # Something to try out:
    # >>> (counts['html_words'] - counts['body_words']).most_common(20)
    # These are the 20 words that show up more frequently with html_words
    # than with body_words.
    
    return counts


def compare_word_counts(page, parsers, num_words=20):
    """Print lists of the most common words in the page using each parser."""
    parsers = [globals()['%s_words' % name] for name in parsers]
    counts = parser_word_counts(page, parsers)
    print_comparison(counts, num_words=num_words)


def page_distance(frequencies1, frequencies2):
    """Euclidean distance between word frequencies, where each word is an axis."""
    f1, f2 = frequencies1, frequencies2
    words = set(f1) | set(f2)
    diffs = (f1[word] - f2[word] for word in words)
    return math.sqrt(sum(d * d for d in diffs))


def normalize(word_count):
    """Turn word counts into word fractions."""
    total = float(sum(word_count.itervalues()))
    return Counter({word: count / total for word, count in word_count.iteritems()})


def get_page(page):
    """Download a Wikipedia page."""
    url = 'http://en.wikipedia.org/wiki/{page}'
    response = requests.get(url.format(page=page))
    if response.status_code == requests.codes.ok:
        return response.content


def get_pages(pages, wait=1.0):
    """Download Wikipedia pages at a chosen pace."""   
    iterpages = iter(pages)
    page = next(iterpages)
    content = get_page(page)
    if content is not None:
        yield page, content
    for page in iterpages:       
        # Be especially nice to Wikipedia:
        # http://en.wikipedia.org/wiki/Wikipedia:Database_download#Please_do_not_use_a_web_crawler
        time.sleep(wait)        
        content = get_page(page)
        if content is not None:
            yield page, content


def judge(frequencies, pages):
    """Make a judgement about which pages are more similar."""
    w0, w1, w2 = (frequencies[page] for page in pages)
    pairs = (w0, w1), (w0, w2)
    distances = [page_distance(*pair) for pair in pairs]
    closer_idx = ci = 1 + min([0, 1], key=lambda i: distances[i])
    farther_idx = fi = 3 - ci
    judgement = (pages[0], pages[ci], pages[fi])
    print "%s is closer to %s than to %s" % judgement


def snap_judgement(parse, pages=None, page_file=None, wait=2.0):
    """Randomly assess similarity between some pages."""
    if page_file is not None:    
        pages = [line.strip() for line in page_file]
        pages = random.sample(pages, 3)
    pages = pages[:3]
    fractions = {}
    parse = globals()['%s_words' % parse]
    for page, html in get_pages(pages, wait=wait):
        fractions[page] = normalize(Counter(parse(html)))
    judge(fractions, pages)


def save_frequencies(page, directory, parse, type):
    """Save a page's word frequencies as JSON to a file."""

    get_frequencies = {
        'count': lambda word_count: word_count,
        'fraction': lambda word_count: normalize(word_count)
    }
    html = get_page(page)
    parse = globals()['%s_words' % parse]
    frequencies = get_frequencies[type](Counter(parse(html)))

    if not os.path.isdir(directory):
        os.makedirs(directory)
    filename = os.path.join(directory, '%s.json' % page)
    with open(filename, 'w') as file_out:
        json.dump(dict(frequencies), file_out, indent=1)


def from_cli(command):
    """A decorator that feeds a function its arguments from the parsed command line."""
    
    def run_with_namespace(namespace):
        """Run a function with a namespace's attribute values as its arguments."""
        delattr(namespace, 'func')
        return command(**vars(namespace))
    
    return run_with_namespace


def get_parser():
    """The command line argument parser used when running wikiwords as a script."""
    
    desc = 'Inspect similarity between Wikipedia pages.'
    parser = argparse.ArgumentParser(description=desc)
    
    # For the shared --page option
    page_parser = argparse.ArgumentParser(add_help=False)
    page_parser.add_argument('--page', '-p', help='name of page to load (not URL)')
    
    # For the shared --parse option
    parser_choices = ['raw', 'html', 'body', 'paragraph']
    parsing_parser = argparse.ArgumentParser(add_help=False)
    kwargs = {
        'help': 'parser to get words from page with',
        'choices': parser_choices,
        'default': 'body'
    }
    parsing_parser.add_argument('--parse', **kwargs)
    
    subparsers = parser.add_subparsers(help='commands')
 
    # The judge command
    kwargs = {
        'help': 'Judge similarity between pages',
        'parents': [parsing_parser],
        'conflict_handler': 'resolve'
    }
    judge_parser = subparsers.add_parser('judge', **kwargs)
    judge_parser.set_defaults(func=from_cli(snap_judgement))
    
    help = 'seconds to wait between downloads'
    judge_parser.add_argument('--wait', '-w', type=float, default=1.0, help=help)
    group = judge_parser.add_mutually_exclusive_group()
    help = 'file containing a list of pages to judge from'
    group.add_argument('--page-file', '-f', type=file, default=None, help=help)
    help = 'three pages to judge from; the first is compared to the others'
    group.add_argument('--pages', default=None, help=help, nargs=3)
 
    # The save command
    kwargs = {
        'help': "Save a pages's word frequencies",
        'parents': [page_parser, parsing_parser],
        'conflict_handler': 'resolve'
    }
    save_parser = subparsers.add_parser('save', **kwargs)
    save_parser.set_defaults(func=from_cli(save_frequencies))
    
    help = 'directory to save word frequencies in'
    save_parser.add_argument('--directory', '-d', default='.', help=help)
    help = 'type of frequencies to save'
    choices = ['count', 'fraction']
    save_parser.add_argument('--type', '-t', default='fraction',
                             choices=choices, help=help)
    
    # The compare command
    kwargs = {
        'help': 'Compare word parsers',
        'parents': [page_parser],
        'conflict_handler': 'resolve'
    }
    compare_parser = subparsers.add_parser('compare', **kwargs)
    compare_parser.set_defaults(func=from_cli(compare_word_counts))
    
    parser_kwargs = {
        'default': parser_choices,
        'choices': parser_choices,
        'help': 'parsers to get words from pages with',
        'nargs': '+'
    }
    compare_parser.add_argument('--parsers', **parser_kwargs)
    help = 'number of most frequent words to display'
    compare_parser.add_argument('--num-words', '-n', type=int, default=20, help=help)
        
    return parser


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    args.func(args)







