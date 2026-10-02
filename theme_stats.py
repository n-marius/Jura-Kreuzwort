"""Bilanz der Themenlisten und Reichweitenrechnung.

  python theme_stats.py            (Buchumfang aus core.GESAMT_RAETSEL)
  python theme_stats.py 80         (abweichender Umfang)

Es gibt KEINE Zielgroesse je Thema und keine Obergrenze. Der Anspruch lautet:
so viele sinnvolle Woerter wie moeglich. Ein Nischenthema wie eine einzelne
Stadt gibt vielleicht 250 her, Jura oder Reisen mehrere Tausend - beides ist
richtig. Mehr Themen bedeuten immer mehr Gesamtvorrat.

Gemeldet wird deshalb nicht "zu wenig Woerter", sondern nur:
  * der Anteil kurzer Woerter (4 bis 6 Buchstaben) - der ist der echte Engpass
  * die Reichweite: wie oft muesste jedes Kernwort im Schnitt herhalten
"""
import sys
from collections import Counter
from themes import theme_map, load, stufe
from core import ZIEL_KERN, ZIEL_UMFELD, GESAMT_RAETSEL

N = int(sys.argv[1]) if len(sys.argv) > 1 else GESAMT_RAETSEL
tm, alle = load(), theme_map()
# Nach den Automatikstufen ist eine niedrige Quote normal: Subsuche und
# Expander liefern fast nur lange Zusammensetzungen. Gefordert werden 25 %
# an der HANDLISTE (das prueft theme_facets.py). Hier zaehlt, ob genug kurze
# Woerter absolut vorhanden sind - das ist der Engpass beim Fuellen. Gemeldet
# wird nur, wenn beides zugleich verfehlt wird.
MIN_KURZ = 0.12                       # Quote nach der Automatik
KURZ_JE_RAETSEL = 4                   # kurze Themenwoerter, die ein Thema je
#                                       Raetsel beisteuern koennen soll
MIN_KURZ_ABS = 40                     # Untergrenze auch bei kleinen Buechern

print(f"Buchumfang {N} Raetsel | Bedarf {N*ZIEL_KERN} Kern-, "
      f"{N*ZIEL_UMFELD} Umfeldeinsaetze")
ges = Counter()
for name in sorted(tm):
    ws = tm[name]["woerter"]
    if isinstance(ws, list):
        ws = {w: 1.0 for w in ws}
    st = Counter(stufe(v) for v in ws.values())
    kurz = sum(1 for w in ws if 4 <= len(w) <= 6)
    ges.update(st)
    ges["KURZ"] += kurz
    bedarf = max(MIN_KURZ_ABS, N * KURZ_JE_RAETSEL)
    hinweis = ("   kurze Woerter ergaenzen"
               if kurz < len(ws) * MIN_KURZ and kurz < bedarf else "")
    print(f"  {name:14s} {len(ws):5d}  Kern {st['KERN']:5d}  Umfeld "
          f"{st['UMFELD']:4d}  Kolorit {st['KOLORIT']:5d}  "
          f"kurz {kurz:4d} ({kurz/max(1,len(ws)):3.0%}){hinweis}")
print(f"  {'GESAMT':14s} {len(alle):5d}  Kern {ges['KERN']:5d}  Umfeld "
      f"{ges['UMFELD']:4d}  Kolorit {ges['KOLORIT']:5d}  kurz {ges['KURZ']:4d}")

kurz_bedarf = N * 25                  # grobe Zahl kurzer Slots im ganzen Buch
print(f"Kurze Woerter (4-6) gesamt: {ges['KURZ']} bei rund {kurz_bedarf} "
      f"kurzen Slots im Buch - "
      f"{'ausreichend' if ges['KURZ'] >= kurz_bedarf else 'knapp'}")

reichweite = N * ZIEL_KERN / max(1, ges["KERN"])
if reichweite <= 1:
    urteil = "jedes Kernwort reicht einmal - Wiederholungen praktisch ausgeschlossen"
elif reichweite <= 2:
    urteil = "vereinzelte Wiederholungen zu erwarten"
else:
    urteil = "haeufige Wiederholungen unvermeidlich - Facetten erweitern"
print(f"Reichweite: {reichweite:.2f} Einsaetze je Kernwort - {urteil}")
