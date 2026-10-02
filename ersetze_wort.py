"""Ersetzt ein einzelnes Wort in einem fertigen Raetsel, ohne die Seite neu zu bauen.

  python ersetze_wort.py 15 ASOW              # zeigt die moeglichen Ersatzwoerter
  python ersetze_wort.py 15 ASOW --nimm KAHN  # setzt den Ersatz und pflegt das Konto

Stufe 1 dieses Werkzeugs: nur der eine Slot wird neu belegt, alle Kreuzungs-
buchstaben bleiben stehen. Findet sich dort kein brauchbares Wort, meldet das
Skript das und die naechste Stufe ist dran (Umgebung einbeziehen, wie es
core.improve_theme tut) - erst danach lohnt ein vollstaendiger Neubau.

Das Konto wird mitgefuehrt: das alte Wort wird ausgetragen, das neue eingetragen.
"""
import sys, os, json, time, pickle, collections

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skanvord"))
import layout  # noqa: F401  (wird fuer das Entpickeln gebraucht)
import core
from themes import theme_map, stufe

# Zeitdeckel der beiden Suchstufen. Laeuft eine Stufe ab, wird die Suche
# sofort abgebrochen - auch mitten in der Rekursion - und die naechste Stufe
# uebernimmt. Eine Stufe 4 gibt es nicht mehr; nach Stufe 3 folgt der Neubau.
ZEIT_STUFE2 = 360          # 6 Minuten
ZEIT_STUFE3 = 720          # 12 Minuten


class _Zeitaus(Exception):
    """Wird aus der Rekursion geworfen, wenn der Zeitdeckel abgelaufen ist."""

a = [x for x in sys.argv[1:] if not x.startswith("--")]
if len(a) < 2:
    print(__doc__)
    raise SystemExit(1)
nr, alt = int(a[0]), a[1].upper()
nimm = None
if "--nimm" in sys.argv:
    nimm = sys.argv[sys.argv.index("--nimm") + 1].upper()

pfad = f"puzzles/{nr:02d}.pkl"
lay, grid = pickle.load(open(pfad, "rb"))
ziel = [e for e in lay.entries if e.word == alt]
if not ziel:
    print(f"{alt} steht nicht in Raetsel {nr:02d}.")
    raise SystemExit(1)
if len(ziel) > 1:
    print(f"{alt} steht mehrfach in Raetsel {nr:02d} - bitte von Hand loesen.")
    raise SystemExit(1)
e = ziel[0]

# Welche Zellen des Slots sind Kreuzungen? Nur die muessen erhalten bleiben.
zahl = collections.Counter()
for x in lay.entries:
    for c in x.cells():
        zahl[c] += 1
muster = [grid.get(c) if zahl[c] >= 2 else None for c in e.cells()]

lex, tm, prim, rank = core.build_lexicon()
led = json.load(open("used_words.json", encoding="utf-8"))

# Vorgabewoerter dieser Seite sind unantastbar - sie duerfen weder ersetzt
# noch als Nachbar mitgeleert werden.
plan = json.load(open("plan.json", encoding="utf-8"))
schutz = set(plan.get(str(nr), {}).get("pflicht", [])) | set(
    plan.get(str(nr), {}).get("weich", []))
if alt in schutz:
    print(f"{alt} ist Vorgabewort von Seite {nr:02d} und wird nicht ersetzt.")
    raise SystemExit(1)
belegt = {x.word for x in lay.entries}
kand = sorted(lex.match(muster) - belegt)

def stufe2(sperre, seed=0, group_max=7, runden=400, ringe=1, zeitdeckel=None):
    _t0 = time.time()
    _ende = (_t0 + zeitdeckel) if zeitdeckel else None
    """Slot samt Nachbarn leeren und neu fuellen - wie core.improve_theme.

    Uebernommen wird die erste Loesung, in der das beanstandete Wort nicht mehr
    vorkommt. Unter mehreren Versuchen gewinnt die mit den meisten Themenwoertern.
    """
    import random
    rng = random.Random(seed)
    E = lay.entries
    cellmap = {}
    for i, x in enumerate(E):
        for cell in x.cells():
            cellmap.setdefault(cell, []).append(i)
    neigh = {i: sorted({j for cell in E[i].cells() for j in cellmap[cell] if j != i})
             for i in range(len(E))}
    ziel_i = E.index(e)
    umfeld = set(neigh[ziel_i])
    if ringe >= 2:                        # zweite Kreuzungsebene dazunehmen
        for j in list(umfeld):
            umfeld |= set(neigh[j])
    umfeld.discard(ziel_i)

    def build_grid(words):
        g = {}
        for x, w in zip(E, words):
            if w:
                for cell, ch in zip(x.cells(), w):
                    g[cell] = ch
        return g

    def theme_count(words):
        return sum((2 if tm[w][2] >= 0.8 else 1) for w in words if w in tm)

    words = [x.word for x in E]
    bestes, beste_n = None, -1
    for _ in range(runden):
        if zeitdeckel and time.time() - _t0 > zeitdeckel:
            print("    (Abbruch nach Zeitdeckel)")
            break
        nb = [j for j in sorted(umfeld) if E[j].word not in schutz]
        rng.shuffle(nb)
        group = [ziel_i] + nb[:group_max - 1]
        trial = list(words)
        for j in group:
            trial[j] = None
        g = build_grid(trial)
        used = {w for w in trial if w}

        def solve(k):
            if _ende and time.time() > _ende:
                raise _Zeitaus
            if k == len(group):
                return True
            j = group[k]
            pat = [g.get(cell) for cell in E[j].cells()]
            cs = (lex.match(pat) - used - getattr(lex, "gesperrt", set())
                  - sperre)
            if not cs:
                return False
            order = sorted(cs, key=lambda w: (-(80.0 if (w in tm and tm[w][2] >= 0.8)
                                                else (30.0 if w in tm else 0.0))
                                              - lex.weights.get(w, 0.0)
                                              + rng.random() * 3))[:30]
            for w in order:
                changed = []
                for cell, ch in zip(E[j].cells(), w):
                    if cell not in g:
                        g[cell] = ch
                        changed.append(cell)
                trial[j] = w
                used.add(w)
                if solve(k + 1):
                    return True
                used.discard(w)
                trial[j] = None
                for cell in changed:
                    del g[cell]
            return False

        try:
            gelungen = solve(0)
        except _Zeitaus:
            print(f"    (Zeitdeckel {zeitdeckel:.0f} s waehrend der Suche "
                  f"erreicht - Abbruch, weiter mit der naechsten Stufe)")
            break
        if gelungen:
            n = theme_count(trial)
            if n > beste_n:
                bestes, beste_n = list(trial), n
    return bestes


