#!/usr/bin/env python3
"""Re-pull live HuggingFace upvotes for a day's paper feed.

Reads episodes/feed/papers-<DATE>.json, queries
https://huggingface.co/api/papers/<id> for every arxiv id (0.5s pacing,
3 retries with backoff), prints the ranked list, and writes
episodes/feed/true_upvotes-<DATE>.json.

Usage: .venv/bin/python debugging/pull_true_upvotes.py 2026-10-30
"""
import json
import sys
import time
import urllib.request

PC = "/home/patrick/papercast"

def main():
    date = sys.argv[1]
    feed = json.load(open(f"{PC}/episodes/feed/papers-{date}.json"))
    papers = feed["papers"]
    ids = [p["arxiv_id"] for p in papers]

    res = {}
    for i in ids:
        url = f"https://huggingface.co/api/papers/{i}"
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "papercast-nightly/1.0 (research digest)"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    d = json.loads(r.read())
                title = (d.get("title") or papers[i].get("title", ""))[:70]
                res[i] = (title, d.get("upvotes", 0))
                break
            except Exception:
                if attempt == 2:
                    res[i] = ("ERR", None)
                time.sleep(3)
        time.sleep(0.5)

    ranked = sorted(((v[1] if v[1] is not None else -1, k, v[0]) for k, v in res.items()),
                    reverse=True)
    for up, k, t in ranked:
        print(up, k, t)

    json.dump({k: {"title": v[0], "upvotes": v[1]} for k, v in res.items()},
              open(f"{PC}/episodes/feed/true_upvotes-{date}.json", "w"), indent=1)

if __name__ == "__main__":
    main()
