#!/usr/bin/env bash
# Publish the generated static site (index.html, feed.xml, episodes/*.mp3,
# cover.png) to the `gh-pages` branch, which GitHub Pages serves at
# https://agent-sora.github.io/agent-sora/
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
ASKPASS="/workspace/.git_askpass.sh"
REPO="https://github.com/$(sed -n 's/^GH_REPO: *"\(.*\)".*/\1/p' "$ROOT/config.yaml").git"
BRANCH="gh-pages"

[ -s "$TOKEN_FILE" ] || { echo "!! no token at $TOKEN_FILE" >&2; exit 1; }
[ -f "$ASKPASS" ] || { echo "!! no askpass at $ASKPASS" >&2; exit 1; }
[ -d "$SITE_DIR" ] || { echo "!! site dir missing: $SITE_DIR" >&2; exit 1; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

export GIT_ASKPASS="$ASKPASS"
echo ">> cloning $BRANCH to temp..." >&2
git clone -q -b "$BRANCH" "$REPO" "$WORK"

# clear existing site files (keep .git)
find "$WORK" -mindepth 1 -maxdepth 2 ! -path "$WORK/.git" ! -path "$WORK/.git/*" \
  -exec rm -rf {} + 2>/dev/null || true

# copy new site
cp -r "$SITE_DIR"/. "$WORK"/

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

LIVE="https://$(sed -n 's/^GH_REPO: *"\([^/]*\)\/\(.*\)".*/\1.github.io\/\2\//p' "$ROOT/config.yaml")"
echo ">> live base: $LIVE" >&2
echo "$LIVE"