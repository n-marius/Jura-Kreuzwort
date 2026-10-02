"""Themen werden je Chat vorgegeben und aus themes.json geladen.

Aufbau themes.json:
{
  "JURA":   {"gewicht": 30, "woerter": {"URTEIL": 1.0, "AKTE": 0.6}},
  "REISEN": {"gewicht": 15, "woerter": ["MUSEUM", "FAEHRE"]}
}
"gewicht"  = Gewicht des Themas insgesamt
"woerter"  = Wort -> Themennaehe 0..1  (Liste erlaubt, dann Naehe 1.0)

Das wirksame Gewicht eines Wortes ist gewicht * naehe. Dadurch koennen auch
locker zugehoerige Woerter aufgenommen werden, ohne die Kernbegriffe zu verdraengen.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "themes.json")


def _n(w):
    w = w.replace("\u00df", "ss").upper()
    for a, b in (("\u00c4", "AE"), ("\u00d6", "OE"), ("\u00dc", "UE")):
        w = w.replace(a, b)
    return w


def load():
    if not os.path.exists(PATH):
        return {}
    return json.load(open(PATH, encoding="utf-8"))


def theme_map():
    """Wort -> (Themenname, Themengewicht, Themennaehe).

    Die Naehe bestimmt zweierlei: das Fuellgewicht (quadratisch, damit Kolorit
    die Kernbegriffe nicht verdraengt) und die Wiederholungsdaempfung
    (Kolorit wird wie ein Fuellwort behandelt, es ist ja nicht knapp).
    """
    out = {}
    for name, spec in load().items():
        g = float(spec.get("gewicht", 10))
        ws = spec.get("woerter", {})
        if isinstance(ws, list):
            ws = {w: 1.0 for w in ws}
        for w, nah in ws.items():
            w = _n(w)
            nah = float(nah)
            if w not in out or g * nah > out[w][1] * out[w][2]:
                out[w] = (name, g, nah)
    return out


def stufe(nah):
    """KERN | UMFELD | KOLORIT"""
    return "KERN" if nah >= 0.8 else ("UMFELD" if nah >= 0.45 else "KOLORIT")


def theme_names():
    return sorted(load().keys())
