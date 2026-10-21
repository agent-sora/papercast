"""Re-pull true HF upvotes for a day's full feed and rank.

Writes .tmp/true_upvotes-<D>.json (list of {id,title,upvotes,authors,summary,url,publishedAt}).
Used by the Papercast night-shift: selected-*.json upvotes are stale/zero, so the
true-upvote ranking must be re-pulled live from https://huggingface.co/api/papers/<id>.
"""
import json, subprocess, time, os, sys

PC = "/home/patrick/papercast"
D = sys.argv[1] if len(sys.argv) > 1 else "2026-10-21"

feed = json.load(open(f"{PC}/episodes/feed/papers-{D}.json"))
papers = feed["papers"]
print(f"TOTAL FEED PAPERS: {len(papers)}")
print("=" * 80)
for i, p in enumerate(papers):
    print(f"[{i}] up={p.get('upvotes', 0):>3} id={p.get('arxiv_id')} :: {p.get('title','')[:95]}")
print("=" * 80)

results = []
for i, p in enumerate(papers):
    aid = p.get("arxiv_id")
    if not aid:
        continue
    uv = 0
    for attempt in range(3):
        try:
            out = subprocess.run(
                ["curl", "-sS", "--max-time", "20", "-A", "papercast/1.0",
                 "https://huggingface.co/api/papers/" + aid],
                capture_output=True, text=True, timeout=25)
            d = json.loads(out.stdout)
            uv = d.get("upvotes", 0)
            break
        except Exception as e:
            if attempt == 2:
                print(f"  ERR {aid}: {e}")
            time.sleep(2)
    results.append({"id": aid, "title": p.get("title", ""), "upvotes": uv,
                    "authors": p.get("authors", []), "summary": p.get("summary", ""),
                    "url": p.get("url", ""), "publishedAt": p.get("publishedAt", "")})
    time.sleep(0.5)

results.sort(key=lambda r: r.get("upvotes", 0), reverse=True)
print("\n=== TRUE UPVOTE RANKING (all %d) ===" % len(results))
for i, r in enumerate(results):
    print(f"[{i}] up={r['upvotes']:>3} id={r['id']} :: {r['title'][:90]}")

json.dump(results, open(f"{PC}/.tmp/true_upvotes-{D}.json", "w"), indent=1)
print("\nSaved .tmp/true_upvotes-%s.json" % D)
print("\nTOP 6:")
for r in results[:6]:
    print(f"  up={r['upvotes']} id={r['id']} :: {r['title'][:90]}")
