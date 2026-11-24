#!/usr/bin/env python3
"""Scan a daily HF papers feed (papers-<date>.json) and print a compact table.

Usage: feed_scan.py <papers-YYYY-MM-DD.json>
Prints for each paper: upvotes, id, and title. Sorted by upvotes desc.
Used by the Papercast nightly agent to pick the slate and spot-check the
full day feed for standing-rule categories.
"""
import json
import sys


def main(path):
    d = json.load(open(path))
    papers = d.get("papers", [])
    rows = []
    for p in papers:
        pid = (
            p.get("arxiv_id")
            or p.get("id")
            or p.get("paper", {}).get("id", "?")
        )
        title = (p.get("title") or p.get("paper", {}).get("title", "?")).strip()
        up = p.get("upvotes")
        if up is None:
            up = p.get("paper", {}).get("upvotes", 0)
        rows.append((int(up or 0), str(pid), title))
    rows.sort(key=lambda r: (-r[0], r[1]))
    print(f"papers_date={d.get('papers_date')} requested={d.get('requested_date')} count={len(rows)}")
    for i, (up, pid, title) in enumerate(rows, 1):
        print(f"{i:2d}. up={up:<4d} {pid}  {title[:110]}")


if __name__ == "__main__":
    main(sys.argv[1])
