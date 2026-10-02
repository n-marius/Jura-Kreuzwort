"""Sammelt ueber alle erzeugten Raetsel, welche Fragen noch fehlen.

Aufruf:  python collect_clues.py
Gibt zwei Listen aus:
  FEHLT     - Wort hat ueberhaupt keine Frage
  VARIANTE  - Wort kommt oefter vor, als Fragevarianten vorliegen
"""
import glob, pickle, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skanvord"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "kreuz"))
import layout                     # noqa
# PUZZLE_DIR=kr_puzzles python collect_clues.py  -> Kreuzwortbuch
PUZZLE_DIR = os.environ.get("PUZZLE_DIR", "puzzles")
import json
from core import clue_store, load_formen
from wordcheck import plural_verdacht
from themes import theme_map, theme_names, stufe

C = clue_store()
FORM = load_formen()
tm = theme_map()
count = {}
for f in sorted(glob.glob(os.path.join(PUZZLE_DIR, "*.pkl"))):
    lay, _ = pickle.load(open(f, "rb"))
    for e in lay.entries:
        count[e.word] = count.get(e.word, 0) + 1
fehlt = sorted(w for w in count if w not in C)
var = sorted((w, count[w], len(C[w])) for w in count
             if w in C and count[w] > len(C[w]))
print("Woerter gesamt:", len(count), "| Einsaetze:", sum(count.values()))
MARK = {"KERN": "!", "UMFELD": "+", "KOLORIT": "~"}
FMARK = {"PL": "(Pl)", "KOMP": "(Komp)"}
from wordcheck import lade_kennzeichen
KENNZ = lade_kennzeichen()
HERE = os.path.dirname(os.path.abspath(__file__))
WORTSCHATZ = {d["w"] for f in ("words_v3.json", "fallback_v3.json")
              for d in json.load(open(os.path.join(HERE, f), encoding="utf-8"))}


def zeige(w):
    f = FORM.get(w)
    marke = FMARK.get(f, "")
    if not f and plural_verdacht(w, WORTSCHATZ):
        marke = "(Pl?)"          # Verdacht, kein Befund - bitte selbst pruefen
    # Pflichtzusatz gleich hier anzeigen, nicht erst beim Rendern melden:
    # die Frage soll ihn von Anfang an tragen.
    zus = KENNZ.get(w)
    if zus:
        marke += zus
    return (w + (MARK.get(stufe(tm[w][2]), "") if w in tm else "") + marke)


print("FEHLT:", " ".join(zeige(w) for w in fehlt))
print("Legende: ! Kernbegriff (Frage muss thematisch sein) | "
      "+ Umfeld (thematisch erwuenscht) | ~ Kolorit (thematische Frage "
      "nur, wenn sie nicht gezwungen wirkt) | ohne Zeichen: freie Frage")
print("Formen: (Pl) Mehrzahl - Frage muss den Plural erkennen lassen, "
      "notfalls mit dem Zusatz (Pl.) | (Komp) Komparativ - Frage selbst "
      "in der Steigerungsform, z. B. dichter -> NAEHER")
print("(engl.) / (Abk.) hinter einem Wort: dieser Zusatz MUSS in der Frage "
      "stehen (Quelle kennzeichen.txt).")
print("(Pl?) = Formverdacht aus der Heuristik, kein Befund. Pruefe das Wort "
      "und trage das Ergebnis in formen.txt ein (WORT PL | WORT SG). Ein "
      "Plural ist KEIN Sperrgrund - er verlangt nur eine Frage in der "
      "Mehrzahl, notfalls mit dem Zusatz (Pl.).")
print("VARIANTE:", " ".join(f"{w}:{n}/{h}" for w, n, h in var))
print("AKTIVE THEMEN:", " ".join(theme_names()) or "(keine)")


# --------------------------------------------------------------------------
# Pruefung der Fassung, die beim Rendern tatsaechlich gewaehlt wird.
#
# render_book.variants() sortiert die Fassungen eines Wortes um: zuerst die an
# ein aktives Thema gebundenen, dann die neutralen; Fassungen fremder Themen
# fallen ganz heraus. Welche Fassung auf einer Seite steht, entscheidet danach
# der Einsatzzaehler des Wortes in der Reihenfolge der Seiten. Diese Auswahl
# wird hier eins zu eins nachgebildet, damit zwei Faelle vor dem Rendern
# auffallen statt danach:
#
#   KERNBEGRIFF MIT NEUTRALER FRAGE
#       Das Wort ist Kern eines Themas, die gewaehlte Fassung ist aber an kein
#       Thema des Buches gebunden. Im ersten Band stand GITTER als Kernbegriff
#       von SALZGITTERBAD mit "Staebe vor dem Fenster" im Buch.
#   ALLE FASSUNGEN BUCHFREMD
#       Saemtliche Fassungen haengen an Themen, die es in diesem Buch nicht
#       gibt. render_book.py setzt dann das Loesungswort selbst in die Zelle.
#
# Die Auswahl richtet sich nach dem Zaehler der Seitenfolge, nicht nach
# used_words.json: das Konto zaehlt auch Einsaetze aus frueheren Baenden mit
# und wuerde einen anderen Index liefern als der Renderlauf.
THEMEN_AKTIV = set(theme_names())


def _fassungen(wort):
    """Wie render_book.variants, aber mit Themenbindung je Fassung."""
    roh = C.get(wort)
    if not roh:
        return None, False
    passend, neutral, fremd = [], [], 0
    for v in roh:
        if isinstance(v, dict):
            text, t = v.get("c", ""), v.get("t")
            if t and t in THEMEN_AKTIV:
                passend.append((text, t))
            elif not t:
                neutral.append((text, None))
            else:
                fremd += 1
        else:
            neutral.append((v, None))
    reihe = passend + neutral
    return (reihe or None), (fremd > 0 and not reihe)


neutral_kern, nur_fremd, zaehler = [], [], {}
for f in sorted(glob.glob(os.path.join(PUZZLE_DIR, "*.pkl"))):
    nr = int(os.path.basename(f)[:2])
    lay, _ = pickle.load(open(f, "rb"))
    for e in lay.entries:
        reihe, buchfremd = _fassungen(e.word)
        if buchfremd:
            nur_fremd.append((nr, e.word))
            continue
        if not reihe:
            continue                      # gar keine Frage - steht in FEHLT
        k = zaehler.get(e.word, 0)
        zaehler[e.word] = k + 1
        text, thema = reihe[k % len(reihe)]
        if thema is None and e.word in tm and stufe(tm[e.word][2]) == "KERN":
            neutral_kern.append((nr, e.word, tm[e.word][0], text))

print()
print(f"KERNBEGRIFF MIT NEUTRALER FRAGE: {len(neutral_kern)}")
for nr, w, th, text in neutral_kern:
    print(f"  {nr:02d} {w:16s} {th:14s} {text!r}")
if neutral_kern:
    print("  -> thematische Fassung ergaenzen (fitcheck.py --eintragen) und "
          "an das Thema binden; die neutrale Fassung bleibt stehen.")
print(f"ALLE FASSUNGEN BUCHFREMD: {len(nur_fremd)}")
for nr, w in sorted(set(nur_fremd)):
    print(f"  {nr:02d} {w}")
if nur_fremd:
    print("  -> ohne neutrale oder passende Fassung setzt render_book.py das "
          "Loesungswort in die Zelle.")
