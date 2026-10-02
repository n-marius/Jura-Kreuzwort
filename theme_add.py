"""Uebernimmt Woerter in ein Thema.

  python theme_add.py JURA 30 --datei scan_JURA.txt --naehe 0.5
  python theme_add.py JURA 30 --woerter URTEIL AKTE KLAGE --naehe 1.0

Vorhandene Eintraege mit hoeherer Naehe bleiben erhalten.
"""
import sys, json, os
from themes import _n, PATH

a = sys.argv[1:]
name, gew = a[0].upper(), float(a[1])
naehe, datei, woerter = 1.0, None, []
i = 2
while i < len(a):
    if a[i] == "--naehe":
        naehe = float(a[i + 1]); i += 2
    elif a[i] == "--datei":
        datei = a[i + 1]; i += 2
    elif a[i] == "--woerter":
        i += 1
        while i < len(a) and not a[i].startswith("--"):
            woerter.append(a[i]); i += 1
    else:
        i += 1
if datei:
    woerter += open(datei, encoding="utf-8").read().split()

t = json.load(open(PATH, encoding="utf-8")) if os.path.exists(PATH) else {}
spec = t.setdefault(name, {"gewicht": gew, "woerter": {}})
spec["gewicht"] = gew
ws = spec["woerter"]
if isinstance(ws, list):
    ws = {w: 1.0 for w in ws}
add = 0
for w in woerter:
    w = _n(w)
    if len(w) < 4:
        continue
    if w not in ws or ws[w] < naehe:
        ws[w] = naehe; add += 1
spec["woerter"] = ws
json.dump(t, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
from collections import Counter
h = Counter(len(w) for w in ws)
print(f"{name}: +{add}, jetzt {len(ws)} Woerter, Gewicht {gew}")
print("Laengen:", " ".join(f"{k}:{h[k]}" for k in sorted(h)))
short = sum(v for k, v in h.items() if k <= 6)
if short < len(ws) * 0.25:
    print(f"WARNUNG: nur {short} Woerter mit 4-6 Buchstaben "
          f"({short/max(1,len(ws)):.0%}). Kurze Begriffe gezielt ergaenzen.")
