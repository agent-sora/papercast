#!/usr/bin/env python3
"""Generate compact per-paper briefings for episode drafting.

For each arxiv id in an ids file, emit .tmp/briefing-<id>.txt containing:
  - front-matter source values (title, first 3 authors, upvotes, link)
  - a suggested Labs string (affiliation lines scraped from the PDF first page)
  - the abstract (HF summary)
  - the top-level section headings (so the drafter sees the paper's structure)
  - key quantitative sentences (result markers, digits, percentages), deduped

The point is to give a drafter a fact-dense digest instead of an 80k-char raw
PDF dump, while the full text stays on disk for the drafter to verify specific
figures. Every number in a transcript must trace to the paper text, so the
briefing's sentences are a starting menu, not a substitute for checking.

Usage:
  .venv/bin/python debugging/make_briefings.py .tmp/final-28.txt
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/patrick/papercast")
META = ROOT / "episodes/feed/meta"
TEXT = ROOT / "episodes/feed/text"
OUT = ROOT / ".tmp"

RESULT_MARKERS = re.compile(
    r"\b(outperform|outperforms|state.of.the.art|sota|achieve|achieves|achieved|improve"
    r"|improves|improved|surpass|surpasses|exceed|exceeds|reduce|reduces|reduced|increase"
    r"|increases|increased|accuracy|precision|recall|f1|bleu|rouge|pass rate|success rate"
    r"|win rate|winrate|accuracy|top.?1|top.?5|top.?k|baseline|ablat|ablation"
    r"|benchmark|leaderboard|compare|compared|compares|we propose|we introduce"
    r"|we present|we show|we demonstrate|we find|we report|we evaluate)\b", re.I)

# A sentence is "key" if it has a result marker OR a digit (incl. %), and is a
# reasonable length.
def is_key(sent):
    if len(sent.split()) < 8 or len(sent.split()) > 60:
        return False
    if not (re.search(r"\d", sent) or RESULT_MARKERS.search(sent)):
        return False
    # skip pure references / figure-caption noise
    if re.search(r"\b(figure|fig\.)\s*\d", sent, re.I) and not re.search(r"\d[\d,.]*\s*%", sent):
        return False
    return True


def section_headings(text):
    """Rough top-level heading extraction from PDF-extracted text."""
    heads = []
    # numbered headings like "1  Introduction" or "1.2  Method"
    for m in re.finditer(r"(?m)^\s*(\d{1,2}(?:\.\d{1,2})?)\s+([A-Z][A-Za-z0-9 ,:&\-]{3,60})\s*$", text):
        label, title = m.group(1), m.group(2).strip()
        if title.lower() in ("abstract", "introduction", "references", "appendix",
                             "conclusion", "related work", "method", "methods",
                             "experiments", "evaluation", "results", "discussion",
                             "limitations", "background", "problem setup",
                             "preliminaries", "notation", "setup"):
            heads.append(f"{label} {title}")
    # unnumbered ALL-CAPS or Title-Case headings
    for m in re.finditer(r"(?m)^\s*([A-Z][A-Za-z0-9 ,:&\-]{3,45})\s*$", text):
        t = m.group(1).strip()
        if t.isupper() or (t[0].isupper() and not t.isupper()):
            heads.append(t)
    # dedupe preserve order, cap
    seen, out = set(), []
    for h in heads:
        if h not in seen:
            seen.add(h); out.append(h)
    return out[:24]


def affiliation_lines(text):
    """Heuristic: affiliation lines near the top (first ~1500 chars)."""
    head = text[:1600]
    cands = []
    for line in head.splitlines():
        line = line.strip()
        if re.search(r"\b(University|Institute|Institut|Laborator|Laboratory|Lab\b|College"
                     r"|School|Academy|Research|Center|Centre|Microsoft|Google|OpenAI"
                     r"|DeepMind|Meta|NVIDIA|Amazon|Apple|Anthropic|Tsinghua|ETH|EPFL"
                     r"|MIT|Stanford|Berkeley|CMU|KAIST|MPI|Tencent|Baidu|Alibaba"
                     r"|ByteDance|Huawei|Samsung|Sber|Yandex|Oracle|Adobe|IBM|Intel)\b", line):
            if 2 < len(line) < 90 and not line.startswith(("http", "www", "arXiv", "Abstract")):
                cands.append(line)
    seen, out = set(), []
    for c in cands:
        c = re.sub(r"\s+", " ", c).strip(" .,;")
        if c not in seen:
            seen.add(c); out.append(c)
    return out[:8]


def key_sentences(text, n=40):
    text = re.sub(r"\s+", " ", text)
    # split on sentence-ish boundaries
    sents = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text)
    picked, seen = [], set()
    for s in sents:
        s = s.strip()
        if not is_key(s):
            continue
        key = s[:60]
        if key in seen:
            continue
        seen.add(key); picked.append(s)
        if len(picked) >= n:
            break
    return picked


def brief(pid):
    meta = json.loads((META / f"{pid}.json").read_text())
    tpath = TEXT / f"{pid}.txt"
    text = tpath.read_text() if tpath.exists() else ""
    authors = meta.get("authors", [])
    first3 = ", ".join(authors[:3])
    labs = "; ".join(affiliation_lines(text)) or "(verify from PDF first page)"
    L = []
    L.append(f"ARXIV: {pid}")
    L.append(f"TITLE: {meta.get('title','')}")
    L.append(f"AUTHORS (full): {', '.join(authors)}")
    L.append(f"FIRST 3 (cold open): {first3}")
    L.append(f"UPVOTES: {meta.get('upvotes','')}")
    L.append(f"PUBLISHED_AT: {meta.get('publishedAt','')}")
    L.append(f"SUGGESTED LABS: {labs}")
    L.append("")
    L.append("ABSTRACT:")
    L.append(meta.get("summary", "").strip())
    L.append("")
    L.append("SECTION STRUCTURE:")
    for h in section_headings(text):
        L.append(f"  - {h}")
    L.append("")
    L.append("KEY QUANTITATIVE / RESULT SENTENCES (verify each against full text before using):")
    for i, s in enumerate(key_sentences(text), 1):
        L.append(f"  {i}. {s}")
    L.append("")
    L.append(f"FULL TEXT: {tpath} ({len(text)} chars) — read it for exact figures.")
    return "\n".join(L)


def main():
    ids_file = sys.argv[1]
    ids = [l.strip() for l in open(ids_file) if l.strip()]
    for pid in ids:
        try:
            b = brief(pid)
            (OUT / f"briefing-{pid}.txt").write_text(b)
            print(f"OK {pid} ({len(b)} chars)")
        except Exception as e:
            print(f"FAIL {pid}: {e}")


if __name__ == "__main__":
    main()
