"""Subsuche: durchsucht den Wortschatz mit den Saatwoertern JEDER Facette.

  python theme_subscan.py facetten_JURA.txt            (nur anzeigen)
  python theme_subscan.py facetten_JURA.txt --add      (aufnehmen)

Unterschied zu theme_scan.py: dort tippt man ein Dutzend Stichwoerter in die
Kommandozeile, hier dient jedes handkuratierte Facettenwort selbst als Saat.
Die Ausbeute ist dadurch um ein Vielfaches groesser und bleibt trotzdem
facettengenau, weil jeder Treffer die Naehe seiner Facette erbt.

Treffermuster, alle deterministisch:
  * Wort beginnt oder endet mit dem Saatwort           (URKUNDE -> URKUNDENFAELSCHUNG)
  * Stammfamilie: erste fuenf Zeichen, umlautunempfindlich  (KLAGE -> KLAEGER)
Treffer im Wortinneren bleiben aussen vor (ABGESETZT enthaelt GESETZ).

Aufgenommen wird mit Naehe = Facettennaehe x FAKTOR, also im Kolorit-Bereich
unter 0,45. Das ist Absicht: ein Treffer ist nur formal verwandt und nicht
handgeprueft. Kolorit verdraengt Fuellwoerter, aber keine Kernbegriffe, und
wird bei Wiederholung hart gedaempft. Kernvokabular entsteht ausschliesslich
aus der handkuratierten Facettenliste — daran nicht sparen.
"""
import sys, json, os, re
from collections import Counter
from themes import _n, PATH, stufe
from wordcheck import ist_partizip, lade_sperrliste

HERE = os.path.dirname(os.path.abspath(__file__))
FAKTOR = 0.42        # Treffer landen bewusst im Kolorit (< 0,45)
MIN_SAAT = 5          # kuerzere Saatwoerter fangen zu viel Beifang


def entumlaut(x):
    for a, b in (("AE", "A"), ("OE", "O"), ("UE", "U")):
        x = x.replace(a, b)
    return x


def lies_facetten(pfad):
    """-> (thema, gewicht, [(facettenname, naehe, [woerter])])"""
    thema, gewicht, facetten = None, 10.0, []
    # Woerter vor der ersten [Facette] sind die Direktliste des Themas
    akt = ("Direkt zum Thema", 1.0, [])
    facetten.append(akt)
    for zeile in open(pfad, encoding="utf-8"):
        z = zeile.strip()
        if not z:
            continue
        m = re.match(r"#\s*THEMA\s+(\S+)\s+GEWICHT\s+([\d.]+)", z, re.I)
        if m:
            thema, gewicht = m.group(1).upper(), float(m.group(2))
            continue
        if z.startswith("#"):
            continue
        m = re.match(r"\[(.+?)\]\s*([\d.]+)?", z)
        if m:
            akt = (m.group(1), float(m.group(2) or 1.0), [])
            facetten.append(akt)
            continue
        if akt is not None:
            akt[2].extend(_n(w) for w in z.split())
    return thema, gewicht, facetten


def main():
    pfad = sys.argv[1]
    add = "--add" in sys.argv
    thema, gewicht, facetten = lies_facetten(pfad)
    if not thema:
        sys.exit("Kopfzeile '# THEMA NAME GEWICHT n' fehlt")

    alle = set()
    for f in ("words_v3.json", "fallback_v3.json"):
        for d in json.load(open(os.path.join(HERE, f), encoding="utf-8")):
            alle.add(d["w"])
    bad = (lade_sperrliste(os.path.join(HERE, "blacklist.txt"))
           | lade_sperrliste(os.path.join(HERE, "stopwords.txt")))
    alle = {w for w in alle - bad if len(w) >= 4 and not ist_partizip(w)}

    t = json.load(open(PATH, encoding="utf-8")) if os.path.exists(PATH) else {}
    spec = t.setdefault(thema, {"gewicht": gewicht, "woerter": {}})
    ws = spec["woerter"]
    if isinstance(ws, list):
        ws = {w: 1.0 for w in ws}

    neu, je_facette = {}, Counter()
    for name, naehe, woerter in facetten:
        ziel = max(0.3, round(naehe * FAKTOR, 2))
        saat = [s for s in woerter if len(s) >= MIN_SAAT]
        staemme = {entumlaut(s)[:5] for s in saat if len(s) >= 6}
        for w in alle:
            if w in ws or w in neu:
                continue
            e = entumlaut(w)
            # Stammfamilie nur am Wortanfang: das Wortende trifft sonst
            # Zufallsopfer (ANTRAG -> MANTRA, SCHADEN -> TSCHAD).
            if any(w != s and (w.startswith(s) or w.endswith(s)) for s in saat) \
               or any(e.startswith(st) for st in staemme):
                neu[w] = ziel
                je_facette[name] += 1

    print(f"{thema}: {len(neu)} neue Treffer aus {len(facetten)} Facetten")
    print("je Facette:", " | ".join(f"{k} {v}" for k, v in je_facette.most_common()))
    kurz = sorted(w for w in neu if len(w) <= 6)
    print(f"kurz 4-6 ({len(kurz)}):", " ".join(kurz[:120]))
    if not add:
        print("(nur Anzeige — mit --add aufnehmen)")
        return
    ws.update(neu)
    spec["woerter"], spec["gewicht"] = ws, gewicht
    t[thema] = spec
    json.dump(t, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    h = Counter(stufe(v) for v in ws.values())
    print(f"aufgenommen. {thema} hat jetzt {len(ws)} Woerter, Stufen: {dict(h)}")


if __name__ == "__main__":
    main()
