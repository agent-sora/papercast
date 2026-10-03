#!/usr/bin/env bash
# debugging/fetch_2026_dailies.sh — fetch every weekday HF papers-day of 2026
# (2026-01-01 .. today) into the episodes/feed cache. Weekend requests are
# skipped (HF daily feed has no weekend entries; fetch_papers.py would just
# snap back to Friday). Idempotent: existing caches are re-fetched only if
# the file is missing. Paced at 1.2s between requests.
set -u
cd /home/patrick/papercast
export TMPDIR="$PWD/.tmp"
LOG="$PWD/.tmp/fetch-2026.log"
: > "$LOG"
python3 - <<'PY' > "$PWD/.tmp/weekdays-2026.txt"
import datetime
d = datetime.date(2026, 1, 1)
end = datetime.date.today()
while d <= end:
    if d.weekday() < 5:
        print(d.isoformat())
    d += datetime.timedelta(days=1)
PY
n=0
while read -r day; do
    if [ -f "episodes/feed/papers-$day.json" ]; then
        echo "skip $day (cached)" >> "$LOG"
        continue
    fi
    n=$((n+1))
    out=$(./.venv/bin/python scripts/fetch_papers.py --date "$day" --cache episodes/feed 2>&1)
    code=$?
    pd=$(echo "$out" | grep -o '"papers_date": "[0-9-]*"' | head -1 | cut -d'"' -f4)
    echo "fetched $day -> $pd (exit $code)" >> "$LOG"
    sleep 1.2
done < "$PWD/.tmp/weekdays-2026.txt"
echo "FETCH2026_DONE count=$n" >> "$LOG"
