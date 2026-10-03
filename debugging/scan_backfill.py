#!/usr/bin/env python3
"""Scan all cached HF 2026 dailies for backfill candidates.

Coverage windows (user rules 2026-09-26):
  1. The four new general categories (open_model_training_recipes,
     llm_for_mathematics, interpretability_math_analysis,
     neurosymbolic_ai): past TWO WEEKS only.
  2. Deep scope — mathematics theorem proving (esp. autoformalization in
     Lean/Isabelle/Coq) and neurosymbolic AI (incl. natural language to
     logical form): ALL of 2026 (papers_date >= 2026-01-01).

A paper is a candidate if it matches the relevant scope's flavors and is
NOT already covered (episode transcript filename or any picks file).
Deep-scope matching uses a deliberately strict regex set so the full-year
window doesn't sweep in incidental "Lean"/"formal" mentions.

Output: JSON list of {papers_date, arxiv_id, title, upvotes, scope,
matched_flavors, reasons} sorted by papers_date desc, plus a summary on
stderr.

Usage:
    .venv/bin/python debugging/scan_backfill.py [--weeks 2] [--out candidates.json]
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from select_papers import FLAVORS, score_paper  # noqa: E402

GENERAL_FLAVORS = {
    "open_model_training_recipes", "llm_for_mathematics",
    "interpretability_math_analysis", "neurosymbolic_ai",
}

# Strict deep-scope regexes (full-year window): genuine theorem-proving /
# autoformalization / neurosymbolic work only.
DEEP_THEORY = [
    r"\blean(4|\s*(v4|kernel|mathlib))\b", r"\bisabelle\b", r"\bcoq\b",
    r"\blean\b.{0,40}(theorem|proof|formal|math)",
    r"proof (assistant|assistants)", r"theorem proving", r"theorem.prover",
    r"autoformaliz", r"formaliz.{0,20}(theorem|mathematical|math)",
    r"formal (theorem|proof) ", r"\bmathlib\b", r"\bmetamath\b",
]
DEEP_NEUROSYMBOLIC = [
    r"neurosymbolic", r"neuro.symbolic",
    r"natural.language.{0,20}(logical form|logic|first.order|predicate)",
    r"(convert|translate|translate).{0,20}(text|language|sentence).{0,20}(logic|logical form)",
    r"text to (logic|logical)", r"\bT2L\b", r"\bT2Logic\b",
    r"symbolic (reasoning|integration|grounding)",
    r"logic (language|program).{0,30}(neural|language model|transformer)",
]

DEEP_RE = [re.compile("|".join(DEEP_THEORY), re.I)]
DEEP_NS_RE = [re.compile("|".join(DEEP_NEUROSYMBOLIC), re.I)]


def deep_match(text: str) -> list[str]:
    hits = []
    if any(re.search(p, text) for p in DEEP_RE):
        hits.append("theorem_proving")
    if any(re.search(p, text) for p in DEEP_NS_RE):
        hits.append("neurosymbolic")
    return hits


def covered_ids(feed_dir: str, episodes_dir: str) -> set:
    ids = set()
    for f in os.listdir(episodes_dir):
        m = re.match(r"\d{4}-\d{2}-\d{2}-(\d{4}\.\d{4,5})\.md$", f)
        if m:
            ids.add(m.group(1))
    picks = os.path.join(feed_dir, "picks")
    if os.path.isdir(picks):
        for f in os.listdir(picks):
            if f.startswith("ids-") and f.endswith(".txt"):
                for line in open(os.path.join(picks, f)):
                    line = line.strip()
                    if line:
                        ids.add(line)
    return ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weeks", type=float, default=2.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from datetime import date, timedelta
    today = date.today()
    two_weeks_ago = (today - timedelta(weeks=args.weeks)).isoformat()

    feed_dir = os.path.join(ROOT, "episodes", "feed")
    episodes_dir = os.path.join(ROOT, "episodes")
    covered = covered_ids(feed_dir, episodes_dir)

    files = sorted(f for f in os.listdir(feed_dir)
                   if re.match(r"papers-2026-\d{2}-\d{2}\.json", f))
    print(f"# {len(files)} cached 2026 dailies; {len(covered)} covered ids",
          file=sys.stderr)

    cands = []
    seen = set()
    for fname in files:
        papers_date = fname[len("papers-"):-len(".json")]
        j = json.load(open(os.path.join(feed_dir, fname)))
        papers = j.get("papers", []) if isinstance(j, dict) else j
        for p in papers:
            aid = str(p.get("arxiv_id") or p.get("paperId") or "")
            m = re.search(r"(\d{4}\.\d{4,5})", aid)
            if not m:
                continue
            aid = m.group(1)
            if aid in covered or aid in seen:
                continue
            blob = " ".join([str(p.get("title") or ""),
                             str(p.get("summary") or ""),
                             str(p.get("hf_title") or "")])
            in_2wk = papers_date >= two_weeks_ago
            matched, veto = score_paper(
                {"title": p.get("title"), "hf_title": p.get("hf_title"),
                 "summary": p.get("summary")})
            general = [f for f in matched if f in GENERAL_FLAVORS] if not veto else []
            deep = [] if veto else deep_match(blob)
            if not ((general and in_2wk) or deep):
                continue
            seen.add(aid)
            cands.append({
                "papers_date": papers_date,
                "arxiv_id": aid,
                "title": p.get("title"),
                "upvotes": p.get("upvotes"),
                "scope": "2wk" if (in_2wk and (general or not deep)) else ("2wk+deep" if in_2wk else "full2026"),
                "flavors": sorted(set(general)),
                "deep": deep,
            })

    cands.sort(key=lambda c: (c["papers_date"], -(c["upvotes"] or 0)),
               reverse=True)
    n2wk = sum(1 for c in cands if c["scope"] == "2wk")
    nfull = sum(1 for c in cands if "full2026" in c["scope"])
    print(f"# candidates: {len(cands)} total "
          f"({n2wk} 2wk-general, {nfull} full-2026 deep-scope)",
          file=sys.stderr)
    for c in cands:
        tags = ",".join(c["flavors"] + c["deep"])
        print(f"  {c['papers_date']}  {c['arxiv_id']}  [{c['scope']}] "
              f"up={c['upvotes']}  {tags}  {c['title'][:70]}", file=sys.stderr)

    if args.out:
        json.dump(cands, open(args.out, "w"), indent=2, ensure_ascii=False)
        print(f"# wrote {args.out}", file=sys.stderr)
    else:
        print(json.dumps(cands, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
