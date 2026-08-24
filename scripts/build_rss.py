#!/usr/bin/env python3
"""Build the static podcast site: index.html + feed.xml at LIVE GitHub Pages URLs.

The user's ONLY listening path is GitHub Pages, so every audio link and the RSS
feed must resolve to public URLs under the Pages base:
    https://agent-sora.github.io/<slug>/         (index.html)
    https://agent-sora.github.io/<slug>/feed.xml  (RSS)
    https://agent-sora.github.io/<slug>/episodes/<date>.mp3  (audio)

Scans the `episodes/` dir for `YYYY-MM-DD.mp3` (+ optional matching `.md` script)
and emits `site/index.html` and `site/feed.xml`. Episode order: newest first.

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
import sys

import yaml


def load_cfg(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def scan_episodes(ep_dir: str) -> list[dict]:
    episodes = []
    for mp3 in sorted(glob.glob(os.path.join(ep_dir, "*.mp3"))):
        base = os.path.basename(mp3)[:-4]
        m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})", base)
        if not m:
            continue
        date = m.group(1)
        md = os.path.join(ep_dir, base + ".md")
        script_text = None
        if os.path.exists(md):
            with open(md) as f:
                script_text = f.read()
        import subprocess
        size = os.path.getsize(mp3)
        duration_s = None
        try:
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                                mp3], capture_output=True, text=True, timeout=30)
            duration_s = float(r.stdout.strip()) if r.stdout.strip() else None
        except Exception:
            pass
        episodes.append({"date": date, "mp3": mp3, "size": size,
                         "duration_s": duration_s, "script": script_text})
    episodes.sort(key=lambda e: e["date"], reverse=True)
    return episodes


def fmt_dur(s):
    if s is None:
        return ""
    m, sec = divmod(int(s), 60)
    return f"{m} min {sec:02d}"


def build_feed(cfg, episodes, base_url):
    items = []
    for e in episodes:
        guid = f"{base_url}episodes/{e['date']}.mp3"
        title = f"Daily ML Papers — {e['date']}"
        desc = ""
        if e["script"]:
            lines = [l.lstrip("# ").strip() for l in e["script"].splitlines()
                     if l.strip() and not l.strip().startswith("---")]
            desc = " · ".join(lines[:12])[:1800]
        items.append(f"""    <item>
      <title>{html.escape(title)}</title>
      <link>{guid}</link>
      <guid isPermaLink="true">{guid}</guid>
      <pubDate>{_rfc822(e['date'])}</pubDate>
      <description>{html.escape(desc)}</description>
      <enclosure url="{guid}" type="audio/mpeg" length="{e['size']}"/>
    </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{html.escape(cfg['RSS_TITLE'])}</title>
    <link>{base_url}</link>
    <description>Daily ~30-minute technical briefing of interesting HuggingFace papers for a senior staff software engineer. Read by Rosie (KittenTTS, RP accent).</description>
    <language>en-gb</language>
    <lastBuildDate>{_rfc822(_today())}</lastBuildDate>
    <itunes:author>agent-sora</itunes:author>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href="{base_url}cover.png"/>
{chr(10).join(items)}
  </channel>
</rss>
"""
    return feed


def build_index(cfg, episodes, base_url):
    rows = []
    for i, e in enumerate(episodes):
        url = f"{base_url}episodes/{e['date']}.mp3"
        rows.append(f"""      <li class="ep">
        <a class="play" href="{url}">▶ Play {e['date']}</a>
        <span class="meta">{fmt_dur(e['duration_s'])} · {e['size']//1024} KB</span>
      </li>""")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(cfg['RSS_TITLE'])}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; background:#0f1115; color:#e6e8ec; }}
  h1 {{ font-size: 1.35rem; }}
  p.sub {{ color:#9aa2b1; }}
  ul {{ list-style:none; padding:0; }}
  .ep {{ display:flex; justify-content:space-between; align-items:center; padding:.6rem 0; border-bottom:1px solid #22262e; }}
  a.play {{ color:#7aa2ff; text-decoration:none; font-weight:600; }}
  a.play:hover {{ text-decoration:underline; }}
  .meta {{ color:#9aa2b1; font-size:.85rem; }}
  .sub a {{ color:#7aa2ff; }}
</style>
</head>
<body>
  <h1>🎙 {html.escape(cfg['RSS_TITLE'])}</h1>
  <p class="sub">Daily ~30-min technical briefing of interesting HuggingFace papers. Subscribe: <a href="{base_url}feed.xml">feed.xml</a></p>
  <ul>
{chr(10).join(rows)}
  </ul>
  <p class="sub">Generated by agent-sora · <a href="{base_url}">home</a></p>
</body>
</html>
"""


def _rfc822(date_str):
    # date_str YYYY-MM-DD -> RFC-822 with naive UTC
    d = datetime.date.fromisoformat(date_str)
    return d.strftime("%a, %d %b %Y 00:00:00 +0000")


def _today():
    return datetime.date.today().isoformat()


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
        print("!! no episodes found", file=sys.stderr)
        return 2
    print(f"# {len(episodes)} episodes -> {args.site_dir}", file=sys.stderr)

    os.makedirs(args.site_dir, exist_ok=True)
    with open(os.path.join(args.site_dir, "feed.xml"), "w") as f:
        f.write(build_feed(cfg, episodes, base_url))
    with open(os.path.join(args.site_dir, "index.html"), "w") as f:
        f.write(build_index(cfg, episodes, base_url))
    # cover.png: prefer the real artwork in assets/, else a simple placeholder
    cover = os.path.join(args.site_dir, "cover.png")
    asset_cover = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "cover.png")
    if os.path.exists(asset_cover):
        import shutil
        shutil.copyfile(asset_cover, cover)
    elif not os.path.exists(cover):
        _make_cover(cover)
    print(f"# wrote feed.xml, index.html, cover.png under {args.site_dir}", file=sys.stderr)
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
        open(path, "wb").write(b"\x89PNG\r\n\x1a\n")  # tiny invalid; replaced on next build
    print(f"  cover -> {path}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())