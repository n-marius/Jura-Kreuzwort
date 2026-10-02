"""Rendert das gesamte Buch in eine PDF und prueft alles programmatisch.

Aufruf:  python render_book.py [Zielordner]   (Vorgabe: ./ausgabe)
"""
import glob, os, pickle, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skanvord"))
import layout                                   # noqa
from render2 import wrap, size_for_cap
from reportlab.lib.units import mm
from core import clue_store, CELL_MM, CAP_MM, LINES_MAX
from wordcheck import enthaelt_loesung, kennzeichen_fehlt
from themes import theme_names
from bookpdf import build

_args = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = _args[0] if _args else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "ausgabe")
os.makedirs(OUT, exist_ok=True)
C, THEMES = clue_store(), set(theme_names())
size, width = size_for_cap(CAP_MM), (CELL_MM - 1.0) * mm


def variants(word):
    """Fragevarianten. Zum aktiven Thema passende zuerst, danach themenneutrale.

    Dadurch wird eine themengebundene Variante beim ersten Auftreten des Wortes
    tatsaechlich verwendet und nicht nur mitgefuehrt.
    """
    raw = C.get(word)
    if not raw:
        return None
    passend, neutral = [], []
    for v in raw:
        if isinstance(v, dict):
            text, t = v.get("c", ""), v.get("t")
            if t and t in THEMES:
                passend.append(text)
            elif not t:
                neutral.append(text)
            # Variante eines fremden Themas wird uebergangen
        else:
            neutral.append(v)
    return passend + neutral or None


seen, problem, verraten, puzzles = {}, [], [], []
ohne_zusatz = []
zu_wenig = {}
for f in sorted(glob.glob("puzzles/*.pkl")):
    nr = int(os.path.basename(f)[:2])
    lay, grid = pickle.load(open(f, "rb"))
    for e in lay.entries:
        vs = variants(e.word) or [e.word]
        k = seen.get(e.word, 0)
        seen[e.word] = k + 1
        if k >= len(vs):
            # Das Wort kommt oefter vor, als es Fassungen gibt - die Frage
            # wiederholt sich woertlich. Auffaelliger als das Wort selbst.
            zu_wenig.setdefault(e.word, [len(vs), 0])[1] = k + 1
        e.clue = vs[k % len(vs)]
        given = set(e.clue.replace("\n", " ").split())
        ls = wrap(e.clue, size, width)
        if len(ls) > LINES_MAX or any(l.endswith("-") and l not in given for l in ls):
            problem.append((nr, e.word, e.clue))
        if enthaelt_loesung(e.clue, e.word):
            verraten.append((nr, e.word, e.clue))
        fehlt = kennzeichen_fehlt(e.word, e.clue)
        if fehlt:
            ohne_zusatz.append((nr, e.word, fehlt))
    leer = len(lay.blocks - {e.clue_rc for e in lay.entries})
    zellen = {(r, c) for r in range(lay.H) for c in range(lay.W)} - lay.blocks
    cov = set()
    for e in lay.entries:
        cov.update(e.cells())
    print(f"{nr:02d} n={len(lay.entries)} leereBloecke={leer} ohneEintrag={len(zellen-cov)}")
    puzzles.append((nr, lay, grid))

# Reihenfolge im fertigen Buch: vorne die Seite mit den meisten Salzgitter-
# Woertern, danach die Seiten mit den Wunschwoertern, dann der Rest in der
# bisherigen Folge. Die gedruckte Seitenzahl ist die neue Position.
VORNE = []        # Band 1: [14, 20, 4, 2] - je Buch neu setzen
puzzles = ([p for nr in VORNE for p in puzzles if p[0] == nr]
           + [p for p in puzzles if p[0] not in VORNE])
puzzles = [(i + 1, lay, grid) for i, (_, lay, grid) in enumerate(puzzles)]

nur_los = "--nur-loesungen" in sys.argv
build(puzzles, os.path.join(OUT, "loesungsprobe.pdf" if nur_los
                            else "raetselbuch.pdf"),
      cell_mm=CELL_MM, cap_mm=CAP_MM, lines_max=LINES_MAX,
      nur_loesungen=nur_los)
if zu_wenig:
    print("GLEICHE FRAGE MEHRFACH (weitere Fassung in clues.json anlegen):")
    for w, (hat, braucht) in sorted(zu_wenig.items()):
        print(f"  {w}: {braucht} Einsaetze, nur {hat} Fassung(en)")
if ohne_zusatz:
    print("ZUSATZ FEHLT (engl./Abk./Pl. gehoert in die Frage):")
    for nr, w, z in ohne_zusatz:
        print(f"  {nr:02d} {w} braucht {z}")
print(f"raetselbuch.pdf: {len(puzzles)} Raetselseiten + "
      f"{-(-len(puzzles)//9)} Loesungsseiten")
if problem:
    print("PASST NICHT INS KAESTCHEN:")
    for nr, w, cl in problem:
        print(f"  {nr:02d} {w} = {cl!r}")
if verraten:
    print("FRAGE ENTHAELT DEN WORTSTAMM (pruefen):")
    for nr, w, cl in verraten:
        print(f"  {nr:02d} {w} = {cl!r}")
