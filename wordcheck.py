"""Deterministische Wortpruefungen — sparen Sichtpruefung und damit Token."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def lade_sperrliste(pfad):
    """Liest stopwords.txt / blacklist.txt ZEILENWEISE.

    Wichtig: eine Zeile, die mit # beginnt, ist vollstaendig Kommentar. Die
    fruehere Fassung las die Datei mit read().split() und verwarf nur einzelne
    Tokens, die selbst mit # anfingen — dadurch landeten alle Woerter der
    Kommentarzeilen ("Dauerhaft", "gesperrt", "Sexuelles") in der Sperrliste
    und jede zeilenweise Zaehlung lieferte unsinnige Werte.
    """
    out = set()
    if not os.path.exists(pfad):
        return out
    for zeile in open(pfad, encoding="utf-8"):
        z = zeile.strip()
        if not z or z.startswith("#"):
            continue
        for token in z.split():
            if token.startswith("#"):
                break
            out.add(normal(token))
    return out


def normal(w):
    w = w.replace("\u00df", "ss").upper()
    for a, b in (("\u00c4", "AE"), ("\u00d6", "OE"), ("\u00dc", "UE")):
        w = w.replace(a, b)
    return w


UMLAUT_PL = (("AE", "A"), ("OE", "O"), ("UE", "U"))


def plural_verdacht(w, wortschatz):
    """Heuristik: koennte w eine Mehrzahlform sein, die nicht markiert ist?

    Erkennt zusaetzlich zur Endungspruefung den Umlautplural (NAEGEL -> NAGEL,
    LAEDEN -> LADEN, BUECHER -> BUCH). Ergebnis ist ein Verdacht, kein Befund:
    die Frageschreibung prueft nach, gesperrt wird nichts.
    """
    kand = set()
    for endung in ("ER", "EN", "E", "N", "S"):
        if w.endswith(endung) and len(w) - len(endung) >= 3:
            kand.add(w[: -len(endung)])
    kand.add(w)
    for k in list(kand):
        for a, b in UMLAUT_PL:
            if a in k:
                kand.add(k.replace(a, b))
    kand.discard(w)
    return any(k in wortschatz for k in kand)
VORSILBEN = ("AB", "AN", "AUF", "AUS", "BE", "DURCH", "EIN", "ENT", "ER", "MIT",
             "NACH", "UEBER", "UM", "UNTER", "VER", "VOR", "WEG", "ZER", "ZU")


_KEIN_PARTIZIP = None


def lade_keinpartizip(pfad=None):
    """Substantive, die dem Partizip-Muster gleichen (keinpartizip.txt).

    Format je Zeile: WORT [rang]. Rueckgabe: Wort -> Rang (Vorgabe 15000).
    Die Datei hat zwei Abnehmer: ist_partizip (hier) und core.build_lexicon,
    das die Woerter dem Grundwortschatz zuschlaegt.
    """
    global _KEIN_PARTIZIP
    if pfad is None and _KEIN_PARTIZIP is not None:
        return _KEIN_PARTIZIP
    pfad = pfad or os.path.join(HERE, "keinpartizip.txt")
    out = {}
    if os.path.exists(pfad):
        for zeile in open(pfad, encoding="utf-8"):
            z = zeile.strip()
            if not z or z.startswith("#"):
                continue
            p = z.split()
            out[normal(p[0])] = int(p[1]) if len(p) > 1 and p[1].isdigit() else 15000
    if pfad.endswith("keinpartizip.txt"):
        _KEIN_PARTIZIP = out
    return out


def ist_partizip(w):
    """Partizip II erkennen: [Vorsilbe]GE...T/EN, z. B. ABGESETZT, GEMACHT.

    Woerter aus keinpartizip.txt sind ausgenommen: GERICHT, GESICHT, GEBURT
    und viele andere Substantive folgen demselben Muster, sind aber keine
    Partizipien. Ohne diese Ausnahme fehlen sie im ganzen System.
    """
    if w in lade_keinpartizip():
        return False
    if not w.endswith(("T", "EN")):
        return False
    if w.startswith("GE") and len(w) >= 6:
        return True
    for v in VORSILBEN:
        if w.startswith(v + "GE") and len(w) >= len(v) + 6:
            return True
    return False


def enthaelt_loesung(frage, wort, mindest=4):
    """Frage verraet die Loesung, wenn sie deren Wortstamm enthaelt."""
    f = frage.upper().replace("\n", "").replace("-", "")
    for a, b in (("\u00c4", "AE"), ("\u00d6", "OE"), ("\u00dc", "UE"),
                 ("\u00df", "SS")):
        f = f.replace(a, b)
    stamm = wort[:3] if len(wort) <= 5 else wort[:4]
    return len(wort) >= mindest and stamm in f


# --- Wortstamm-Vergleich ----------------------------------------------------
# Zwei Antworten desselben Wortstamms im selben Raster (EKEL und EKLIG, BUND
# und BUENDE) sind ein Mangel. fill.py verhindert das hart, indem es je Raster
# nur einen Eintrag je Stamm zulaesst. Die Ableitung ist bewusst vorsichtig:
# lieber ein Paar uebersehen als unverwandte Woerter gegeneinander sperren.
_SUFFIXE = ("LICHKEIT", "IGKEIT", "SCHAFT", "KEITEN", "HEITEN", "UNGEN",
            "LICH", "HEIT", "KEIT", "ISCH", "CHEN", "LEIN", "UNG", "NIS",
            "BAR", "SAM", "IG", "ER", "EN", "E", "S", "N")
_VOKALE = set("AEIOU")


def stamm(w):
    """Grober Wortstamm fuer den Dublettenvergleich im Raster.

    Zwei Schritte: die laengste bekannte Endung abtrennen, danach das
    Schwa-E vor dem Schlusskonsonanten tilgen. Damit fallen EKEL und EKLIG
    auf denselben Stamm EKL, waehrend LESER (LES) und LASER (LAS)
    auseinanderbleiben.
    """
    s = w
    for suf in _SUFFIXE:
        if s.endswith(suf) and len(s) - len(suf) >= 3:
            s = s[: -len(suf)]
            break
    if (len(s) >= 4 and s[-2] == "E"
            and s[-1] not in _VOKALE and s[-3] not in _VOKALE):
        s = s[:-2] + s[-1]
    for a, b in UMLAUT_PL:              # Umlautplural: BUENDE -> BUND
        s = s.replace(a, b)
    return s


def stamm_kollision(woerter):
    """Liste der Woerter, die sich im Raster einen Stamm teilen."""
    from collections import defaultdict
    g = defaultdict(list)
    for w in woerter:
        if len(w) >= 4:
            g[stamm(w)].append(w)
    return [v for v in g.values() if len(v) > 1]


_KENNZ = None


def lade_kennzeichen(pfad=None):
    """Antworten, deren Frage einen Klammerzusatz braucht (kennzeichen.txt).

    Rueckgabe: Wort -> geforderter Zusatz, z. B. "GLOWUP" -> "(engl.)".
    Plurale kommen nicht von hier, sondern aus formen.txt.
    """
    global _KENNZ
    if pfad is None and _KENNZ is not None:
        return _KENNZ
    pfad = pfad or os.path.join(HERE, "kennzeichen.txt")
    out = {}
    if os.path.exists(pfad):
        for zeile in open(pfad, encoding="utf-8"):
            z = zeile.strip()
            if not z or z.startswith("#"):
                continue
            p = z.split()
            if len(p) >= 2:
                out[normal(p[0])] = f"({p[1]})"
    if pfad.endswith("kennzeichen.txt"):
        _KENNZ = out
    return out


def kennzeichen_fehlt(wort, frage):
    """Gibt den fehlenden Zusatz zurueck oder None.

    Deckt drei Faelle ab: englische Woerter und Abkuerzungen aus
    kennzeichen.txt sowie Plurale aus formen.txt.
    """
    soll = lade_kennzeichen().get(wort)
    if soll is None:
        try:
            from core import load_formen
            formen = load_formen()
        except Exception:
            formen = {}
        if formen.get(wort) == "PL":
            soll = "(Pl.)"
    if not soll:
        return None
    # Trennstriche am Zeilenende aufloesen, sonst findet die Suche
    # "ukrainisch" nicht in "Ukrai-\nnisch".
    import re as _re
    f = _re.sub(r"-?\n", "", frage).lower()
    if soll.lower() in f:
        return None
    # Statt der Klammerform genuegt auch die ausgeschriebene Sprache in der
    # Frage: "Dorf auf Ukrainisch" sagt dasselbe wie "(Ukr.)".
    ausgeschrieben = {"(engl.)": "englisch", "(ukr.)": "ukrainisch",
                      "(frz.)": "franzoesisch", "(ital.)": "italienisch",
                      "(span.)": "spanisch", "(lat.)": "latein"}
    lang = ausgeschrieben.get(soll.lower())
    if lang and (lang in f or lang.replace("oe", "ö") in f):
        return None
    return soll
