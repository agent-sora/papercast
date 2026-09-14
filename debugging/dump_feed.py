"""Dump the raw structure of the day's feed file for inspection.
Usage: .venv/bin/python debugging/dump_feed.py 2026-09-14
"""
import json
import sys

date = sys.argv[1]
f = json.load(open(f"/home/patrick/papercast/episodes/feed/papers-{date}.json"))
papers = f["papers"]
print("n papers:", len(papers))
print("keys of first paper:", sorted(papers[0].keys()))
for p in papers:
    for k in ("id", "arxiv_id", "paperId"):
        if k in p:
            print("idkey:", k, "=", p[k])
            break
    else:
        print("no id key; keys:", sorted(p.keys()))
    break
