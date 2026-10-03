"""Re-pull true upvotes from the HF papers API for every candidate in the
selected shortlist, then print the full day's feed (titles + summaries) for
standing-rules re-scanning. Usage: python reupvote.py <papers-date>
"""
import json
import subprocess
import sys
import time

PC = '/home/patrick/papercast'
d = sys.argv[1] if len(sys.argv) > 1 else '2026-10-02'

papers = json.load(open(f'{PC}/episodes/feed/papers-{d}.json'))['papers']
sel = json.load(open(f'{PC}/episodes/feed/selected-{d}.json'))
cands = {p['arxiv_id'] for p in sel} | {p['arxiv_id'] for p in papers}
ids = sorted(cands)
print(f'{len(ids)} candidates')

true = {}
for i, pid in enumerate(ids):
    url = f'https://huggingface.co/api/papers/{pid}'
    try:
        out = subprocess.run(
            ['curl', '-s', '--max-time', '20', '-A', 'papercast/1.0 (nightly cron)', url],
            capture_output=True, text=True, timeout=30)
        data = json.loads(out.stdout)
        true[pid] = int(data.get('upvotes', 0))
    except Exception as e:
        true[pid] = -1
        print(f'FAIL {pid}: {e}')
    if i % 10 == 9:
        time.sleep(3)

json.dump(true, open(f'{PC}/episodes/feed/true_upvotes-{d}.json', 'w'), indent=1)
print('--- TOP 20 TRUE UPVOTES ---')
for pid, uv in sorted(true.items(), key=lambda kv: -kv[1])[:20]:
    title = next((p['title'] for p in papers if p['arxiv_id'] == pid), '?')
    print(pid, uv, title[:80])
print('--- FULL FEED (47) ---')
for p in papers:
    print(f"== {p['arxiv_id']} | uv={true.get(p['arxiv_id'])} | {p['title']}")
    print('   A:', ', '.join(p['authors'][:4]))
    print('   S:', p['summary'][:400].replace('\n', ' '))
