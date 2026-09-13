#!/usr/bin/env python3
"""Re-pull true upvotes from the HuggingFace papers API for every candidate
in the day's fetched feed, print a ranked table, and write the top-6 picks
plus any standing-rule add-ons (foundation-model tech reports, reasoning-model
topology) to episodes/feed/picks/ids-D.txt.

Usage: python debugging/rank_upvotes.py 2026-09-11
Prints: full feed ranked by true upvotes, with a topology/tech-report scan
so the agent can add rule-mandated papers beyond the top 6.
"""
import json, sys, urllib.request, pathlib

PC = pathlib.Path("/home/patrick/papercast")
D = sys.argv[1] if len(sys.argv) > 1 else "2026-09-11"

def upvote(pid):
    url = f"https://huggingface.co/api/papers/{pid}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            d = json.load(r)
        return int(d.get("upvotes", 0) or 0), d.get("title", "")
    except Exception as e:
        return -1, f"ERROR {e}"

_feed = json.load(open(PC / f"episodes/feed/papers-{D}.json"))
feed = _feed.get("papers") if isinstance(_feed, dict) else _feed
_sel = json.load(open(PC / f"episodes/feed/selected-{D}.json"))
if isinstance(_sel, dict):
    sel = _sel.get("shortlist") or _sel.get("papers") or list(_sel.values())
    sel = [v for v in sel if isinstance(v, dict)]
else:
    sel = _sel
cands = {}
for p in feed:
    pid = p.get("arxiv_id") or p.get("id")
    if pid:
        cands[pid] = p.get("title", "")
for p in sel:
    pid = p.get("arxiv_id") or p.get("id")
    if pid:
        cands.setdefault(pid, p.get("title", ""))

results = []
for pid in cands:
    u, t = upvote(pid)
    results.append((pid, u, t or cands[pid]))
results.sort(key=lambda x: -x[1])
print(f"{'rank':>4} {'id':<12} {'up':>5}  title")
for i, (pid, u, t) in enumerate(results, 1):
    print(f"{i:>4} {pid:<12} {u:>5}  {t[:95]}")

# Standing-rule scans over the FULL feed
TOPO = ["latent chain-of-thought", "latent reasoning", "continuous chain-of-thought",
        "recurrent depth", "looping", "looped", "weight tying", "weight-tied",
        "linear attention", "fast weight", "fast-weight", "state space model", "ssm",
        "adaptive computation", "adaptive depth", "adaptive depth", "test-time training",
        "iterative refinement", "chain-of-thought", "test-time scaling"]
TECH = ["technical report", "foundation model", "technical reports"]
print("\n--- TOPOLOGY SCAN (title+summary) ---")
for p in feed:
    text = ((p.get("title") or "") + " " + (p.get("summary") or "")).lower()
    hits = [w for w in TOPO if w in text]
    if hits:
        print(f"  {p.get('arxiv_id')}  {hits}  {(p.get('title') or '')[:90]}")
print("\n--- TECH-REPORT / FOUNDATION SCAN ---")
for p in feed:
    text = ((p.get("title") or "") + " " + (p.get("summary") or "")).lower()
    hits = [w for w in TECH if w in text]
    if hits:
        print(f"  {p.get('arxiv_id')}  {hits}  {(p.get('title') or '')[:90]}")
