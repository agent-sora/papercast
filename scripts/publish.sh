#!/usr/bin/env bash
# Publish the generated static site (index.html, feed.xml, episodes/*.mp3,
# cover.png) to the `gh-pages` branch, which GitHub Pages serves at
# https://agent-sora.github.io/papercast/
#
# Stateless: clones gh-pages into a temp dir, replaces site files, commits,
# pushes. Keeps the token out of URLs/.git/config via the askpass helper.
#
# Usage:
#   publish.sh <site-dir>
set -euo pipefail

SITE_DIR="${1:?usage: publish.sh <site-dir>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOKEN_FILE="$ROOT/.gh_token"
ASKPASS="${GIT_ASKPASS:-$ROOT/.git_askpass.sh}"
REPO="https://github.com/$(sed -n 's/^GH_REPO: *"\(.*\)".*/\1/p' "$ROOT/config.yaml").git"
BRANCH="gh-pages"
LIVE_URL="https://$(sed -n 's/^GH_REPO: *"\([^/]*\)\/\(.*\)".*/\1.github.io\/\2\//p' "$ROOT/config.yaml")"

[ -s "$TOKEN_FILE" ] || { echo "!! no token at $TOKEN_FILE" >&2; exit 1; }
[ -f "$ASKPASS" ] || { echo "!! no askpass at $ASKPASS" >&2; exit 1; }
[ -d "$SITE_DIR" ] || { echo "!! site dir missing: $SITE_DIR" >&2; exit 1; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

export GIT_ASKPASS="$ASKPASS"
echo ">> cloning $BRANCH to temp..." >&2
git clone -q -b "$BRANCH" "$REPO" "$WORK"
# Large pushes (~45 MB of new mp3s) fail with HTTP 408 inside GitHub's chunked
# upload path unless the http post buffer is raised (documented 2026-08-25 and
# hit again 2026-08-31). Set it inside the deploy clone so every push is safe
# without relying on the caller's environment.
git -C "$WORK" config http.postBuffer 524288000

# clear existing site files (keep .git). -mindepth 1 -maxdepth 1: do NOT delete
# dotfiles (e.g. .nojekyll) inside the deploy tree — a wipe of .nojekyll would
# 404 feed.xml via Jekyll. build_rss.py does not emit dotfiles, so nothing
# stale can survive (all current filenames are literal).
find "$WORK" -mindepth 1 -maxdepth 1 ! -path "$WORK/.git" -exec rm -rf {} + 2>/dev/null || true

# copy new site
cp -r "$SITE_DIR"/. "$WORK"/

# ---------------------------------------------------------------- status line
# "Last updated" banner on index.html: filled here at DEPLOY time (the single
# choke point for every run — nightly cron or manual), so the timestamp is the
# deploy moment and the count is measured against the LIVE feed, not a guess.
# build_rss.py emits <p class="status" id="last-updated"></p> as placeholder.
NEW=$(grep -c '<item>' "$SITE_DIR/feed.xml" || true)
[ -n "$NEW" ] || NEW=0
OLD=$(curl -fsS --max-time 20 "$LIVE_URL/feed.xml" | grep -c '<item>' || true)
[ -n "$OLD" ] && [ "$OLD" -gt 0 ] 2>/dev/null || OLD=0
DIFF=$((NEW - OLD)); [ "$DIFF" -lt 0 ] && DIFF=0
STAMP=$(TZ=America/New_York date '+%Y-%m-%d %H:%M %Z')
if [ "$DIFF" -gt 0 ]; then
  MSG="Last updated $STAMP — added $DIFF new episode$([ "$DIFF" -eq 1 ] || echo s) ($NEW total)."
else
  MSG="Last updated $STAMP — no new episodes ($NEW total)."
fi
python3 - "$WORK/index.html" "$MSG" <<'PY'
import sys
path, msg = sys.argv[1], sys.argv[2]
s = open(path, encoding="utf-8").read()
old = '<p class="status" id="last-updated"></p>'
assert old in s, "status placeholder missing from index.html"
open(path, "w", encoding="utf-8").write(s.replace(old, f'<p class="status" id="last-updated">{msg}</p>'))
PY
echo ">> status: $MSG" >&2

# Disable Jekyll processing on Pages: our generated HTML/XML contain
# Liquid-like sequences ({{ ... }}) from paper abstracts that break the
# Jekyll build ("Page build failed"). With .nojekyll, files ship verbatim.
touch "$WORK/.nojekyll"

# episode audio lives outside the site dir; ship it alongside
mkdir -p "$WORK/episodes"
count=0
for f in "$ROOT"/episodes/*.mp3; do
  [ -e "$f" ] || continue
  cp "$f" "$WORK/episodes/"
  count=$((count+1))
done
echo ">> copied $count episode mp3(s)" >&2

git -C "$WORK" add -A
git -C "$WORK" -c user.email="agent-sora@local" \
                -c user.name="agent-sora" \
                commit -q -m "Update site $(date -u +%F_%H%M)"
git -C "$WORK" push -q origin "$BRANCH"
echo ">> pushed $BRANCH" >&2
echo "OK"

echo ">> live base: $LIVE_URL" >&2
echo "$LIVE_URL"