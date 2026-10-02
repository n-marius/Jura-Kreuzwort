"""Freies Kreuzwortraetsel: Woerter werden nacheinander auf ein leeres Raster
gelegt. Keine Vollfuellung, keine Frageblöcke.

Regeln fuer eine gueltige Lage
  * jedes neue Wort kreuzt mindestens ein vorhandenes (Zusammenhang)
  * vor dem ersten und hinter dem letzten Buchstaben ist die Zelle frei
  * neue Buchstaben haben quer zur Legerichtung keine Nachbarn
    (keine parallel anliegenden Woerter, nur echte Kreuzungen)
  * beginnen ein waagerechtes und ein senkrechtes Wort in derselben Zelle,
    teilen sie sich eine Nummer (Fragenliste nach Waagerecht/Senkrecht getrennt)
  * je Raster ein Eintrag pro Wortstamm
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field

from layout import Entry
from wordcheck import stamm

LAENGE_BONUS = 0.0    # Legebewertung je Buchstabe (kurze Woerter regelt kurz_strafe)


@dataclass
class KLayout:
    H: int
    W: int
    entries: list = field(default_factory=list)
    blocks: set = field(default_factory=set)   # leer; Kompatibilitaet

    def zellen(self):
        out = set()
        for e in self.entries:
            out.update(e.cells())
        return out


class Zustand:
    def __init__(self, H, W, periode=1):
        self.H, self.W = H, W
        self.periode = periode      # Gitter: waagerecht nur in Zeilen r % periode == 0,
        #                             senkrecht nur in Spalten c % periode == 0
        self.g = {}                 # (r,c) -> Buchstabe
        self.dir = {}               # (r,c) -> {"H","V"}
        self.starts = set()
        self.words = []             # (wort, r, c, dir)
        self.staemme = set()
        self.kreuz = 0
        self.nach_buchstabe = {}    # Buchstabe -> Liste von Zellen
        self.wied = 0               # Woerter, die im Buch schon vorkamen

    def frei(self, r, c):
        return not (0 <= r < self.H and 0 <= c < self.W) or (r, c) not in self.g

    def pruefe(self, w, r, c, d):
        """Anzahl Kreuzungen oder -1, wenn die Lage ungueltig ist."""
        L = len(w)
        if (r if d == "H" else c) % self.periode:
            return -1
        dr, dc = (0, 1) if d == "H" else (1, 0)
        er, ec = r + dr * (L - 1), c + dc * (L - 1)
        if r < 0 or c < 0 or er >= self.H or ec >= self.W:
            return -1
        if not self.frei(r - dr, c - dc) or not self.frei(er + dr, ec + dc):
            return -1
        k = 0
        for i, ch in enumerate(w):
            rr, cc = r + dr * i, c + dc * i
            vorh = self.g.get((rr, cc))
            if vorh is not None:
                if vorh != ch or d in self.dir[(rr, cc)]:
                    return -1
                k += 1
            else:
                if d == "H":
                    if not self.frei(rr - 1, cc) or not self.frei(rr + 1, cc):
                        return -1
                else:
                    if not self.frei(rr, cc - 1) or not self.frei(rr, cc + 1):
                        return -1
        if self.words and k == 0:
            return -1
        if k == L:
            return -1
        return k

    def lege(self, w, r, c, d, k):
        dr, dc = (0, 1) if d == "H" else (1, 0)
        for i, ch in enumerate(w):
            p = (r + dr * i, c + dc * i)
            if p not in self.g:
                self.nach_buchstabe.setdefault(ch, []).append(p)
            self.g[p] = ch
            self.dir.setdefault(p, set()).add(d)
        self.starts.add((r, c))
        self.words.append((w, r, c, d))
        self.staemme.add(stamm(w))
        self.kreuz += k


def _lagen(z, w):
    """Alle gueltigen Lagen eines Wortes: (kreuzungen, r, c, d)."""
    out = []
    gesehen = set()
    for i, ch in enumerate(w):
        for (r, c) in z.nach_buchstabe.get(ch, ()):
            ds = z.dir[(r, c)]
            for d in ("H", "V"):
                if d in ds:
                    continue
                sr, sc = (r, c - i) if d == "H" else (r - i, c)
                if (sr, sc, d) in gesehen:
                    continue
                gesehen.add((sr, sc, d))
                k = z.pruefe(w, sr, sc, d)
                if k > 0:
                    out.append((k, sr, sc, d))
    return out


def _gewichtet(rng, woerter, gewichte, n):
    """n verschiedene Woerter, Ziehung nach Gewicht (Efraimidis-Spirakis)."""
    keyed = []
    for w in woerter:
        g = gewichte.get(w, 0.0)
        if g > 0:
            keyed.append((rng.random() ** (1.0 / g), w))
    keyed.sort(reverse=True)
    return [w for _, w in keyed[:n]]


def aufbau(woerter, gewichte, H, W, rng, stichprobe, max_woerter,
           vorgaben=(), bekannt=frozenset(), wied_max_quote=1.0,
           kurz_strafe=None, periode=1):
    """bekannt: Woerter, die im Buch schon verwendet wurden. wied_max_quote
    begrenzt ihren Anteil an der Seite (gemessen an max_woerter)."""
    wied_max = int(wied_max_quote * max_woerter)
    kurz_strafe = kurz_strafe or {}
    z = Zustand(H, W, periode)

    def erlaubt(w):
        return w not in bekannt or z.wied < wied_max

    def lege(w, r, c, d, k):
        if w in bekannt:
            z.wied += 1
        z.lege(w, r, c, d, k)

    # Startwort: erste Vorgabe, sonst ein langes gewichtetes Wort, waagerecht
    # etwa in der Mitte.
    pool_lang = [w for w in woerter if W // 2 <= len(w) <= W - 2]
    vorg = [v for v in vorgaben if len(v) <= max(H, W)]
    start = vorg.pop(0) if vorg else (
        _gewichtet(rng, pool_lang, gewichte, 1) or [None])[0]
    if not start:
        return z
    if len(start) <= W:                     # waagerecht in der Mitte
        r0 = (H // 2 + rng.randint(-2, 1)) // periode * periode
        c0 = max(0, min(W - len(start), (W - len(start)) // 2 + rng.randint(-1, 1)))
        lege(start, r0, c0, "H", 0)
    else:                                   # zu lang fuer die Breite: senkrecht
        c0 = (W // 2 + rng.randint(-2, 1)) // periode * periode
        r0 = max(0, min(H - len(start), (H - len(start)) // 2))
        lege(start, r0, c0, "V", 0)
    fehlgriffe = 0
    while len(z.words) < max_woerter and fehlgriffe < 6:
        benutzt = {w for w, *_ in z.words}
        if vorg:                            # Vorgaben zuerst unterbringen
            kand = [vorg.pop(0)]
        else:
            kand = _gewichtet(rng, [w for w in woerter if w not in benutzt],
                              gewichte, stichprobe)
        best, bestwert = None, -1e9
        for w in kand:
            if w in benutzt or stamm(w) in z.staemme or not erlaubt(w):
                continue
            for k, r, c, d in _lagen(z, w):
                # Mehr Kreuzungen und laengere Woerter bevorzugen, Zufall
                # gegen immer gleiche Bilder, Gewicht fuer die Wortwahl.
                wert = (k * 3.0 + len(w) * LAENGE_BONUS + gewichte.get(w, 0.1) * 0.5
                        + rng.random() * 1.5 - kurz_strafe.get(len(w), 0.0))
                if wert > bestwert:
                    best, bestwert = (w, r, c, d, k), wert
        if best is None:
            fehlgriffe += 1
            continue
        fehlgriffe = 0
        lege(*best)
    # Schlussdurchgang ueber den ganzen Wortschatz: jede noch moegliche Lage
    # nutzen, meiste Kreuzungen zuerst, bis die Obergrenze erreicht ist.
    if len(z.words) < max_woerter:
        benutzt = {w for w, *_ in z.words}
        rest = _gewichtet(rng, [w for w in woerter if w not in benutzt],
                          gewichte, len(woerter))
        for w in rest:
            if len(z.words) >= max_woerter:
                break
            if stamm(w) in z.staemme or not erlaubt(w):
                continue
            lagen = _lagen(z, w)
            if lagen:
                k, r, c, d = max(lagen, key=lambda t: (t[0], rng.random()))
                # Kurze Woerter im Schlussdurchgang nur, wenn sie mehrfach
                # kreuzen: je hoeher die Strafe, desto mehr Kreuzungen noetig.
                if k * 3.0 < kurz_strafe.get(len(w), 0.0):
                    continue
                lege(w, r, c, d, k)
    return z


def in_layout(z):
    lay = KLayout(z.H, z.W)
    for w, r, c, d in z.words:
        lay.entries.append(Entry(r, c, d, len(w), word=w))
    # Eine Nummer je Anfangsfeld, in Lesereihenfolge; waagerecht vor senkrecht
    felder = sorted({(e.r, e.c) for e in lay.entries})
    nummer = {f: i for i, f in enumerate(felder, 1)}
    for e in lay.entries:
        e.nr = nummer[(e.r, e.c)]
    lay.entries.sort(key=lambda e: (e.direction != "H", e.nr))
    return lay, dict(z.g)


def kennzahlen(z):
    buch = len(z.g)
    gekreuzt = sum(1 for d in z.dir.values() if len(d) == 2)
    return {"woerter": len(z.words), "zellen": buch,
            "kreuzrate": round(gekreuzt / buch, 3) if buch else 0,
            "fuellung": round(buch / (z.H * z.W), 3)}


def erzeuge(woerter, gewichte, H, W, seed, versuche, stichprobe,
            max_woerter, min_woerter, kreuz_min, fuell_min, bonus_kreuz,
            vorgaben=(), bekannt=frozenset(), wied_ziel=1.0, wied_max=1.0,
            wied_strafe=25.0, kurz_strafe=None, periode=1, fuell_max=1.0):
    """Bester von `versuche` Aufbauten. Rueckgabe (layout, grid, info) oder None.

    Wiederholungen (Woerter aus `bekannt`): mehr als wied_max je Seite wird
    verworfen; jede Wiederholung ueber wied_ziel kostet wied_strafe Punkte in
    der Bewertung, sodass ein Versuch im Zielbereich regelmaessig gewinnt."""
    rng = random.Random(seed)
    best, bestwert, bestinfo = None, -1, None
    verworfen = 0
    for _ in range(versuche):
        z = aufbau(woerter, gewichte, H, W, rng, stichprobe, max_woerter,
                   vorgaben, bekannt, wied_max, kurz_strafe, periode)
        if z.words and z.wied > wied_max * len(z.words):
            verworfen += 1
            continue
        info = kennzahlen(z)
        if any(v not in {w for w, *_ in z.words} for v in vorgaben):
            verworfen += 1
            continue
        if (info["woerter"] < min_woerter or info["kreuzrate"] < kreuz_min
                or info["fuellung"] < fuell_min or info["fuellung"] > fuell_max):
            verworfen += 1
            continue
        info["wied"] = z.wied
        wert = (info["zellen"] + bonus_kreuz * z.kreuz
                - wied_strafe * max(0.0, z.wied - wied_ziel * len(z.words))
                - 2.0 * sum((kurz_strafe or {}).get(len(w), 0.0)
                            for w, *_ in z.words))
        if wert > bestwert:
            best, bestwert, bestinfo = z, wert, info
    if best is None:
        return None
    lay, grid = in_layout(best)
    bestinfo["verworfen"] = verworfen
    bestinfo["wert"] = bestwert
    return lay, grid, bestinfo
