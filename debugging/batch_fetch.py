#!/usr/bin/env python3
"""Batch-fetch HF meta + PDF text for a list of arXiv ids (idempotent).

For each id: (a) ensure episodes/feed/meta/<id>.json exists (HF API title,
authors, upvotes, published), (b) ensure episodes/feed/text/<id>.txt exists
(download arXiv PDF -> pymupdf text). Skips anything already cached so a
re-run only does the missing work. Paced: 1.0s between HF calls, 1.5s between
PDF downloads (arXiv front-door etiquette).

Usage:
    .venv/bin/python debugging/batch_fetch.py ids.txt [--feed episodes/feed]
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "papercast/1.0 (agent-sora podcast)"


def hf_meta(aid: str) -> dict | None:
    url = f"https://huggingface.co/api/papers/{aid}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except Exception as e:  # noqa: BLE001
        print(f"  hf meta FAIL {aid}: {e}", file=sys.stderr)
        return None


def extract_pdf_text(aid: str, text_path: str) -> None:
    import pymupdf
    pdf = text_path.replace(".txt", ".pdf")
    if not os.path.exists(pdf):
        for ver in (f"{aid}v1", f"{aid}v2"):
            u = f"https://arxiv.org/pdf/{ver}"
            try:
                req = urllib.request.Request(u, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=60) as r, open(pdf, "wb") as f:
                    f.write(r.read())
                break
            except Exception:
                continue
    doc = pymupdf.open(pdf)
    parts = []
    for pg in doc:
        parts.append(pg.get_text())
    text = "\n".join(parts)
    with open(text_path, "w") as f:
        f.write(text)
    print(f"  text {aid}: {len(doc)} pages, {len(text)} chars", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids_file")
    ap.add_argument("--feed", default=os.path.join(ROOT, "episodes", "feed"))
    args = ap.parse_args()

    meta_dir = os.path.join(args.feed, "meta")
    text_dir = os.path.join(args.feed, "text")
    os.makedirs(meta_dir, exist_ok=True)
    os.makedirs(text_dir, exist_ok=True)

    ids = [l.strip() for l in open(args.ids_file) if l.strip()]
    print(f"# batch-fetch {len(ids)} ids", file=sys.stderr)
    for i, aid in enumerate(ids, 1):
        print(f"[{i}/{len(ids)}] {aid}", file=sys.stderr)
        mp = os.path.join(meta_dir, f"{aid}.json")
        if os.path.exists(mp) and os.path.getsize(mp) > 50:
            print("  meta cached", file=sys.stderr)
        else:
            d = hf_meta(aid)
            if d:
                rec = {
                    "arxiv_id": aid,
                    "title": d.get("title"),
                    "authors": [a.get("name") for a in d.get("authors", [])],
                    "upvotes": d.get("upvotes"),
                    "publishedAt": d.get("publishedAt", "")[:10],
                    "summary": d.get("summary"),
                }
                json.dump(rec, open(mp, "w"), indent=2, ensure_ascii=False)
                print(f"  meta OK up={rec['upvotes']}", file=sys.stderr)
            time.sleep(1.0)
        tp = os.path.join(text_dir, f"{aid}.txt")
        if os.path.exists(tp) and os.path.getsize(tp) > 500:
            print("  text cached", file=sys.stderr)
        else:
            try:
                extract_pdf_text(aid, tp)
            except Exception as e:  # noqa: BLE001
                print(f"  text FAIL {aid}: {e}", file=sys.stderr)
            time.sleep(1.5)
    print("BATCH_FETCH_DONE", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
