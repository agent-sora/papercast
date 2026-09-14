#!/usr/bin/env python3
"""Dump full abstracts + first-page key numbers for the 3 remaining picks."""
import json
import re

PC = "/home/patrick/papercast"
feed = json.load(open(f"{PC}/episodes/feed/papers-2026-09-10.json"))
papers = feed if isinstance(feed, list) else (feed.get("papers") or feed.get("data") or [])
by_id = {str(p.get("id")): p for p in papers}

for pid in ["2609.09113", "2609.09219", "2609.06703"]:
    p = by_id.get(pid, {})
    print("=" * 30, pid)
    print("TITLE:", p.get("title"))
    print("ABSTRACT:", (p.get("abstract") or "").strip()[:2200])
    print()

# key numbers from first page text
def clean(path):
    raw = open(path, "rb").read().decode("utf-8", "ignore")
    raw = re.sub(r"[^\x20-\x7e\n]", "", raw)
    return raw

for pid in ["2609.06703"]:
    t = clean(f"{PC}/episodes/feed/text/{pid}.txt")
    # print paragraphs 4000..9000 for details
    print("#" * 20, pid, "first-page body 4000-9500")
    print(t[4000:9500])
