#!/usr/bin/env python3
"""Print a char range of a text file, masking any credential-like tokens."""
import re, sys

path = sys.argv[1]
start = int(sys.argv[2])
end = int(sys.argv[3])
t = open(path, encoding="utf-8", errors="replace").read()
seg = t[start:end]
# Mask anything that looks like an API key/token/password literal (>=22 token chars).
seg = re.sub(r"[A-Za-z0-9+/_\-=]{22,}", "[REDACTED]", seg)
print(f"[{path} chars {start}:{end} of {len(t)}]")
print(seg)
