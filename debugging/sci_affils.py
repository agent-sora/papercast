"""Scan all pages of the ScienceIDE PDF for the numbered affiliation list and
print the first 25 distinct institution lines found.

Usage: python debugging/sci_affils.py
"""
import re
import pymupdf

PC = "/home/patrick/papercast"
d = pymupdf.open(f"{PC}/episodes/feed/text/_pdf/2609.19134.pdf")
seen = []
for i in range(len(d)):
    t = d[i].get_text()
    for line in t.split("\n"):
        s = line.strip()
        if re.match(r"^\d{1,2}\s", s) and re.search(
            r"University|Institute|Laboratory|Academy|College|School|Technology|Technique|AI", s
        ) and len(s) < 80:
            if s not in seen:
                seen.append(s)
    if len(seen) > 30:
        break
for s in seen[:30]:
    print(s)
