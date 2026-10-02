"""Erzeugt Layout und Fuellung fuer eine Spanne von Raetseln.

Aufruf:  python book.py 1 10          (Raetsel 1 bis 10)
Liest plan.json, falls vorhanden. Schreibt puzzles/NN.pkl und fuehrt
used_words.json fort. Ausgabe: eine Zeile je Raetsel.

Der Lauf ist auf Dauerbetrieb ausgelegt: fertige Seiten werden uebersprungen,
eine misslungene Seite wird mit verschobenem Rasterfenster wiederholt, und
ein Fehler in einer Seite beendet nicht den ganzen Lauf. "python book.py 1 50"
laeuft damit ohne Eingriff durch und kann nach einem Abbruch mit demselben
Befehl fortgesetzt werden.

Umgebungsvariable SEED_VERSATZ verschiebt das Rasterfenster zusaetzlich, damit
ein Neubau derselben Seite ein anderes Layout bekommt:
    SEED_VERSATZ=100 python book.py 22 22
"""
import sys, os, json, time, pickle, traceback
from core import (build_lexicon, set_weights, make_puzzle,
                  load_ledger, save_ledger, improve_theme, GESAMT_RAETSEL)

SEED_VERSATZ = int(os.environ.get("SEED_VERSATZ", "0"))
VERSUCHE = int(os.environ.get("VERSUCHE", "4"))   # Anlaeufe je Seite, jeder
#                                                  mit um 100 verschobenem
#                                                  Rasterfenster

os.makedirs("puzzles", exist_ok=True)


def _eine_seite(i, versatz, lex, tm, prim, rank, plan, led):
    """Baut genau eine Seite. Rueckgabe (lay, grid, info) oder None."""
    eintrag = plan.get(str(i), [])
    if isinstance(eintrag, dict):                 # neues Format
        pflicht = list(eintrag.get("pflicht", []))
        weich = list(eintrag.get("weich", []))
    else:                                         # altes Format: Liste
        pflicht, weich = list(eintrag), []
    forced = pflicht + weich
    # Themenwoerter der letzten SPERRE_SEITEN Raetsel sperren.
    from core import SPERRE_SEITEN
    vorseiten = []
    for k in range(max(1, i - SPERRE_SEITEN), i):
        vor = f"puzzles/{k:02d}.pkl"
        if os.path.exists(vor):
            vorseiten.append([e.word for e in
                              pickle.load(open(vor, "rb"))[0].entries])
    set_weights(lex, tm, prim, rank, led, fortschritt=i / GESAMT_RAETSEL,
                vorseiten=vorseiten)
    req = tuple(len(w) for w in forced) if forced else ()
    diag = {}
    fenster = range(i * 37 + versatz, i * 37 + versatz + 8)
    res = make_puzzle(lex, tm, prim, fenster, forced=forced or None,
                      required=req, diag=diag, ledger=led)
    # Weiche Vorgaben stufenweise fallen lassen, bevor Pflichtwoerter
    # geopfert werden. So erschwert eine lange Wunschliste die Fuellung
    # nicht, die Pflichtwoerter bleiben aber so lange wie moeglich drin.
    while res is None and weich:
        weich.pop()
        forced = pflicht + weich
        req = tuple(len(w) for w in forced) if forced else ()
        res = make_puzzle(lex, tm, prim, fenster, forced=forced or None,
                          required=req, diag=diag, ledger=led)
    if res is None and forced:                      # zuletzt auch Pflicht
        res = make_puzzle(lex, tm, prim, fenster, diag=diag, ledger=led)
        if res:
            res[2]["vorgaben"] = 0
    return res, diag


def main(a, b):
    lex, tm, prim, rank = build_lexicon()
    plan = json.load(open("plan.json", encoding="utf-8")) if os.path.exists("plan.json") else {}
    led = load_ledger()
    t_lauf = time.time()
    fertig, uebersprungen, gescheitert = [], [], []
    for i in range(a, b + 1):
        pfad = f"puzzles/{i:02d}.pkl"
        if os.path.exists(pfad):
            # Wiederaufnahme nach einem Abbruch: fertige Seiten bleiben stehen,
            # ihre Woerter stehen bereits im Konto.
            uebersprungen.append(i)
            print(f"{i:02d} liegt schon vor - uebersprungen", flush=True)
            continue
        for versuch in range(VERSUCHE):
            versatz = SEED_VERSATZ + 100 * versuch
            t0 = time.time()
            try:
                res, diag = _eine_seite(i, versatz, lex, tm, prim, rank,
                                        plan, led)
            except Exception:
                # Ein Fehler in einer Seite darf den Lauf nicht beenden.
                print(f"{i:02d} FEHLER im Versuch {versuch + 1}/{VERSUCHE} "
                      f"(Versatz {versatz}):", flush=True)
                traceback.print_exc()
                sys.stdout.flush()
                continue
            if res is None:
                print(f"{i:02d} ohne Ergebnis, Versuch {versuch + 1}/"
                      f"{VERSUCHE}, Versatz {versatz}, "
                      f"{time.time() - t0:.0f}s", flush=True)
                continue
            lay, grid, info = res
            info["thematisch"] = sum(1 for e in lay.entries if e.word in tm)
            info["kern"] = sum(1 for e in lay.entries
                               if e.word in tm and tm[e.word][2] >= 0.8)
            pickle.dump((lay, grid), open(pfad, "wb"))
            for e in lay.entries:
                led[e.word] = led.get(e.word, 0) + 1
            save_ledger(led)
            fertig.append(i)
            print(f"{i:02d} seed={info['seed']} n={info['entries']} "
                  f"kern={info.get('kern', 0)} them={info['thematisch']} "
                  f"selten={info['selten']} kreuz={info.get('kreuzrate')} "
                  f"leer={info.get('leer')} vorgaben={info['vorgaben']} "
                  f"wied={sum(1 for e in lay.entries if led.get(e.word, 0) > 1)} "
                  f"{time.time() - t0:.0f}s "
                  f"[{time.strftime('%H:%M:%S')}]", flush=True)
            # Diagnose: warum wurde wie viel verworfen? Erklaert die Laufzeit.
            if diag:
                print("   diag " + " ".join(f"{k}={v}"
                                            for k, v in sorted(diag.items())),
                      flush=True)
            break
        else:
            gescheitert.append(i)
            print(f"{i:02d} FEHLGESCHLAGEN nach {VERSUCHE} Versuchen",
                  flush=True)
    print(f"\nLauf beendet nach {(time.time() - t_lauf) / 60:.0f} min: "
          f"{len(fertig)} neu, {len(uebersprungen)} uebersprungen, "
          f"{len(gescheitert)} gescheitert"
          + (f" -> {gescheitert}" if gescheitert else ""), flush=True)
    return 1 if gescheitert else 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]), int(sys.argv[2])))
