#!/usr/bin/env python3
"""Re-pull true upvote counts from the HuggingFace papers API.

The nightly shortlist (selected-*.json) carries stale/zero upvotes from the
cache-first fetch; this script re-pulls each candidate id from
https://huggingface.co/api/papers/<id> and writes a ranked JSON to
episodes/feed/picks/true-upvotes-<date>.json. Usage:
    python debugging/repull_upvotes.py 2026-09-22
"""
import json, sys, time, urllib.request

date = sys.argv[1]
d = json.load(open(f'episodes/feed/papers-{date}.json'))
papers = d if isinstance(d, list) else d.get('papers', d)
ids = [p['arxiv_id'] for p in papers]
titles = {p['arxiv_id']: p['title'] for p in papers}

res = {}
for i in ids:
    try:
        req = urllib.request.Request(
            f'https://huggingface.co/api/papers/{i}',
            headers={'User-Agent': 'papercast-nightly/1.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.load(r)
        res[i] = {'upvotes': j.get('upvotes', 0), 'publishedAt': j.get('publishedAt', '')}
    except Exception as e:
        res[i] = {'upvotes': None, 'error': str(e)}
    time.sleep(1)

ranked = sorted(res.items(), key=lambda kv: -(kv[1]['upvotes'] or -1))
print(f'=== TRUE UPVOTES for {date} ===')
for k, v in ranked:
    print(f"{k} | up={v['upvotes']} | {titles[k][:90]}")

import os
have = {k for f in os.listdir('episodes') if f.endswith('.md') for k in ids if k in f}
print('ALREADY COVERED:', have or 'none')

json.dump(res, open(f'episodes/feed/picks/true-upvotes-{date}.json', 'w'), indent=1)
print('saved episodes/feed/picks/true-upvotes-%s.json' % date)
