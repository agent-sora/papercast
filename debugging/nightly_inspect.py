"""Inspect the nightly feed for the Papercast pipeline.

Prints structure of papers-<D>.json and selected-<D>.json so the agent
can decide picks without flooding context.
"""
import json
import sys

pc = '/home/patrick/papercast'
d = sys.argv[1] if len(sys.argv) > 1 else '2026-10-02'
papers = json.load(open(f'{pc}/episodes/feed/papers-{d}.json'))
print('papers type:', type(papers).__name__)
if isinstance(papers, dict):
    for k, v in papers.items():
        print(' key:', k, type(v).__name__, len(v) if hasattr(v, '__len__') else v)
    items = papers.get('papers') or list(papers.values())[0]
elif isinstance(papers, list):
    items = papers
print('paper entries:', len(items))
if items:
    print('entry keys:', list(items[0].keys()))
sel = json.load(open(f'{pc}/episodes/feed/selected-{d}.json'))
print('selected:', len(sel))
for p in sel:
    print(p.get('arxiv_id'), '|', p.get('upvotes'), '|', p.get('title', '')[:75])
