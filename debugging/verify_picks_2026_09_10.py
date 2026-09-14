#!/usr/bin/env python3
"""Print titles/upvotes for the 2026-09-10 picks and re-run the standing-rule scan."""
import json
import subprocess
import sys

PC = "/home/patrick/papercast"
picks = [
    "2609.10522",
    "2609.10540",
    "2609.05405",
    "2609.09113",
    "2609.09219",
    "2609.06703",
]

feed = json.load(open(f"{PC}/episodes/feed/papers-2026-09-10.json"))
papers = feed if isinstance(feed, list) else (feed.get("papers") or feed.get("data") or [])
print("feed size:", len(papers))
by_id = {}
for p in papers:
    pid = str(p.get("id") or p.get("arxiv_id") or p.get("paper_id") or "")
    if pid:
        by_id[pid.lstrip("v").split("v")[-1] if pid.startswith("v") else pid] = p
# normalize: keep both raw and stripped forms
for p in papers:
    for key in ("id", "arxiv_id", "paper_id"):
        v = p.get(key)
        if v:
            by_id[str(v)] = p
            by_id[str(v).replace("v", "", 1) if str(v).startswith("v") and "." in str(v) else str(v)] = p

for pid in picks:
    p = by_id.get(pid, {})
    print("=" * 10, pid)
    print("  title:", p.get("title"))
    print("  upvotes:", p.get("upvotes"))

print("=== STANDING RULE SCAN ===")
r = subprocess.run(
    [sys.executable, f"{PC}/debugging/scan_rules_2026_09_10.py"],
    capture_output=True, text=True,
)
print(r.stdout)
print(r.stderr, file=sys.stderr)
