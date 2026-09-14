#!/usr/bin/env python3
"""Scan the 2026-09-10 full feed for standing-rule candidates.

Rule 2a: new foundation-model technical reports always get an episode.
Rule 2b: papers on topological/architectural changes to reasoning LMs
(looping/recurrent depth, weight tying, adaptive computation, linear/fast-
weight/SSM attention, latent CoT) always get an episode.

Prints each feed paper's id, upvotes, title, abstract so the agent can
judge; also flags likely matches with a crude lexicon.

Usage: .venv/bin/python debugging/scan_rules_2026_09_10.py
"""
import json
import os

D = "2026-09-10"
PC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
feed = json.load(open(f"{PC}/episodes/feed/papers-{D}.json"))
papers = feed if isinstance(feed, list) else feed.get("papers", feed)

TOPO_WORDS = [
    "loop", "recurrent", "weight-ty", "weight tie", "shared weights",
    "adaptive computation", "variable-depth", "dynamic depth",
    "linear attention", "fast weight", "state space", "ssm", "mamba",
    "latent chain", "continuous chain", "latent thought",
    "recurrent depth", "iterate", "iterative depth",
]
FOUND_WORDS = ["technical report", "foundation model", "world model"]

for p in papers:
    pid = p.get("id") or p.get("paper_id") or p.get("arxiv_id")
    up = p.get("upvotes", 0)
    title = (p.get("title") or "").replace("\n", " ")
    abs_ = (p.get("summary") or p.get("abstract") or "").replace("\n", " ")
    low = (title + " " + abs_).lower()
    flags = []
    for w in TOPO_WORDS:
        if w in low:
            flags.append("TOPO:" + w)
    for w in FOUND_WORDS:
        if w in low:
            flags.append("FOUND:" + w)
    if flags:
        print(f"\n##### FLAGGED {pid} up={up} {' '.join(flags)}")
        print("TITLE:", title)
        print("ABS:", abs_[:600])
print("\n=== ALL TITLES ===")
for p in papers:
    pid = p.get("id") or p.get("paper_id") or p.get("arxiv_id")
    title = (p.get("title") or "").replace("\n", " ")
    print(f"{pid} | {title}")
