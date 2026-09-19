#!/usr/bin/env python3
"""Print titles of the 2026-09-18 papers-day feed (Saturday duplicate-guard log).

Usage: .venv/bin/python debugging/feed_titles_2026_09_19.py
"""
import json

feed = json.load(open("/home/patrick/papercast/episodes/feed/papers-2026-09-18.json"))
if isinstance(feed, dict):
    feed = feed.get("papers", feed.get("items", []))
for p in feed:
    print((p.get("id") or p.get("arxiv_id") or "?"), "|", (p.get("title") or "").strip())
