"""Re-pull true Hugging Face upvote counts for the day's shortlisted papers.

The upvote counts inside episodes/feed/selected-<date>.json are stale (often
zero) because the selector snapshots them at fetch time, before upvotes have
accumulated. This script re-pulls each candidate's paper endpoint from the HF
API, ranks by true upvotes, writes the top 6 ids to
episodes/feed/picks/ids-<date>.txt (one per line), and prints the full ranked
list plus the day's full feed titles (for the standing-rules topology /
foundation-model re-scan).

Usage: .venv/bin/python debugging/pull_true_upvotes.py 2026-09-04
"""
import json
import sys
import time
import urllib.request

PC = "/home/patrick/papercast"


def fetch_upvotes(pid: str) -> int:
    for _ in range(3):
        try:
            with urllib.request.urlopen(
                f"https://huggingface.co/api/papers/{pid}", timeout=30
            ) as r:
                return int(json.load(r).get("upvotes", 0))
        except Exception:
            time.sleep(2)
    return -1


def main() -> None:
    date = sys.argv[1]
    sel = json.load(open(f"{PC}/episodes/feed/selected-{date}.json"))
    feed = json.load(open(f"{PC}/episodes/feed/papers-{date}.json"))
    ids = [p["arxiv_id"] for p in sel]
    print("candidates:", ids)

    res = {}
    for pid in ids:
        res[pid] = fetch_upvotes(pid)
        print(pid, res[pid])

    ranked = sorted(res.items(), key=lambda kv: -kv[1])
    print("RANKED:", ranked)
    top6 = [pid for pid, _ in ranked[:6]]
    with open(f"{PC}/episodes/feed/picks/ids-{date}.txt", "w") as f:
        f.write("\n".join(top6) + "\n")
    print("TOP6:", top6)
    print("#1 true-upvote in picks:", ranked[0][0] in top6)

    print(f"\nFULL FEED ({len(feed['papers'])}):")
    for p in feed["papers"]:
        print(
            p.get("id") or p.get("arxiv_id"),
            "|",
            (p.get("title") or "")[:120],
        )


if __name__ == "__main__":
    main()
