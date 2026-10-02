"""Prueft Fragetexte auf Kaestchenbreite, ohne zu rendern.

  python fitcheck.py "Zeile1\nZeile2" ...        prueft die Texte
  python fitcheck.py --auto "Klagelied" ...     schlaegt einen Umbruch vor
  python fitcheck.py --eintragen WORT=Frage ... bricht um, prueft, speichert
  python fitcheck.py --durchsehen               prueft die ganze clues.json

--eintragen ist der Regelweg beim Fragenschreiben. Es erledigt in einem
Aufruf, was sonst drei Runden kostet: Silbentrennung setzen (pyphen),
Kaestchenbreite messen, Wortstamm der Loesung in der Frage suchen
(wordcheck.enthaelt_loesung) und den Klammerzusatz pruefen
(wordcheck.kennzeichen_fehlt: engl., Abk., Pl.). Nur einwandfreie Fragen
landen in clues.json, alles andere wird gemeldet und uebersprungen.

Die Breite entscheidet, nicht die Zeichenzahl: ein Wort mit neun schmalen
Buchstaben passt, eines mit neun breiten nicht. Deshalb immer messen statt
schaetzen. --auto setzt Zeilenumbrueche und Trennstriche selbst und meldet,
wenn der Text auch dann nicht in vier Zeilen passt - dann muss die Frage
kuerzer formuliert werden.
"""
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skanvord"))
from render2 import wrap, size_for_cap
from reportlab.lib.units import mm
from core import CELL_MM, CAP_MM, LINES_MAX
size, width = size_for_cap(CAP_MM), (CELL_MM - 1.0) * mm


def passt(text):
    given = set(text.replace("\n", " ").split())
    ls = wrap(text, size, width)
    return not (len(ls) > LINES_MAX or
                any(l.endswith("-") and l not in given for l in ls))


def umbrechen(text):
    """Setzt Umbrueche und Trennstriche so, dass jede Zeile in das Kaestchen
    passt. Rueckgabe: umgebrochener Text (kann mehr als LINES_MAX Zeilen haben,
    dann ist die Frage zu lang)."""
    from reportlab.pdfbase import pdfmetrics
    from render2 import FONTB

    try:                      # saubere Silbentrennung, falls verfuegbar
        import pyphen
        _hy = pyphen.Pyphen(lang="de_DE")
    except Exception:         # sonst hart nach Breite trennen
        _hy = None

    def breit(s):
        # Die Tilde markiert nur eine erlaubte Trennstelle und wird nie
        # gesetzt - sie darf die Breitenmessung nicht verfaelschen.
        return pdfmetrics.stringWidth(s.replace("~", ""), FONTB, size)

    def trenne(wort):
        """Groesstmoegliches Anfangsstueck, das mit Trennstrich passt.

        Steht ein ~ im Wort, gelten NUR diese Stellen. pyphen trennt
        Zusammensetzungen nicht zuverlaessig ("Heils-chlamm" statt
        "Heil-schlamm"); dann wird die Trennstelle von Hand gesetzt:
        "Heil~schlamm im Bad". Die Tilde selbst erscheint nie im Text.
        """
        if "~" in wort:
            stellen, pos = [], 0
            for teil in wort.split("~")[:-1]:
                pos += len(teil)
                stellen.append(pos)
            rein = wort.replace("~", "")
            for st in reversed(stellen):
                if breit(rein[:st] + "-") <= width:
                    return st
            return 0
        if _hy:
            stellen = []
            rest = _hy.inserted(wort, "-")
            pos = 0
            for teil in rest.split("-")[:-1]:
                pos += len(teil)
                stellen.append(pos)
            for p in reversed(stellen):
                if breit(wort[:p] + "-") <= width:
                    return p
            return 0
        i = len(wort)
        while i > 2 and breit(wort[:i] + "-") > width:
            i -= 1
        return i if i > 2 else 0

    # Ein bereits umgebrochener Text enthaelt Trennstriche am Zeilenende.
    # Ohne diesen Schritt wird "Schmerz-\nhaft" als zwei Woerter gelesen und
    # zu "Schmer-\nz- haft" verunstaltet: ein zweiter Bindestrich mitten in
    # der Zeile. Erst zusammenfuegen, dann neu trennen.
    text = re.sub(r"-\s*\n\s*", "", text)
    zeilen, cur = [], ""
    for wort in text.replace("\n", " ").split():
        while breit(wort) > width:                  # Wort allein zu breit
            i = trenne(wort)
            if not i:
                break
            if cur:
                zeilen.append(cur)
                cur = ""
            zeilen.append(wort[:i].replace("~", "") + "-")
            wort = wort[i:]
        probe = (cur + " " + wort).strip()
        if not cur or breit(probe) <= width:
            cur = probe
        else:
            zeilen.append(cur)
            cur = wort
    if cur:
        zeilen.append(cur)
    return "\n".join(zeilen).replace("~", "")


