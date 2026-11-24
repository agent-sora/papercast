"""Re-pull live upvote counts from the HF papers API for one day's fetched feed.

Cron's nightly picks files carry stale/zero upvotes, so this script re-queries
https://huggingface.co/api/papers/<id> for every paper in episodes/feed/papers-<D>.json
and writes the sorted results to episodes/feed/picks/true-upvotes-<D>.json.

Usage:
    .venv/bin/python debugging/fetch_true_upvotes.py 2026-11-02
"""
import json, sys, time, urllib.request, os

PC = os.environ.get("PC", "/home/patrick/papercast")

def main():
    day = sys.argv[1]
    feed = json.load(open(f"{PC}/episodes/feed/papers-{day}.json"))
    papers = feed["papers"]
    results = []
    for p in papers:
        pid = p.get("arxiv_id") or p.get("id") or p.get("paper_id")
        try:
            req = urllib.request.Request(
                f"https://huggingface.co/api/papers/{pid}",
                headers={"User-Agent": "papercast/1.0 (nightly digest)"})
            with urllib.request.urlopen(req, timeout=20) as r:
                j = json.load(r)
            results.append({"id": j.get("id"), "upvotes": j.get("upvotes"),
                            "title": j.get("title", p.get("title"))})
        except Exception as e:  # keep going on single-paper failures
            results.append({"id": pid, "upvotes": None,
                            "title": (p.get("title") or "") + f"  [ERR {e}]"})
        time.sleep(0.5)
    results.sort(key=lambda x: (x["upvotes"] is None, -(x["upvotes"] or 0)))
    out = f"{PC}/episodes/feed/picks/true-upvotes-{day}.json"
    json.dump(results, open(out, "w"), indent=1)
    for r in results:
        print(r["upvotes"], r["id"], (r["title"] or "")[:100])

if __name__ == "__main__":
    main()
