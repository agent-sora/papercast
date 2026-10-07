#!/usr/bin/env python3
"""Show a window of text after a regex match. Usage: show_after.py <file> <regex> [chars]"""
import re, sys
path, pat = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 2400
t = open(path).read()
m = re.search(pat, t)
if not m:
    print('NOT FOUND:', pat)
else:
    print(t[m.start():m.start()+n])