if nimm is None:
    print(f"Raetsel {nr:02d}, Slot von {alt} ({e.length} Zeichen)")
    print("Muster (Kreuzungen fest):", "".join(ch or "_" for ch in muster))
    if kand and "--stufe2" in sys.argv:
        print(f"Stufe 1 haette {len(kand)} Kandidat(en), --stufe2 erzwingt "
              f"trotzdem die Umgebung.")
        kand = []
    if not kand:
        print("Stufe 1 (nur dieser Slot): kein Ersatz moeglich.")
        if "--stufe2" not in sys.argv:
            print("Naechster Schritt: nochmal mit --stufe2 aufrufen. Dann werden "
                  "der Slot und seine direkten Nachbarn geleert und neu gefuellt.")
            raise SystemExit(2)
        print(f"Stufe 2: Slot und direkte Nachbarn neu belegen "
              f"(hoechstens {ZEIT_STUFE2 // 60} Minuten) ...")
        neu_words = stufe2({alt}, ringe=1, zeitdeckel=ZEIT_STUFE2)
        if neu_words is None:
            print(f"Stufe 3: zweite Kreuzungsebene dazunehmen "
                  f"(hoechstens {ZEIT_STUFE3 // 60} Minuten) ...")
            neu_words = stufe2({alt}, ringe=2, group_max=10, runden=600,
                               zeitdeckel=ZEIT_STUFE3)
        if neu_words is None:
            print("Stufe 3 erfolglos. Eine weitere Suchstufe gibt es nicht; "
                  "naechster Schritt ist der Neubau der Seite - vorher den "
                  "Projektleiter fragen.")
            raise SystemExit(3)
        vorher = [x.word for x in lay.entries]
        geaendert = [(a_, b_) for a_, b_ in zip(vorher, neu_words) if a_ != b_]
        for x, w in zip(lay.entries, neu_words):
            x.word = w
        grid2 = {}
        for x in lay.entries:
            for c, ch in zip(x.cells(), x.word):
                grid2[c] = ch
        pickle.dump((lay, grid2), open(pfad, "wb"))
        core.update_ledger(geaendert)
        print(f"Raetsel {nr:02d}: {len(geaendert)} Wort(e) getauscht:")
        for a_, b_ in geaendert:
            print(f"  {a_} -> {b_}")
        print("Jetzt collect_clues.py laufen lassen und die Fragen nachtragen.")
        raise SystemExit(0)
    for w in kand:
        t = tm.get(w)
        marke = "im Buch" if led.get(w) else ""
        print(f"  {w:16s} {(t[0] if t else '-'):16s} "
              f"{(stufe(t[2]) if t else ''):8s} {marke}")
    print(f"\n{len(kand)} Kandidat(en). Mit --nimm WORT setzen.")
    raise SystemExit(0)

if nimm not in kand:
    print(f"{nimm} passt nicht in den Slot oder steht schon auf der Seite.")
    raise SystemExit(1)

e.word = nimm
for c, ch in zip(e.cells(), nimm):
    grid[c] = ch
# Gitter gegen alle Woerter pruefen, bevor gespeichert wird
for x in lay.entries:
    for c, ch in zip(x.cells(), x.word):
        assert grid.get(c) == ch, f"Gitter passt nicht mehr bei {x.word}"
pickle.dump((lay, grid), open(pfad, "wb"))

core.update_ledger([(alt, nimm)])
print(f"Raetsel {nr:02d}: {alt} -> {nimm}. Konto gepflegt.")
print("Jetzt collect_clues.py laufen lassen und die Frage nachtragen.")
