#!/usr/bin/env bash
# debugging/verify_live.sh — cache-busted verification of the live papercast
# site and feed. Usage: bash debugging/verify_live.sh
set -u
CB="cb=$RANDOM"
BASE="https://agent-sora.github.io/papercast"
echo "=== live feed headers (cache-busted) ==="
curl -s -I -H "Cache-Control: no-cache" "$BASE/feed.xml?$CB" | grep -iE "HTTP/|last-modified|etag|cache-control|age:|date:|x-|server"
echo
echo "live feed item count:"
curl -s -H "Cache-Control: no-cache" "$BASE/feed.xml?$CB" | grep -c "<item>"
echo
echo "=== live html (cache-busted) ==="
curl -s -H "Cache-Control: no-cache" "$BASE/index.html?$CB" -o /tmp/live.html
echo "html bytes: $(wc -c < /tmp/live.html)"
echo "mp3 refs: $(grep -c mp3 /tmp/live.html)"
echo "2026-09-20 refs: $(grep -c '2026-09-20' /tmp/live.html)"
echo "2609.20807 refs:"
grep -o '2609\.20807[^"< ]*' /tmp/live.html | head -4
echo "banner:"
grep -o 'Last updated[^<]*' /tmp/live.html
echo
echo "=== newest feed items (title + pubDate) ==="
curl -s -H "Cache-Control: no-cache" "$BASE/feed.xml?$CB" | grep -E "<title>|<pubDate>" | head -12
echo
echo "=== local site for comparison ==="
echo "local feed items: $(grep -c '<item' site/feed.xml)"
grep -o 'Last updated[^<]*' site/index.html 2>/dev/null || grep -o 'Last updated[^<]*' site/index.html
