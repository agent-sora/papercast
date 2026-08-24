#!/usr/bin/env python3
"""Fetch HuggingFace Daily Papers (huggingface.co/papers) for a target date.

The page is React server-rendered: paper data lives in an HTML-escaped
`data-props` JSON blob keyed by `dailyPapers`. Each item has:
    paper.id             -> arXiv id (e.g. "2608.20061")
    paper.title          -> paper title
    paper.publishedAt    -> arXiv publish timestamp
    paper.authors        -> author list (name, optional user info)
    title                -> HF daily-papers "twitter-style" title
    summary              -> HF short summary
    submittedOnDailyAt   -> which daily-papers day this landed on
    submittedOnDailyBy   -> submitter

The HF daily-papers feed is not a calendar: a request for a date with no new
papers (weekends, holidays) snaps backward to the previous real papers-day
(the returned `dateString` is the actual papers-day). This script returns the
real papers-day it landed on plus that day's papers, cached to disk so re-runs
don't re-fetch.

Usage:
    python scripts/fetch_papers.py --date 2026-08-21 [--cache episodes/feed/]
Prints JSON: {requested_date, papers_date, papers: [...]}, and writes a cache
file <cache>/papers-<papers_date>.json.
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.request

BASE_URL = "https://huggingface.co/papers"
UA = "agent-sora/0.1 (contact: agent-sora@local)"


def _fetch_data_props(date_str: str) -> dict:
    url = f"{BASE_URL}?date={date_str}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    data = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    for p in re.findall(r'data-props="((?:[^"\\]|\\.)*)"', data):
        try:
            obj = json.loads(html.unescape(p))
        except Exception:
            continue
        if isinstance(obj, dict) and "dailyPapers" in obj:
            return obj
    raise RuntimeError(f"no dailyPapers blob found for date={date_str}")


def fetch_papers(date_str: str, cache_dir: str | None = None, force: bool = False) -> dict:
    """Return {requested_date, papers_date, papers:[...]}. Caches per papers-day."""
    # Normalize input to YYYY-MM-DD
    try:
        y, m, d = date_str.split("-")
        _ = (int(y), int(m), int(d))
    except Exception:
        raise SystemExit(f"bad date {date_str!r}; expected YYYY-MM-DD")

    obj = _fetch_data_props(date_str)
    papers_date = obj["dateString"]
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, f"papers-{papers_date}.json")
        if os.path.exists(cache_path) and not force:
            with open(cache_path) as f:
                cached = json.load(f)
            cached["requested_date"] = date_str
            cached["_cache_path"] = cache_path
            return cached

    items = obj.get("dailyPapers", [])
    papers = []
    for it in items:
        pp = it.get("paper", {})
        authors = [a.get("name", "") for a in pp.get("authors", [])]
        papers.append({
            "arxiv_id": pp.get("id"),
            "title": pp.get("title"),
            "authors": authors,
            "publishedAt": pp.get("publishedAt"),
            "submittedOnDailyAt": pp.get("submittedOnDailyAt"),
            "hf_title": it.get("title"),
            "summary": it.get("summary"),
            "upvotes": pp.get("upvoted", 0),
            "comments": it.get("numComments", 0),
            "url": f"https://huggingface.co/papers/{pp.get('id')}",
        })

    result = {
        "requested_date": date_str,
        "papers_date": papers_date,
        "papers": papers,
    }
    if cache_dir:
        with open(cache_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        result["_cache_path"] = cache_path
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="target date YYYY-MM-DD")
    ap.add_argument("--cache", default=None, help="cache dir (default: none)")
    ap.add_argument("--force", action="store_true", help="ignore cache")
    ap.add_argument("--no-print", action="store_true", help="suppress JSON to stdout")
    args = ap.parse_args()

    result = fetch_papers(args.date, cache_dir=args.cache, force=args.force)
    if not args.no_print:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"# {result['papers_date']}: {len(result['papers'])} papers", file=sys.stderr)
    if "_cache_path" in result:
        print(f"# cache: {result['_cache_path']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())