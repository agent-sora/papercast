"""Print experiment-section lines (with decimal numbers) for a paper.

Usage: .venv/bin/python debugging/show_results.py <arxiv_id> [page_lo] [page_hi]
"""
import fitz, re, sys

PC = "/home/patrick/papercast"
pid = sys.argv[1]
lo = int(sys.argv[2]) if len(sys.argv) > 2 else 5
hi = int(sys.argv[3]) if len(sys.argv) > 3 else 8
doc = fitz.open(f"{PC}/episodes/feed/meta/{pid}.pdf")
for i in range(lo, min(hi, doc.page_count)):
    t = doc[i].get_text()
    print(f"===== PAGE {i} =====")
    print(t[:6000])
