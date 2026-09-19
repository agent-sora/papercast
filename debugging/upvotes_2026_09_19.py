#!/usr/bin/env python3
"""Re-pull true HuggingFace upvote counts for the 2026-09-18 papers-day feed.

Saturday duplicate-guard run (2026-09-19): no new episodes are produced, but the
true-upvote re-pull is recorded for the work log, following the 2026-09-13
duplicate-guard precedent. Reads episodes/feed/papers-2026-09-18.json and prints
every paper's current upvote count, sorted descending, with the title truncated.

Usage:
    .venv/bin/python debugging/upvotes_2026_09_19.py
"""
import json
import urllib.request

PC = "/home/patrick/papercast"
FEED = f"{PC}/episodes/feed/papers-2026-09-18.json"


def main() -> None:
    with open(FEED) as f:
        feed = json.load(f)
    if isinstance(feed, dict):
        feed = feed.get("papers", feed.get("items", []))
    rows = []
    for p in feed:
        pid = p.get("id") or p.get("arxiv_id") or ""
        if pid and pid.startswith("https"):
            pid = pid.rsplit("/", 1)[-1]
        title = (p.get("title") or "")[:70]
        try:
            with urllib.request.urlopen(
                f"https://huggingface.co/api/papers/{pid}", timeout=30
            ) as r:
                data = json.loads(r.read().decode())
            up = int(data.get("upvotes", 0) or 0)
        except Exception as e:  # noqa: BLE001
            up = -1
            title = f"{title}  [ERR {e}]"
        rows.append((up, pid, title))
    rows.sort(reverse=True)
    for up, pid, title in rows:
        print(f"{up:>4}  {pid}  {title}")
    # save for the work log
    out = f"{PC}/episodes/feed/true_upvotes-2026-09-18.json"
    with open(out, "w") as f:
        json.dump(
            [{"id": pid, "upvotes": up, "title": title} for up, pid, title in rows],
            f, indent=2,
        )
    print(f"\n(saved -> {out})")


if __name__ == "__main__":
    main()
