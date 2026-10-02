"""Einstellungen fuer das freie deutsche Kreuzwortraetsel (kr_*.py).

Alle Seitenmasse sind fuer das ganze Buch fest. Masse in mm, bezogen auf das
Endformat 148 x 210 mm (Beschnitt und Bundsteg regelt bookpdf._seitenanfang).
"""
# ---------------------------------------------------------------- Seite
SATZ_B = 132.0          # Breite von Raster und Fragenfenster
SATZ_OBEN = 9.0         # Oberkante Endformat -> Versalhoehe der Ueberschrift
SATZ_UNTEN = 8.0        # Unterkante Endformat -> Unterkante Fragenfenster
UEBER_PT = 14           # Ueberschrift "– § N –", fett (wie LÖSUNGEN)
UEBER_ABSTAND = 3.5     # Ueberschrift -> Rasterbereich
FENSTER_H = 36.0        # Fragenfenster, fest; fasst 11 Zeilen
FENSTER_ABSTAND = 3.5   # Rasterbereich -> Fragenfenster

# ---------------------------------------------------------------- Raster
ZELLE_MM = 7.5          # Antwortkaestchen (Schwedenraetsel: 11 mm)
RASTER_W, RASTER_H = 17, 19   # 127,5 x 142,5 mm im Rasterbereich 132 x ~146 mm
NR_PT = 5.2             # Fragenummer im Kaestchen, kleiner als in der Liste
NR_PAD_MM = 0.5         # Abstand der Nummer von der Kaestchenecke

# ---------------------------------------------------------------- Fragenliste
CAP_MM = 2.0            # wie in den Frageblöcken (7,90 pt)
ZEILENABSTAND = 1.22    # Vielfaches der Schriftgroesse
TRENNER = "   "         # zwischen zwei Fragen
KOPF_W, KOPF_S = "Waagerecht", "Senkrecht"
KOPF_EIGENE_ZEILE = False   # True: Blocktitel auf eigener Zeile statt vorangestellt

# ---------------------------------------------------------------- Wortschatz
WORTLISTE = "themen/facetten_JURA_KR.txt"   # einziger Wortschatz (Facettenformat)
THEMA = "JURA"          # Themenkennung fuer themengebundene Fragen in clues.json
MIN_NAH = 0.0           # Mindestnaehe (0 = auch Kolorit)
MIN_LEN = 3
MAX_LEN = 10            # laengere Woerter machen das Bild unruhig (vorher bis 19)

# ---------------------------------------------------------------- Erzeugung
VERSUCHE = 240          # Aufbauversuche je Seite (alle Prozesse zusammen); der beste zaehlt
PARALLEL = 8            # Rechenprozesse (i5-8350U: 8 logische Kerne); 1 = Einzelbetrieb.
#                         Umgebungsvariable PARALLEL ueberschreibt. Die Versuche werden
#                         gleichmaessig auf die Prozesse verteilt.
ANLAEUFE = 4            # Anlaeufe je Seite; jeder weitere mit Seed + 100. Scheitert die
#                         Seite in allen, haelt der Lauf an (folgende Seiten bauen auf ihr auf).
FORTSCHRITT = True      # Zeile je Seite und Anlauf mit Uhrzeit
STICHPROBE = 220        # Kandidatenwoerter je Legeschritt
MAX_WOERTER = 26        # Obergrenze je Seite (vorher 38)
MIN_WOERTER = 20
WIED_ZIEL = 0.10        # Regel: 10 % bereits im Buch verwendete Woerter
WIED_MAX = 0.15         # harte Grenze je Seite; liegt der Buchschnitt ueber
#                         WIED_ZIEL, gilt fuer die naechste Seite WIED_ZIEL hart
WIED_STRAFE = 25.0      # Bewertungsabzug je Wiederholung ueber WIED_ZIEL
WIED_DATEI = "kr_wiederholung.json"   # Seite -> [Woerter, Wiederholungen]
GITTER = 2              # Zeilen-/Spaltenraster: waagerechte Woerter nur in Zeilen 0,2,4 ..,
#                         senkrechte nur in Spalten 0,2,4 .. (1 = frei, wie bisher). Ergibt das
#                         klare Zeilen-/Spaltenmuster eines deutschen Kreuzwortraetsels.
KREUZ_MIN = 0.25        # Kreuzungsrate = gekreuzte Zellen / Buchstabenzellen
FUELL_MIN = 0.30        # Buchstabenzellen / Rasterzellen
FUELL_MAX = 0.50        # Obergrenze, damit die Seite nicht ueberfuellt wirkt
# Kurze Woerter benachteiligen (Wortlaenge -> Abzug). Wirkt dreifach:
#   Legebewertung (eine Kreuzung = 3 Punkte), Schlussdurchgang (ein kurzes
#   Wort braucht mehr Kreuzungen als Strafe/3) und Auswahl des besten Versuchs
#   (doppelter Abzug je kurzem Wort). KURZ_GEWICHT daempft zusaetzlich die
#   Ziehwahrscheinlichkeit.
KURZ_STRAFE = {3: 9.0, 4: 3.5, 5: 1.5}
KURZ_GEWICHT = {3: 0.15, 4: 0.45, 5: 0.75}
# Bewertung eines Versuchs: Buchstabenzellen + Gewicht * Kreuzungen
BONUS_KREUZ = 1.5

PUZZLE_DIR = "kr_puzzles"
LEDGER = "kr_used_words.json"
