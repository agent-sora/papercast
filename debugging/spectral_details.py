"""Print method/numbers context around key terms in the SpectralShift paper.
Reads the extracted text files and prints matched lines with surrounding
context, so the transcript can cite concrete method details and benchmark
numbers.

Usage: python debugging/spectral_details.py
"""
import re

PC = "/home/patrick/papercast"
TERMS = re.compile(
    r"RULER|128K|32K|64K|needle|decay|spectral|alpha|gate|reparam|continued pretrain|long-context|context window|4K|8K",
    re.I,
)
files = [
    f"{PC}/episodes/feed/text/2609.14320.txt",
    f"{PC}/episodes/feed/text/2609.14320-more.txt",
    f"{PC}/episodes/feed/text/2609.14320-experiments.txt",
]
seen = set()
for path in files:
    lines = [l.rstrip() for l in open(path, errors="replace")]
    for i, l in enumerate(lines):
        if TERMS.search(l) and len(l) < 160 and l not in seen and not re.search(r"arxiv|http|\.org|et al", l, re.I):
            seen.add(l)
            print(l)
        if len(seen) > 90:
            break
