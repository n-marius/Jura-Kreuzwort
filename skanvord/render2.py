"""PDF-Ausgabe v2: eine Frage je Block, Pfeile im ersten Antwortkaestchen,
feste Schriftgroesse (Versalhoehe in mm vorgegeben)."""
from __future__ import annotations
from reportlab.lib.pagesizes import A4, A5, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import os as _os
_F = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "fonts")
# Nimbus Sans Narrow = freier Nachbau von Helvetica Narrow und damit die
# naechste Entsprechung zu CG Triumvirate Condensed Bold.
FONT, FONTB = "NimbusNarrow", "NimbusNarrow-Bold"
FONTW = "NimbusSans-Bold"         # nicht kondensiert, fuer Ueberschriften
pdfmetrics.registerFont(TTFont(FONT, _os.path.join(_F, "NimbusSansNarrow-Regular.ttf")))
pdfmetrics.registerFont(TTFont(FONTB, _os.path.join(_F, "NimbusSansNarrow-Bold.ttf")))
pdfmetrics.registerFont(TTFont(FONTW, _os.path.join(_F, "NimbusSans-Bold.ttf")))
CAP = 0.718                       # Versalhoehe / em (Nimbus Sans Narrow)
CAP_W = 0.729                     # Versalhoehe / em (Nimbus Sans)
GREY = (0.87, 0.87, 0.87)
PAGES = {"A4": A4, "A5": A5, "A4q": landscape(A4), "A5q": landscape(A5)}


def size_for_cap(cap_mm):
    return cap_mm / CAP * 72.0 / 25.4


# ---------------------------------------------------------------- Textumbruch
def _split_word(w, size, maxw, font=None):
    font = font or FONTB
    parts = []
    while pdfmetrics.stringWidth(w, font, size) > maxw and len(w) > 2:
        k = len(w) - 1
        while k > 1 and pdfmetrics.stringWidth(w[:k] + "-", font, size) > maxw:
            k -= 1
        if k <= 1:
            break
        parts.append(w[:k] + "-")
        w = w[k:]
    parts.append(w)
    return parts


def wrap(text, size, maxw, font=None):
    font = font or FONTB
    out = []
    for seg in text.split("\n"):
        words = []
        for w in seg.split():
            words.extend(_split_word(w, size, maxw, font))
        cur = ""
        for w in words:
            t = (cur + " " + w).strip()
            if pdfmetrics.stringWidth(t, font, size) <= maxw or not cur:
                cur = t
            else:
                out.append(cur)
                cur = w
        if cur:
            out.append(cur)
    return out


# -------------------------------------------------------------------- Pfeile
def _tri(c, pts):
    c.setFillColorRGB(0, 0, 0)
    p = c.beginPath()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _draw_arrow(c, arrow, tx, ty, cs):
    """tx, ty = linke untere Ecke des ERSTEN Antwortkaestchens."""
    top, cy, cx = ty + cs, ty + cs / 2, tx + cs / 2
    c.setLineWidth(0.9)
    c.setStrokeColorRGB(0, 0, 0)
    if arrow == "R":
        _tri(c, [(tx, cy + 1.1 * mm), (tx + 2.4 * mm, cy), (tx, cy - 1.1 * mm)])
    elif arrow == "D":
        _tri(c, [(cx - 1.1 * mm, top), (cx + 1.1 * mm, top), (cx, top - 2.4 * mm)])
    elif arrow == "DR":                       # von oben herein, dann nach rechts
        x = tx + 2.0 * mm
        y = top - 1.8 * mm
        c.line(x, top, x, y)
        c.line(x, y, x + 1.3 * mm, y)
        _tri(c, [(x + 1.3 * mm, y + 1.0 * mm), (x + 3.4 * mm, y),
                 (x + 1.3 * mm, y - 1.0 * mm)])
    elif arrow == "RD":                       # von links herein, dann nach unten
        y = top - 2.2 * mm
        x = tx + 1.8 * mm
        c.line(tx, y, x, y)
        c.line(x, y, x, y - 1.3 * mm)
        _tri(c, [(x - 1.0 * mm, y - 1.3 * mm), (x + 1.0 * mm, y - 1.3 * mm),
                 (x, y - 3.4 * mm)])
    elif arrow == "LD":                       # von rechts herein, dann nach unten
        y = top - 2.2 * mm
        x = tx + cs - 1.8 * mm
        c.line(tx + cs, y, x, y)
        c.line(x, y, x, y - 1.3 * mm)
        _tri(c, [(x - 1.0 * mm, y - 1.3 * mm), (x + 1.0 * mm, y - 1.3 * mm),
                 (x, y - 3.4 * mm)])


