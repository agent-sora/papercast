#!/usr/bin/env python3
"""Re-pull true upvotes from the HF papers API for all candidates in the
day's selected shortlist, rank them, and write the top-N picks file.

Usage:
    .venv/bin/python debugging/upvote_pull.py --date 2026-09-30 [--top 6] [--out <picks file>]

Reads episodes/feed/selected-<date>.json, hits
https://huggingface.co/api/papers/<arxiv_id> for each candidate,
and prints a ranked table. Writes the top-N arxiv ids (one per line)
to the picks file (default episodes/feed/picks/ids-<date>.txt).
"""
import argparse
import json
import os
import sys
import time
import urllib.request

PC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fetch_upvotes(arxiv_id: str) -> int:
    req = urllib.request.Request(
        f"https://huggingface.co/api/papers/{arxiv_id}",
        headers={"User-Agent": "papercast-nightly/1.0"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
            return int(data.get("upvotes", 0))
        except Exception as e:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
            else:
                print(f"  ! {arxiv_id}: {e}", file=sys.stderr)
                return 0
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    sel_path = os.path.join(PC, "episodes/feed", f"selected-{args.date}.json")
    sel = json.load(open(sel_path))
    rows = []
    for p in sel:
        aid = p.get("arxiv_id")
        up = fetch_upvotes(aid)
        rows.append({"id": aid, "up": up, "title": p.get("title", ""),
                     "authors": p.get("authors", [])})
        time.sleep(0.3)
    rows.sort(key=lambda r: (-r["up"], r["id"]))
    for i, r in enumerate(rows, 1):
        print(f"{i:2d}. {r['id']} up={r['up']:3d} {r['title'][:80]}")
    out = args.out or os.path.join(PC, "episodes/feed/picks", f"ids-{args.date}.txt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        for r in rows[: args.top]:
            f.write(r["id"] + "\n")
    print(f"\nwrote {out}: {[r['id'] for r in rows[: args.top]]}")
    json.dump(rows, open(os.path.join(PC, ".tmp", f"upvotes-{args.date}.json"), "w"))


if __name__ == "__main__":
    main()
