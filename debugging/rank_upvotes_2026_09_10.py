#!/usr/bin/env python3
"""Re-pull true HuggingFace upvotes for the 2026-09-10 candidate pool.

The nightly selector's selected-*.json stores stale/zero upvotes. This script
fetches https://huggingface.co/api/papers/<id> for every candidate (the union
of the shortlist and the day's full feed), ranks by true upvotes, writes the
top 6 ids (plus any standing-rule add-ons handled by the agent) to
episodes/feed/picks/ids-<D>.txt, and prints the full ranking for the log.

Usage: .venv/bin/python debugging/rank_upvotes_2026_09_10.py
"""
import json
import os
import time
import urllib.request

D = "2026-09-10"
PC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
feed_path = f"{PC}/episodes/feed/papers-{D}.json"
sel_path = f"{PC}/episodes/feed/selected-{D}.json"
out_path = f"{PC}/episodes/feed/picks/ids-{D}.txt"

feed = json.load(open(feed_path))
papers = feed if isinstance(feed, list) else feed.get("papers", feed)
sel = json.load(open(sel_path))

ids = []
seen = set()
for p in sel:
    i = p.get("id") or p.get("paper_id") or p.get("arxiv_id")
    if i and i not in seen:
        seen.add(i)
        ids.append(i)
for p in papers:
    i = p.get("id") or p.get("paper_id") or p.get("arxiv_id")
    if i and i not in seen:
        seen.add(i)
        ids.append(i)

print(f"candidates to re-pull: {len(ids)}")
ranked = []
for idx, pid in enumerate(ids):
    try:
        req = urllib.request.Request(
            f"https://huggingface.co/api/papers/{pid}",
            headers={"User-Agent": "papercast-nightly/1.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
        up = d.get("upvotes", 0)
        title = d.get("title", "").replace("\n", " ")
        authors = [a.get("name", "") for a in (d.get("authors") or [])][:4]
        ranked.append({"id": pid, "upvotes": up, "title": title, "authors": authors})
        print(f"[{idx+1}/{len(ids)}] {pid} up={up} {title[:70]}")
    except Exception as e:
        print(f"[{idx+1}/{len(ids)}] {pid} FETCH FAILED: {e}")
    if idx < len(ids) - 1:
        time.sleep(1.0)

ranked.sort(key=lambda r: r["upvotes"], reverse=True)
print("\n=== RANKING ===")
for r in ranked:
    print(f"{r['upvotes']:>5}  {r['id']}  {r['title'][:80]}  {', '.join(r['authors'])}")

top6 = [r["id"] for r in ranked[:6]]
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    f.write("\n".join(top6) + "\n")
print(f"\nwrote {out_path}: {top6}")
