"""Extract PDF page ranges to text files for a pick list (pymupdf, NOT fitz).

For each arxiv id in the ids file: downloads/caches the arxiv PDF under
episodes/feed/pdf/, then writes:
  episodes/feed/text/<id>.txt          pages 0-7
  episodes/feed/text/<id>-more.txt     pages 8-15
  episodes/feed/text/<id>-experiments.txt  pages 19-28 (only if PDF > 28 pages)

Usage: .venv/bin/python debugging/extract_texts.py 2026-09-14
"""
import os
import re
import sys
import urllib.request

PC = "/home/patrick/papercast"
DATE = sys.argv[1]
PDF_DIR = f"{PC}/episodes/feed/pdf"
TXT_DIR = f"{PC}/episodes/feed/text"


def get_pdf(aid: str) -> str:
    path = f"{PDF_DIR}/{aid}.pdf"
    if not os.path.exists(path):
        url = f"https://arxiv.org/pdf/{aid}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
            f.write(r.read())
    return path


def extract(path: str, lo: int, hi: int) -> str:
    import pymupdf

    doc = pymupdf.open(path)
    parts = []
    for i in range(lo, min(hi, len(doc))):
        parts.append(doc[i].get_text())
    return "\n".join(parts)


def main() -> None:
    ids = [
        line.strip()
        for line in open(f"{PC}/episodes/feed/picks/ids-{DATE}.txt")
        if line.strip()
    ]
    for aid in ids:
        path = get_pdf(aid)
        for suffix, lo, hi in (("", 0, 8), ("-more", 8, 16), ("-experiments", 19, 29)):
            txt = extract(path, lo, hi)
            out = f"{TXT_DIR}/{aid}{suffix}.txt"
            with open(out, "w") as f:
                f.write(txt)
            print(aid, suffix or "main", len(txt), "chars")


if __name__ == "__main__":
    main()
