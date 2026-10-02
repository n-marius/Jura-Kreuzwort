"""Rendert das Kreuzwortbuch und prueft die Fragen.

Aufruf:  python kr_render.py [Zielordner]                  -> kr_raetselbuch.pdf
         python kr_render.py [Zielordner] --nur-loesungen  -> kr_loesungsprobe.pdf

Seite: Ueberschrift "– § N –", Raster mittig im Rasterbereich, Fragenfenster
fester Hoehe unten. Fragen je Block (Waagerecht, Senkrecht) als Fliesstext
"1: Frage   2: Frage", Nummer und Blocktitel fett. Keine Seitenzahl unten.
Fragen kommen aus clues.json wie bisher (themengebundene Fassung zuerst).
"""
import glob, os, pickle, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "skanvord"))
sys.path.insert(0, os.path.join(HERE, "kreuz"))
sys.path.insert(0, HERE)

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
import layout, platzierung                                    # noqa: F401 (pickle)
import kr_config as K
from render2 import FONT, FONTB, FONTW, CAP, CAP_W, size_for_cap
from bookpdf import (TRIM_W, TRIM_H, BLEED, _seitenanfang, _seitenzahl,
                     SOL_COLS, SOL_ROWS, RAND, SPALT, ZEILENSPALT, LABEL, KOPF,
                     FUSS)
from core import clue_store
from wordcheck import enthaelt_loesung, kennzeichen_fehlt

W, H = TRIM_W, TRIM_H
GROESSE = size_for_cap(K.CAP_MM)
LEAD = GROESSE * K.ZEILENABSTAND
CS = K.ZELLE_MM * mm
X_SATZ = (W - K.SATZ_B * mm) / 2
FEN_OBEN = (K.SATZ_UNTEN + K.FENSTER_H) * mm           # y der Fensteroberkante
UEBER_BASIS = H - K.SATZ_OBEN * mm - K.UEBER_PT * CAP_W   # Grundlinie Ueberschrift
RASTER_OBEN = UEBER_BASIS - K.UEBER_ABSTAND * mm
RASTER_UNTEN = FEN_OBEN + K.FENSTER_ABSTAND * mm


def einzeilig(text):
    """Kaestchenumbrueche aus clues.json entfernen: 'Amts-\\nkleid' -> 'Amtskleid',
    'Ost-\\nWest' -> 'Ost-West', sonst Umbruch -> Leerzeichen."""
    text = re.sub(r"-\n(?=[a-zäöüß])", "", text)
    text = text.replace("-\n", "-").replace("\n", " ")
    return re.sub(r" +", " ", text).strip()


def varianten(C, wort):
    raw = C.get(wort) or []
    passend, neutral = [], []
    for v in raw:
        if isinstance(v, dict):
            if v.get("t") == K.THEMA:
                passend.append(einzeilig(v.get("c", "")))
            elif not v.get("t"):
                neutral.append(einzeilig(v.get("c", "")))
        else:
            neutral.append(einzeilig(v))
    return passend + neutral


# ------------------------------------------------------------ Fragenliste
def _token_block(kopf, eintraege):
    """Token: (text, font, klebt_am_vorigen, trenner_davor, zeilenumbruch_danach)."""
    t = [(kopf, FONTB, False, False, K.KOPF_EIGENE_ZEILE)]
    for e in eintraege:
        t.append((f"{e.nr}:", FONTB, False, True, False))
        for i, w in enumerate(e.clue.split()):
            t.append((w, FONT, i == 0, False, False))   # Nummer + 1. Wort zusammen
    return t


def setze_fragen(eintraege):
    """Zeilen als Listen von (x, text, font). Waagerecht und Senkrecht als
    getrennte Bloecke, jeder beginnt auf einer neuen Zeile."""
    breite = K.SATZ_B * mm
    sep_w = stringWidth(K.TRENNER, FONT, GROESSE)
    sp = stringWidth(" ", FONT, GROESSE)
    zeilen = []
    for kopf, richtung in ((K.KOPF_W, "H"), (K.KOPF_S, "V")):
        block = [e for e in eintraege if e.direction == richtung]
        if not block:
            continue
        token = _token_block(kopf, block)
        zeile, x, i = [], 0.0, 0
        while i < len(token):
            grp = [token[i]]
            j = i + 1
            while j < len(token) and token[j][2]:
                grp.append(token[j])
                j += 1
            gw = sum(stringWidth(t, f, GROESSE) for t, f, *_ in grp) + sp * (len(grp) - 1)
            abst = 0.0 if not zeile else (sep_w if grp[0][3] else sp)
            if zeile and x + abst + gw > breite:
                zeilen.append(zeile)
                zeile, x, abst = [], 0.0, 0.0
            for k, (t, f, *_r) in enumerate(grp):
                a = abst if k == 0 else sp
                zeile.append((x + a, t, f))
                x += a + stringWidth(t, f, GROESSE)
            if grp[-1][4]:
                zeilen.append(zeile)
                zeile, x = [], 0.0
            i = j
        if zeile:
            zeilen.append(zeile)
    return zeilen


