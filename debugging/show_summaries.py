"""Print full summaries for two papers from the day's feed (manual re-scan aid).
Usage: .venv/bin/python debugging/show_summaries.py 2026-09-14 2609.12641 2609.08418
"""
import json
import sys

date = sys.argv[1]
want = sys.argv[2:]
f = json.load(open(f"/home/patrick/papercast/episodes/feed/papers-{date}.json"))
for p in f["papers"]:
    if p.get("arxiv_id") in want:
        print("#" * 90)
        print(p["arxiv_id"], p.get("title"))
        print("authors:", ", ".join(p.get("authors", [])))
        print(p.get("summary", ""))
