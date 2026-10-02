"""Woerter sperren.  Aufruf:  python blacklist_add.py WORT1 WORT2 ..."""
import sys
from themes import _n
words = [_n(w) for w in sys.argv[1:]]
have = set(open("blacklist.txt", encoding="utf-8").read().split())
new = [w for w in words if w not in have]
if new:
    with open("blacklist.txt", "a", encoding="utf-8") as f:
        f.write("\n" + " ".join(new) + "\n")
print("gesperrt:", " ".join(new) if new else "(nichts Neues)")
