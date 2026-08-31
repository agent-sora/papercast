"""Extract arXiv PDF text (pages 0-15) for the 2026-08-31 Papercast batch.

Writes episodes/feed/text/<id>.txt (pages 0-7) and <id>-more.txt (pages 8-15)
for each arxiv id in episodes/feed/picks/ids-2026-08-31.txt, using pymupdf.
"""
import os
import pymupdf

PC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS_FILE = os.path.join(PC, "episodes/feed/picks/ids-2026-08-31.txt")
OUTDIR = os.path.join(PC, "episodes/feed/text")
os.makedirs(OUTDIR, exist_ok=True)

with open(IDS_FILE) as f:
    ids = [l.strip() for l in f if l.strip()]

for i in ids:
    cands = [
        os.path.join(PC, f"episodes/feed/meta/{i}.pdf"),
        os.path.join(PC, f"episodes/feed/meta/{i.replace('.', '-')}.pdf"),
    ]
    path = next((c for c in cands if os.path.exists(c)), cands[0])
    doc = pymupdf.open(path)
    pages = doc.page_count
    first = "".join(doc[p].get_text() for p in range(0, min(8, pages)))
    more = "".join(doc[p].get_text() for p in range(8, min(16, pages)))
    with open(f"{OUTDIR}/{i}.txt", "w") as fh:
        fh.write(first)
    with open(f"{OUTDIR}/{i}-more.txt", "w") as fh:
        fh.write(more)
    print(i, "pages:", pages, "first_chars:", len(first), "more_chars:", len(more))
