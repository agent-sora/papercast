#!/usr/bin/env python3
"""Print a drafting digest for a set of arXiv ids.

Usage: digest.py id1 id2 ...   (or: digest.py --from picks-file)
For each id, from episodes/feed/text/<id>.txt (pages 0-7):
  - first ~2600 chars (title/abstract/intro)
  - all numeric figures with 30-char context, deduped (to cite exact numbers)
Used by the Papercast nightly agent to draft transcripts with verified numbers.
"""
import re
import sys

import pathlib

PC = pathlib.Path("/home/patrick/papercast")


def digest(pid):
    p = PC / f"episodes/feed/text/{pid}.txt"
    if not p.exists():
        print(f"### {pid}: NO TEXT FILE")
        return
    t = p.read_text()
    # strip page markers
    clean = re.sub(r"===== PAGE \d+ =====", " ", t)
    clean = re.sub(r"\s+", " ", clean)
    print(f"\n########## {pid} ##########")
    print("--- HEAD (2600c) ---")
    print(clean[:2600])
    # numbers: digit runs of len>=1 with context, dedupe by the number
    seen = set()
    nums = []
    for m in re.finditer(r"\d[\d,.]*", clean):
        n = m.group(0)
        if n in seen:
            continue
        seen.add(n)
        ctx = clean[max(0, m.start() - 28):m.end() + 28]
        nums.append(f"{n}  …{ctx}…")
    print(f"--- NUMBERS ({len(nums)}) ---")
    for line in nums[:80]:
        print("  " + line)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--from":
        ids = [l.strip() for l in open(sys.argv[2]) if l.strip()]
    else:
        ids = sys.argv[1:]
    for pid in ids:
        digest(pid)


if __name__ == "__main__":
    main()
