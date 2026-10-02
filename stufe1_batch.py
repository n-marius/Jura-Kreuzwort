"""Stufe 1 fuer viele Woerter auf einmal - Lexikon wird nur einmal geladen."""
import sys, os, json, pickle, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skanvord"))
import layout  # noqa
import core

lex, tm, prim, rank = core.build_lexicon()
plan = json.load(open("plan.json", encoding="utf-8"))

auftraege = [tuple(x.split(":")) for x in sys.argv[1:]]
for nr_s, alt in auftraege:
    nr = int(nr_s)
    lay, grid = pickle.load(open(f"puzzles/{nr:02d}.pkl", "rb"))
    ziel = [e for e in lay.entries if e.word == alt]
    if not ziel:
        print(f"{nr:02d} {alt:11s} steht nicht im Raster"); continue
    e = ziel[0]
    schutz = set(plan.get(str(nr), {}).get("pflicht", [])) | set(plan.get(str(nr), {}).get("weich", []))
    if alt in schutz:
        print(f"{nr:02d} {alt:11s} VORGABEWORT, unantastbar"); continue
    zahl = collections.Counter()
    for x in lay.entries:
        for c in x.cells(): zahl[c] += 1
    muster = [grid.get(c) if zahl[c] >= 2 else None for c in e.cells()]
    mstr = "".join(ch or "_" for ch in muster)
    belegt = {x.word for x in lay.entries}
    kand = sorted(lex.match(muster) - belegt)
    info = []
    for k in kand:
        t = tm.get(k)
        info.append(k + (f"({t[1]} {t[2]:.2f})" if t else ""))
    print(f"{nr:02d} {alt:11s} {mstr:12s} " + (", ".join(info) if kand else "— kein Kandidat"))
