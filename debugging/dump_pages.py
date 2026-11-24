#!/usr/bin/env python3
"""Extract specific PDF text pages from papercast feed text dumps.

Splits episodes/feed/text/<id>[-more|-experiments].txt on the
'===== PAGE N =====' markers and prints the requested page ranges
so an agent can mine exact numbers without loading whole files.

Usage: python debugging/dump_pages.py <id> [--more] [--exp] [page page ...]
Example: python debugging/dump_pages.py 2611.25476 --more 5 6 7
"""
import re
import sys
import os

PC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(pid, suf):
    f = os.path.join(PC, "episodes", "feed", "text", f"{pid}{suf}.txt")
    if not os.path.exists(f):
        return None
    t = open(f).read()
    parts = re.split(r"===== PAGE (\d+) =====", t)
    d = {}
    for i in range(1, len(parts), 2):
        d[parts[i]] = parts[i + 1]
    return d


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    pid = args[0]
    more = "--more" in args
    exp = "--exp" in args
    pgs = [a for a in args[1:] if a.isdigit()]
    for suf in (("-more" if more else ""), ("-experiments" if exp else "")):
        d = load(pid, suf)
        if d is None:
            continue
        for p in pgs or sorted(d, key=int)[:1]:
            if p in d:
                print(f"### {pid}{suf} PAGE {p}")
                print(d[p])
                print()


if __name__ == "__main__":
    main()
