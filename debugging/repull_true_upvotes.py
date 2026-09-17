"""Re-pull true upvote counts from the HuggingFace papers API.

The upvote field in episodes/feed/selected-*.json is stale (snapshot time,
often zero). This script re-queries https://huggingface.co/api/papers/<id>
for every candidate in the shortlist, prints a ranked table, and caches the
results to episodes/feed/true_upvotes-<date>.json.

Usage: python debugging/repull_true_upvotes.py <date> [extra_ids...]
"""
import json
import sys
import urllib.request

PC = "/home/patrick/papercast"


def main() -> None:
    date = sys.argv[1]
    sel = json.load(open(f"{PC}/episodes/feed/selected-{date}.json"))
    ids = [p["arxiv_id"] for p in sel]
    # Optional extra ids passed on the command line (e.g. standing-rule add-ons
    # found by re-scanning the full feed).
    ids += [a for a in sys.argv[2:]]

    results = {}
    for pid in ids:
        url = f"https://huggingface.co/api/papers/{pid}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "papercast-bot/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.loads(r.read())
            results[pid] = {
                "upvotes": d.get("upvotes"),
                "title": d.get("title"),
                "publishedAt": d.get("publishedAt"),
            }
        except Exception as e:  # noqa: BLE001
            results[pid] = {"upvotes": None, "error": str(e)}

    ranked = sorted(
        results.items(), key=lambda kv: (kv[1].get("upvotes") is None, -(kv[1].get("upvotes") or 0))
    )
    print(f"ranked upvotes for {date}:")
    for i, (pid, r) in enumerate(ranked, 1):
        print(f"{i:>2}. {pid}  up={r.get('upvotes'):<6} {str(r.get('title'))[:90]}")
    json.dump(results, open(f"{PC}/episodes/feed/true_upvotes-{date}.json", "w"), indent=1)
    print("wrote episodes/feed/true_upvotes-%s.json" % date)


if __name__ == "__main__":
    main()
