"""Baut words_v3.json und fallback_v3.json neu.

Braucht drei Quelldateien in ./wl/ :
  index.dic     igerman98 Hunspell-Lemmaliste
  de_50k.txt    Haeufigkeitsliste, 50.000 Formen
  de_full.txt   Haeufigkeitsliste, vollstaendig

Beide Quellen stammen aus oeffentlichen Repositorien (wooorm/dictionaries,
hermitdave/FrequencyWords). Sie werden nur hier gebraucht, nicht zur Laufzeit,
und liegen deshalb nicht im Paket. Die fertigen JSON-Dateien reichen aus.

Filter, alle deterministisch:
  * nur Lemmata: Substantive (Flag m, kein h), Adjektive (Flag A)
  * keine Infinitive, keine adjektivisch gebrauchten Partizipien
  * keine Partizipien nach Vorsilbenmuster
  * Plurale und einfache Komparative werden nicht verworfen, sondern mit
    "form": "PL" bzw. "KOMP" gekennzeichnet. Sie sind erfragbar, bekommen aber
    ein geringeres Fuellgewicht und verlangen eine passende Frage.
  * Superlative fliegen raus (schwer erfragbar)
  * Pronomen- und Artikelformen fliegen raus, bis auf eine kleine Positivliste
    gut erfragbarer Woerter (ALLE, KEINER, NIEMAND ...)
  * Grundwortschatz: Haeufigkeitsrang < 25.000
  * Rueckfall: Rang 25.000 bis 100.000  (darunter wird es unbekannt)
  * stopwords.txt wird in beiden Stufen ausgeschlossen
"""
import json, os, re
from collections import Counter
from wordcheck import ist_partizip, lade_sperrliste

HERE = os.path.dirname(os.path.abspath(__file__))
WL = os.path.join(HERE, "wl")
PRIM_MAX, FB_MAX = 25000, 100000
ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

PRONOMEN = set("""DEREN DESSEN DENEN DERER JENE JENER JENEM JENEN JENES WELCHE
WELCHER WELCHEM WELCHEN WELCHES DIESE DIESER DIESEM DIESEN DIESES EUCH EURER
IHNEN IHRER MEINER DEINER SEINER UNSER UNSERE EURE JEDER JEDEM JEDEN JEDES
MANCHE MANCHER SOLCHE SOLCHER BEIDE BEIDEN ANDERE ANDEREN ALLER ALLEM ALLEN
DERSELBE DASSELBE DIESELBE ETLICHE SAEMTLICHE""".split())

# trotz Pronomencharakter zugelassen, weil gut erfragbar
PRONOMEN_OK = set("ALLE KEINER KEINE NIEMAND JEMAND ETWAS NICHTS BEIDES "
                  "EINANDER SELBER SELBST".split())
PRONOMEN -= PRONOMEN_OK


def norm(w):
    w = w.replace("\u00df", "ss").upper()
    for a, b in (("\u00c4", "AE"), ("\u00d6", "OE"), ("\u00dc", "UE")):
        w = w.replace(a, b)
    return w


def entumlaut(w):
    for a, b in (("AE", "A"), ("OE", "O"), ("UE", "U")):
        w = w.replace(a, b)
    return w


def lade_freq(pfad):
    f = {}
    for r, line in enumerate(open(pfad, encoding="utf-8")):
        p = line.split()
        if len(p) == 2:
            f.setdefault(p[0], r)
    return f


