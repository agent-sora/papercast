#!/usr/bin/env python3
"""Backfill the 'title' field into episodes/feed/meta/*.json.

Older meta JSONs written by scripts/paper_meta.py pre-title-support have no
'title' key, which breaks the front-matter contract (Title: <title>) for
arXiv-only episodes. This script fills 'title' for every meta file in the
cache dir that is missing it:

1. arXiv ids that appear in an HF daily cache (papers-*.json) -> title from
   the cache entry (no network).
2. Otherwise -> HF papers API (one request per id, 1s pace).

Usage:  .venv/bin/python debugging/fill_meta_titles.py [--cache-dir episodes/feed/meta]
Idempotent: files that already carry a non-empty title are left untouched.
"""
import argparse, json, os, re, urllib.request, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", default="episodes/feed/meta")
    ap.add_argument("--feed-dir", default="episodes/feed")
    args = ap.parse_args()

    # index HF caches: arxiv_id -> title
    hf_titles = {}
    feed_dir = os.path.abspath(args.feed_dir)
    for name in os.listdir(feed_dir):
        if not re.match(r"papers-\d{4}-\d{2}-\d{2}\.json", name):
            continue
        try:
            data = json.load(open(os.path.join(feed_dir, name)))
        except Exception:
            continue
        for p in data.get("papers", []) if isinstance(data, dict) else data:
            aid = re.sub(r"v\d+$", "", str(p.get("arxiv_id", "")).strip())
            if aid and p.get("title"):
                hf_titles[aid] = p["title"]

    done = skipped = failed = 0
    for name in sorted(os.listdir(args.cache_dir)):
        if not re.match(r"\d{4}\.\d{4,5}\.json", name):
            continue
        path = os.path.join(args.cache_dir, name)
        meta = json.load(open(path))
        if meta.get("title"):
            skipped += 1
            continue
        aid = meta["arxiv_id"]
        title = hf_titles.get(aid, "")
        if not title:
            try:
                req = urllib.request.Request(
                    f"https://huggingface.co/api/papers/{aid}",
                    headers={"User-Agent": "papercast/1.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    title = json.load(r).get("title", "")
                time.sleep(1)
            except Exception as e:
                print(f"FAIL {aid}: {e}")
                failed += 1
        if title:
            meta["title"] = re.sub(r"\s+", " ", title).strip()
            json.dump(meta, open(path, "w"), indent=1)
            done += 1
            print(f"filled {aid}: {meta['title'][:70]}")
    print(f"fill_meta_titles done={done} skipped={skipped} failed={failed}")

if __name__ == "__main__":
    main()
