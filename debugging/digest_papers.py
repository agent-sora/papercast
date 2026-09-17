"""Print the abstract + salient numeric/result lines for a set of papers, to feed
transcript drafting without reading every page. Pulls the first ~40 non-empty
lines (abstract/intro) plus lines matching result-ish patterns.

Usage: python debugging/digest_papers.py <date> [ids...]
"""
import re
import sys

PC = "/home/patrick/papercast"
NUM = re.compile(r"\d+(?:\.\d+)?\s*(?:%|percent|pp|points|bps|F1|accuracy|pass@|top-?\d|BLEU|ROUGE|AUC|MRR|NDCG|FLOPs|GB|GB/s|TFLOP|tokens|epochs|layers|params|M\b|B\b|G\b)")
RES = re.compile(r"%|accuracy|pass@|F1|FLOP|baseline|state[- ]of[- ]the[- ]art|outperform|achieve|score|success rate|improv|ablation|latency|throughput|context window|tokens", re.I)
SKIP = re.compile(r"arxiv:|http|www\.|\.org|\.edu|\.cn\b|\.com\b|doi\.|@|et al|et, al|Figure \d|Table \d|Eq\.|equation|ref\(|\[?\d+\]?[,;]", re.I)


def main() -> None:
    date = sys.argv[1]
    if len(sys.argv) > 2:
        ids = sys.argv[2:]
    else:
        ids = [l.strip() for l in open(f"{PC}/episodes/feed/picks/ids-{date}.txt") if l.strip()]
    for pid in ids:
        lines = [l.rstrip() for l in open(f"{PC}/episodes/feed/text/{pid}.txt", errors="replace") if l.strip()]
        more = [l.rstrip() for l in open(f"{PC}/episodes/feed/text/{pid}-more.txt", errors="replace") if l.strip()]
        exp = [l.rstrip() for l in open(f"{PC}/episodes/feed/text/{pid}-experiments.txt", errors="replace") if l.strip()]
        print("=" * 90)
        print(pid)
        print("--- HEAD (first 30) ---")
        for l in lines[:30]:
            print("  |", l)
        print("--- RESULT LINES (more+exp) ---")
        shown = set()
        for l in more + exp:
            if RES.search(l) and not SKIP.search(l) and len(l) < 130 and l not in shown:
                shown.add(l)
                print("  ~", l)
                if len(shown) > 60:
                    break


if __name__ == "__main__":
    main()
