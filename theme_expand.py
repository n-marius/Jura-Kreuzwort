"""Erweitert ein Thema deterministisch um Zusammensetzungen.

  python theme_expand.py JURA --naehe 0.4

Nimmt jedes bereits aufgenommene Themenwort ab fuenf Buchstaben und sucht
Woerter, die damit beginnen oder enden. So waechst die Liste ohne KI-Aufwand.
"""
import sys, json, os
from collections import Counter
from themes import _n, PATH
from wordcheck import ist_partizip

HERE = os.path.dirname(os.path.abspath(__file__))
name = sys.argv[1].upper()
naehe = float(sys.argv[sys.argv.index("--naehe") + 1]) if "--naehe" in sys.argv else 0.4

t = json.load(open(PATH, encoding="utf-8"))
spec = t[name]
ws = spec["woerter"]
if isinstance(ws, list):
    ws = {w: 1.0 for w in ws}
kerne = [w for w in ws if len(w) >= 5 and ws[w] >= 0.8]

alle = set()
for f in ("words_v3.json", "fallback_v3.json"):
    for d in json.load(open(os.path.join(HERE, f), encoding="utf-8")):
        alle.add(d["w"])
bad = {_n(w) for w in open(os.path.join(HERE, "blacklist.txt"),
                           encoding="utf-8").read().split()}
def entumlaut(x):
    for a, b in (("AE", "A"), ("OE", "O"), ("UE", "U")):
        x = x.replace(a, b)
    return x


# Stammfamilie: die ersten fuenf Zeichen des Kernbegriffs, umlautunempfindlich.
# So findet KLAGE auch KLAEGER, RUEGE auch RUGEN.
staemme = {entumlaut(k)[:5] for k in kerne if len(k) >= 6}
add = 0
for w in sorted(alle - bad):
    if w in ws or len(w) < 5 or ist_partizip(w):
        continue
    treffer = any(w != k and (w.startswith(k) or w.endswith(k)) for k in kerne)
    if not treffer:
        e = entumlaut(w)
        treffer = any(e.startswith(s) or e.endswith(s) for s in staemme)
    if treffer:
        ws[w] = naehe
        add += 1
spec["woerter"] = ws
json.dump(t, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
h = Counter(len(w) for w in ws)
print(f"{name}: +{add} durch Zusammensetzungen, jetzt {len(ws)} Woerter")
print("Laengen:", " ".join(f"{k}:{h[k]}" for k in sorted(h)))
