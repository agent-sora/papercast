#!/usr/bin/env python3
"""Get metadata + text-file listing for 2609.09219 and the full pick set."""
import json, glob, os

PC = "/home/patrick/papercast"
feed = json.load(open(f"{PC}/episodes/feed/papers-2026-09-10.json"))
papers = feed if isinstance(feed, list) else feed.get("papers") or feed.get("data")

picks = ["2609.10522", "2609.10540", "2609.05405", "2609.09113", "2609.09219", "2609.06703"]
for p in papers:
    if str(p.get("id")) in picks:
        print("ID:", p.get("id"), "UPV:", p.get("upvotes"))
        print("  TITLE:", p.get("title"))
        print("  AUTHORS:", [a.get("name") for a in (p.get("authors") or [])])
        print("  AFFIL:", (p.get("affiliations") or p.get("affil_lines"))[:3])
print("---TEXT FILES---")
for f in sorted(glob.glob(f"{PC}/episodes/feed/text/2609.09219*")):
    print(f, os.path.getsize(f))
print("---EPISODES EXIST---")
for f in sorted(glob.glob(f"{PC}/episodes/2026-09-10-*.md")):
    print(os.path.basename(f))
