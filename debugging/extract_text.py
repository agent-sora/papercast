#!/usr/bin/env python3
"""Extract PDF text pages for a batch of picked arXiv papers.

For each arxiv id in the picks file, downloads https://arxiv.org/pdf/<id>
into .tmp/pdfs/ and writes three text files into episodes/feed/text/:
  <id>.txt           pages 0-7   (abstract, intro, method)
  <id>-more.txt      pages 8-15  (method continued, setup)
  <id>-experiments.txt pages 19-28 (benchmark tables, when they exist)

Usage:
    .venv/bin/python debugging/extract_text.py --picks episodes/feed/picks/ids-2026-09-30.txt
"""
import argparse
import os
import sys
import time
import urllib.request

import pymupdf

PC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "papercast-nightly/1.0 (contact: patrick)"}
RANGES = {"": (0, 7), "-more": (8, 15), "-experiments": (19, 28)}


def download(aid: str) -> str:
    dest = os.path.join(PC, ".tmp", "pdfs", f"{aid}.pdf")
    if os.path.exists(dest) and os.path.getsize(dest) > 50_000:
        return dest
    url = f"https://arxiv.org/pdf/{aid}"
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
            return dest
        except Exception as e:
            if attempt == 2:
                print(f"  ! {aid}: download failed: {e}", file=sys.stderr)
                return None
            time.sleep(4 * (attempt + 1))
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks", required=True)
    args = ap.parse_args()
    ids = [l.strip() for l in open(args.picks) if l.strip()]
    out_dir = os.path.join(PC, "episodes", "feed", "text")
    os.makedirs(out_dir, exist_ok=True)
    for aid in ids:
        pdf = download(aid)
        if pdf is None:
            continue
        try:
            doc = pymupdf.open(pdf)
        except Exception as e:
            print(f"  ! {aid}: open failed: {e}", file=sys.stderr)
            continue
        n = doc.page_count
        for suffix, (lo, hi) in RANGES.items():
            if lo >= n:
                continue
            hi = min(hi, n - 1)
            text = "\n".join(doc[p].get_text() for p in range(lo, hi + 1))
            with open(os.path.join(out_dir, f"{aid}{suffix}.txt"), "w") as f:
                f.write(text)
        print(f"  {aid}: {n} pages extracted")
        time.sleep(3)


if __name__ == "__main__":
    main()
