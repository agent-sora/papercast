"""Cron helper: download arXiv PDFs and extract text chunks for transcript drafting.

For each arXiv id in the picks file, downloads https://arxiv.org/pdf/<id> to
.tmp/pdfs/ (honest UA, 3s pacing) and writes episodes/feed/text/<id>.txt
(pages 0-7), <id>-more.txt (pages 8-15), and <id>-experiments.txt (pages 19-28,
only if the paper is long enough to have benchmark tables past page 15).
Skips ids whose text files already exist.
"""
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pymupdf

PC = Path("/home/patrick/papercast")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) papercast-nightly/1.0"}


def fetch_pdf(pid: str) -> Path:
    pdf_dir = PC / ".tmp/pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    local = pdf_dir / f"{pid}.pdf"
    if local.exists() and local.stat().st_size > 100_000:
        return local
    url = f"https://arxiv.org/pdf/{pid}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        local.write_bytes(r.read())
    return local


def main() -> None:
    day = sys.argv[1] if len(sys.argv) > 1 else "2026-11-18"
    picks = [
        l.strip()
        for l in (PC / f"episodes/feed/picks/ids-{day}.txt").read_text().splitlines()
        if l.strip()
    ]
    out = PC / "episodes/feed/text"
    out.mkdir(parents=True, exist_ok=True)
    for pid in picks:
        if (out / f"{pid}.txt").exists() and (out / f"{pid}-more.txt").exists():
            print(pid, "CACHED")
            continue
        try:
            local = fetch_pdf(pid)
            doc = pymupdf.open(local)
        except Exception as e:
            print(pid, "FAIL", e)
            time.sleep(5)
            continue
        n = len(doc)
        (out / f"{pid}.txt").write_text("\n".join(doc[i].get_text() for i in range(min(8, n))))
        (out / f"{pid}-more.txt").write_text("\n".join(doc[i].get_text() for i in range(8, min(16, n))))
        if n > 19:
            (out / f"{pid}-experiments.txt").write_text(
                "\n".join(doc[i].get_text() for i in range(19, min(29, n)))
            )
        print(pid, "pages", n)
        time.sleep(3)


if __name__ == "__main__":
    main()
