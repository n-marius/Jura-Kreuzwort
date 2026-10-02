"""Setzt das komplette Buch als eine PDF-Datei.

Raetselseiten: nur das Raster, mittig auf der Seite, keine Ueberschrift.
Seitenzahl fett unten aussen: auf ungeraden (rechten) Seiten rechts, auf
geraden (linken) Seiten links.

Loesungsseiten: Ueberschrift LOESUNGEN weiss auf schwarzem Balken, darunter
je neun Raster im 3x3-Feld, zeilenweise von links nach rechts. Ueber jedem
Raster fett und linksbuendig die zugehoerige Seitenzahl. Frageblocke schwarz,
Loesungsbuchstaben in normaler Staerke, in der Zelle allseitig zentriert.
Die Seitenzaehlung laeuft durch.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skanvord"))
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from render2 import FONT, FONTB, FONTW, GREY, CAP, CAP_W, draw, size_for_cap

SOL_COLS, SOL_ROWS = 3, 3
RAND = 10 * mm            # Seitenrand der Loesungsseiten
SPALT = 4 * mm            # Abstand zwischen den Loesungsrastern (waagerecht)
ZEILENSPALT = 2 * mm      # Abstand zwischen den Rasterzeilen (senkrecht).
#                           Senkrecht ist der Platz knapp: darueber steht die
#                           Zeile "Seite X", darunter die naechste Reihe. Ein
#                           halber SPALT reicht optisch aus und schafft unten
#                           Abstand zur Seitenzahl.
LABEL = 4.2 * mm          # Hoehe der Zeile "Seite X"
KOPF = 21 * mm            # Bereich fuer die Ueberschrift. Der Balken sitzt
#                           mittig darin, deshalb steuert dieser Wert zugleich
#                           seinen Abstand zur oberen Blattkante.
FUSS = 14 * mm            # Bereich fuer die Seitenzahl. Grosszuegig, damit
#                           die unterste Rasterreihe nicht auf der Ziffer sitzt.


def _seitenzahl(c, x, y, nr, groesse=13, links=False):
    """links=True setzt die Zahl linksbuendig ab x, sonst rechtsbuendig bis x."""
    c.setFont(FONTB, groesse)
    c.setFillColorRGB(0, 0, 0)
    (c.drawString if links else c.drawRightString)(x, y, str(nr))


def _mini(c, lay, grid, x0, y0, cs, label):
    """y0 = Oberkante des Rasters."""
    c.setFont(FONTB, 8)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(x0, y0 + 1.3 * mm, label)
    fs = cs * 0.80
    for r in range(lay.H):
        for cc in range(lay.W):
            x, y = x0 + cc * cs, y0 - (r + 1) * cs
            c.setLineWidth(0.25)
            c.setStrokeColorRGB(0.35, 0.35, 0.35)
            if (r, cc) in lay.blocks:
                c.setFillColorRGB(0, 0, 0)
                c.rect(x, y, cs, cs, fill=1, stroke=1)
            else:
                c.setFillColorRGB(1, 1, 1)
                c.rect(x, y, cs, cs, fill=1, stroke=1)
                ch = grid.get((r, cc))
                if ch:
                    c.setFillColorRGB(0, 0, 0)
                    c.setFont(FONT, fs)
                    c.drawCentredString(x + cs / 2,
                                        y + cs / 2 - fs * CAP / 2, ch)
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0.1, 0.1, 0.1)
    c.rect(x0, y0 - lay.H * cs, lay.W * cs, lay.H * cs, fill=0, stroke=1)


TRIM_W, TRIM_H = 148 * mm, 210 * mm   # Endformat laut Datenblatt
BLEED = 3 * mm                        # Beschnittzugabe ringsum -> 154 x 216 mm
BUND = 2 * mm                         # Versatz aus dem Falz: ungerade Seiten
#                                       nach rechts, gerade nach links
GERADE_LINKS = 1 * mm                 # zusaetzlicher Zug nach links auf geraden
#                                       Seiten, ueber den Bundsteg hinaus


def _seitenanfang(c, seite):
    """Nullpunkt auf die Ecke des Endformats legen, dazu der Bundsteg-Versatz."""
    c.saveState()
    versatz = BUND if seite % 2 else -BUND - GERADE_LINKS
    c.translate(BLEED + versatz, BLEED)


def build(puzzles, path, cell_mm=11.0, cap_mm=2.0, lines_max=4,
          nur_loesungen=False, **_):
    """puzzles: Liste von (seitenzahl, layout, grid)."""
    W, H = TRIM_W, TRIM_H
    c = canvas.Canvas(path, pagesize=(W + 2 * BLEED, H + 2 * BLEED))
    size = size_for_cap(cap_mm)
    cs = cell_mm * mm
    seite = 0

    for nr, lay, grid in puzzles:
        seite += 1
        _seitenanfang(c, seite)
        gw, gh = cs * lay.W, cs * lay.H
        x0 = (W - gw) / 2
        y0 = (H + gh) / 2                      # Oberkante, mittig auf der Seite
        # Pruefdruck: dasselbe Raster in voller Groesse samt Fragen, zusaetzlich
        # die Loesungsbuchstaben in den Zellen.
        draw(c, lay, x0, y0, cs, size, lines_max,
             letters=grid if nur_loesungen else None, solution=nur_loesungen)
        links = seite % 2 == 0
        _seitenzahl(c, x0 if links else x0 + gw, (H - gh) / 2 - 5.5 * mm,
                    nr if nur_loesungen else seite, links=links)
        c.restoreState()
        c.showPage()

    if nur_loesungen:                # Pruefdruck endet hier, ohne Miniraster
        c.save()
        return path

    per = SOL_COLS * SOL_ROWS
    H0, W0 = puzzles[0][1].H, puzzles[0][1].W
    # Zellgroesse der Miniraster: frueher nur aus der Breite gerechnet, wodurch
    # die unterste Reihe bei hohen Rastern (12 Zeilen) unten aus der Seite lief.
    # Jetzt bindet die knappere der beiden Richtungen.
    mcs_b = (W - 2 * RAND - (SOL_COLS - 1) * SPALT) / SOL_COLS / W0
    mcs_h = ((H - KOPF - FUSS - SOL_ROWS * LABEL
              - (SOL_ROWS - 1) * ZEILENSPALT) / (SOL_ROWS * H0))
    mcs = min(mcs_b, mcs_h)
    block = H0 * mcs + LABEL + ZEILENSPALT
    # Der uebrige Platz wird gleichmaessig auf oben und unten verteilt, statt
    # oben liegen zu bleiben.
    ges_b = SOL_COLS * W0 * mcs + (SOL_COLS - 1) * SPALT
    ges_h = SOL_ROWS * (H0 * mcs + LABEL) + (SOL_ROWS - 1) * ZEILENSPALT
    x_rand = (W - ges_b) / 2
    y_luft = (H - KOPF - FUSS - ges_h) / 2
    for k in range(0, len(puzzles), per):
        seite += 1
        _seitenanfang(c, seite)
        # Ueberschrift: weiss auf schwarz, mittig im Kopfbereich.
        # Nicht kondensiert, leicht gesperrt, Polster ringsum gleich breit.
        text, ts, sperr, pad = "LÖSUNGEN", 14, 1.6, 1.7 * mm
        tb = c.stringWidth(text, FONTW, ts) + sperr * (len(text) - 1)
        kap = ts * CAP_W
        ymitte = H - KOPF / 2
        c.setFillColorRGB(0, 0, 0)
        c.rect((W - tb) / 2 - pad, ymitte - kap / 2 - pad,
               tb + 2 * pad, kap + 2 * pad, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(FONTW, ts)
        to = c.beginText((W - tb) / 2, ymitte - kap / 2)
        to.setCharSpace(sperr)
        to.setFillColorRGB(1, 1, 1)
        to.textOut(text)
        c.drawText(to)
        reset = c.beginText(0, 0)          # Sperrung ist Teil des Textzustands
        reset.setCharSpace(0)              # und wuerde sonst weiterwirken
        c.drawText(reset)

        for j, (nr, lay, grid) in enumerate(puzzles[k:k + per]):
            col, row = j % SOL_COLS, j // SOL_COLS
            x0 = x_rand + col * (W0 * mcs + SPALT)
            y0 = H - KOPF - y_luft - LABEL - row * block
            _mini(c, lay, grid, x0, y0, mcs, f"Seite {nr}")
        links = seite % 2 == 0
        _seitenzahl(c, RAND if links else W - RAND, FUSS / 2, seite,
                    links=links)
        c.restoreState()
        c.showPage()
    c.save()
    return path
