"""PDF-Ausgabe eines Schwedenraetsels (Raetsel- und Loesungsseite)."""
from __future__ import annotations
from reportlab.lib.pagesizes import A4, A5, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT = "ArialLike"          # Liberation Sans: metrisch kompatibel zu Arial
FONTB = "ArialLike-Bold"
_L = "/usr/share/fonts/truetype/liberation/"
pdfmetrics.registerFont(TTFont(FONT, _L + "LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont(FONTB, _L + "LiberationSans-Bold.ttf"))
CAP_RATIO = 0.688          # Versalhoehe / em fuer Liberation Sans


def size_for_cap(cap_mm):
    """Schriftgrad in Punkt fuer eine gewuenschte Versalhoehe in mm."""
    return cap_mm / CAP_RATIO * 72.0 / 25.4

GREY = (0.87, 0.87, 0.87)


def _hard_split(w, font, size, maxw):
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


def _wrap(text, font, size, maxw, hard=False):
    out = []
    for seg in text.split("\n"):
        words = []
        for w in seg.split():
            words.extend(_hard_split(w, font, size, maxw) if hard else [w])
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


def _fit_text(c, text, x, y, w, h, maxsize=6.0, minsize=2.7):
    """Groesste Schriftgroesse suchen, bei der der Text ohne Notumbruch passt."""
    chosen, lines = None, None
    size = maxsize
    while size >= minsize:
        ls = _wrap(text, FONT, size, w)
        if all(pdfmetrics.stringWidth(l, FONT, size) <= w for l in ls) \
           and len(ls) * size * 1.12 <= h:
            chosen, lines = size, ls
            break
        size -= 0.15
    if chosen is None:                      # Notfall: harte Trennung
        chosen = minsize
        lines = _wrap(text, FONT, chosen, w, hard=True)
    total = len(lines) * chosen * 1.12
    ty = y + h / 2 + total / 2 - chosen
    c.setFont(FONT, chosen)
    c.setFillColorRGB(0, 0, 0)
    for l in lines:
        c.drawCentredString(x + w / 2, ty, l)
        ty -= chosen * 1.12


def _arrow_right(c, x, y, s=2.9):
    c.setFillColorRGB(0, 0, 0)
    p = c.beginPath()
    p.moveTo(x - s * 0.55, y + s * 0.62)
    p.lineTo(x + s * 0.75, y)
    p.lineTo(x - s * 0.55, y - s * 0.62)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _arrow_down(c, x, y, s=2.9):
    c.setFillColorRGB(0, 0, 0)
    p = c.beginPath()
    p.moveTo(x - s * 0.62, y + s * 0.55)
    p.lineTo(x + s * 0.62, y + s * 0.55)
    p.lineTo(x, y - s * 0.75)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _elbow_down_right(c, x, y, s=4.0):
    """Knick: von oben herunter, dann nach rechts."""
    c.setLineWidth(1.2)
    c.setStrokeColorRGB(0, 0, 0)
    c.line(x, y + s * 1.1, x, y)
    c.line(x, y, x + s * 0.8, y)
    _arrow_right(c, x + s * 1.05, y, s * 0.9)


def _elbow_right_down(c, x, y, s=4.0):
    """Knick: nach rechts, dann herunter."""
    c.setLineWidth(1.2)
    c.setStrokeColorRGB(0, 0, 0)
    c.line(x - s * 1.1, y, x, y)
    c.line(x, y, x, y - s * 0.8)
    _arrow_down(c, x, y - s * 1.05, s * 0.9)


def draw_grid(c, layout, x0, y0, cs, letters=None, show_letters=False,
              clue_pt=6.0):
    H, W = layout.H, layout.W

    # Frageblöcke -> zugeordnete Einträge
    byclue = {}
    for e in layout.entries:
        byclue.setdefault(e.clue_rc, []).append(e)

    for r in range(H):
        for cc in range(W):
            x = x0 + cc * cs
            y = y0 - (r + 1) * cs
            isblock = (r, cc) in layout.blocks
            c.setLineWidth(0.5)
            c.setStrokeColorRGB(0.35, 0.35, 0.35)
            if isblock:
                c.setFillColorRGB(*GREY)
                c.rect(x, y, cs, cs, fill=1, stroke=1)
            else:
                c.setFillColorRGB(1, 1, 1)
                c.rect(x, y, cs, cs, fill=1, stroke=1)
                if show_letters and letters and (r, cc) in letters:
                    c.setFillColorRGB(0, 0, 0)
                    c.setFont(FONTB, cs * 0.42)
                    c.drawCentredString(x + cs / 2, y + cs * 0.32,
                                        letters[(r, cc)])

    c.setLineWidth(1.4)
    c.setStrokeColorRGB(0.1, 0.1, 0.1)
    c.rect(x0, y0 - H * cs, W * cs, H * cs, fill=0, stroke=1)

    for rc, ents in byclue.items():
        r, cc = rc
        x = x0 + cc * cs
        y = y0 - (r + 1) * cs
        n = len(ents)
        # Trennlinie bei zwei Aufgaben
        if n == 2:
            c.setLineWidth(0.4)
            c.setStrokeColorRGB(0.55, 0.55, 0.55)
            c.line(x + 0.8, y + cs / 2, x + cs - 0.8, y + cs / 2)
        # Text
        pad = 1.0
        right_arrows = [e for e in ents if e.arrow in ("R", "RD")]
        bottom_arrows = [e for e in ents if e.arrow in ("D", "DR")]
        ents = right_arrows + bottom_arrows
        rmargin = 4.6 if right_arrows else pad
        bmargin = 4.6 if bottom_arrows else pad
        for k, e in enumerate(ents):
            bh = (cs - bmargin) / n
            by = y + bmargin + (n - 1 - k) * bh
            _fit_text(c, e.clue, x + pad, by, cs - pad - rmargin, bh,
                      maxsize=clue_pt)
        # Pfeile
        for j, e in enumerate(right_arrows):
            off = cs / 2 if n == 1 else cs * 0.75
            if e.arrow == "R":
                _arrow_right(c, x + cs - 2.4, y + off)
            else:
                _elbow_right_down(c, x + cs - 2.4, y + off)
        for j, e in enumerate(bottom_arrows):
            off = cs / 2
            if e.arrow == "D":
                _arrow_down(c, x + off, y + 2.4)
            else:
                _elbow_down_right(c, x + off, y + 3.4)


def render(layout, grid, path, title="Schwedenrätsel", subtitle="",
           land=False, cell_mm=None, clue_pt=6.0):
    size = landscape(A4) if land else A4
    W, H = size
    c = canvas.Canvas(path, pagesize=size)
    cs = cell_mm * mm if cell_mm else min((W - 16 * mm) / layout.W,
                                          (H - 34 * mm) / layout.H)
    gw = cs * layout.W
    x0 = (W - gw) / 2
    y0 = H - (20 * mm if cell_mm else (24 * mm if land else 34 * mm))

    def header(t, s):
        c.setFillColorRGB(0, 0, 0)
        c.setFont(FONTB, 13 if land else 16)
        c.drawCentredString(W / 2, H - (13 * mm if (land or cell_mm) else 20 * mm), t)
        if s:
            c.setFont(FONT, 9)
            c.setFillColorRGB(0.35, 0.35, 0.35)
            c.drawCentredString(W / 2, H - (18 * mm if (land or cell_mm) else 26 * mm), s)

    header(title, subtitle)
    draw_grid(c, layout, x0, y0, cs, clue_pt=clue_pt)
    c.showPage()

    header(title + " – Lösung", subtitle)
    draw_grid(c, layout, x0, y0, cs, letters=grid, show_letters=True,
              clue_pt=clue_pt)
    c.showPage()
    c.save()
    return path
