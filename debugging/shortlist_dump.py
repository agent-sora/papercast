#!/usr/bin/env python3
"""Dump the selector shortlist (selected-<date>.json, a list) compactly.

Usage: shortlist_dump.py <selected-YYYY-MM-DD.json>
Prints rank, upvotes, arxiv id, and title for each entry. The shortlist is a
list of dicts (selector output). Used to cross-check standing-rule coverage
before re-ranking by true HF upvotes.
"""
import json
import sys


def main(path):
    d = json.load(open(path))
    if isinstance(d, dict):
        # some runs wrap in {"selected": [...]}
        for k, v in d.items():
            if isinstance(v, list):
                d = v
                break
    rows = []
    for p in d:
        pid = p.get("arxiv_id") or p.get("id") or "?"
        title = (p.get("title") or "").strip()
        up = p.get("upvotes", 0) or 0
        lane = p.get("lane") or p.get("reason") or ""
        rows.append((int(up), str(pid), title, str(lane)[:60]))
    rows.sort(key=lambda r: (-r[0], r[1]))
    print(f"count={len(rows)}")
    for i, (up, pid, title, lane) in enumerate(rows, 1):
        print(f"{i:2d}. up={up:<4d} {pid}  {title[:95]}  [{lane}]")


if __name__ == "__main__":
    main(sys.argv[1])
