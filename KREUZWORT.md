# Freies Kreuzworträtsel (Jura-Buch)

Parallel zum Schwedenrätsel. `book.py`, `render_book.py` und `puzzles/` bleiben unberührt.

## Dateien
- `kr_config.py` – alle Maße und Schwellen (Seite, Raster, Fragenfenster, Erzeugung)
- `kreuz/platzierung.py` – Legealgorithmus
- `kr_book.py` – Seiten erzeugen → `kr_puzzles/NNN.pkl`, Wortkonto `kr_used_words.json`, Wiederholungen je Seite `kr_wiederholung.json`
- `kr_render.py` – `kr_raetselbuch.pdf` (Rätsel + Lösungsminiraster) bzw. `--nur-loesungen` → `kr_loesungsprobe.pdf`
- `collect_clues.py` – mit `PUZZLE_DIR=kr_puzzles` für dieses Buch

## Ablauf (Windows, PowerShell, im Paketordner)
```
$env:PYTHONUTF8=1
python -m pip install -r requirements.txt
.\start_kreuzwort.ps1 1 50          # entspricht: python -u kr_book.py 1 50, Log in kr_lauf.txt
```
`kr_book.py` setzt nach Abbruch mit demselben Befehl fort (fertige Seiten werden uebersprungen).
Die Zeilen darunter sind die Einzelschritte danach:
```
python kr_book.py 1 10
set PUZZLE_DIR=kr_puzzles
python collect_clues.py
python kr_render.py ausgabe
python kr_render.py ausgabe --nur-loesungen
```
Neubau einer Seite: `python kr_book.py --rollback 7 7`, dann
`set SEED_VERSATZ=100` und `python kr_book.py 7 7`.

## Ausfuehrung (aus Band 2 uebernommen)
- `kr_config.PARALLEL = 8` Prozesse (Umgebungsvariable `PARALLEL` ueberschreibt, 1 = Einzelbetrieb); die `VERSUCHE` (240 je Seite) werden gleichmaessig verteilt, der beste Aufbau zaehlt. Prozesse starten per `spawn` (wie unter Windows noetig).
- `ANLAEUFE = 4`: schlaegt eine Seite fehl, folgt ein neuer Anlauf mit Seed + 100. Scheitert sie in allen, haelt der Lauf an, weil die folgenden Seiten auf ihr aufbauen. Rueckgabewert 1 bei Scheitern.
- Konto, Wiederholungsdatei und Seitendateien werden atomar geschrieben (Nebendatei, dann ersetzen); ein Abbruch beschaedigt nichts.
- Fortschrittszeilen mit Uhrzeit (`FORTSCHRITT`), am Ende Summe der neuen Seiten.
- Gemessen (4 Kerne, Sandbox): 240 Versuche je Seite = ca. 67 s; ein Kern schafft 60 Versuche in ca. 66 s. Mit 8 Prozessen ist rund 1 min je Seite zu erwarten (nicht gemessen).

## Regeln des Legealgorithmus
- Gitter (`GITTER = 2`): waagerechte Woerter nur in Zeilen 0, 2, 4 ..., senkrechte nur in Spalten 0, 2, 4 ... Das ergibt das Zeilen-/Spaltenmuster; Woerter 3-10 Buchstaben, 20-26 je Seite, Fuellung 0,30-0,50.
- jedes Wort kreuzt mindestens ein anderes; keine parallel anliegenden Buchstaben
- beginnen ein waagerechtes und ein senkrechtes Wort in derselben Zelle, teilen sie sich eine Nummer
- ein Eintrag je Wortstamm pro Seite; Sperre der letzten `SPERRE_SEITEN` Seiten und `WORT_MAX` aus `core.py`
- Wortschatz: ausschließlich `WORTLISTE` (`themen/facetten_JURA_KR.txt`), kein Lexikon, keine Sperrlisten; 3–19 Buchstaben, über 17 nur senkrecht
- Wiederholungen: Ziel 10 % (Bewertungsabzug darüber), hart 15 % je Seite; liegt der Buchschnitt über 10 %, gilt für die nächste Seite 10 % hart
- kurze Wörter benachteiligt: `KURZ_STRAFE` (Legebewertung, Schlussdurchgang, Versuchsauswahl) und `KURZ_GEWICHT` (Ziehwahrscheinlichkeit), 3 Buchstaben am stärksten
- `VERSUCHE` als Umgebungsvariable überschreibt den Wert aus `kr_config.py`
- Vorgaben je Seite aus `plan.json` (`pflicht`)

## Seite
Überschrift „– § N –“ (Seitenposition), Raster, Fragenfenster mit den Blöcken Waagerecht und Senkrecht. Keine Seitenzahl unten. `KOPF_EIGENE_ZEILE` setzt die Blocktitel auf eine eigene Zeile.

## Fragen
Aus `clues.json` wie bisher; Kästchenumbrüche werden beim Setzen entfernt
(`Amts-\nkleid` → `Amtskleid`). `kr_render.py` meldet fehlende Fragen, fehlendes „(Abk.)“ (Facetten „Abk…“) und „(lat.)“ (Facetten „Latein…“),
Überlauf des Fragenfensters, Wiederholungen, fehlende Zusätze und verratene Stämme.
