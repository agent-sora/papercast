#!/usr/bin/env python3
"""Lint episode transcripts against docs/STYLE_GUIDE.md (producer brief).

Checks, per transcript .md:
  1. Front matter has Title / Authors / Labs / Arxiv / Day / Upvotes / Link.
  2. Word count within [min,max] (default 1300-1750 for ~10 min).
  3. Cold open: first prose paragraph names paper + >=3 authors + >=1 lab.
  4. No LaTeX commands, no scientific notation (1.2e5 / x10^3), no inline $..$
     math beyond currency amounts.
  5. Violence-word scan: kill*, slaugher, violent, war-, battle, destroy*,
     weapon, blood... (allowed when quoting the paper: line flagged REVIEW,
     not FAIL).
  6. Banned-style scan: slang/hype markers ("game-changer", "revolutioniz*",
     "mind-blow*", "let's dive", "buckle up", "folks", contractions count is
     a WARN only), exclamation-mark density > 1 per 300 words -> WARN.

Exit code: number of FAIL findings (0 = clean). WARNs are reported only.

Usage:
    python scripts/lint_script.py episodes/*.md [--min-words 1300 --max-words 1750]
"""
import argparse
import glob
import re
import sys

REQUIRED_FIELDS = ["Title", "Authors", "Labs", "Arxiv", "Day", "Upvotes", "Link"]

LATEX_RE = re.compile(r"\\[a-zA-Z]+|\\begin\{|\\end\{")
SCI_RE = re.compile(r"\d(?:\.\d+)?\s*[eE][+-]?\d|\d+\s*[x×]\s*10\s*\^")
DOLLAR_MATH_RE = re.compile(r"\$\s*[a-zA-Z\\]")
VIOLENCE_RE = re.compile(
    r"\b(kil[l]|killed|killing|kills|slaughter\w*|massacr\w*|violent\w*|violence|"
    r"war\b|warfare|battle\w*|destroy\w*|annihilat\w*|obliterat\w*|weapon\w*|blood\w*|"
    r"brutal\w*|deadly|lethal|attackers?|kill switch|rubble|shatter\w*|"
    r"wreck\w*|crush\w*)\b", re.I)
BANNED_STYLE_RE = re.compile(
    r"\b(game.?changer\w*|revolutioni[sz]\w*|mind.?blow\w*|buckle up|folks|"
    r"let'?s dive|deep dive in|super cool|insane\w*|crazy\w*|magic\w*|"
    r"jaw.?dropp\w*|stunning\w*|blazing\w*|crushing it|nail\w* it)\b", re.I)


def parse(md_path):
    with open(md_path, encoding="utf-8") as f:
        text = f.read()
    meta, body = {}, text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                m = re.match(r"([A-Za-z]+)\s*:\s*(.*)", line.strip())
                if m:
                    meta[m.group(1)] = m.group(2).strip().strip('"')
            body = parts[2]
    return meta, body


def cold_open_ok(body):
    paras = [p.strip() for p in body.split("\n\n") if p.strip()
             and not p.strip().startswith("#")]
    if not paras:
        return False, "no prose paragraphs"
    p = re.sub(r"\s+", " ", paras[0])
    words = len(p.split())
    if words < 25:
        return False, f"cold open too short ({words} words)"
    # authors: capitalized name pairs, at least 3 distinct surname-ish tokens
    names = re.findall(r"\b[A-Z][a-z]+\s+[A-Z][a-zA-Z\-']+", p)
    if len(names) < 3:
        return False, f"cold open names only {len(names)} author(s): {names[:4]}"
    lab_words = ("University", "Institute", "Laboratory", "Lab", "College",
                 "School", "Academy", "Research", "AI", "Google", "DeepMind",
                 "Meta", "Microsoft", "Amazon", "NVIDIA", "MIT", "Stanford",
                 "Berkeley", "Tsinghua", "ETH", "EPFL", "CMU", "KAIST")
    if not any(w in p for w in lab_words):
        return False, "cold open lacks any institution mention"
    return True, f"{len(names)} authors named, institutions present"


def check_file(path: str, min_words: int = 1300, max_words: int = 1750):
    """Lint one transcript. Returns (fails, warns, word_count)."""
    fails, warns = [], []
    meta, body = parse(path)
    for fld in REQUIRED_FIELDS:
        if not meta.get(fld):
            fails.append(f"front matter missing {fld}")
    wc = len(re.findall(r"[A-Za-z0-9'-]+", body))
    if not (min_words <= wc <= max_words):
        fails.append(f"word count {wc} outside [{min_words},{max_words}]")
    ok, why = cold_open_ok(body)
    if meta.get("Title") and not ok:
        fails.append(f"cold open: {why}")
    for rx, label in ((LATEX_RE, "LaTeX command"),
                      (SCI_RE, "scientific notation"),
                      (DOLLAR_MATH_RE, "$math$")):
        hits = rx.findall(body)
        if hits:
            fails.append(f"{label}: {hits[:3]}")
    for m in VIOLENCE_RE.finditer(body):
        ctx = body[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
        warns.append(f"violence-word '{m.group(0)}' — verify it is quoted "
                     f"from the paper or remove: …{ctx}…")
    bhits = BANNED_STYLE_RE.findall(body)
    if bhits:
        warns.append(f"banned style words: {sorted(set(bhits))[:6]}")
    excl = body.count("!")
    if excl * 300 > wc:
        warns.append(f"{excl} exclamation marks (>{wc // 300} allowed)")
    return fails, warns, wc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--min-words", type=int, default=1300)
    ap.add_argument("--max-words", type=int, default=1750)
    args = ap.parse_args()

    total_fail = 0
    for path in sorted(args.files):
        fails, warns, wc = check_file(path, args.min_words, args.max_words)
        status = "FAIL" if fails else "ok"
        print(f"== {path}: {wc} words [{status}]")
        for f_ in fails:
            print(f"   FAIL: {f_}")
        for w in warns:
            print(f"   warn: {w}")
        total_fail += len(fails)
    print(f"\ntotal FAILs: {total_fail}")
    return 1 if total_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
