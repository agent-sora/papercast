#!/usr/bin/env python3
"""Report lint word-count (regex [A-Za-z0-9'-]+) per transcript and shortfall to 1300."""
import re, glob, sys

def wc(path):
    text = open(path, encoding="utf-8").read()
    body = text.split("---", 2)[2] if text.startswith("---") else text
    return len(re.findall(r"[A-Za-z0-9'-]+", body))

target_min = 1330  # small buffer above 1300
for p in sorted(glob.glob("/home/patrick/papercast/episodes/2026-09-10-*.md")):
    w = wc(p)
    short = max(0, target_min - w)
    print(f"{p.split('/')[-1]}: {w} words  shortfall~{short}")
