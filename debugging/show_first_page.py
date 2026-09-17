"""Print the first ~12 non-empty lines of page 0 for each picked paper, so the
cold-open affiliations can be read by eye. Uses episodes/feed/text/<id>.txt
(pages 0-7 already extracted); the header block is the first chunk.

Usage: python debugging/show_first_page.py <date>
"""
import sys

PC = "/home/patrick/papercast"


def main() -> None:
    date = sys.argv[1]
    ids = [l.strip() for l in open(f"{PC}/episodes/feed/picks/ids-{date}.txt") if l.strip()]
    for pid in ids:
        lines = [l.rstrip() for l in open(f"{PC}/episodes/feed/text/{pid}.txt")]
        nonempty = [l for l in lines if l.strip()]
        print("=" * 90)
        print(pid)
        for l in nonempty[:16]:
            print("   |", l)


if __name__ == "__main__":
    main()
