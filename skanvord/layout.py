"""Layout-Generator fuer Schwedenraetsel (Skanvord).

Modell
------
Raster H x W. Jede Zelle ist entweder Frageblock (True) oder Buchstabenzelle.
Ein Eintrag ist ein maximaler Lauf von Buchstabenzellen der Laenge >= MIN_LEN.
Jeder Eintrag braucht genau einen Frageblock als "Absender"; ein Frageblock
kann hoechstens MAX_PER_CLUE Eintraege bedienen.

Pfeiltypen
----------
 R   Frageblock links vom Wortanfang, Pfeil nach rechts        -> waagerecht
 DR  Frageblock ueber dem Wortanfang, Pfeil runter+rechts      -> waagerecht
 D   Frageblock ueber dem Wortanfang, Pfeil nach unten         -> senkrecht
 RD  Frageblock links vom Wortanfang, Pfeil rechts+runter      -> senkrecht
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field

MIN_LEN = 4          # kuerzeste zugelassene Antwort (Buch: 4)
STRAFE_L4 = 8.0      # Strafpunkte je Vierer-Slot, moderat
STRAFE_L5 = 2.0      # je Fuenfer-Slot, minimal
MAX_LEN = 30
MAX_PER_CLUE = 1
MIN_CROSS = 0.58     # Mindestanteil gekreuzter Buchstabenzellen


@dataclass
class Entry:
    r: int
    c: int
    direction: str          # 'H' oder 'V'
    length: int
    clue_rc: tuple | None = None
    arrow: str | None = None
    word: str | None = None
    clue: str = ""

    def cells(self):
        if self.direction == "H":
            return [(self.r, self.c + i) for i in range(self.length)]
        return [(self.r + i, self.c) for i in range(self.length)]


@dataclass
class Layout:
    H: int
    W: int
    blocks: set = field(default_factory=set)     # (r,c) der Frageblöcke
    entries: list = field(default_factory=list)

    def is_block(self, r, c):
        return (r, c) in self.blocks


# --------------------------------------------------------------------------
# Läufe und Kandidaten
# --------------------------------------------------------------------------
def _runs(H, W, blocks):
    out = []
    for r in range(H):
        c = 0
        while c < W:
            if (r, c) in blocks:
                c += 1
                continue
            s = c
            while c < W and (r, c) not in blocks:
                c += 1
            out.append(("H", r, s, c - s))
    for c in range(W):
        r = 0
        while r < H:
            if (r, c) in blocks:
                r += 1
                continue
            s = r
            while r < H and (r, c) not in blocks:
                r += 1
            out.append(("V", s, c, r - s))
    return out


W_GLOBAL = [0]


def _candidates(e: Entry, blocks):
    """Mögliche Frageblöcke für einen Eintrag, als (rc, arrow)."""
    out = []
    if e.direction == "H":
        if e.c > 0 and (e.r, e.c - 1) in blocks:
            out.append(((e.r, e.c - 1), "R"))
        if e.r > 0 and (e.r - 1, e.c) in blocks:
            out.append(((e.r - 1, e.c), "DR"))
    else:
        if e.r > 0 and (e.r - 1, e.c) in blocks:
            out.append(((e.r - 1, e.c), "D"))
        if e.c > 0 and (e.r, e.c - 1) in blocks:
            out.append(((e.r, e.c - 1), "RD"))
        if e.c + 1 < W_GLOBAL[0] and (e.r, e.c + 1) in blocks:
            out.append(((e.r, e.c + 1), "LD"))
    return out


# --------------------------------------------------------------------------
# Zuordnung Eintrag -> Frageblock (bipartites Matching, Kapazität 2)
# --------------------------------------------------------------------------
def _match(entries, blocks, priority=()):
    cand = [_candidates(e, blocks) for e in entries]
    slot_owner = {}          # (rc, k) -> entry index

    def try_assign(i, seen):
        for rc, arrow in cand[i]:
            for k in range(MAX_PER_CLUE):
                key = (rc, k)
                if key in seen:
                    continue
                seen.add(key)
                if key not in slot_owner or try_assign(slot_owner[key], seen):
                    slot_owner[key] = i
                    entries[i].clue_rc, entries[i].arrow = rc, arrow
                    return True
        return False

    order = [i for i in range(len(entries)) if i in priority] + \
            sorted((i for i in range(len(entries)) if i not in priority),
                   key=lambda i: len(cand[i]))
    ok = 0
    for i in order:
        if try_assign(i, set()):
            ok += 1
    return ok


# --------------------------------------------------------------------------
# Bewertung
# --------------------------------------------------------------------------
def evaluate(H, W, blocks, target_density=0.18, free_rows=(), required=(),
             slots3=0):
    W_GLOBAL[0] = W
    entries = [Entry(r, c, d, L) for d, r, c, L in _runs(H, W, blocks)
               if L >= MIN_LEN
               and not (d == "V" and any(x in free_rows
                                         for x in range(r, r + L)))]
    for e in entries:
        e.clue_rc = None
    prio = {i for i, e in enumerate(entries)
            if e.direction == "H" and e.r in free_rows and e.length == W}
    matched = _match(entries, blocks, prio)

    covered = set()
    for e in entries:
        if e.clue_rc is not None:
            covered.update(e.cells())
    letters = {(r, c) for r in range(H) for c in range(W)
               if (r, c) not in blocks}
    uncovered = len(letters - covered)

    pen = 0.0
    for e in entries:                         # Laeufe ohne Frage bleiben
        if e.clue_rc is None:                 # als freie Buchstabenfolge stehen
            if e.direction == "H" and e.r in free_rows and e.length == W:
                pen += 3000               # Zwangszeile MUSS eine Frage haben
            else:
                pen += 9 * e.length

    pen += 400 * uncovered                    # tote Buchstabenzellen

    # Frageblöcke ohne Aufgabe
    used = {e.clue_rc for e in entries if e.clue_rc}
    pen += 900 * len(blocks - used)

    # Dichte
    pen += 400 * abs(len(blocks) / (H * W) - target_density)

    # Längenverteilung: 3..8 gut, darueber zunehmend schlecht
    for e in entries:
        if e.direction == "H" and e.r in free_rows and e.length == W:
            continue                      # Zwangszeile: von der Strafe befreit
        if e.length >= 10:
            pen += 4 * (e.length - 9) ** 2
        elif e.length <= 5:
            pen += {3: 20.0, 4: 7.0, 5: 2.0}[e.length]

    # Senkrechte, die die Zwangszeile durchschneiden, sind unbrauchbar
    for d, r, c, L in _runs(H, W, blocks):
        if d == "V" and any(x in free_rows for x in range(r, r + L)) and L >= 3:
            pen += 7 * L

    # Waagerechte und Senkrechte im Gleichgewicht halten
    nh = sum(1 for e in entries if e.clue_rc and e.direction == "H")
    nv = sum(1 for e in entries if e.clue_rc and e.direction == "V")
    pen += 6 * abs(nh - nv)

    # Dreibuchstabige Slots: nur so viele, wie Vorgabewoerter dieser Laenge da
    # sind. Der Fuellwortschatz beginnt bei vier Buchstaben, jeder ueberzaehlige
    # Dreier-Slot waere unfuellbar; jeder fehlende macht das Vorgabewort
    # unplatzierbar. Deshalb Abweichung in beide Richtungen bestrafen.
    n3 = sum(1 for e in entries if e.clue_rc and e.length == 3)
    if n3 != slots3:
        pen += 900 * abs(n3 - slots3)

    # geforderte Slotlaengen bereitstellen
    if required:
        avail = sorted(e.length for e in entries if e.clue_rc)
        for need in sorted(required, reverse=True):
            if need in avail:
                avail.remove(need)
            else:
                pen += 500

    # Slotlaengen: kurze Slots ganz leicht bremsen. Drei Viertel aller Slots
    # haben vier bis sechs Zeichen, was den Kurzwortanteil der Antworten
    # bestimmt - der Loeser kann in einen Vierer nichts Laengeres schreiben.
    # Da Themenvokabular ueberwiegend lang ist, haengt daran auch der
    # Themenanteil. Vorsichtig dosiert: zu harte Strafen kosten Eintraege und
    # Kreuzungsrate.
    pen += STRAFE_L4 * sum(1 for e in entries if e.clue_rc and e.length == 4)
    pen += STRAFE_L5 * sum(1 for e in entries if e.clue_rc and e.length == 5)

    # Verteilung: jedes 3x3-Fenster soll mindestens einen Block enthalten
    for r in range(H - 2):
        for c in range(W - 2):
            if not any((r + i, c + j) in blocks for i in range(3) for j in range(3)):
                pen += 25

    # Optik: benachbarte Frageblöcke
    pen += 2.5 * sum(1 for (r, c) in blocks
                     if (r, c + 1) in blocks or (r + 1, c) in blocks)

    # Kreuzungen belohnen
    cnt = {}
    for e in entries:
        if e.clue_rc:
            for cell in e.cells():
                cnt[cell] = cnt.get(cell, 0) + 1
    cross = sum(1 for v in cnt.values() if v >= 2)
    ratio = cross / max(1, len(letters))
    pen += 1500 * max(0.0, MIN_CROSS - ratio)      # Kreuzungsrate hart nach unten
    pen -= 40 * min(ratio, 0.75)                   # darueber hinaus belohnt
    for e in entries:                              # nur extreme Saettigung bremsen
        if e.clue_rc:
            sat = sum(1 for cell in e.cells() if cnt[cell] >= 2) / e.length
            pen += 25 * max(0.0, sat - 0.80) * e.length

    # Randregel: in Spalte 0 und Zeile 0 nur Frageblock oder Wortanfang
    starts = {(e.r, e.c) for e in entries if e.clue_rc}
    for r in range(H):
        if (r, 0) not in blocks and (r, 0) not in starts:
            pen += 2000
    for c in range(W):
        if (0, c) not in blocks and (0, c) not in starts:
            pen += 2000

    return pen, entries, matched, uncovered


def generate(H=9, W=9, density=0.18, iters=40000, seed=None,
             free_rows=(), required=(), slots3=0):
    rng = random.Random(seed)
    fixed = {(r - 1, 0) for r in free_rows if r > 0}
    cells = [(r, c) for r in range(H) for c in range(W)
             if r not in free_rows and (r, c) not in fixed]
    n = max(1, round(H * W * density)) - len(fixed)
    blocks = set(rng.sample(cells, n)) | fixed
    best_pen, *_ = evaluate(H, W, blocks, density, free_rows, required, slots3)
    cur = set(blocks)
    cur_pen = best_pen
    best = set(blocks)

    T0, T1 = 6.0, 0.05
    for it in range(iters):
        T = T0 * (T1 / T0) ** (it / iters)
        new = set(cur)
        movable = sorted(new - fixed)
        if rng.random() < 0.6 and movable:
            new.remove(rng.choice(movable))
            new.add(rng.choice([c for c in cells if c not in new]))
        elif rng.random() < 0.5:
            new.add(rng.choice([c for c in cells if c not in new]))
        elif movable:
            new.remove(rng.choice(movable))
        pen, *_ = evaluate(H, W, new, density, free_rows, required, slots3)
        if pen < cur_pen or rng.random() < pow(2.718, -(pen - cur_pen) / T):
            cur, cur_pen = new, pen
            if pen < best_pen:
                best, best_pen = set(new), pen

    # --- Reparatur: verbliebene unversorgte Zellen gezielt beseitigen ------
    pen, entries, matched, uncovered = evaluate(H, W, best, density,
                                                free_rows, required, slots3)
    def _randfehler(bl, ents):
        st = {(e.r, e.c) for e in ents if e.clue_rc}
        return (sum(1 for r in range(H)
                    if (r, 0) not in bl and (r, 0) not in st)
                + sum(1 for c in range(W)
                      if (0, c) not in bl and (0, c) not in st))

    for _ in range(80):
        if uncovered == 0 and _randfehler(best, entries) == 0:
            break
        covered = set()
        for e in entries:
            if e.clue_rc:
                covered.update(e.cells())
        starts = {(e.r, e.c) for e in entries if e.clue_rc}
        bad = [(r, c) for r in range(H) for c in range(W)
               if (r, c) not in best and (r, c) not in covered
               and r not in free_rows]
        bad += [(r, 0) for r in range(H)
                if (r, 0) not in best and (r, 0) not in starts
                and r not in free_rows]
        bad += [(0, c) for c in range(W)
                if (0, c) not in best and (0, c) not in starts
                and 0 not in free_rows]
        if not bad:
            break
        improved = False
        for cell in bad:
            for cand in ({cell} | {b for b in best if b not in fixed
                                   and abs(b[0] - cell[0]) + abs(b[1] - cell[1]) <= 2}):
                trial = (best | {cell}) if cand == cell else (best - {cand})
                p, en, ma, un = evaluate(H, W, trial, density, free_rows, required, slots3)
                if un < uncovered or (un == uncovered and p < pen - 1e-9):
                    best, pen, entries, uncovered = trial, p, en, un
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break
    pen, entries, matched, uncovered = evaluate(H, W, best, density,
                                                free_rows, required, slots3)
    lay = Layout(H, W, best, [e for e in entries if e.clue_rc is not None])
    return lay, dict(penalty=round(pen, 1), entries=len(entries),
                     matched=matched, uncovered=uncovered,
                     blocks=len(best))
