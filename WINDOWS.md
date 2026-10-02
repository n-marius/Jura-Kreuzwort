# Betrieb auf einem Windows-PC

Dieses Paket laeuft unveraendert unter Windows. Es braucht nur Python 3.10
oder neuer sowie zwei Zusatzbibliotheken.

## Einrichtung

    python -m pip install -r requirements.txt

## Vor jeder Sitzung

In der PowerShell im Paketordner:

    $env:PYTHONUTF8=1

Damit liest und schreibt Python alle Dateien als UTF-8, unabhaengig von der
Windows-Systemkodierung.

## Befehle

Alle Befehle aus README.md gelten unveraendert. Der Interpreter heisst unter
Windows `python`, nicht `python3`; die Dokumentation ist entsprechend
angepasst. Fuer lange Laeufe empfiehlt sich

    python -u book.py 1 50 2>&1 | Tee-Object lauf.txt

`-u` schaltet die Ausgabepufferung ab, sonst erscheint beim Umleiten
minutenlang nichts.

## Aenderungen gegenueber der Sandbox-Fassung

* `render_book.py` legt ohne Argument den Unterordner `ausgabe` an statt
  `/mnt/user-data/outputs`.
* `core.MAX_NODES` 10000 -> 12000, `core.make_puzzle(tries=)` 45 -> 50.
* `book.py` laeuft ohne Aufsicht durch: fertige Seiten werden uebersprungen
  (Wiederaufnahme nach Abbruch mit demselben Befehl), eine misslungene Seite
  wird bis zu `VERSUCHE` mal mit um 100 verschobenem Rasterfenster wiederholt,
  und eine Ausnahme in einer Seite beendet den Lauf nicht. Am Ende steht eine
  Bilanz; der Rueckgabewert ist 1, wenn Seiten gescheitert sind.
* `collect_clues.py` meldet zusaetzlich KERNBEGRIFF MIT NEUTRALER FRAGE und
  ALLE FASSUNGEN BUCHFREMD (siehe README-Abschnitt zum Rendern).
* Seitenzahl auf geraden Seiten unten links, auf ungeraden unten rechts; der
  Inhalt gerader Seiten steht zusaetzlich 1 mm weiter links
  (`bookpdf.GERADE_LINKS`).
* `core.GEWICHT_FAKTOR = 2.15` hebt alle Themengewichte auf den Pegel des
  Vorgaengerbuchs, ohne die Verhaeltnisse zwischen den Themen zu aendern.
* `altwoerter.txt`: Wunschwoerter frueherer Baende sind normal ziehbar.
  Fuer ein voellig neues Buch die Datei loeschen (`neues_buch.py` tut es).
* Wiederholungsdaempfung auf rund 10 Prozent eingestellt
  (`REUSE_THEMA`, `REUSE_FILL`, `KURZ_DAEMPFUNG`, `WIED_ZIEL`, `WIED_MAX`,
  `WIED_STRAFE`).
* `ersetze_wort.py`: Stufe 2 hat einen Zeitdeckel von 360 s, Stufe 3 von
  720 s (`ZEIT_STUFE2`, `ZEIT_STUFE3`). Der Deckel wird nicht mehr nur
  zwischen den Runden geprueft, sondern auch innerhalb der Rekursion; bei
  Ablauf bricht die Stufe sofort ab und die naechste uebernimmt. Nach Stufe 3
  folgt unmittelbar der Neubau der Seite, eine vierte Stufe gibt es nicht.
* `core.update_ledger()` traegt Wortwechsel unter einer Dateisperre
  (`used_words.json.lock`) nach: gelesen wird der Stand von der Platte, dann
  werden nur die eigenen Aenderungen angewendet. Dadurch koennen mehrere
  Ersetzungslaeufe gleichzeitig arbeiten, ohne sich zu ueberschreiben.

## Parallelbetrieb der Ersetzungen

Mehrere `ersetze_wort.py`-Laeufe duerfen gleichzeitig laufen, solange sie
**verschiedene Seiten** betreffen. Jeder Prozess belegt rund 40 MB und einen
Kern. Zwei Laeufe auf derselben Seite sind nicht zulaessig, weil beide
dieselbe `puzzles/NN.pkl` schreiben.

`book.py` bleibt strikt sequenziell: jede Seite liest die `.pkl`-Dateien der
beiden vorangegangenen Seiten, um deren Themenwoerter zu sperren.

Nach einem Parallellauf pruefen, ob zwei Prozesse zufaellig dasselbe Wort
gewaehlt haben:

    python -c "import json;d=json.load(open('used_words.json',encoding='utf-8'));print({k:v for k,v in d.items() if v>1})"
