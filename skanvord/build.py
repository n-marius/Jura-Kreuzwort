"""Pipeline: Layout erzeugen -> fuellen -> bestes Ergebnis waehlen."""
import sys, json, pickle
sys.path.insert(0, "/home/claude/skanvord")
from layout import generate
from fill import Lexicon, fill


def load_de(max_rank=20000):
    data = json.load(open("/home/claude/wordlist_de.json", encoding="utf-8"))
    pool = [d for d in data if d["rank"] < max_rank]
    lex = Lexicon([d["w"] for d in pool],
                  {d["w"]: 1.0 / (1 + d["rank"] / 1500) for d in pool})
    rank = {d["w"]: d["rank"] for d in pool}
    return lex, rank


def build(H=9, W=9, density=0.20, seeds=range(12), forced=None,
          lex=None, rank=None, iters=15000):
    best = None
    for s in seeds:
        lay, info = generate(H, W, density, iters=iters, seed=s)
        if info["matched"] != info["entries"] or info["uncovered"]:
            continue
        ok = False
        for fs in range(3):
            try:
                ok, grid, nodes = fill(lay, lex, forced=forced,
                                       seed=s * 100 + fs, max_nodes=120000)
            except (RecursionError, TimeoutError):
                ok = False
            if ok:
                break
        if not ok:
            print(f"  seed {s}: Layout ok ({info['entries']} Eintraege), Fuellung fehlgeschlagen")
            continue
        avg = sum(rank.get(e.word, 99999) for e in lay.entries) / len(lay.entries)
        print(f"  seed {s}: {info['entries']} Eintraege, Bloecke {info['blocks']}, "
              f"mittl. Haeufigkeitsrang {avg:.0f}")
        if best is None or avg < best[0]:
            best = (avg, lay, grid, s)
    return best


if __name__ == "__main__":
    lex, rank = load_de()
    best = build(lex=lex, rank=rank)
    avg, lay, grid, s = best
    pickle.dump((lay, grid), open("/home/claude/puzzle.pkl", "wb"))
    print("gewaehlt: seed", s)
    for e in sorted(lay.entries, key=lambda e: (e.r, e.c)):
        print(f"{e.direction} r{e.r} c{e.c} L{e.length} {e.arrow:2s} {e.word}")
