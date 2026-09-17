"""Extract page ranges from each picked paper's PDF into episodes/feed/text/.

For every arxiv id in the picks file, downloads the arXiv PDF (cached under
episodes/feed/text/_pdf/<id>.pdf) and extracts:
  <id>.txt            pages 0-7   (abstract, intro, method)
  <id>-more.txt       pages 8-15  (details, setup)
  <id>-experiments.txt pages 19-28 (benchmark tables, when they exist)
Uses pymupdf (import pymupdf), not fitz. Idempotent: skips existing files.

Usage: python debugging/extract_paper_text.py <date>
"""
import json
import os
import sys
import urllib.request

PC = "/home/patrick/papercast"


def main() -> None:
    date = sys.argv[1]
    picks_path = f"{PC}/episodes/feed/picks/ids-{date}.txt"
    ids = [l.strip() for l in open(picks_path) if l.strip()]
    text_dir = f"{PC}/episodes/feed/text"
    pdf_dir = os.path.join(text_dir, "_pdf")
    os.makedirs(pdf_dir, exist_ok=True)
    import pymupdf  # noqa: N813

    ranges = {
        "": [(0, 7)],
        "-more": [(8, 15)],
        "-experiments": [(19, 28)],
    }
    for pid in ids:
        pdf_path = os.path.join(pdf_dir, f"{pid}.pdf")
        if not os.path.exists(pdf_path):
            url = f"https://arxiv.org/pdf/{pid}"
            req = urllib.request.Request(url, headers={"User-Agent": "papercast/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r, open(pdf_path, "wb") as f:
                f.write(r.read())
            print(f"{pid}: downloaded {os.path.getsize(pdf_path)//1024} KB")
        else:
            print(f"{pid}: pdf cached")
        doc = pymupdf.open(pdf_path)
        n = len(doc)
        for suffix, spans in ranges.items():
            out = os.path.join(text_dir, f"{pid}{suffix}.txt")
            if os.path.exists(out) and os.path.getsize(out) > 500:
                continue
            parts = []
            for lo, hi in spans:
                for i in range(lo, min(hi + 1, n)):
                    parts.append(doc[i].get_text())
            with open(out, "w") as f:
                f.write("\n".join(parts))
            print(f"  wrote {os.path.basename(out)} ({sum(len(p) for p in parts)} chars)")
        doc.close()
    print("EXTRACT_DONE")


if __name__ == "__main__":
    main()
