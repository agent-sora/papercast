#!/usr/bin/env python3
"""Fetch per-paper metadata (authors, affiliations) for Agent-Sora episodes.

For each selected arxiv paper: scrape the arXiv abs page for the author list,
download the PDF and pull affiliation-looking lines from page 1 (departments,
universities, labs, companies). Results cached as JSON per paper.

Usage: paper_meta.py --ids-file ids.txt --cache-dir episodes/feed/meta
"""
import argparse, json, os, re, subprocess, sys, time

UA = {"User-Agent": "agent-sora/0.2 (contact: agent-sora@local)"}

def http_get(url, out_path=None):
    cmd = ["curl", "-sL", "--max-time", "90", "-H", f"User-Agent: {UA['User-Agent']}"]
    if out_path:
        cmd += ["-o", out_path]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True)
    if out_path:
        return os.path.exists(out_path) and os.path.getsize(out_path) > 500
    return r.stdout.decode("utf-8", "replace")

def authors_from_abs(arxiv_id):
    html = http_get(f"https://arxiv.org/abs/{arxiv_id}")
    if not html:
        return []
    m = re.search(r'<div class="authors">(.*?)</div>', html, re.S)
    block = m.group(1) if m else ""
    names = re.findall(r'>([^<>]+)</a>', block)
    return [n.strip() for n in names if n.strip()]

AFFIL_RE = re.compile(
    r"([A-Z]?[^\n]{0,120}?\b(?:University|Universit|Institute|Laborator|Lab\b|College|"
    r"School of|Academy|EPFL|ETH|MIT|CMU|Caltech|UCL|MPI|CNRS|INRIA|KAIST|"
    r"DeepMind|Google|Meta AI|Microsoft Research|Anthropic|OpenAI|Amazon|NVIDIA|"
    r"Apple|ByteDance|Tencent|Alibaba|Huawei|Zhipu|Tsinghua|Peking|Fudan|"
    r"SJTU|CAS|Harvard|Stanford|Berkeley|Oxford|Cambridge|Yale)[^\n]{0,80})", re.I)

def affiliations_from_pdf(pdf_path):
    try:
        import pymupdf
        doc = pymupdf.open(pdf_path)
        text = doc[0].get_text()
        doc.close()
    except Exception as e:
        return [f"<pdf error: {e}>"]
    hits, seen = [], set()
    # affiliations may sit in a numbered legend anywhere on page 1 (often in
    # the footnotes under a long abstract), so scan the full page
    for line in text.split("\n"):
        line = line.strip()
        if len(line) < 6 or len(line) > 120:
            continue
        low = line.lower()
        if any(s in low for s in ("@", "http", "arxiv", "abstract", "figure",
                                  "table", "doi", "github", "citation",
                                  "proceedings", "conference", "journal",
                                  "(openai", "(2025", "(2024")):
            continue
        line = re.sub(r"^[\d\s*†‡§]+", "", line).strip()  # legend indices
        if len(line) < 6:
            continue
        if AFFIL_RE.search(line):
            key = line.lower()
            if key not in seen:
                seen.add(key)
                hits.append(line)
    return hits[:12]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids-file", required=True)
    ap.add_argument("--cache-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.cache_dir, exist_ok=True)
    import pymupdf  # fail fast if missing

    ids = [l.strip() for l in open(args.ids_file) if l.strip()]
    tmp_pdf = os.path.join(args.cache_dir, "_tmp.pdf")
    for i, aid in enumerate(ids, 1):
        out = os.path.join(args.cache_dir, f"{aid}.json")
        if os.path.exists(out):
            print(f"[{i}/{len(ids)}] {aid} cached", flush=True)
            continue
        authors = authors_from_abs(aid)
        pdf_path = os.path.join(args.cache_dir, f"{aid}.pdf")
        ok = os.path.exists(pdf_path) or http_get(
            f"https://arxiv.org/pdf/{aid}", out_path=pdf_path)
        affils = affiliations_from_pdf(pdf_path) if ok else ["<pdf dl failed>"]
        rec = {"arxiv_id": aid, "authors": authors, "affiliations": affils}
        json.dump(rec, open(out, "w"), indent=1)
        print(f"[{i}/{len(ids)}] {aid}: {len(authors)} authors, "
              f"{len(affils)} affil lines", flush=True)
        time.sleep(1.2)          # be polite to arxiv
    print("META_DONE", flush=True)

if __name__ == "__main__":
    main()
