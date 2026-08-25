#!/usr/bin/env python3
"""Keep the live RSS feed + website in sync with finished episode audio.

Watches episodes/ for new or changed *.mp3 files (atomic rename = publish
event). On change: waits for the burst to settle (no new file for N seconds),
rebuilds feed.xml/index.html via build_rss.py, and pushes to gh-pages via
publish.sh. Also publishes once at startup if the live feed is behind.

Usage (background):
    python scripts/publish_watch.py [--episodes-dir episodes] \
        [--settle 180] [--once]
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def snapshot(ep_dir):
    out = {}
    if os.path.isdir(ep_dir):
        for f in sorted(os.listdir(ep_dir)):
            if f.endswith(".mp3"):
                p = os.path.join(ep_dir, f)
                out[f] = (os.path.getmtime(p), os.path.getsize(p))
    return out


def build_and_publish():
    site = "/tmp/site_live"
    r = subprocess.run([sys.executable, os.path.join(HERE, "build_rss.py"),
                        "--episodes-dir", "episodes", "--site-dir", site],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print("BUILD FAILED:", r.stderr[-500:], flush=True)
        return False
    n = [l for l in r.stdout.splitlines() if l.startswith("#")]
    print(n[0] if n else "built", flush=True)
    r = subprocess.run(["bash", os.path.join(HERE, "publish.sh"), site],
                       cwd=ROOT, capture_output=True, text=True)
    ok = r.returncode == 0 and "OK" in (r.stdout + r.stderr)
    print(("PUBLISHED" if ok else "PUBLISH FAILED:")
          + (" " + (r.stderr or r.stdout).strip().splitlines()[-1]
             if ok else " " + (r.stderr or "")[-400:]), flush=True)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes-dir", default="episodes")
    ap.add_argument("--settle", type=int, default=180,
                    help="seconds of quiet before publishing a burst")
    ap.add_argument("--once", action="store_true",
                    help="single check-then-publish pass, then exit")
    args = ap.parse_args()

    ep_dir = os.path.join(ROOT, args.episodes_dir)
    known = snapshot(ep_dir)
    prev = dict(known)
    last_change = None
    print(f"[watch] start: {len(known)} mp3 present", flush=True)

    while True:
        time.sleep(10)
        cur = snapshot(ep_dir)
        if cur != prev:
            prev = cur
            last_change = time.time()
            if args.once:
                break
            continue
        # state stable since last poll: publish if there is anything new and
        # it has stayed quiet for --settle seconds
        if last_change and time.time() - last_change >= args.settle:
            changed = {f for f in cur
                       if f not in known or cur[f][1] != known[f][1]}
            print(f"[watch] publishing after {len(changed)} new mp3(s)", flush=True)
            if build_and_publish():
                known = dict(cur)
            else:
                known = dict(cur)  # next event retries; don't hot-loop here
            last_change = None
        if args.once:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
