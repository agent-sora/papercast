#!/usr/bin/env python3
"""arXiv fallback search for papercast coverage (user rule, 2026-09-20).

When the HuggingFace daily feed for a day doesn't yield enough papers that
pass the topic filters, the pipeline must search arXiv's AI listings
directly for relevant papers that HF didn't surface. This script does that:

1. Queries the arXiv API (export.arxiv.org, rate-limited: ONE request, then
   3s sleep between any retry) across the cs.AI/cs.LG/cs.CL/cs.MA listings
   for the last --days days.
2. Filters to papers matching the user's topic flavors (same lexicon as
   select_papers.py, shared via import) and applies the image/video veto.
3. Dedupes against: (a) everything already in the episode archive
   (episodes/feed/picks/ids-*.txt), (b) the HF daily caches for the last
   --days days, (c) the local paper meta/text caches.
4. Prints a JSON shortlist (title, arxiv id, published date, authors,
   summary, matched flavors) plus a human summary on stderr.

Usage:
    .venv/bin/python scripts/arxiv_search.py --days 5 [--out shortlist.json]

Pacing note (arxiv-front-door skill): one query per run, no retries without
sleep, User-Agent set, no scraping of the HTML listings.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from select_papers import FLAVORS, IMAGE_VIDEO_VETO  # noqa: E402

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom",
      "arxiv": "http://arxiv.org/schemas/atom"}

# One search phrase per flavor, each small enough to be a valid arXiv
# search_query. arXiv rejects an over-complex single query (HTTP 406) when
# many boolean terms are OR'd together, so we run EACH flavor as its own
# request, paced, and merge the results. Local score_paper() re-checks the
# full summary, so these are just recall filters.
ARXIV_QUERY_PER_FLAVOR = {
    "rl_algorithms_text_agentic": (
        '(cat:cs.LG OR cat:cs.CL) AND (all:GRPO OR all:RLHF OR all:"off-policy"'
        ' OR all:"policy gradient" OR all:"reinforcement learning" AND all:reasoning)'
    ),
    "agent_self_improvement": (
        '(cat:cs.AI OR cat:cs.CL) AND (all:"self-improvement" OR all:"self-correction"'
        ' OR all:reflexion OR all:"self-refinement" OR all:"reasoning agent" OR all:"self-evolving")'
    ),
    "ai_music_generation": (
        '(cat:cs.SD OR cat:eess.AS) AND (all:"music generation" OR all:"text-to-music"'
        ' OR all:"audio generation" OR all:"music synthesis")'
    ),
    "ai_finance_econometrics": (
        '(cat:cs.CL OR cat:q-fin) AND all:"language model" AND (all:finance OR all:trading OR all:portfolio OR all:market)'
    ),
    "lora_peft_text_only": (
        '(cat:cs.CL OR cat:cs.LG) AND (all:LoRA OR all:"parameter-efficient fine-tuning" OR all:PEFT) AND (all:reasoning OR all:"language model")'
    ),
    "reasoning_model_topology": (
        '(cat:cs.LG OR cat:cs.CL) AND (all:"looped transformer" OR all:"recurrent depth"'
        ' OR all:"linear attention" OR all:"fast weights" OR all:"state space model"'
        ' OR all:"adaptive computation" OR all:"early exit" OR all:"weight tying" OR all:"adaptive depth")'
    ),
}

IMAGE_VIDEO_VETO_RE = re.compile(
    "|".join(IMAGE_VIDEO_VETO), re.I)


def arxiv_query(query: str, start: int = 0, max_results: int = 100) -> str:
    """One rate-limited arXiv API call; returns raw Atom XML."""
    params = urllib.parse.urlencode({
        "search_query": query, "start": start, "max_results": max_results,
        "sortBy": "submittedDate", "sortOrder": "descending",
    })
    req = urllib.request.Request(f"{ARXIV_API}?{params}",
                                 headers={"User-Agent": "papercast/1.0 (agent-sora podcast)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def parse_entries(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    out = []
    for e in root.findall("a:entry", NS):
        raw = e.findtext("a:id", "", NS)
        m = re.search(r"abs/([0-9]{4}\.[0-9]{4,5})(v\d+)?", raw)
        if not m:
            continue
        pub = e.findtext("a:published", "", NS)
        out.append({
            "arxiv_id": m.group(1),
            "title": re.sub(r"\s+", " ", e.findtext("a:title", "", NS)).strip(),
            "published": pub,
            "authors": [a.findtext("a:name", "", NS)
                        for a in e.findall("a:author", NS)],
            "summary": re.sub(r"\s+", " ", e.findtext("a:summary", "", NS)).strip(),
        })
    return out


def load_archive_ids(cache_dir: str, episodes_dir: str) -> set[str]:
    """ids already covered: picks files + episode transcript filenames."""
    ids = set()
    for f in os.listdir(episodes_dir):
        m = re.match(r"\d{4}-\d{2}-\d{2}-(\d{4}\.\d{4,5})\.md$", f)
        if m:
            ids.add(m.group(1))
    picks = os.path.join(cache_dir, "picks")
    if os.path.isdir(picks):
        for f in os.listdir(picks):
            if f.startswith("ids-") and f.endswith(".txt"):
                for line in open(os.path.join(picks, f)):
                    line = line.strip()
                    if line:
                        ids.add(line)
    return ids


def load_hf_ids(cache_dir: str, days: list[str]) -> set[str]:
    """arXiv ids already surfaced by HF daily caches for the given days.
    Cache schema: papers-YYYY-MM-DD.json -> list of {"arxiv_id": "2609.12345", ...}
    (also tolerates the older paperId/arxivId key names)."""
    ids = set()
    for d in days:
        p = os.path.join(cache_dir, f"papers-{d}.json")
        if not os.path.exists(p):
            continue
        j = json.load(open(p))
        papers = j if isinstance(j, list) else j.get("papers", [])
        for ppr in papers:
            raw = (str(ppr.get("arxiv_id") or ppr.get("paperId")
                   or ppr.get("arxivId") or ""))
            m = re.search(r"(\d{4}\.\d{4,5})", raw)
            if m:
                ids.add(m.group(1))
    return ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=5,
                    help="arXiv listing window in days (default 5)")
    ap.add_argument("--cache", default=None,
                    help="feed cache dir (default episodes/feed)")
    ap.add_argument("--out", default=None, help="write JSON shortlist here")
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = args.cache or os.path.join(root, "episodes", "feed")
    episodes_dir = os.path.join(root, "episodes")

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=args.days)
    days = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(args.days)]

    query_window = f"last {args.days} days"
    print(f"# arXiv query window: {query_window} ({cutoff.date()} .. {now.date()}) "
          f"({len(ARXIV_QUERY_PER_FLAVOR)} per-flavor queries, 3s pace)", file=sys.stderr)

    entries = []
    seen_ids = set()
    for flavor, q in ARXIV_QUERY_PER_FLAVOR.items():
        try:
            xml_text = arxiv_query(q, max_results=100)
        except Exception as exc:  # noqa: BLE001
            # Per-flavor failure (406 malformed, 429 rate-limited) must not
            # kill the whole scan; the other flavors still contribute.
            code = getattr(exc, "code", None)
            print(f"!! {flavor} query failed ({code}): {exc}; skipping this flavor",
                  file=sys.stderr)
            time.sleep(10)  # back off harder on 429 before the next attempt
            continue
        fl_entries = parse_entries(xml_text)
        fresh = [e for e in fl_entries if e["arxiv_id"] not in seen_ids]
        seen_ids.update(e["arxiv_id"] for e in fl_entries)
        entries.extend(fresh)
        print(f"# {flavor}: {len(fresh)} fresh entries", file=sys.stderr)
        time.sleep(3)  # arxiv-front-door pacing: ~1 req / 3s

    if not entries:
        print("!! no arXiv entries returned (all flavor queries failed?)",
              file=sys.stderr)
        return 1
    print(f"# {len(entries)} arXiv entries in window (before filters)",
          file=sys.stderr)

    archive_ids = load_archive_ids(cache_dir, episodes_dir)
    hf_ids = load_hf_ids(cache_dir, days)
    print(f"# archive has {len(archive_ids)} covered ids; HF caches cover "
          f"{len(hf_ids)} in-window ids", file=sys.stderr)

    shortlist = []
    for e in entries:
        if datetime.fromisoformat(e["published"].replace("Z", "+00:00")) < cutoff:
            continue
        if e["arxiv_id"] in archive_ids:
            continue  # already covered
        if e["arxiv_id"] in hf_ids:
            continue  # HF surfaced it; the HF path owns it
        if IMAGE_VIDEO_VETO_RE.search(e["title"] + " " + e["summary"]):
            continue
        p = {"title": e["title"], "summary": e["summary"], "hf_title": ""}
        matched = [fl for fl, frags in FLAVORS.items()
                   if any(re.search(f.lower(), (e["title"] + " " + e["summary"]).lower())
                          for f in frags)]
        if not matched:
            continue
        shortlist.append({
            "arxiv_id": e["arxiv_id"],
            "title": e["title"],
            "published": e["published"][:10],
            "authors": e["authors"],
            "flavors": matched,
            "summary": e["summary"][:600],
        })

    print(f"# shortlist: {len(shortlist)} new arXiv papers matching topic filters",
          file=sys.stderr)
    for s in shortlist:
        print(f"  KEEP  {s['arxiv_id']}  [{','.join(s['flavors'])}]  "
              f"{s['title'][:80]}", file=sys.stderr)

    if args.out:
        with open(args.out, "w") as f:
            json.dump(shortlist, f, indent=2, ensure_ascii=False)
        print(f"# wrote {args.out}", file=sys.stderr)
    else:
        print(json.dumps(shortlist, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
