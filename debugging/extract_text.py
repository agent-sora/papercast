"""Extract paper text (pages 0-7, 8-15, 19-28) via pymupdf from cached PDFs
or arXiv, for the nightly Papercast batch. Usage: python extract_text.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, '/home/patrick/papercast/.venv/lib/python3.11/site-packages')
import pymupdf  # noqa: E402

PC = '/home/patrick/papercast'
ids = [l.strip() for l in open(f'{PC}/episodes/feed/picks/ids-2026-10-03.txt') if l.strip()]
os.makedirs(f'{PC}/episodes/feed/text', exist_ok=True)
os.makedirs(f'{PC}/episodes/feed/pdf', exist_ok=True)

for pid in ids:
    pdf = f'{PC}/episodes/feed/pdf/{pid}.pdf'
    if not os.path.exists(pdf):
        url = f'https://arxiv.org/pdf/{pid}'
        req = urllib.request.Request(url, headers={'User-Agent': 'papercast/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                open(pdf, 'wb').write(r.read())
        except Exception as e:
            print(f'PDF FAIL {pid}: {e}')
            continue
    doc = pymupdf.open(pdf)
    n = len(doc)
    base = f'{PC}/episodes/feed/text/{pid}.txt'
    open(base, 'w').write('\n'.join(doc[i].get_text() for i in range(0, min(8, n))))
    if n > 8:
        open(f'{PC}/episodes/feed/text/{pid}-more.txt', 'w').write(
            '\n'.join(doc[i].get_text() for i in range(8, min(16, n))))
    if n > 19:
        open(f'{PC}/episodes/feed/text/{pid}-experiments.txt', 'w').write(
            '\n'.join(doc[i].get_text() for i in range(19, min(29, n))))
    print(pid, 'pages', n)
