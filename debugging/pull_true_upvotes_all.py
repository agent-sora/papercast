"""Re-pull true HF upvotes for ALL candidates (full feed, not just shortlist).

Variant of debugging/pull_true_upvotes.py used when the shortlist is smaller
than the feed and standing rules need the full-day re-scan. Ranks the full
feed's ids by true upvotes, writes the top 6 to picks/ids-<date>.txt, and
prints ranked list + full feed titles.

Usage: .venv/bin/python debugging/pull_true_upvotes_all.py 2026-09-14
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
    feed = json.load(open(f"{PC}/episodes/feed/papers-{date}.json"))
    sel = json.load(open(f"{PC}/episodes/feed/selected-{date}.json"))
    sel_ids = {p["arxiv_id"] for p in sel}
    ids = [p.get("id") or p.get("arxiv_id") for p in feed["papers"]]
    print("feed candidates:", ids)

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
    print("shortlisted:", sorted(sel_ids))

    print(f"\nFULL FEED ({len(feed['papers'])}):")
    for p in feed["papers"]:
        print(
            p.get("id") or p.get("arxiv_id"),
            "|",
            (p.get("title") or "")[:130],
        )


if __name__ == "__main__":
    main()
