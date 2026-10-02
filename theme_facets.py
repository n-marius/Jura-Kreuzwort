"""Importiert eine Facettendatei in ein Thema.

  python theme_facets.py facetten_JURA.txt

Dateiformat (eine Facette je Block):

    # THEMA JURA GEWICHT 30
    [Rollen und Personen] 1.0
    RICHTER ANWALT KLAEGER ZEUGE SCHOEFFE
    [Requisiten und Symbolik] 0.6
    ROBE HAMMER WAAGE SIEGEL

Die Zahl hinter der Facette ist die Themennaehe. Sie steuert zweierlei:
  >= 0.8  KERN     volles Fuellgewicht, sanfte Wiederholungsdaempfung,
                   Frage MUSS thematisch sein
  >= 0.45 UMFELD   mittleres Gewicht, thematische Frage erwuenscht
  <  0.45 KOLORIT  knapp ueber Fuellwort, harte Daempfung wie ein Fuellwort,
                   thematische Frage nur, wenn sie nicht gezwungen wirkt

Die Facettennamen werden zur spaeteren Sichtpruefung mitgespeichert.

Zwei Pflichtbestandteile jeder Facettendatei (siehe README 2a):

  DIREKTLISTE   Woerter, die direkt hinter der Kopfzeile stehen, noch vor der
                ersten [Facette], gelten als Direktliste des Themas und
                bekommen Naehe 1.0. Das ist der erste Abruf: was faellt zum
                Thema unmittelbar ein, ohne Ordnungsraster.
  KURZWOERTER   Eine Facette, deren Name mit "Kurz" beginnt. Sie sammelt
                gezielt Antworten mit vier bis sechs Buchstaben. Fehlt sie
                oder bleibt der Kurzwortanteil unter 25 %, meldet das Skript
                das als Mangel.
"""
import sys, json, os, re
from collections import Counter
from themes import _n, PATH
from wordcheck import ist_partizip

txt = open(sys.argv[1], encoding="utf-8").read().splitlines()
name = gewicht = None
FACETTE_MAX = 0.95                          # Obergrenze fuer Facettenwerte
ALLTAG = set()                              # alltagstaugliche Woerter (Stern)
verworfen = {"zu kurz": [], "Partizipverdacht": []}
facette, naehe = "Direkt zum Thema", 1.0     # gilt bis zur ersten [Facette]
woerter, facmap = {}, {}
for line in txt:
    line = line.strip()
    if not line:
        continue
    m = re.match(r"#\s*THEMA\s+(\S+)\s+GEWICHT\s+([\d.]+)", line, re.I)
    if m:
        name, gewicht = m.group(1).upper(), float(m.group(2))
        continue
    if line.startswith("#"):
        continue
    m = re.match(r"\[(.+?)\]\s*([\d.]+)?", line)
    if m:
        facette = m.group(1).strip()
        naehe = float(m.group(2)) if m.group(2) else 1.0
        # Facetten werden bei FACETTE_MAX gekappt. Die Direktliste behaelt 1.0
        # und damit einen kleinen Vorsprung: die Woerter, die einem zum Thema
        # unmittelbar einfallen, sollen vor denen stehen, die erst ueber eine
        # Facette dazukommen. Das Fuellgewicht waechst quadratisch, 0,95 gegen
        # 1,0 sind rund zehn Prozent Unterschied - spuerbar, nicht dominant.
        naehe = min(naehe, FACETTE_MAX)
        continue
    for w in line.split():
        # Ein Stern hinter dem Wort heisst: alltagstauglich. Das Wort gehoert
        # damit nicht nur zu diesem Thema, sondern dauerhaft in den
        # allgemeinen Wortschatz (alltag.txt). Die Markierung wird Wort fuer
        # Wort gesetzt, nicht je Facette - innerhalb einer Facette stehen
        # regelmaessig beides nebeneinander: ZEUGE ja, ZEDENT nein.
        alltag = w.endswith("*")
        if alltag:
            w = w[:-1]
            ALLTAG.add(_n(w))
        w = _n(w)
        if len(w) < 4:
            # Der Fuellwortschatz beginnt bei vier Zeichen (core.MIN_LEN);
            # kuerzere Handwoerter sind nur als Vorgabewort setzbar.
            verworfen["zu kurz"].append(w)
            continue
        if ist_partizip(w):
            # Echte Substantive, die dem Muster gleichen, gehoeren nach
            # keinpartizip.txt - dann laesst ist_partizip sie durch.
            verworfen["Partizipverdacht"].append(w)
            continue
        if w not in woerter or naehe > woerter[w]:
            woerter[w], facmap[w] = naehe, facette

