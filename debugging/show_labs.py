"""Print affiliation-like lines from the extracted first-page text of each pick.
Greps for institution name patterns, skipping lines that look like emails, URLs,
or running headers. Used to build the honest Labs: front-matter field.

Usage: python debugging/show_labs.py <date>
"""
import re
import sys

PC = "/home/patrick/papercast"
PAT = re.compile(
    r"University|Institute|Laboratory|Lab\b|KAIST|Tsinghua|Peking|Microsoft|Google|"
    r"NVIDIA|Alibaba|Tencent|ByteDance|DeepAuto|Academy|School|Polytechnic|College",
    re.I,
)
SKIP = re.compile(r"arxiv|http|www\.|@|et al|et, al|doi\.|\.org|\.edu|\.cn|\.com", re.I)


def main() -> None:
    date = sys.argv[1]
    ids = [l.strip() for l in open(f"{PC}/episodes/feed/picks/ids-{date}.txt") if l.strip()]
    for pid in ids:
        print("=" * 80)
        print(pid)
        seen = set()
        for raw in open(f"{PC}/episodes/feed/text/{pid}.txt", errors="replace"):
            line = raw.strip()
            if not line or len(line) > 120:
                continue
            if PAT.search(line) and not SKIP.search(line):
                # drop lines that are clearly sentence fragments, not affiliations
                if line.count(" ") < 14 and re.search(r"\d{4}|University|Institute|Lab|KAIST|School|Academy|Microsoft|Google|NVIDIA", line, re.I):
                    key = line.lower()
                    if key not in seen:
                        seen.add(key)
                        print("   |", line)


if __name__ == "__main__":
    main()
