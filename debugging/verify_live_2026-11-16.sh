#!/usr/bin/env bash
# Live verification for the 2026-11-16 Papercast publish.
# Checks: feed item count, presence of the 7 new arxiv ids in feed.xml,
# and HTTP status of each new episode mp3 on the live site.
set -u
B=https://agent-sora.github.io/papercast/
IDS="2611.18397 2611.18359 2611.18482 2611.07226 2611.18549 2611.18338 2611.14504"
FEED=$(curl -s "$B/feed.xml")
echo "feed items: $(printf '%s' "$FEED" | grep -c '<item>')"
N=0
for id in $IDS; do
  if printf '%s' "$FEED" | grep -q "$id"; then N=$((N+1)); fi
done
echo "new ids in feed: $N/7"
for id in $IDS; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$B/episodes/2026-11-16-$id.mp3")
  echo "$id $code"
done
