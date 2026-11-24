#!/usr/bin/env python3
"""Re-pull true upvote counts from the HF papers API for all candidates in a
selected-*.json shortlist, rank them, and save true-upvotes-<D>.json in picks/.

Usage: python debugging/pull_true_upvotes.py <selected.json> <date>
"""
import json, sys, time, urllib.request

def main():
    sel_path, date = sys.argv[1], sys.argv[2]
    sel = json.load(open(sel_path))
    ids = [p['arxiv_id'] for p in sel]
    up = {}
    for i in ids:
        try:
            req = urllib.request.Request(
                f'https://huggingface.co/api/papers/{i}',
                headers={'User-Agent': 'papercast-cron/1.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                d = json.load(r)
                up[i] = d.get('upvotes', 0)
        except Exception as e:
            up[i] = -1
            print('ERR', i, e)
        time.sleep(0.3)
    ranked = sorted(up.items(), key=lambda kv: -kv[1])
    out = f'episodes/feed/picks/true-upvotes-{date}.json'
    json.dump({i: up[i] for i in ids}, open(out, 'w'), indent=1)
    for i, u in ranked:
        print(u, i)
    top6 = [i for i, _ in ranked[:6]]
    open(f'episodes/feed/picks/ids-{date}.txt', 'w').write('\n'.join(top6) + '\n')
    print('PICKS', top6)

if __name__ == '__main__':
    main()
