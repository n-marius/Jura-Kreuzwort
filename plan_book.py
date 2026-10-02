"""Verteilt die Wunschwoerter locker ueber das ganze Buch.

Aufruf:  python plan_book.py wunschwoerter.txt 50
Ergebnis: plan.json  {"1": {"pflicht": [...], "weich": [...]}, ...}

Zwei Faelle, beide werden abgedeckt:

  weniger Wunschwoerter als Raetsel - sie werden gleichmaessig ueber die
  gesamte Strecke gestreut, nicht vorne zusammengedraengt. 25 Woerter auf
  50 Raetsel landen also auf 1, 3, 5, ... und nicht auf 1 bis 25.

  mehr Wunschwoerter als Raetsel - je Raetsel gelten hoechstens PFLICHT_MAX
  Woerter als Pflicht, alles Weitere ist "weich": book.py versucht es
  mitzunehmen und laesst es fallen, sobald es die Fuellung blockiert. So
  erschweren viele Wunschwoerter das Fuellen nicht unnoetig.
"""
import sys, json
from core import GRID_W, GRID_H
from themes import _n

MAXLEN = max(GRID_W, GRID_H)          # laengste ueberhaupt platzierbare Antwort
MINLEN = 3                            # Vorgabewoerter duerfen kuerzer sein als
#                                       der Fuellwortschatz (MIN_LEN = 4): fuer
#                                       jedes dreibuchstabige Vorgabewort legt
#                                       core.make_puzzle genau einen Dreier-Slot
#                                       im Raster an.
PFLICHT_MAX = 2                       # harte Vorgaben je Raetsel
WEICH_MAX = 4                         # zusaetzliche weiche Vorgaben je Raetsel


def verteile(words, n):
    """Gleichmaessige Streuung ueber 1..n, unabhaengig von der Wortzahl."""
    plan = {str(i): {"pflicht": [], "weich": []} for i in range(1, n + 1)}
    m = len(words)
    for k, w in enumerate(words):
        # Position im Buch: k-tes von m Woertern faellt auf Raetsel round(...)
        nr = int(k * n / m) + 1 if m > n else round(k * (n - 1) / max(1, m - 1)) + 1
        nr = min(max(nr, 1), n)
        for schritt in range(n):                 # naechstes Raetsel mit Platz
            for kandidat in (nr + schritt, nr - schritt):
                if not 1 <= kandidat <= n:
                    continue
                z = plan[str(kandidat)]
                if len(z["pflicht"]) < PFLICHT_MAX:
                    z["pflicht"].append(w)
                    break
                if len(z["weich"]) < WEICH_MAX:
                    z["weich"].append(w)
                    break
            else:
                continue
            break
    return plan


def main(path, n):
    raw = [w.strip() for w in open(path, encoding="utf-8").read().split() if w.strip()]
    words, drop_long, drop_short, seen = [], [], [], set()
    for w in raw:
        x = _n(w)
        if x in seen:
            continue
        seen.add(x)
        if len(x) > MAXLEN:
            drop_long.append(x)
        elif len(x) < MINLEN:
            drop_short.append(x)
        else:
            words.append(x)
    # lange Woerter zuerst auf die Plaetze, sie sind am sperrigsten; die
    # Streuung ueber das Buch bleibt davon unberuehrt
    words.sort(key=len, reverse=True)
    plan = verteile(words, n)
    json.dump(plan, open("plan.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    pf = sum(len(v["pflicht"]) for v in plan.values())
    we = sum(len(v["weich"]) for v in plan.values())
    belegt = sum(1 for v in plan.values() if v["pflicht"] or v["weich"])
    print(f"verplant {len(words)} Woerter auf {n} Raetsel: "
          f"{pf} Pflicht, {we} weich, {belegt} Raetsel belegt")
    letzte = max((int(k) for k, v in plan.items() if v["pflicht"] or v["weich"]),
                 default=0)
    print(f"letztes belegtes Raetsel: {letzte} von {n}")
    if drop_long:
        print("ZU LANG, entfaellt:", " ".join(drop_long))
    if drop_short:
        print(f"KUERZER ALS {MINLEN}, entfaellt:", " ".join(drop_short))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