def max_zeilen():
    return int((K.FENSTER_H * mm - GROESSE * CAP) // LEAD) + 1


def zeichne_fragen(c, zeilen):
    y = FEN_OBEN - GROESSE * CAP                 # erste Grundlinie: Versal oben buendig
    c.setFillColorRGB(0, 0, 0)
    for zeile in zeilen[:max_zeilen()]:
        for x, t, f in zeile:
            c.setFont(f, GROESSE)
            c.drawString(X_SATZ + x, y, t)
        y -= LEAD


# ------------------------------------------------------------ Raster
def raster_ursprung(lay):
    zellen = lay.zellen()
    r0 = min(r for r, _ in zellen); r1 = max(r for r, _ in zellen)
    c0 = min(cc for _, cc in zellen); c1 = max(cc for _, cc in zellen)
    bw, bh = (c1 - c0 + 1) * CS, (r1 - r0 + 1) * CS
    x = (W - bw) / 2 - c0 * CS
    y = RASTER_OBEN - (RASTER_OBEN - RASTER_UNTEN - bh) / 2 + r0 * CS
    return x, y, zellen


def zeichne_raster(c, lay, grid, loesung=False):
    x0, y0, zellen = raster_ursprung(lay)
    c.setLineWidth(0.6)
    c.setStrokeColorRGB(0.1, 0.1, 0.1)
    c.setFillColorRGB(1, 1, 1)
    for r, cc in zellen:
        c.rect(x0 + cc * CS, y0 - (r + 1) * CS, CS, CS, fill=1, stroke=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFont(FONTB, K.NR_PT)
    pad = K.NR_PAD_MM * mm
    for (r, cc), nr in sorted({(e.r, e.c): e.nr for e in lay.entries}.items()):
        c.drawString(x0 + cc * CS + pad,
                     y0 - r * CS - pad - K.NR_PT * CAP_W, str(nr))
    if loesung:
        c.setFont(FONTB, CS * 0.48)
        for (r, cc), ch in grid.items():
            c.drawCentredString(x0 + cc * CS + CS / 2, y0 - (r + 1) * CS + CS * 0.26, ch)


def ueberschrift(c, nr, lay):
    """Mittig zwischen Oberkante Endformat und Oberkante des Rasters dieser Seite."""
    x0, y0, zellen = raster_ursprung(lay)
    oben = y0 - min(r for r, _ in zellen) * CS
    basis = (H + oben) / 2 - K.UEBER_PT * CAP_W / 2
    c.setFillColorRGB(0, 0, 0)
    c.setFont(FONTW, K.UEBER_PT)
    c.drawCentredString(W / 2, basis, f"\u2013 \u00a7 {nr} \u2013")


def mini(c, lay, grid, x0, y0, cs, label):
    c.setFont(FONTB, 8)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(x0, y0 + 1.3 * mm, label)
    fs = cs * 0.80
    for (r, cc), ch in grid.items():
        x, y = x0 + cc * cs, y0 - (r + 1) * cs
        c.setLineWidth(0.25)
        c.setStrokeColorRGB(0.35, 0.35, 0.35)
        c.setFillColorRGB(1, 1, 1)
        c.rect(x, y, cs, cs, fill=1, stroke=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont(FONT, fs)
        c.drawCentredString(x + cs / 2, y + cs / 2 - fs * CAP / 2, ch)


def loesungsteil(c, puzzles, seite):
    per = SOL_COLS * SOL_ROWS
    mcs = min((W - 2 * RAND - (SOL_COLS - 1) * SPALT) / SOL_COLS / K.RASTER_W,
              (H - KOPF - FUSS - SOL_ROWS * LABEL - (SOL_ROWS - 1) * ZEILENSPALT)
              / (SOL_ROWS * K.RASTER_H))
    ges_b = SOL_COLS * K.RASTER_W * mcs + (SOL_COLS - 1) * SPALT
    ges_h = SOL_ROWS * (K.RASTER_H * mcs + LABEL) + (SOL_ROWS - 1) * ZEILENSPALT
    # Freie Hoehe gleichmaessig ueber, zwischen und unter die Rasterzeilen
    # verteilen (keine Seitenzahl mehr, unten gilt der Satzrand).
    x_rand = (W - ges_b) / 2
    luft = (H - KOPF - K.SATZ_UNTEN * mm - ges_h + (SOL_ROWS - 1) * ZEILENSPALT) / (SOL_ROWS + 1)
    block = K.RASTER_H * mcs + LABEL + luft
    for k in range(0, len(puzzles), per):
        seite += 1
        _seitenanfang(c, seite)
        text, ts, sperr, pad = "LÖSUNGEN", 14, 1.6, 1.7 * mm
        tb = c.stringWidth(text, FONTW, ts) + sperr * (len(text) - 1)
        kap, ym = ts * CAP_W, H - KOPF / 2
        c.setFillColorRGB(0, 0, 0)
        c.rect((W - tb) / 2 - pad, ym - kap / 2 - pad, tb + 2 * pad, kap + 2 * pad,
               fill=1, stroke=0)
        to = c.beginText((W - tb) / 2, ym - kap / 2)
        to.setFont(FONTW, ts)
        to.setCharSpace(sperr)
        to.setFillColorRGB(1, 1, 1)
        to.textOut(text)
        c.drawText(to)
        for j, (nr, lay, grid) in enumerate(puzzles[k:k + per]):
            col, row = j % SOL_COLS, j // SOL_COLS
            mini(c, lay, grid, x_rand + col * (K.RASTER_W * mcs + SPALT),
                 H - KOPF - luft - LABEL - row * block, mcs, f"\u00a7 {nr}")
        c.restoreState()
        c.showPage()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = args[0] if args else os.path.join(HERE, "ausgabe")
    os.makedirs(out, exist_ok=True)
    nur_los = "--nur-loesungen" in sys.argv
    C = clue_store()
    from kr_book import lese_wortliste, lese_latein
    ABK = lese_wortliste()[1]
    LAT = lese_latein()
    seen, fehlt, doppelt, verraten, zusatz, ueberlauf = {}, {}, {}, [], [], []
    puzzles = []
    for f in sorted(glob.glob(os.path.join(HERE, K.PUZZLE_DIR, "*.pkl"))):
        nr = int(os.path.basename(f)[:3])
        lay, grid = pickle.load(open(f, "rb"))
        for e in lay.entries:
            vs = varianten(C, e.word)
            k = seen.get(e.word, 0)
            seen[e.word] = k + 1
            if not vs:
                fehlt.setdefault(e.word, []).append(nr)
                e.clue = f"[{e.word}]"
                continue
            if k >= len(vs):
                doppelt[e.word] = (len(vs), k + 1)
            e.clue = vs[k % len(vs)]
            if enthaelt_loesung(e.clue, e.word):
                verraten.append((nr, e.word, e.clue))
            z = kennzeichen_fehlt(e.word, e.clue) or (
                "(Abk.)" if e.word in ABK and "(Abk.)" not in e.clue else None) or (
                "(lat.)" if e.word in LAT and "(lat.)" not in e.clue else None)
            if z:
                zusatz.append((nr, e.word, z))
        zeilen = setze_fragen(lay.entries)
        if len(zeilen) > max_zeilen():
            ueberlauf.append((nr, len(zeilen)))
        puzzles.append((nr, lay, grid, zeilen))

    ziel = os.path.join(out, "kr_loesungsprobe.pdf" if nur_los else "kr_raetselbuch.pdf")
    c = canvas.Canvas(ziel, pagesize=(W + 2 * BLEED, H + 2 * BLEED))
    seite = 0
    for nr, lay, grid, zeilen in puzzles:
        seite += 1
        _seitenanfang(c, seite)
        zeichne_raster(c, lay, grid, loesung=nur_los)
        zeichne_fragen(c, zeilen)
        ueberschrift(c, nr if nur_los else seite, lay)
        c.restoreState()
        c.showPage()
    if not nur_los:
        loesungsteil(c, [(i + 1, l, g) for i, (_, l, g, _z) in enumerate(puzzles)], seite)
    c.save()

    print(f"{os.path.basename(ziel)}: {len(puzzles)} Raetselseiten"
          + ("" if nur_los else f" + {-(-len(puzzles) // 9)} Loesungsseiten")
          + f" | Fenster fasst {max_zeilen()} Zeilen")
    for nr, lay, grid, zeilen in puzzles:
        print(f"  {nr:03d} n={len(lay.entries)} zeilen={len(zeilen)}")
    if fehlt:
        print(f"FRAGE FEHLT ({len(fehlt)} Woerter):")
        for w, s in sorted(fehlt.items()):
            print(f"  {w} (Seite {', '.join(map(str, s))})")
    if ueberlauf:
        print("FRAGENFENSTER ZU KLEIN:")
        for nr, n in ueberlauf:
            print(f"  {nr:03d}: {n} Zeilen, Platz fuer {max_zeilen()}")
    if doppelt:
        print("GLEICHE FRAGE MEHRFACH:")
        for w, (hat, braucht) in sorted(doppelt.items()):
            print(f"  {w}: {braucht} Einsaetze, {hat} Fassung(en)")
    if zusatz:
        print("ZUSATZ FEHLT:")
        for nr, w, z in zusatz:
            print(f"  {nr:03d} {w} braucht {z}")
    if verraten:
        print("FRAGE ENTHAELT DEN WORTSTAMM:")
        for nr, w, cl in verraten:
            print(f"  {nr:03d} {w} = {cl!r}")


if __name__ == "__main__":
    main()
