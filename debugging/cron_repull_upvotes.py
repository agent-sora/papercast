"""Cron helper: re-pull true HF upvotes for a shortlist and write the picks file.

Reads episodes/feed/selected-<DATE>.json (list of candidates with arxiv_id),
re-queries https://huggingface.co/api/papers/<id> for each, sorts by true
upvotes, and writes the top N ids to episodes/feed/picks/ids-<DATE>.txt
(one id per line, bare arXiv id). Prints a ranked table so the agent can
verify the #1 true-upvote paper made the picks before drafting.
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

PC = Path("/home/patrick/papercast")
UA = {"User-Agent": "papercast-agent/1.0 (cron nightly; contact: patrick)"}


def fetch_upvotes(arxiv_id: str, retries: int = 3) -> int:
    url = f"https://huggingface.co/api/papers/{arxiv_id}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode())
            up = data.get("upvotes")
            if isinstance(up, (int, float)):
                return int(up)
            # some responses nest under "paper"
            p = data.get("paper") or {}
            return int(p.get("upvotes") or 0)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
            else:
                print(f"WARN {arxiv_id}: {e}", file=sys.stderr)
                return 0
    return 0


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: cron_repull_upvotes.py <date> <top_n>")
        sys.exit(1)
    date, top_n = sys.argv[1], int(sys.argv[2])
    sel_path = PC / f"episodes/feed/papers-{date}.json"
    full = json.loads(sel_path.read_text())
    sel = full["papers"] if isinstance(full, dict) else full
    # also include any candidates present in the full feed but not selected?
    # The prompt says re-pull for "all candidates" = selected shortlist.
    cands = []
    seen = set()
    for p in sel:
        aid = p.get("arxiv_id") or p.get("id")
        if aid and aid not in seen:
            seen.add(aid)
            cands.append((aid, p.get("title", "")))

    rows = []
    for aid, title in cands:
        up = fetch_upvotes(aid)
        rows.append((aid, up, title))
        time.sleep(1.0)

    rows.sort(key=lambda r: r[1], reverse=True)
    for i, (aid, up, title) in enumerate(rows, 1):
        print(f"{i:2d}. {aid}  up={up:<5d} {title[:80]}")

    picks = PC / "episodes/feed/picks"
    picks.mkdir(parents=True, exist_ok=True)
    top = [r[0] for r in rows[:top_n]]
    (picks / f"ids-{date}.txt").write_text("\n".join(top) + "\n")
    print(f"WROTE {picks / f'ids-{date}.txt'}: {top}")


if __name__ == "__main__":
    main()
