"""Findet Kandidaten fuer eine Themenliste im vorhandenen Wortschatz.

  python theme_scan.py JURA RECHT GESETZ GERICHT KLAGE STRAF

Ein Stichwort zaehlt nur, wenn es am Wortanfang oder am Wortende steht oder das
Wort selbst ist. Das unterdrueckt Zufallstreffer im Wortinneren: ABGESETZT
enthaelt zwar GESETZ, aber weder vorn noch hinten, und faellt heraus.
Zusaetzlich werden Partizipien deterministisch aussortiert.

Ausgabe: Laengenhistogramm und die vollstaendige Liste der 4- bis
6-Buchstaben-Treffer. Alles Uebrige steht in scan_<THEMA>.txt.
"""
import sys, json, os
from collections import Counter
from themes import _n
from wordcheck import ist_partizip

HERE = os.path.dirname(os.path.abspath(__file__))
name, keys = sys.argv[1].upper(), [_n(k) for k in sys.argv[2:]]
lose = "--lose" in sys.argv          # auch Treffer im Wortinneren zulassen
keys = [k for k in keys if not k.startswith("--")]

words = set()
for f in ("words_v3.json", "fallback_v3.json"):
    for d in json.load(open(os.path.join(HERE, f), encoding="utf-8")):
        words.add(d["w"])
bad = {_n(w) for w in open(os.path.join(HERE, "blacklist.txt"),
                           encoding="utf-8").read().split()}


def trifft(w, k):
    if lose:
        return k in w
    return w.startswith(k) or w.endswith(k) or w == k


hits = sorted(w for w in words - bad
              if len(w) >= 4 and not ist_partizip(w)
              and any(trifft(w, k) for k in keys))
open(os.path.join(HERE, f"scan_{name}.txt"), "w",
     encoding="utf-8").write("\n".join(hits))
h = Counter(len(w) for w in hits)
print(f"{name}: {len(hits)} Treffer -> scan_{name}.txt")
print("Laengen:", " ".join(f"{k}:{h[k]}" for k in sorted(h)))
kurz = [w for w in hits if len(w) <= 6]
print(f"KURZ (4-6, {len(kurz)}):", " ".join(kurz))
