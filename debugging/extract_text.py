#!/usr/bin/env python3
"""Extract PDF page ranges to text for draft transcripts.

Usage: extract_text.py
Reads episodes/feed/picks/ids-<today>.txt (or a given ids file) and, for each
arXiv id, pulls the matching PDF from episodes/feed/meta/<id>.pdf and writes:
  episodes/feed/text/<id>.txt            pages 0-7   (abstract + intro)
  episodes/feed/text/<id>-more.txt       pages 8-15
  episodes/feed/text/<id>-experiments.txt pages 19-28 (only if >= 20 pages)
Uses pymupdf (import fitz). Idempotent: skips ids whose .txt already exists.
"""
import os
import sys

import fitz  # pymupdf

PC = "/home/patrick/papercast"
META = os.path.join(PC, "episodes/feed/meta")
TEXT = os.path.join(PC, "episodes/feed/text")
PICKS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PC, "episodes/feed/picks/ids-2026-10-05.txt")


def pages_text(doc, lo, hi):
    n = doc.page_count
    hi = min(hi, n - 1)
    parts = []
    for i in range(lo, hi + 1):
        parts.append(f"\n===== PAGE {i} =====\n")
        parts.append(doc[i].get_text())
    return "".join(parts)


def main():
    ids = [ln.strip() for ln in open(PICKS) if ln.strip()]
    os.makedirs(TEXT, exist_ok=True)
    for pid in ids:
        pdf = os.path.join(META, f"{pid}.pdf")
        base = os.path.join(TEXT, f"{pid}.txt")
        if os.path.exists(base):
            print(f"skip {pid} (exists)")
            continue
        if not os.path.exists(pdf):
            print(f"MISSING pdf {pid}")
            continue
        doc = fitz.open(pdf)
        n = doc.page_count
        open(base, "w").write(pages_text(doc, 0, 7))
        open(base.replace(".txt", "-more.txt"), "w").write(pages_text(doc, 8, 15))
        if n >= 20:
            open(base.replace(".txt", "-experiments.txt"), "w").write(pages_text(doc, 19, 28))
        print(f"{pid}: {n} pages -> text written")
        doc.close()


if __name__ == "__main__":
    main()
