"""Fetch true upvotes from HF API for 2026-09-18 candidates, rank, scan full feed.

Re-pulls https://huggingface.co/api/papers/<id> for each candidate in
episodes/feed/selected-2026-09-18.json (stale/zero in the shortlist), prints the
true-upvote ranking, then re-scans the day's full feed (papers-2026-09-18.json)
for standing-rule patterns (foundation-model tech reports, reasoning-model
topology) that the selector's lexicon may have missed.
"""
import json
import urllib.request

PC = "/home/patrick/papercast"
D = "2026-09-18"

sel = json.load(open(f"{PC}/episodes/feed/selected-{D}.json"))
ids = [p["arxiv_id"] for p in sel]
res = {}
for i in ids:
    try:
        req = urllib.request.Request(
            f"https://huggingface.co/api/papers/{i}", headers={"User-Agent": "Mozilla/5.0"}
        )
        d = json.load(urllib.request.urlopen(req, timeout=30))
        res[i] = (d.get("upvotes", 0), d.get("title", "")[:90])
    except Exception as e:  # noqa: BLE001
        res[i] = (None, str(e)[:80])

ranked = sorted(((v[0], i) for i, v in res.items() if v[0] is not None), reverse=True)
print("RANKED (true upvotes):")
for u, i in ranked:
    print(f"  {i}  {u}")
for i, (u, t) in res.items():
    if u is None:
        print("FAIL", i, t)

feed = json.load(open(f"{PC}/episodes/feed/papers-{D}.json"))
papers = feed if isinstance(feed, list) else feed.get("papers", feed.get("items", []))
print("\nFULL FEED count:", len(papers))

topo_kw = [
    "weight-tied", "weight tied", "adaptive computation", "linear attention",
    "fast-weight", "fast weight", "state space", "ssm", "latent chain",
    "continuous chain-of-thought", "chain of thought", "chain-of-thought",
    "recurrent", "looping", "loop", "depth",
]
print("\nTOPOLOGY/LANE title hits in full feed:")
for p in papers:
    t = (p.get("title") or "").lower()
    hit = [k for k in topo_kw if k in t]
    if hit:
        print("  ", p.get("id") or p.get("arxiv_id"), "|", (p.get("title") or "")[:110], "|", hit)

print("\nTECH-REPORT title hits:")
for p in papers:
    t = p.get("title") or ""
    if "technical report" in t.lower():
        print("  ", p.get("id") or p.get("arxiv_id"), "|", t[:110])
