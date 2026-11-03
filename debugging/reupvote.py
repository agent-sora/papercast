#!/usr/bin/env python3
"""Re-pull TRUE HuggingFace upvotes for a day's paper ids and rank them.

Usage: reupvote.py <papers-YYYY-MM-DD.json> <out-json>
  For each paper's arxiv_id, GET https://huggingface.co/api/papers/<id> and
  record upvotes/comments. Writes {id: {upvotes, comments, title}} to out-json.
  Prints a ranking table sorted by true upvotes desc.

HF ids here ARE the arXiv ids (the HF daily feed keys papers by arXiv id),
so /api/papers/<arxiv_id> resolves. 3s pacing, honest UA; tolerates 404/429.
"""
import json
import sys
import time
import urllib.request
import urllib.error

UA = "papercast-nightly/1.0 (+https://agent-sora.github.io/papercast)"


def fetch(pid):
    url = f"https://huggingface.co/api/papers/{pid}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_err": f"HTTP {e.code}"}
    except Exception as e:  # noqa: BLE001
        return {"_err": str(e)}


def main(day_path, out_path):
    d = json.load(open(day_path))
    papers = d.get("papers", [])
    res = {}
    for p in papers:
        pid = str(p.get("arxiv_id") or p.get("id"))
        title = (p.get("title") or "").strip()
        data = fetch(pid)
        if "_err" in data:
            res[pid] = {"upvotes": None, "comments": None, "title": title, "err": data["_err"]}
        else:
            res[pid] = {
                "upvotes": int(data.get("upvotes", 0) or 0),
                "comments": data.get("numComments", data.get("comments", 0)),
                "title": title,
                "err": None,
            }
        time.sleep(3.0)
    json.dump(res, open(out_path, "w"), indent=2)
    rows = [(v["upvotes"] if v["upvotes"] is not None else -1, k, v["title"], v["err"])
            for k, v in res.items()]
    rows.sort(key=lambda r: (-r[0], r[1]))
    print(f"date={d.get('papers_date')} n={len(rows)}")
    for i, (up, pid, title, err) in enumerate(rows, 1):
        flag = f"  ERR={err}" if err else ""
        print(f"{i:2d}. up={up:<4d} {pid}  {title[:95]}{flag}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
