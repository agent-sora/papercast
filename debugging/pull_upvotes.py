#!/usr/bin/env python3
"""Re-pull true HF upvotes for the day's selected papers.

Usage: .venv/bin/python debugging/pull_upvotes.py <papers-date>
Reads episodes/feed/selected-<date>.json, hits the HF API per id (paced),
writes .tmp/upvotes-<date>.json with {id: upvotes, feed_extra_ids: [...]}.
"""
import json, sys, time, urllib.request

PC = '/home/patrick/papercast'

def fetch_upvotes(pid):
    url = f'https://huggingface.co/api/papers/{pid}'
    req = urllib.request.Request(url, headers={'User-Agent': 'papercast-nightly/1.0'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                d = json.loads(r.read())
            return d.get('paper', {}).get('upvotes') or d.get('upvotes', 0)
        except Exception as e:
            if attempt == 2:
                return f'ERR:{e}'
            time.sleep(2)

def main():
    date = sys.argv[1]
    sel = json.load(open(f'{PC}/episodes/feed/selected-{date}.json'))
    papers = json.load(open(f'{PC}/episodes/feed/papers-{date}.json'))
    plist = papers if isinstance(papers, list) else (papers.get('papers') or papers.get('items') or [])
    results = {}
    for p in sel:
        pid = p['arxiv_id']
        results[pid] = fetch_upvotes(pid)
        time.sleep(0.5)
    ids = set(results)
    feed_extra = []
    for p in plist:
        aid = p.get('arxiv_id') or p.get('id')
        if aid and aid not in ids:
            feed_extra.append(aid)
    json.dump({'ids': results, 'feed_extra_ids': feed_extra},
              open(f'{PC}/.tmp/upvotes-{date}.json', 'w'))
    ranked = sorted(results.items(), key=lambda kv: (kv[1] if isinstance(kv[1], int) else -1), reverse=True)
    for pid, u in ranked:
        title = next((p['title'] for p in sel if p['arxiv_id'] == pid), '')[:85]
        print(f'{u}\t{pid}\t{title}')
    print('feed_extra:', len(feed_extra))

if __name__ == '__main__':
    main()