t = json.load(open(PATH, encoding="utf-8")) if os.path.exists(PATH) else {}
spec = t.setdefault(name, {"gewicht": gewicht, "woerter": {}, "facetten": {}})
spec["gewicht"] = gewicht
ws = spec["woerter"]
if isinstance(ws, list):
    ws = {w: 1.0 for w in ws}
fm = spec.setdefault("facetten", {})
neu = 0
for w, nah in woerter.items():
    if w not in ws or nah > ws[w]:
        ws[w] = nah
        neu += 1
    fm.setdefault(w, facmap[w])
spec["woerter"], spec["facetten"] = ws, fm
json.dump(t, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
h = Counter(len(w) for w in ws)
# Der Kurzwortanteil wird an der HANDLISTE gemessen, nicht am fertigen Thema.
# Die Automatikstufen 2 bis 4 schuetten spaeter ueberwiegend lange
# Zusammensetzungen dazu und druecken jede Quote, ohne dass die Handliste
# schlechter geworden waere. Gepruefte Groesse ist deshalb diese Datei.
hand = Counter(len(w) for w in woerter)
hand_kurz = sum(v for k, v in hand.items() if 4 <= k <= 6)
hand_anteil = hand_kurz / max(1, len(woerter))
st = Counter("KERN" if v >= 0.8 else ("UMFELD" if v >= 0.45 else "KOLORIT")
             for v in ws.values())
print(f"{name}: +{neu}, jetzt {len(ws)} Woerter, Gewicht {gewicht}")
for grund, liste in verworfen.items():
    if liste:
        print(f"  verworfen ({grund}): {len(liste)}  "
              + " ".join(sorted(set(liste))[:30]))
print("Stufen:", dict(st))
print("Laengen:", " ".join(f"{k}:{h[k]}" for k in sorted(h)))
kurz = sum(v for k, v in h.items() if 4 <= k <= 6)
anteil = kurz / max(1, len(ws))
print(f"kurz 4-6: Handliste {hand_kurz}/{len(woerter)} ({hand_anteil:.0%}), "
      f"Thema gesamt {kurz} ({anteil:.0%})")

# --- Pflichtbestandteile pruefen -------------------------------------------
direkt = sum(1 for w, fac in facmap.items() if fac == "Direkt zum Thema")
kurzfac = sorted({fac for fac in facmap.values()
                  if fac and fac.lower().startswith("kurz")})
if direkt:
    print(f"Direktliste: {direkt} Woerter mit Naehe 1.0")
else:
    print("MANGEL: keine Direktliste. Vor die erste [Facette] gehoeren die "
          "Woerter, die dir zum Thema unmittelbar einfallen (Naehe 1.0).")
if kurzfac:
    kw = sum(1 for w, fac in facmap.items() if fac in kurzfac)
    print(f"Kurzwortfacette: {' / '.join(kurzfac)} mit {kw} Woertern")
else:
    print("MANGEL: keine Kurzwortfacette. Lege eine Facette an, deren Name mit "
          "'Kurz' beginnt, und sammle dort gezielt Antworten mit vier bis "
          "sechs Buchstaben.")
if hand_anteil < 0.25:
    print(f"MANGEL: Kurzwortanteil der Handliste {hand_anteil:.0%}, gefordert "
          f"sind mindestens 25 %. "
          "Die Kurzwortfacette erweitern, nicht die Automatik nochmals laufen "
          "lassen - sie liefert ueberwiegend lange Zusammensetzungen.")


# --- alltagstaugliche Woerter dauerhaft sichern -----------------------------
if ALLTAG:
    pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alltag.txt")
    schon = set()
    if os.path.exists(pfad):
        for z in open(pfad, encoding="utf-8"):
            z = z.strip()
            if z and not z.startswith("#"):
                schon.add(z.split()[0])
    neu = sorted(ALLTAG - schon)
    if neu:
        with open(pfad, "a", encoding="utf-8") as f:
            if not schon:
                f.write("# Woerter aus Themenlisten, die auch ohne ihr Thema\n"
                        "# gelaeufig sind (Markierung * in der Facettendatei).\n"
                        "# core.build_lexicon nimmt sie dauerhaft auf.\n")
            for w in neu:
                f.write(w + "\n")
    print(f"alltagstauglich: {len(ALLTAG)} markiert, {len(neu)} neu in alltag.txt")
