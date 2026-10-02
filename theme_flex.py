"""Kolorit aus Beugungen und Ableitungen der bereits aufgenommenen Themenwoerter.

  python theme_flex.py JURA             (nur anzeigen)
  python theme_flex.py JURA --add       (aufnehmen, Naehe 0,3)

Der Expander findet Zusammensetzungen (URKUNDE -> URKUNDENFAELSCHUNG). Diese
Stufe holt das Uebrige: Mehrzahlen, schwache Beugungen und die typischen
Ableitungssilben. RECHT zieht RECHTLICH nach, MIETER die Form MIETERIN, URTEIL
die Mehrzahl URTEILE.

Warum nur Kolorit (0,3): eine gebeugte Form ist thematisch, traegt das Raetsel
aber nicht wie ein Kernbegriff. Sie soll Fuellwoerter verdraengen, keine
Kernbegriffe. Mehrzahlformen bekommen ausserdem ueber FORM_FAKTOR ohnehin ein
geringeres Fuellgewicht und verlangen eine Frage, die die Mehrzahl ausdrueckt.
"""
import sys, json, os
from collections import Counter
from themes import _n, PATH, stufe
from wordcheck import ist_partizip, lade_sperrliste

HERE = os.path.dirname(os.path.abspath(__file__))
NAEHE = 0.3
ENDUNGEN = ("E", "EN", "ER", "ES", "N", "S", "EM")
ABLEITUNG = ("LICH", "ISCH", "IG", "HAFT", "LOS", "BAR", "IN", "CHEN", "LEIN",
             "UNG", "HEIT", "KEIT", "SCHAFT", "TUM")
UML = (("A", "AE"), ("O", "OE"), ("U", "UE"))


def varianten(w):
    """Alle Formen, die als Beugung oder Ableitung von w gelten."""
    out = set()
    for e in ENDUNGEN + ABLEITUNG:
        out.add(w + e)
    # Umlautplural: NAGEL -> NAEGEL, BUCH -> BUECHER
    for a, b in UML:
        if a in w:
            u = w.replace(a, b, 1)
            for e in ("", "E", "ER", "EN"):
                out.add(u + e)
    out.discard(w)
    return out


def main():
    name = sys.argv[1].upper()
    add = "--add" in sys.argv
    alle = set()
    for f in ("words_v3.json", "fallback_v3.json"):
        for d in json.load(open(os.path.join(HERE, f), encoding="utf-8")):
            alle.add(d["w"])
    bad = (lade_sperrliste(os.path.join(HERE, "blacklist.txt"))
           | lade_sperrliste(os.path.join(HERE, "stopwords.txt")))
    alle -= bad

    t = json.load(open(PATH, encoding="utf-8"))
    spec = t[name]
    ws = spec["woerter"]
    if isinstance(ws, list):
        ws = {w: 1.0 for w in ws}

    neu = {}
    for w, nah in list(ws.items()):
        if nah < 0.45 or len(w) < 4:
            continue
        for v in varianten(w):
            if v in ws or v in neu or v not in alle:
                continue
            if len(v) < 4 or ist_partizip(v):
                continue
            neu[v] = NAEHE

    print(f"{name}: {len(neu)} Beugungen und Ableitungen gefunden")
    kurz = sorted(v for v in neu if len(v) <= 6)
    print(f"kurz 4-6 ({len(kurz)}):", " ".join(kurz[:120]))
    if not add:
        print("(nur Anzeige — mit --add aufnehmen)")
        return
    ws.update(neu)
    spec["woerter"] = ws
    json.dump(t, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    h = Counter(stufe(v) for v in ws.values())
    print(f"aufgenommen. {name} hat jetzt {len(ws)} Woerter, Stufen: {dict(h)}")


if __name__ == "__main__":
    main()
