"""Rank the full day's HF feed by true upvotes (re-pulled from the API).

select_papers.py scores by topic flavor, not upvotes, so the shortlist is not
the same as the true upvote leader. This script re-pulls every paper in
episodes/feed/papers-<date>.json from the HF API and prints the full ranking so
the true top-6 (and the true #1) can be confirmed before drafting.

Usage: .venv/bin/python debugging/rank_full_feed.py 2026-09-04
"""
import json
import sys
import time
import urllib.request

PC = "/home/patrick/papercast"


def up(pid: str) -> int:
    for _ in range(3):
        try:
            with urllib.request.urlopen(
                f"https://huggingface.co/api/papers/{pid}", timeout=30
            ) as r:
                return int(json.load(r).get("upvotes", 0))
        except Exception:
            time.sleep(2)
    return -1


def main() -> None:
    date = sys.argv[1]
    feed = json.load(open(f"{PC}/episodes/feed/papers-{date}.json"))
    papers = feed["papers"]
    res = {}
    for p in papers:
        pid = p.get("id") or p.get("arxiv_id")
        res[pid] = up(pid)
        print(pid, res[pid], "|", (p.get("title") or "")[:80])
        time.sleep(0.3)
    ranked = sorted(res.items(), key=lambda kv: -kv[1])
    print("\nRANKED:")
    for i, (pid, n) in enumerate(ranked, 1):
        print(f"{i:2d}. {pid}  {n}")
    top6 = [pid for pid, _ in ranked[:6]]
    print("\nTOP6:", top6)
    print("TRUE #1:", ranked[0])


if __name__ == "__main__":
    main()
