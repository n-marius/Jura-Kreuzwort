"""Fuellen der Eintraege mit Woertern (Constraint Satisfaction).

Nur echte Kreuzungen sind Constraints - Nachbarschaften ohne Pfeil bleiben frei.
Das macht das Problem deutlich leichter als ein klassisches Kreuzwortraetsel.
"""
from __future__ import annotations
import os, random, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wordcheck import stamm as _stamm            # noqa: E402


class Lexicon:
    """Musterindex: (Laenge, Position, Buchstabe) -> Menge von Wortindizes."""

    def __init__(self, words, weights=None):
        self.words = list(words)
        self.weights = weights or {w: 1.0 for w in self.words}
        self.by_len = {}
        self.idx = {}
        for w in self.words:
            L = len(w)
            self.by_len.setdefault(L, set()).add(w)
            for p, ch in enumerate(w):
                self.idx.setdefault((L, p, ch), set()).add(w)

    def match(self, pattern):
        """pattern: Liste aus Buchstaben oder None."""
        L = len(pattern)
        cands = None
        for p, ch in enumerate(pattern):
            if ch is None:
                continue
            s = self.idx.get((L, p, ch))
            if not s:
                return set()
            cands = s if cands is None else (cands & s)
            if not cands:
                return set()
        return set(self.by_len.get(L, ())) if cands is None else cands


KAPPE = 200


