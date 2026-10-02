"""Sichtpruefung einer Themenliste — kompakte Ausgabe nach Laenge.

  python theme_review.py JURA          alle Woerter
  python theme_review.py JURA 4 7      nur Laenge 4 bis 7
  python theme_review.py JURA --neu    nur automatisch ergaenzte (Naehe < 0.45)
"""
import sys, json
from themes import PATH, stufe
from collections import defaultdict

name = sys.argv[1].upper()
args = [a for a in sys.argv[2:] if not a.startswith("--")]
lo, hi = (int(args[0]), int(args[1])) if len(args) == 2 else (3, 30)
nur_neu = "--neu" in sys.argv
ws = json.load(open(PATH, encoding="utf-8"))[name]["woerter"]
gruppen = defaultdict(list)
for w, n in sorted(ws.items()):
    if not lo <= len(w) <= hi:
        continue
    if nur_neu and n >= 0.45:
        continue
    gruppen[len(w)].append(f"{w}{'!' if n >= 0.8 else ('+' if n >= 0.45 else '~')}")
for L in sorted(gruppen):
    print(f"{L:2d} ({len(gruppen[L])}): " + " ".join(gruppen[L]))
print("! Kern  + Umfeld  ~ Kolorit")
