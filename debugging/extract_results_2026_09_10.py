#!/usr/bin/env python3
"""Extract result-section numbers from Show-Harness and PwM for transcript grounding."""
import re

PC = "/home/patrick/papercast"

def show(path, a, b):
    t = open(path, encoding="utf-8", errors="ignore").read()
    print("#" * 25, path.split("/")[-1], f"[{a}:{b}]")
    print(t[a:b])

# Show-Harness results: find "success rate" / SR numbers
t = open(f"{PC}/episodes/feed/text/2609.10522-more.txt", encoding="utf-8", errors="ignore").read()
print("LEN more:", len(t))
# print the results portion (usually middle)
i = t.lower().find("result")
print(t[i:i+3500])
print("======== PwM MORE ========")
p = open(f"{PC}/episodes/feed/text/2609.10540-more.txt", encoding="utf-8", errors="ignore").read()
j = p.lower().find("combatstatebench")
if j < 0:
    j = p.lower().find("result")
print(p[j:j+3000])