def _first_cell(e):
    return (e.r, e.c)


# --------------------------------------------------------------------- Raster
def draw(c, layout, x0, y0, cs, size, lines_max, letters=None, solution=False):
    H, W = layout.H, layout.W
    hpad, vpad = 0.45 * mm, 0.3 * mm
    maxw = cs - 0.5 * mm          # linker Einzug plus minimale Reserve rechts
    lead = (cs - 2 * vpad) / lines_max
    overflow = []

    def cellxy(r, cc):
        return x0 + cc * cs, y0 - (r + 1) * cs

    for r in range(H):
        for cc in range(W):
            x, y = cellxy(r, cc)
            c.setLineWidth(0.5)
            c.setStrokeColorRGB(0.35, 0.35, 0.35)
            if (r, cc) in layout.blocks:
                c.setFillColorRGB(*GREY)
            else:
                c.setFillColorRGB(1, 1, 1)
            c.rect(x, y, cs, cs, fill=1, stroke=1)
            if solution and letters and (r, cc) in letters:
                c.setFillColorRGB(0, 0, 0)
                c.setFont(FONTB, cs * 0.44)
                c.drawCentredString(x + cs / 2, y + cs * 0.30, letters[(r, cc)])

    c.setLineWidth(1.3)
    c.setStrokeColorRGB(0.1, 0.1, 0.1)
    c.rect(x0, y0 - H * cs, W * cs, H * cs, fill=0, stroke=1)

    for e in layout.entries:
        br, bc = e.clue_rc
        bx, by = cellxy(br, bc)
        lines = wrap(e.clue, size, maxw, font=FONTB)
        if len(lines) > lines_max:
            overflow.append((e.word, e.clue, len(lines)))
            lines = lines[:lines_max]
        total = len(lines) * lead
        c.setFont(FONTB, size)
        c.setFillColorRGB(0, 0, 0)
        for i, ln in enumerate(lines):
            base = by + cs / 2 + total / 2 - (i + 1) * lead + (lead - size * CAP) / 2
            c.drawString(bx + hpad, base, ln)
        fx, fy = cellxy(*_first_cell(e))
        _draw_arrow(c, e.arrow, fx, fy, cs)
    return overflow


def render(layout, grid, path, title="", subtitle="", page="A5",
           cell_mm=11.0, cap_mm=2.0, lines_max=4):
    W, H = PAGES[page]
    size = size_for_cap(cap_mm)
    cs = cell_mm * mm
    x0 = (W - cs * layout.W) / 2
    y0 = H - 17 * mm
    c = canvas.Canvas(path, pagesize=(W, H))

    def head(t, s):
        c.setFillColorRGB(0, 0, 0)
        c.setFont(FONTB, 11)
        c.drawCentredString(W / 2, H - 8 * mm, t)
        if s:
            c.setFont(FONT, 6.5)
            c.setFillColorRGB(0.35, 0.35, 0.35)
            c.drawCentredString(W / 2, H - 12.5 * mm, s)

    head(title, subtitle)
    ov = draw(c, layout, x0, y0, cs, size, lines_max)
    c.showPage()
    head(title + " – Lösung", subtitle)
    draw(c, layout, x0, y0, cs, size, lines_max, letters=grid, solution=True)
    c.showPage()
    c.save()
    return ov, size
