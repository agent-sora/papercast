"""Re-pull true HuggingFace upvotes for all candidate papers of the day.

Reads episodes/feed/papers-<D>.json, fetches https://huggingface.co/api/papers/<id>
for each arxiv id, prints a sorted table with titles, and writes the top-6 ids
(one per line) to episodes/feed/picks/ids-<D>.txt. Usage:
  .venv/bin/python debugging/repull_upvotes.py 2026-09-16
"""
import json, sys, urllib.request, time

D = sys.argv[1] if len(sys.argv) > 1 else None
assert D, "need papers date"
feed = json.load(open(f"episodes/feed/papers-{D}.json"))
papers = feed["papers"]
out = []
for p in papers:
    pid = p["arxiv_id"]
    try:
        req = urllib.request.Request(
            f"https://huggingface.co/api/papers/{pid}",
            headers={"User-Agent": "papercast-nightly/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        up = int(data.get("upvotes", 0))
    except Exception as e:
        up = -1
        print(f"  ! {pid} fetch failed: {e}", file=sys.stderr)
    out.append((up, pid, p["title"]))
    time.sleep(0.5)
out.sort(key=lambda t: -t[0])
print(f"{'UP':>5}  {'id':<12} title")
for up, pid, title in out:
    print(f"{up:>5}  {pid:<12} {title[:80]}")
import os
os.makedirs("episodes/feed/picks", exist_ok=True)
top6 = [pid for up, pid, title in out[:6] if up >= 0]
with open(f"episodes/feed/picks/ids-{D}.txt", "w") as f:
    f.write("\n".join(top6) + "\n")
print("WROTE ids:", top6)
