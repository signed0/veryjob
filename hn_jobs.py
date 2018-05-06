#!/usr/bin/env python3

import os
import logging
import sys

import requests
from flask import Flask, render_template

from bs4 import BeautifulSoup

PLACE_MATCHES = ('SF', 'San Francisco', 'san francisco')
BODY_MATCHES = ('java', 'python')
FETCH_PAGES = True

app = Flask(__name__)


def get_hn_comments(article_id):
    def _page_comments(page=1):
        logging.info("Fetching page %d for %d", page, article_id)
        url = 'https://news.ycombinator.com/item?id=%d&p=%d' % (article_id, page)
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        comments = soup.find_all('div', class_='comment')
        comments = (c.find('span', class_='c00') for c in comments)
        def clean_comment_div(c):
            strings = list(c.strings)[::-1]
            first_string = next(i for i, x in enumerate(strings) if x.strip() not in ('', 'reply'))
            return '\n'.join(reversed(strings[first_string:]))
        comments = (clean_comment_div(c) for c in comments if c)
        comments = (c for c in comments if '|' in c)

        is_last_page = soup.find('a', class_="morelink") is None

        return comments, is_last_page

    for page in range(1, 25):
        comments, is_last_page = _page_comments(page)
        yield from comments
        if not FETCH_PAGES or is_last_page:
            break

def get_jobs(article_id):
    for comment in get_hn_comments(article_id):
        head, *body = comment.split('\n')
        head_parts = [p for p in (p.strip() for p in head.split('|')) if p]
        yield {
            'head': head,
            'company': head_parts[0],
            'parts': head_parts[1:],
            'body': '<br>'.join(body)
            }

def filter(job):
    if not any(p in job['head'] for p in PLACE_MATCHES):
        return False
    lower_body = job['body'].lower()
    if not any(t.lower() in lower_body for t in BODY_MATCHES):
        return False
    return True

@app.route("/hn/<int:article_id>")
def main(article_id):
    jobs = list(get_jobs(article_id))
    filtered_jobs = [job for job in jobs if filter(job)]
    logging.info("%d total jobs, %d after filters", len(jobs), len(filtered_jobs))
    return render_template('results.html', jobs=filtered_jobs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)

