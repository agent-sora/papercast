#!/usr/bin/env python3
"""Build the static podcast site: index.html + feed.xml at LIVE GitHub Pages URLs.

The user's ONLY listening path is GitHub Pages, so every audio link and the RSS
feed must resolve to public URLs under the Pages base:
    https://agent-sora.github.io/<slug>/         (index.html)
    https://agent-sora.github.io/<slug>/feed.xml  (RSS)
    https://agent-sora.github.io/<slug>/episodes/<file>.mp3   (audio)

Per-paper episode layout (2026-08-24 pivot): one ~10-min episode PER PAPER.
Files in the episodes dir follow  YYYY-MM-DD-<arxiv_id>.mp3  (arxiv_id like
2608.12036, version suffix stripped). Each mp3 has a sibling .md transcript
whose YAML-ish front matter carries Title / Authors / Labs / Arxiv / Day /
Upvotes / Link. Episode order: newest day first, then by upvotes desc.

Usage:
    python scripts/build_rss.py --episodes-dir episodes --site-dir site
Reads GH_REPO + RSS_* from config.yaml.
"""
import argparse
import datetime
import glob
import html
import os
import re
import subprocess
import sys

import yaml


def load_cfg(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


FNAME_RE = re.compile(r"(\d{4}-\d{2}-\d{2})-(\d{4}\.\d{4,5})\.mp3$")


def parse_front_matter(md_path: str) -> dict:
    meta = {}
    try:
        with open(md_path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return meta
    if not lines or lines[0].strip() != "---":
        return meta
    for line in lines[1:]:
        s = line.strip()
        if s == "---":
            break
        m = re.match(r"([A-Za-z]+)\s*:\s*(.*)", s)
        if m:
            meta[m.group(1)] = m.group(2).strip().strip('"')
    return meta


def probe_duration(mp3: str):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", mp3],
            capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip()) if r.stdout.strip() else None
    except Exception:
        return None


def scan_episodes(ep_dir: str) -> list[dict]:
    episodes = []
    for mp3 in sorted(glob.glob(os.path.join(ep_dir, "*.mp3"))):
        base = os.path.basename(mp3)
        m = FNAME_RE.search(base)
        if not m:
            print(f"  [skip] {base}: not YYYY-MM-DD-<arxiv_id>.mp3",
                  file=sys.stderr)
            continue
        day, arxiv_id = m.group(1), m.group(2)
        md = mp3[:-4] + ".md"
        meta = parse_front_matter(md)
        upvotes = 0
        try:
            upvotes = int(meta.get("Upvotes", "0"))
        except ValueError:
            pass
        episodes.append({
            "day": day,
            "arxiv_id": arxiv_id,
            "title": meta.get("Title") or f"Paper {arxiv_id}",
            "authors": meta.get("Authors", ""),
            "labs": meta.get("Labs", ""),
            "upvotes": upvotes,
            "link": meta.get("Link") or f"https://arxiv.org/abs/{arxiv_id}",
            "script_path": md if os.path.exists(md) else None,
            "mp3": mp3,
            "size": os.path.getsize(mp3),
            "duration_s": probe_duration(mp3),
        })
    # newest day first; within a day, most-upvoted first
    episodes.sort(key=lambda e: (e["day"], -e["upvotes"]), reverse=False)
    episodes.sort(key=lambda e: e["day"], reverse=True)
    return episodes


def fmt_dur(s):
    if s is None:
        return ""
    m, sec = divmod(int(s), 60)
    return f"{m} min {sec:02d}"


def ep_desc(e) -> str:
    parts = []
    if e["authors"]:
        parts.append(f"By {e['authors']}" +
                     (f" ({e['labs']})" if e["labs"] else ""))
    if e["script_path"]:
        with open(e["script_path"], encoding="utf-8") as f:
            body = f.read()
        # skip front matter, take first prose paragraphs
        body = re.sub(r"^---\n.*?\n---\n", "", body, flags=re.S)
        paras = [p.strip().replace("\n", " ")
                 for p in body.split("\n\n") if p.strip()]
        for p in paras:
            if p.startswith("#"):
                continue
            parts.append(p)
            if sum(len(x) for x in parts) > 1400:
                break
    return " ".join(parts)[:1900]


def _rfc822(date_str):
    d = datetime.date.fromisoformat(date_str)
    return d.strftime("%a, %d %b %Y 06:00:00 +0000")


def _today():
    return datetime.date.today().isoformat()


def build_feed(cfg, episodes, base_url):
    items = []
    for e in episodes:
        url = f"{base_url}episodes/{os.path.basename(e['mp3'])}"
        title = e["title"]
        desc = ep_desc(e)
        items.append(f"""    <item>
      <title>{html.escape(title)}</title>
      <link>{html.escape(e['link'])}</link>
      <guid isPermaLink="true">{url}</guid>
      <pubDate>{_rfc822(e['day'])}</pubDate>
      <description>{html.escape(desc)}</description>
      {f"<itunes:duration>{int(e['duration_s'])}</itunes:duration>" if e['duration_s'] else ""}
      <enclosure url="{url}" type="audio/mpeg" length="{e['size']}"/>
    </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{html.escape(cfg['RSS_TITLE'])}</title>
    <link>{base_url}</link>
    <description>{html.escape(cfg.get('RSS_DESCRIPTION', 'One technical deep-dive per paper.'))}</description>
    <language>{cfg.get('RSS_LANGUAGE', 'en-gb')}</language>
    <lastBuildDate>{_rfc822(_today())}</lastBuildDate>
    <itunes:author>agent-sora</itunes:author>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href="{base_url}cover.png"/>
{chr(10).join(items)}
  </channel>
</rss>
"""


def build_index(cfg, episodes, base_url):
    rows = []
    cur_day = None
    for e in episodes:
        url = f"{base_url}episodes/{os.path.basename(e['mp3'])}"
        if e["day"] != cur_day:
            cur_day = e["day"]
            rows.append(f'      <li class="day">{cur_day}</li>')
        lab = f' · {html.escape(e["labs"])}' if e["labs"] else ""
        rows.append(f"""      <li class="ep">
        <a class="play" href="{url}">▶ {html.escape(e['title'])}</a>
        <span class="meta">{fmt_dur(e['duration_s'])} · {e['size']//1024} KB{lab}
          · <a class="paper" href="{html.escape(e['link'])}">arXiv {e['arxiv_id']}</a></span>
      </li>""")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(cfg['RSS_TITLE'])}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; background:#0f1115; color:#e6e8ec; }}
  h1 {{ font-size: 1.35rem; }}
  p.sub {{ color:#9aa2b1; }}
  ul {{ list-style:none; padding:0; }}
  li.day {{ font-weight:700; margin-top:1.4rem; color:#7aa2ff; letter-spacing:.03em; }}
  .ep {{ display:flex; flex-direction:column; padding:.55rem 0; border-bottom:1px solid #22262e; gap:.15rem; }}
  a.play {{ color:#e6e8ec; text-decoration:none; font-weight:600; font-size:.98rem; }}
  a.play:hover {{ color:#7aa2ff; }}
  .meta {{ color:#9aa2b1; font-size:.82rem; }}
  .meta a, .sub a {{ color:#7aa2ff; text-decoration:none; }}
</style>
</head>
<body>
  <h1>🎙 {html.escape(cfg['RSS_TITLE'])}</h1>
  <p class="sub">{html.escape(cfg.get('RSS_DESCRIPTION', ''))}<br/>
     Subscribe: <a href="{base_url}feed.xml">feed.xml</a></p>
  <ul>
{chr(10).join(rows)}
  </ul>
  <p class="sub">Generated by agent-sora · <a href="{base_url}">home</a></p>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes-dir", required=True)
    ap.add_argument("--site-dir", required=True)
    ap.add_argument("--config", default=None)
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = load_cfg(args.config or os.path.join(root, "config.yaml"))

    owner, slug = cfg["GH_REPO"].split("/")
    base_url = f"https://{owner}.github.io/{slug}/"

    episodes = scan_episodes(args.episodes_dir)
    if not episodes:
        print("!! no per-paper episodes found (YYYY-MM-DD-<arxiv_id>.mp3)",
              file=sys.stderr)
        return 2
    print(f"# {len(episodes)} episodes -> {args.site_dir}", file=sys.stderr)

    os.makedirs(args.site_dir, exist_ok=True)
    with open(os.path.join(args.site_dir, "feed.xml"), "w") as f:
        f.write(build_feed(cfg, episodes, base_url))
    with open(os.path.join(args.site_dir, "index.html"), "w") as f:
        f.write(build_index(cfg, episodes, base_url))
    # cover.png: prefer the real artwork in assets/, else a simple placeholder
    cover = os.path.join(args.site_dir, "cover.png")
    asset_cover = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "cover.png")
    if os.path.exists(asset_cover):
        import shutil
        shutil.copyfile(asset_cover, cover)
    elif not os.path.exists(cover):
        _make_cover(cover)
    print(f"# wrote feed.xml, index.html, cover.png under {args.site_dir}",
          file=sys.stderr)
    print(f"# base_url = {base_url}", file=sys.stderr)
    return 0


def _make_cover(path: str):
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (1400, 1400), (15, 17, 21))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 1399, 1399], outline=(122, 162, 255), width=24)
        d.text((700, 700), "Agent-Sora", fill=(230, 232, 236), anchor="mm")
        img.save(path, "PNG")
    except Exception:
        open(path, "wb").write(b"\x89PNG\r\n\x1a\n")  # tiny invalid; replaced next build
    print(f"  cover -> {path}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
