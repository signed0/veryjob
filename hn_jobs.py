#!/usr/bin/env python3

import logging

from bs4 import BeautifulSoup
from flask import Flask, render_template, redirect
import requests

API_BASE = 'https://hn.algolia.com/api/v1'

PLACE_MATCHES = ('SF', 'San Francisco', 'san francisco')
BODY_MATCHES = ('java', 'python')


app = Flask(__name__)


def get_latest_hiring_story():
    url = API_BASE + '/search_by_date?query=Ask+HN+Who+is+hiring&tags=author_whoishiring,ask_hn'
    r = requests.get(url)
    return int(r.json()['hits'][0]['objectID'])


def get_hn_comments(story_id):
    r = requests.get('%s/items/%d' % (API_BASE, story_id))
    return [c for c in r.json()['children'] if c['text']]


def get_jobs(story_id):
    for comment in get_hn_comments(story_id):
        soup = BeautifulSoup(comment['text'], 'html.parser')
        head, *body = '\n'.join(soup.strings).split('\n')
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


@app.route("/hn")
def latest_jobs():
    story_id = get_latest_hiring_story()
    return redirect("/hn/%d" % story_id, code=302)


@app.route("/hn/<int:story_id>")
def monthly_jobs(story_id):
    jobs = list(get_jobs(story_id))
    filtered_jobs = [job for job in jobs if filter(job)]
    logging.info("%d total jobs, %d after filters", len(jobs), len(filtered_jobs))
    return render_template('results.html', jobs=filtered_jobs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
