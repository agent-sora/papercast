"""Extract remaining pages (15+) of a paper PDF to an -experiments text file.

Usage: .venv/bin/python debugging/extract_tail.py <arxiv_id>
"""
import fitz, os, sys

PC = "/home/patrick/papercast"
pid = sys.argv[1]
doc = fitz.open(f"{PC}/episodes/feed/meta/{pid}.pdf")
txt = ""
for i in range(15, doc.page_count):
    txt += f"\n===== PAGE {i} =====\n" + doc[i].get_text()
out = f"{PC}/episodes/feed/text/{pid}-experiments.txt"
open(out, "w").write(txt)
print(pid, "pages:", doc.page_count, "->", out)