def fill(layout, lexicon, forced=None, seed=None, max_nodes=400000,
         forced_slots=3,
         tier_bonus=None, stamm_sperre=True):
    """stamm_sperre: je Raster nur ein Eintrag pro Wortstamm.

    Ohne sie stehen EKEL und EKLIG oder BUND und BUENDE nebeneinander im
    selben Raetsel. Die Sperre wirkt beim Kandidatenfilter, nicht erst bei
    der Nachpruefung, und kostet nur einen Mengenvergleich je Slot.
    """
    rng = random.Random(seed)
    entries = layout.entries
    cellmap = {}                      # (r,c) -> [(entry_idx, pos), ...]
    for i, e in enumerate(entries):
        for p, cell in enumerate(e.cells()):
            cellmap.setdefault(cell, []).append((i, p))

    for e in entries:                 # Zustand fruehrer Versuche loeschen
        e.word = None
    neigh = {i: sorted({j for cell in entries[i].cells()
                        for j, _ in cellmap[cell] if j != i})
             for i in range(len(entries))}
    grid = {}                         # (r,c) -> Buchstabe
    used = set()
    knotengrenze = [False]
    stamm_zaehler = {}                # Wortstamm -> Anzahl im Raster
    # Die Staemme einmal fuer das ganze Lexikon ausrechnen. wordcheck.stamm
    # laeuft ueber zwei Dutzend Endungen; je Kandidat und Suchknoten aufgerufen
    # kostet das ein Vielfaches der eigentlichen Suche.
    stamm_von = {w: _stamm(w) for w in lexicon.words} if stamm_sperre else {}
    forced = list(forced or [])
    nodes = [0]

    def _st(w):
        st = stamm_von.get(w)
        return _stamm(w) if st is None else st       # Pflichtwoerter

    def _stamm_auf(w):
        if stamm_sperre:
            st = _st(w)
            stamm_zaehler[st] = stamm_zaehler.get(st, 0) + 1

    def _stamm_ab(w):
        if stamm_sperre:
            st = _st(w)
            if stamm_zaehler.get(st, 0) <= 1:
                stamm_zaehler.pop(st, None)
            else:
                stamm_zaehler[st] -= 1

    def pattern(i):
        return [grid.get(cell) for cell in entries[i].cells()]

    def place(i, word):
        changed = []
        for cell, ch in zip(entries[i].cells(), word):
            if cell not in grid:
                grid[cell] = ch
                changed.append(cell)
        return changed

    def unplace(changed):
        for cell in changed:
            del grid[cell]

    def candidates(i):
        """Kandidaten ohne Stammfilter - Grundlage der MRV-Auswahl.

        MRV ist eine Heuristik; eine leicht zu hohe Zahl schadet ihr nicht.
        Der Stammfilter greift erst beim tatsaechlichen Setzen (siehe solve),
        weil candidates() je Knoten fuer jeden offenen Slot laeuft.
        """
        if entries[i].word:
            return []
        # gesperrt: Themenwoerter, die auf einer der letzten Seiten standen
        # oder ihre Obergrenze erreicht haben (core.set_weights).
        return (lexicon.match(pattern(i)) - used
                - getattr(lexicon, "gesperrt", set()))

    def score(w):
        base = lexicon.weights.get(w, 1.0)
        return base * (1 + rng.random() * 0.35)

    def solve(remaining):
        nodes[0] += 1
        if nodes[0] > max_nodes:
            raise TimeoutError
        if not remaining:
            return True
        # MRV
        best_i, best_cs = None, None
        for i in remaining:
            cs = candidates(i)
            if best_cs is None or len(cs) < len(best_cs):
                best_i, best_cs = i, cs
                if len(cs) == 0:
                    break
        if not best_cs:
            return False
        rest = [i for i in remaining if i != best_i]
        if stamm_sperre and stamm_zaehler:
            best_cs = [w for w in best_cs
                       if stamm_von.get(w, "") not in stamm_zaehler]
            if not best_cs:
                return False
        # Kandidatenkappung: fuehren die bestbewerteten Woerter eines Slots
        # alle in Sackgassen, bleibt der Rest ungeprueft und der Versuch
        # scheitert. 220 statt 150 gibt etwas mehr Luft.
        for w in sorted(best_cs, key=lambda x: -score(x))[:KAPPE]:
            ch = place(best_i, w)
            entries[best_i].word = w
            used.add(w)
            _stamm_auf(w)
            # Vorwaertspruefung. Erste Ebene immer: hat ein direkter Nachbar
            # gar keinen Kandidaten mehr, ist die Belegung tot. Zweite Ebene
            # nur, wenn die erste eng wird (ein Nachbar mit hoechstens drei
            # Kandidaten) - sonst kostet die Pruefung mehr als sie spart.
            dead, eng = False, False
            for j in neigh[best_i]:
                if entries[j].word is not None:
                    continue
                cj = lexicon.match(pattern(j)) - used
                if not cj:
                    dead = True
                    break
                if len(cj) <= 3:
                    eng = True
            if not dead and eng:
                for j in neigh[best_i]:
                    if entries[j].word is not None:
                        continue
                    for k in neigh[j]:
                        if k == best_i or entries[k].word is not None:
                            continue
                        if not (lexicon.match(pattern(k)) - used):
                            dead = True
                            break
                    if dead:
                        break
            if not dead and solve(rest):
                return True
            used.discard(w)
            _stamm_ab(w)
            entries[best_i].word = None
            unplace(ch)
        return False

    # --- Vorgabewoerter zuerst auf passende Slots verteilen -----------------
    def assign_forced(k, remaining_slots):
        if k == len(forced):
            try:
                return solve([i for i in range(len(entries))
                              if entries[i].word is None])
            except TimeoutError:
                knotengrenze[0] = True     # nicht Sackgasse, sondern Budget
                return False
        w = forced[k]
        slots = [i for i in remaining_slots if entries[i].length == len(w)]
        rng.shuffle(slots)
        # Jeder Platzierungsversuch zieht eine vollstaendige Fuellung nach sich.
        # Alle passenden Slots durchzuprobieren vervielfacht die Laufzeit, ohne
        # viel zu bringen - make_puzzle startet ohnehin dutzende Fuellversuche
        # mit neuem Zufall. Deshalb nur wenige Slots je Versuch.
        slots = slots[:forced_slots]
        for i in slots:
            pat = pattern(i)
            if any(a is not None and a != b for a, b in zip(pat, w)):
                continue
            ch = place(i, w)
            entries[i].word = w
            used.add(w)
            _stamm_auf(w)
            dead = any(entries[j].word is None
                       and any(cell in grid for cell in entries[j].cells())
                       and not (lexicon.match(pattern(j)) - used)
                       for j in range(len(entries)))
            if not dead and assign_forced(k + 1,
                                          [s for s in remaining_slots if s != i]):
                return True
            used.discard(w)
            _stamm_ab(w)
            entries[i].word = None
            unplace(ch)
        return False

    deepest = [0]
    # knotengrenze wird gesetzt, wenn der Versuch am Budget scheitert und
    # nicht daran, dass die Suche erschoepft ist. core.make_puzzle zaehlt
    # beides getrennt - sonst sieht jeder Fehlschlag gleich aus.
    _orig_solve = solve

    def solve(remaining):
        deepest[0] = max(deepest[0], len(entries) - len(remaining))
        return _orig_solve(remaining)

    ok = assign_forced(0, list(range(len(entries))))
    return ok, grid, (nodes[0], deepest[0], knotengrenze[0])