def eintragen(paare):
    """paare: Liste von (WORT, Rohtext). Rueckgabe: Zahl der Eintraege."""
    import json
    from wordcheck import enthaelt_loesung, kennzeichen_fehlt, normal
    pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clues.json")
    c = json.load(open(pfad, encoding="utf-8"))
    n, mangel = 0, []
    for wort, roh in paare:
        wort = normal(wort)
        text = umbrechen(roh)
        if not passt(text):
            mangel.append(f"{wort}: passt nicht in vier Zeilen -> {roh!r}")
            continue
        if enthaelt_loesung(text, wort):
            mangel.append(f"{wort}: Frage enthaelt den Wortstamm -> {roh!r}")
            continue
        fehlt = kennzeichen_fehlt(wort, text)
        if fehlt:
            mangel.append(f"{wort}: Zusatz {fehlt} fehlt -> {roh!r}")
            continue
        v = c.setdefault(wort, [])
        if text not in v:
            # ANHAENGEN, nicht voranstellen. render_book waehlt die Fassung
            # nach der Zahl der bisherigen Einsaetze (vs[k % len(vs)]). Wer
            # vorn einfuegt, veraendert damit die Frage auf jeder bereits
            # fertigen Seite. Angehaengt wird die neue Fassung erst beim
            # naechsten Einsatz sichtbar - genau das ist gewollt.
            v.append(text)
        n += 1
    json.dump(c, open(pfad, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    for m in mangel:
        print("MANGEL", m)
    print(f"eingetragen {n}, abgelehnt {len(mangel)}")
    return n


def durchsehen(schreiben=True):
    """Geht clues.json durch: neu umbrechen, Unrettbares melden.

    Fragen aus frueheren Buechern sind oft von Hand umgebrochen und passen
    nach einer Schriftaenderung nicht mehr. Der Renderer faellt nur ueber die,
    die im aktuellen Buch vorkommen - der Rest schlummert weiter. Dieser Lauf
    nimmt sich alle vor. Der Wortlaut bleibt unangetastet, nur die Umbrueche
    werden neu gesetzt; was auch dann nicht passt, muss neu formuliert werden
    und wird nur gemeldet.
    """
    import json
    pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clues.json")
    c = json.load(open(pfad, encoding="utf-8"))
    geaendert, hoffnungslos, gesamt = 0, [], 0
    for wort, liste in c.items():
        for i, eintrag in enumerate(liste):
            text = eintrag["c"] if isinstance(eintrag, dict) else eintrag
            gesamt += 1
            if passt(text):
                continue
            neu = umbrechen(text)
            if passt(neu):
                if isinstance(eintrag, dict):
                    eintrag["c"] = neu
                else:
                    liste[i] = neu
                geaendert += 1
            else:
                hoffnungslos.append((wort, text))
    if schreiben:
        json.dump(c, open(pfad, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=0)
    print(f"{gesamt} Fragen geprueft, {geaendert} neu umgebrochen, "
          f"{len(hoffnungslos)} zu lang")
    for wort, text in hoffnungslos:
        print(f"  NEU FORMULIEREN {wort}: {text!r}")
    return hoffnungslos


if __name__ == "__main__":
    if "--durchsehen" in sys.argv:
        durchsehen()
        sys.exit(0)
    if "--eintragen" in sys.argv:
        paare = []
        for t in sys.argv[1:]:
            if t == "--eintragen":
                continue
            w, _, f = t.partition("=")
            paare.append((w.strip(), f.strip()))
        eintragen(paare)
        sys.exit(0)
    auto = "--auto" in sys.argv
    for t in sys.argv[1:]:
        if t == "--auto":
            continue
        t = t.replace("\\n", "\n")
        if auto:
            u = umbrechen(t)
            print(("OK   " if passt(u) else "ZU LANG "), repr(u))
        else:
            print("OK " if passt(t) else "ZU BREIT ", repr(t))
