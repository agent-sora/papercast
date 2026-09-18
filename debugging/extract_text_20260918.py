"""Extract arXiv paper text to episodes/feed/text/ for the 2026-09-18 batch.

Uses pymupdf (NOT fitz) to pull, for each id in the picks file:
  <id>.txt            pages 0-7
  <id>-more.txt       pages 8-15
  <id>-experiments.txt pages 19-28 (only when the paper has benchmark tables
                      past page 15, i.e. total pages >= 20)
PDFs are expected in episodes/feed/meta/<id>.pdf (cached by paper_meta.py).
"""
import json
import os
import sys

import pymupdf

PC = "/home/patrick/papercast"
D = "2026-09-18"
ids = [l.strip() for l in open(f"{PC}/episodes/feed/picks/ids-{D}.txt") if l.strip()]
text_dir = f"{PC}/episodes/feed/text"
os.makedirs(text_dir, exist_ok=True)


def pages(doc, lo, hi):
    out = []
    for i in range(lo, min(hi + 1, len(doc))):
        out.append(doc[i].get_text())
    return "\n\n".join(out)


for i in ids:
    pdf = f"{PC}/episodes/feed/meta/{i}.pdf"
    if not os.path.exists(pdf):
        print(f"{i}: PDF MISSING at {pdf}")
        continue
    doc = pymupdf.open(pdf)
    n = len(doc)
    open(f"{text_dir}/{i}.txt", "w").write(pages(doc, 0, 7))
    open(f"{text_dir}/{i}-more.txt", "w").write(pages(doc, 8, 15))
    if n >= 20:
        open(f"{text_dir}/{i}-experiments.txt", "w").write(pages(doc, 19, 28))
    print(f"{i}: {n} pages -> main+more" + (f"+experiments" if n >= 20 else ""))
    doc.close()
print("TEXT_DONE")