def main():
    freq50 = lade_freq(os.path.join(WL, "de_50k.txt"))
    freqall = lade_freq(os.path.join(WL, "de_full.txt"))
    # zeilenweise, vollstaendige Kommentarzeilen werden uebersprungen
    stop = lade_sperrliste(os.path.join(HERE, "stopwords.txt"))

    adj, inf, roh = set(), set(), []
    f = open(os.path.join(WL, "index.dic"), encoding="utf-8", errors="replace")
    next(f)
    for line in f:
        line = line.strip()
        if not line or line.startswith("\t"):
            continue
        p = line.split("/")
        lem, fl = p[0], (p[1] if len(p) > 1 else "")
        if lem and lem[0].islower():
            if "A" in fl:
                adj.add(lem)
            if "I" in fl:
                inf.add(lem)
        roh.append((lem, fl))

    kandidaten = {}
    for lem, fl in roh:
        if not lem:
            continue
        w = norm(lem)
        if not set(w) <= ALLOWED or not 3 <= len(w) <= 15:
            continue
        if w in stop or w in PRONOMEN or ist_partizip(w):
            continue
        low = lem.lower()
        if lem[0].isupper():
            if "m" not in fl or "h" in fl or low in inf or low in adj:
                continue
            art = "N"
        else:
            if "A" not in fl or low in inf:
                continue
            art = "A"
        rang = freqall.get(low, 10 ** 9)
        r50 = freq50.get(low, 10 ** 9)
        rang = min(rang, r50)
        if w not in kandidaten or rang < kandidaten[w][0]:
            kandidaten[w] = (rang, lem, art)

    haeufig = {w for w, v in kandidaten.items() if v[0] < PRIM_MAX}

    def ist_plural(w):
        s = entumlaut(w)
        for endung in ("ER", "EN", "E", "N", "S"):
            if s.endswith(endung) and len(s) - len(endung) >= 3:
                if s[:-len(endung)] in haeufig:
                    return True
        return False

    import re
    ORD = re.compile(r"^(ERST|ZWEIT|DRITT|VIERT|FUENFT|SECHST|SIEBT|ACHT|NEUNT|"
                     r"ZEHNT|ELFT|ZWOELFT|HUNDERTST|TAUSENDST)(E|EN|ER|ES|EM)?$")
    # Die Grundformen MEIN, DEIN, SELBE ... bleiben zugelassen: sie sind mit
    # einer Abgrenzungsfrage erfragbar ("Nicht dein, sondern ..."). Nur die
    # voll flektierten Formen fliegen raus.
    POSS = re.compile(r"^(MEIN|DEIN|IHR|UNSER|EUER)(E|EN|ER|ES|EM)$")

    def ist_superlativ(w, art):
        return art == "A" and len(w) >= 6 and w.endswith(("STE", "STEN", "ESTE"))

    def ist_flexionsform(w, art):
        """Substantivierte Komparative, Ordnungszahlen, Possessivformen."""
        if art == "A" and len(w) >= 6 and w.endswith(("ERE", "EREN", "ERES",
                                                      "EREM", "ERER")):
            return True                     # INNERE, AEUSSERE, LETZTERE ...
        if art != "N" and ORD.match(w):
            return True
        if art != "N" and POSS.match(w):
            return True
        return False

    def ist_komparativ(w, art):
        return (art == "A" and len(w) >= 5 and w.endswith("ER")
                and entumlaut(w[:-2]) in haeufig)

    prim, fb = [], []
    for w, (rang, lem, art) in sorted(kandidaten.items(), key=lambda x: x[1][0]):
        if ist_superlativ(w, art) or ist_flexionsform(w, art):
            continue
        form = None
        if ist_komparativ(w, art):
            form = "KOMP"
        elif ist_plural(w):
            form = "PL"
        eintrag = {"w": w, "lemma": lem, "rank": rang, "k": art}
        if form:
            eintrag["form"] = form
        if rang < PRIM_MAX:
            prim.append(eintrag)
        elif rang < FB_MAX:
            fb.append(eintrag)

    zusatz = """nicht nunmehr mithin ebenda sehr immer kaum stets bald sofort
    zumal dennoch ferner indes sogar vorab oben unten gestern heute morgen nie
    oft gern etwa fast zudem daher deshalb somit also zwar aber oder weil obwohl
    falls sonst gemaess laut trotz wegen binnen mangels kraft zwecks infolge
    hierbei sodann naemlich zunaechst jedoch vielmehr insoweit insofern ansonsten
    uebrigens egal okay ich sie wir uns ihm ihn mir dir sich man wer was wie wann
    warum wohin woher mich dich etwas nichts jemand niemand irgend allein
    zusammen bloss eben schon noch nur erst wieder dort hier damals einst
    neulich kuenftig alsbald derzeit alle keiner keine niemand jemand etwas
    nichts beides einander selber selbst""".split()
    da = {d["w"] for d in prim}
    for z in zusatz:
        w = norm(z)
        if 3 <= len(w) <= 15 and set(w) <= ALLOWED and w not in da and w not in stop:
            prim.append({"w": w, "lemma": z, "rank": 4000, "k": "P"})

    json.dump(prim, open(os.path.join(HERE, "words_v3.json"), "w",
                         encoding="utf-8"), ensure_ascii=False)
    json.dump(fb, open(os.path.join(HERE, "fallback_v3.json"), "w",
                       encoding="utf-8"), ensure_ascii=False)
    print("Grundwortschatz:", len(prim), Counter(d["k"] for d in prim))
    print("Rueckfall:", len(fb))
    print("Formen:", Counter(d.get("form", "GRUND") for d in prim + fb))
    for name, lst in (("Grundwortschatz", prim), ("Rueckfall", fb)):
        h = Counter(len(d["w"]) for d in lst)
        print(f"  {name} Laengen:", " ".join(f"{k}:{h[k]}" for k in sorted(h)))


if __name__ == "__main__":
    main()
