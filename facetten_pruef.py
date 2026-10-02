"""Sucht Kernbegriffe, die in Wahrheit Allerweltswoerter sind.

Aufruf:  python facetten_pruef.py [THEMA ...]      (ohne Angabe: alle Themen)
         python facetten_pruef.py --facetten       (nur die Facettenuebersicht)

Hintergrund: Kern heisst Naehe >= 0,8, und Kern heisst "die Frage MUSS
thematisch sein". Steht dort ein Wort, das mit dem Thema nichts Eigenes zu tun
hat, ist diese Pflicht nicht erfuellbar - im ersten Band stand GITTER als
Kernbegriff von SALZGITTERBAD mit "Staebe vor dem Fenster" im Buch.

Die Pruefung ist eine Heuristik, kein Urteil: sie meldet Kernbegriffe, die im
allgemeinen Sprachgebrauch sehr haeufig sind (Haeufigkeitsrang unter GRENZE)
und ausserdem in mehreren Themen zugleich als Kern gefuehrt werden. Beides
zusammen ist das Muster eines Wortes, das ueber eine Sammelfacette
hereingekommen ist. Die Entscheidung trifft der Projektleiter: entweder die
Facette auf Umfeldniveau senken (0,5 bis 0,65) oder das Wort streichen.
"""
import json, os, sys, re, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "skanvord"))

GRENZE = 3000          # Haeufigkeitsrang, unter dem ein Wort als Allerwelts-
#                        wort gilt (kleiner Rang = haeufiger)


def rangtabelle():
    r = {}
    for f in ("words_v3.json", "fallback_v3.json"):
        p = os.path.join(HERE, f)
        if not os.path.exists(p):
            continue
        for i, d in enumerate(json.load(open(p, encoding="utf-8"))):
            r.setdefault(d["w"], d.get("r", i))
    return r


def facetten(pfad):
    """[(Name, Naehe, [Woerter])] plus Direktliste unter dem Namen 'direkt'."""
    out, akt = [], ["direkt", 1.0, []]
    out.append(akt)
    for z in open(pfad, encoding="utf-8"):
        z = z.rstrip()
        if z.startswith("#") or not z.strip():
            continue
        m = re.match(r"\[(.+?)\]\s*([\d.]+)?", z)
        if m:
            akt = [m.group(1), float(m.group(2) or 1.0), []]
            out.append(akt)
            continue
        akt[2].extend(w for w in z.split() if w.isalpha())
    return out


def main():
    nur_fac = "--facetten" in sys.argv
    wunsch = [a.upper() for a in sys.argv[1:] if not a.startswith("--")]
    T = json.load(open(os.path.join(HERE, "themes.json"), encoding="utf-8"))
    rang = rangtabelle()

    print("Facetten je Thema (Naehe / Woerter der Handliste):")
    for pfad in sorted(glob.glob(os.path.join(HERE, "facetten_*.txt"))):
        th = os.path.basename(pfad)[9:-4]
        if th == "VORLAGE" or (wunsch and th not in wunsch):
            continue
        fac = facetten(pfad)
        kern = sum(len(f[2]) for f in fac if f[1] >= 0.8)
        print(f"\n  {th} (Gewicht {T.get(th, {}).get('gewicht', '?')}, "
              f"{kern} Handwoerter auf Kernniveau)")
        for name, nah, ws in fac:
            if not ws:
                continue
            marke = "KERN   " if nah >= 0.8 else ("UMFELD " if nah >= 0.45
                                                 else "KOLORIT")
            print(f"    {nah:4.2f} {marke} {len(ws):4d}  {name}")
    if nur_fac:
        return

    # In wie vielen Themen ist ein Wort Kern?
    mehrfach = collections.Counter()
    for th, d in T.items():
        for w, nah in d["woerter"].items():
            if (nah if not isinstance(nah, dict) else nah["naehe"]) >= 0.8:
                mehrfach[w] += 1

    print("\n\nVerdaechtige Kernbegriffe "
          f"(Haeufigkeitsrang < {GRENZE}, in mehreren Themen Kern):")
    for th, d in sorted(T.items()):
        if wunsch and th not in wunsch:
            continue
        treffer = []
        for w, nah in d["woerter"].items():
            n = nah if not isinstance(nah, dict) else nah["naehe"]
            if n < 0.8:
                continue
            r = rang.get(w)
            if r is not None and r < GRENZE and mehrfach[w] >= 2:
                treffer.append((r, w, mehrfach[w]))
        treffer.sort()
        if treffer:
            print(f"\n  {th} ({len(treffer)}):")
            print("    " + " ".join(f"{w}({m}x)" for _, w, m in treffer[:60]))


if __name__ == "__main__":
    main()
