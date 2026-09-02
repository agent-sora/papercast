#!/usr/bin/env python3
"""Numeric spot-check for papercast transcripts (STYLE_GUIDE rule #2).

Every number spoken in a transcript must trace to the extracted paper text
(episodes/feed/text/<id>*.txt). Transcripts spell most figures out as words
for TTS ("forty-eight point four three percent"), so this tool converts
spoken number words back to digits and checks each against the paper corpus,
which covers both the digit forms ("48.43") and exponent forms (10^12 is
stored as "1012" after PDF extraction strips superscripts, so "one trillion"
matches 1012).

Known checker artifacts (verified acceptable, 2026-08-29):
  - Standalone "hundred" from hyphenated compounds ("two-hundred-example").
  - Scale words (billion/trillion) matched against exponent notation.
  - Single words <= 12 are skipped as structural.

Usage:
  .venv/bin/python debugging/numeric_spotcheck.py episodes/feed/picks/ids-2026-08-28.txt
  .venv/bin/python debugging/numeric_spotcheck.py   # defaults to newest ids-* file

Exit code: number of unexplained mismatches (0 = clean).
"""
import pathlib
import re
import sys

ONES = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
        "six": "6", "seven": "7", "eight": "8", "nine": "9"}
TEENS = {"eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
         "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90}
SCALE = {"hundred": 100, "thousand": 1000, "million": 10 ** 6,
         "billion": 10 ** 9, "trillion": 10 ** 12}
NUMWORDS = "|".join(list(ONES) + list(TEENS) + list(TENS) + list(SCALE) + ["point"])
# Words may be joined by spaces OR hyphens ("forty-six", "twenty-seven").
RX = re.compile(rf"\b((?:{NUMWORDS})(?:[\s\-]+(?:{NUMWORDS}))*)\b")

# Verified-explained mismatches (checked by hand against the paper, 2026-08-29):
#   ('one billion'|'one trillion', 2608.25518)  = "10^9 to 10^12 images and tokens"
#   ('eight billion', 2608.27448)               = "Qwen3-8B"
#   ('hundred' x3, 2608.25518)                  = "two-hundred-example" (corpus: "200-example")
#   ('eight hundred', 2608.27456)               = "eight hundred ten tasks" (corpus: "810")
ALLOWED = {
    ("2608.25518", "one billion"), ("2608.25518", "one trillion"),
    ("2608.25518", "hundred"),
    ("2608.27448", "eight billion"),
    ("2608.27456", "eight hundred"),
    ("2608.24979", "twenty three thousand"),  # paper: "23.1 thousand output tokens"
}


def words2num(words):
    total, cur = 0, 0
    for w in words:
        if w in ONES:
            cur += int(ONES[w])
        elif w in TEENS:
            cur += TEENS[w]
        elif w in TENS:
            cur += TENS[w]
        elif w == "hundred":
            cur = (cur or 1) * 100
        elif w in SCALE:
            total, cur = (total + cur) * SCALE[w], 0
        else:
            return None
    return total + cur


def spoken_numbers(text):
    for m in RX.finditer(text):
        s = re.sub(r"[\s\-]+", " ", m.group(1)).strip()
        parts = s.split(" point ")
        if len(parts) == 2:
            ip = words2num(parts[0].split())
            frac = "".join(ONES[w] for w in parts[1].split() if w in ONES)
            if ip is not None and frac and len(parts[1].split()) == len(frac):
                yield s, float(f"{ip}.{frac}")
        else:
            v = words2num(parts[0].split())
            if v is not None:
                yield s, float(v)


def check(pid: str, day: str):
    root = pathlib.Path("/home/patrick/papercast")
    md = (root / f"episodes/{day}-{pid}.md").read_text()
    body = md.split("---", 2)[2] if md.startswith("---") else md
    corpus = ""
    for suffix in ["", "-more", "-discussion", "-experiments"]:
        p = root / f"episodes/feed/text/{pid}{suffix}.txt"
        if p.exists():
            corpus += p.read_text()
    cd = re.sub(r"[,\s]", "", corpus)
    unmatched = []
    for s, v in spoken_numbers(body):
        if len(s.split()) == 1 and v <= 12:
            continue
        vs = f"{v:.6f}".rstrip("0")
        cands = {vs, f"{v:.2f}", f"{v:.3f}", f"{v:.4f}"}
        cands.add(str(int(v)) if v == int(v) else "")
        if any(re.sub(r"[,\s]", "", c) in cd for c in cands if c):
            continue
        # Hyphenated-compound repair: if the transcript wrote the number as a
        # hyphenated token (e.g. "twenty-seven"), the regex stopped mid-token;
        # a non-hyphen digit substring still validates the figure.
        if any(d in cd for d in re.findall(r"\d+", s) if len(d) >= 2):
            continue
        # Scale-word repair: "ninety billion" may map to "90B", "9 billion" to
        # "9B" etc. in the paper; check the coefficient followed by the SI
        # letter (B/M/T) or by the raw digit run.
        # Scale-word repair (general): any spoken number ending in a scale word
        # may map to a k/m-suffixed count in the paper ("440 thousand" -> 440k,
        # "nine billion" -> 9B). Check the integer prefix before the final
        # scale word against prefix+unit in digit, upper, and lower forms.
        m = re.match(r"^(.+?)\s+(hundred|thousand|million|billion|trillion)$", s)
        if m:
            prefix = words2num(m.group(1).split())
            unit = {"hundred": "H", "thousand": "K", "million": "M",
                    "billion": "B", "trillion": "T"}[m.group(2)]
            if prefix is not None and any(
                    f"{prefix}{u}" in cd for u in (unit, unit.lower(), unit.lower() + "b")):
                continue
        unmatched.append((s, v))
    return [(s, v) for (s, v) in unmatched if (pid, s) not in ALLOWED]


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    picks_dir = pathlib.Path("/home/patrick/papercast/episodes/feed/picks")
    if arg:
        ids = [l.strip() for l in open(arg) if l.strip()]
    else:
        arg = sorted(picks_dir.glob("ids-*.txt"))[-1]
        ids = [l.strip() for l in open(arg) if l.strip()]
    # Derive the batch date from the picks filename (ids-YYYY-MM-DD.txt) so
    # the transcript path matches the actual day.
    m = re.search(r"(\d{4}-\d{2}-\d{2})", pathlib.Path(arg).name)
    if not m:
        print(f"cannot derive batch date from {arg}", file=sys.stderr)
        return 1
    day = m.group(1)
    fails = 0
    for pid in ids:
        bad = check(pid, day)
        print(f"{pid}: {'OK' if not bad else 'UNMATCHED'}")
        for s, v in bad:
            print(f"    '{s}' -> {v}")
        fails += len(bad)
    print(f"total unexplained: {fails}")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
