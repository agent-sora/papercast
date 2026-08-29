#!/usr/bin/env bash
# Unattended pre-step for the nightly cycle: fetch the HF daily-papers feed for
# "today" (snaps backward to the real papers-day on weekends) and run the
# selector. Writes the shortlist JSON so the morning agent can start at pick
# review instead of fetching. Does NOT choose picks, draft, or synthesize.
#
# Usage: bash scripts/nightly_prep.sh [YYYY-MM-DD]
#        (no argument = today in America/New_York)
# Safe to re-run (fetch is cache-first; select is idempotent).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PC="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PC"
TODAY="${1:-$(TZ=America/New_York date +%F)}"

mkdir -p "$PC/.tmp" episodes/feed
export TMPDIR="${TMPDIR:-$PC/.tmp}"

echo "[prep] fetching feed for $TODAY"
"$PC/.venv/bin/python" scripts/fetch_papers.py --date "$TODAY" \
  --cache episodes/feed/ --no-print \
  > "$PC/.tmp/prep_fetch.log" 2>&1

# fetch_papers prints "# <papers_date>: N papers" to stderr
PAPERS_DATE="$(sed -n 's/^# \([0-9-]*\):.*/\1/p' "$PC/.tmp/prep_fetch.log" | head -1)"
[ -n "${PAPERS_DATE:-}" ] || { echo "[prep] could not resolve papers_date; see .tmp/prep_fetch.log"; exit 1; }

echo "[prep] papers-day = $PAPERS_DATE; selecting"
"$PC/.venv/bin/python" scripts/select_papers.py --date "$PAPERS_DATE" \
  --cache episodes/feed/ --config config.yaml \
  --json-out "episodes/feed/selected-$PAPERS_DATE.json" \
  > "$PC/.tmp/prep_select.log" 2>&1

echo "[prep] shortlist: episodes/feed/selected-$PAPERS_DATE.json"
echo "[prep] PREP_DONE"
