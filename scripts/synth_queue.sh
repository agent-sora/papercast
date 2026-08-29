#!/usr/bin/env bash
# Serial synthesis queue: one TTS job at a time (box OOMs with 2 concurrent),
# publishing the site after each episode so the live feed grows incrementally.
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

for d in 2026-08-14 2026-08-13 2026-08-19 2026-08-18 2026-08-17 2026-08-20; do
  md="episodes/$d.md"
  mp3="episodes/$d.mp3"
  if [ -s "$mp3" ]; then
    echo "[queue] skip $d (mp3 already exists)"
  else
    echo "[queue] === synthesizing $d ==="
    TMPDIR="${TMPDIR:-/tmp}" .venv/bin/python scripts/synthesize.py \
      --transcript "$md" --out "$mp3" || { echo "[queue] SYNTH_FAIL $d"; exit 1; }
  fi
  echo "[queue] --- rebuilding site + publishing $d ---"
  TMPDIR="${TMPDIR:-/tmp}" .venv/bin/python scripts/build_rss.py \
    --episodes-dir episodes --site-dir site || { echo "[queue] BUILD_FAIL $d"; exit 1; }
  bash scripts/publish.sh site || { echo "[queue] PUBLISH_FAIL $d"; exit 1; }
done
echo "[queue] QUEUE_DONE"
