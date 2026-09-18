"""Find JEPA-Anything (2609.20800) affiliations from the PDF.

The paper_meta.py extraction returned an empty affiliation list, so the
transcript needs a manual scan of the PDF for the author-affiliation block.
"""
import pymupdf

d = pymupdf.open("/home/patrick/papercast/episodes/feed/meta/2609.20800.pdf")
for i in range(len(d)):
    t = d[i].get_text()
    if "Pheng Ann Heng" in t and ("Nanyang" in t or "Tencent" in t or "Correspondence" in t):
        print("PAGE", i)
        print(t[:2000])
        break
else:
    # fallback: search all pages for common org tokens
    for i in range(len(d)):
        t = d[i].get_text()
        if any(k in t for k in ("Nanyang", "Tencent", "Peking", "Fudan", "SUSTech")):
            print("HIT PAGE", i)
            idx = max(t.find(k) - 200 for k in ("Nanyang", "Tencent", "Peking", "Fudan", "SUSTech") if k in t)
            print(t[max(0, idx): idx + 800])
            break
