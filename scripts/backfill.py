#!/usr/bin/env python3
"""Backfill candidate discovery for papercast (user rule, 2026-09-20).

When recent HF papers-days don't yield enough papers that pass the topic
filters, the pipeline backfills from OLDER HF days that still have
uncovered, filter-passing papers. This script scans the local HF caches
(oldest -> newest), reports for each day how many papers remain
uncovered by the episode archive, and writes picks files for the days
worth covering (up to --max-days, newest first).

It only SELECTS; the operator/cron then runs the normal per-paper flow
(paper_meta.py -> text extract -> draft -> gates -> synth -> publish),
stamping the Day of each backfilled episode with the PUBLICATION date
(the papers-day), which matches the "date = when covered" convention
already used by the nightly job.

Usage:
    .venv/bin/python scripts/backfill.py --min-kept 3 --max-days 3
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from select_papers import score_paper  # noqa: E402


def archive_ids(episodes_dir: str) -> set[str]:
    ids = set()
    for f in os.listdir(episodes_dir):
        m = re.match(r"\d{4}-\d{2}-\d{2}-(\d{4}\.\d{4,5})\.md$", f)
        if m:
            ids.add(m.group(1))
    return ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=None)
    ap.add_argument("--min-kept", type=int, default=3,
                    help="minimum uncovered keepers a day must have to be picked")
    ap.add_argument("--max-days", type=int, default=3,
                    help="most recent days to emit picks for (newest first)")
    ap.add_argument("--emit", action="store_true",
                    help="write ids-<day>.txt picks files for eligible days")
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = args.cache or os.path.join(root, "episodes", "feed")
    episodes_dir = os.path.join(root, "episodes")
    covered = archive_ids(episodes_dir)

    days = sorted(f[len("papers-"):-5] for f in os.listdir(cache_dir)
                  if f.startswith("papers-") and f.endswith(".json"))
    print(f"# {len(days)} cached papers-days; archive covers {len(covered)} ids",
          file=sys.stderr)

    eligible = []  # (day, [ids]) newest first
    for day in reversed(days):
        j = json.load(open(os.path.join(cache_dir, f"papers-{day}.json")))
        papers = j if isinstance(j, list) else j.get("papers", [])
        keepers = []
        for p in papers:
            # Cache schema: "arxiv_id" (older caches may use paperId/arxivId).
            raw = str(p.get("arxiv_id") or p.get("paperId") or p.get("arxivId") or "")
            m = re.search(r"(\d{4}\.\d{4,5})", raw)
            pid = m.group(1) if m else raw
            if not pid:
                continue
            if pid in covered:
                continue
            matched, veto = score_paper(p)
            if veto or not matched:
                continue
            up = int(p.get("upvotes") or 0)
            keepers.append((up, pid, p.get("title", "")[:60]))
        keepers.sort(reverse=True)
        n_uncovered = len(keepers)
        print(f"  {day}: {len(papers)} papers, {n_uncovered} uncovered keepers",
              file=sys.stderr)
        if n_uncovered >= args.min_kept:
            eligible.append((day, [k[1] for k in keepers]))
            for up, pid, title in keepers[:8]:
                print(f"      keep  {pid} ({up} up) {title}", file=sys.stderr)

    for day, ids in eligible[:args.max_days]:
        if args.emit:
            out = os.path.join(cache_dir, "picks", f"ids-{day}.txt")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w") as f:
                f.write("\n".join(ids) + "\n")
            print(f"# wrote {out} ({len(ids)} ids)", file=sys.stderr)
        else:
            print(f"  ELIGIBLE {day}: {len(ids)} ids (use --emit to write picks)",
                  file=sys.stderr)

    if not eligible:
        print("# no eligible days; consider arxiv_search.py instead",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
