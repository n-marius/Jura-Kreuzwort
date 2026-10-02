# Schwedenrätsel-Buch — Arbeitsanleitung

Diese Anleitung richtet sich an ein Sprachmodell, das die Produktion durchführt.
Lies sie vollständig, bevor du etwas ausführst.

**Lies zuerst `UEBERGABE_STAND.md`.** Dort steht, was seit dieser Anleitung am
Paket geändert wurde (Druckformat, Prüfdruck, Seitenreihenfolge, vierte
Ersetzungsstufe), welche Regeln der Projektleiter präzisiert hat und welche
Schwächen der Werkzeuge bekannt sind. Bei Widersprüchen gilt das Übergabeblatt.

**Dieses Paket ist themenneutral.** Themen, Gewichte und Wunschwörter kommen vom
Projektleiter im jeweiligen Chat. Der Fragen-Cache ist dagegen dauerhaft und wird
über alle Bücher hinweg weitergeführt.

## Grundhaltung

**Der Projektleiter gibt die Richtung vor, das Modell führt aus.** Themen,
Gewichte, Wunschwörter, Ton und Umfang sind Vorgaben, keine Diskussionsgrundlage.

* **Wunschwörter werden nicht hinterfragt.** Weder das Wort noch die
  mitgelieferte Frage. Ob ein Werbeslogan wirklich existiert, ob ein Name
  erfunden ist, ob eine Frage rätselhaft wirkt — all das ist entschieden. Wörter
  nach `wunschwoerter.txt`, Fragen nach `clues.json`, fertig. Passt eine Frage
  nicht ins Kästchen, wird sie gekürzt oder umgebrochen, nicht verworfen; nur
  diese eine Änderung ist erlaubt und wird gemeldet.
* **Anweisungen umsetzen statt Probleme erzeugen.** Wer eine Aufgabe bekommt,
  erledigt sie. Nicht jede Auffälligkeit ist ein Mangel, und ein gemeldeter
  Scheinmangel kostet den Projektleiter mehr Zeit als er einbringt.
* **Echte Mängel dagegen ansprechen** — kurz, mit Vorschlag, und dann die
  Entscheidung abwarten. Behoben wird auf Anweisung, nicht auf Verdacht.
* **Am Paket wird nur auf ausdrückliche Anweisung geändert.** „Erstelle Rätsel 3"
  heißt: Raster erzeugen, Wortliste prüfen, Fragen schreiben, PDF rendern. Es
  heißt **nicht**: Skripte anpassen, Schwellen verschieben, Listen umbauen. Wer
  beim Arbeiten einen Programmfehler bemerkt, meldet ihn und arbeitet weiter.
* **„Erstelle Rätsel N" schließt Fragen und PDF ein.** Ein Rätsel ohne Fragen
  ist kein Rätsel. Geliefert wird die fertige Seite.

## Ablauf im neuen Chat — Kurzfassung

Kommt das Paket mit einem fertigen Buch an, zuerst `neues_buch.py` laufen
lassen (Abschnitt 0a). Themenneutral heißt: `themes.json` und
`used_words.json` leer, `plan.json` und `puzzles/` fehlen, keine
`facetten_*.txt`. Dauerhaft mitgeführt werden `clues.json` (Fragen-Cache),
`stopwords.txt`, `formen.txt`, `freigabe.txt`, `keinpartizip.txt`,
`kennzeichen.txt` und die drei Wortschatzstufen.

1. Entpacken und `pip install reportlab pyphen --break-system-packages`
   (Abschnitt 0), Buchumfang in `core.py` setzen (`GESAMT_RAETSEL`).
2. Je Thema eine Facettendatei schreiben — **das ist der Hauptaufwand**, Zielgrößen
   in Abschnitt 2a — und mit `theme_build.py` aufbauen (2b).
3. Sichtprüfung und `theme_stats.py` (2c).
4. Wunschwörter nach `wunschwoerter.txt`, `plan_book.py` (Abschnitt 3).
5. Rätsel blockweise erzeugen, im Hintergrund (Abschnitt 4 und 10).
6. **Erst** Wortlisten prüfen und bereinigen (Abschnitt 5), **dann** Fragen
   schreiben (Abschnitt 6) — nie umgekehrt.
7. `fitcheck.py`, dann `render_book.py`, dann ausliefern (Abschnitt 7).
8. Am Ende den vollständigen Stand als ZIP zurückgeben.

## 0a. Neues Buch beginnen

Das Paket trägt zweierlei mit sich: **dauerhaftes Wissen**, das mit jedem Buch
wertvoller wird, und den **Zustand genau eines Buchs**. Beim Wechsel wird nur
das Zweite zurückgesetzt.

```bash
python neues_buch.py                          # Probelauf, zeigt nur an
python neues_buch.py --ja --archiv harz_2026  # legt eine Kopie ab und setzt zurück
```

| wird zurückgesetzt | bleibt |
|---|---|
| `themes.json`, `used_words.json`, `blacklist.txt` (geleert) | `clues.json` |
| `plan.json`, `wunschwoerter.txt` (gelöscht) | `stopwords.txt`, `formen.txt` |
| `puzzles/*.pkl`, `facetten_*.txt` (gelöscht) | `freigabe.txt`, `keinpartizip.txt`, `kennzeichen.txt` |
| `raetselbuch.pdf`, `loesungsprobe.pdf` | `words_v3.json`, `fallback_v3.json`, `selten_v3.json`, `raetselwoerter.txt` |

`facetten_VORLAGE.txt` bleibt als Muster erhalten.

**`clues.json` wird nie gelöscht.** Es ist das Wertvollste im Paket: jede Frage,
die einmal geschrieben wurde, spart beim nächsten Buch Arbeit. Die
themengebundenen Fassungen (Abschnitt 6a-0a) greifen automatisch nur dann,
wenn das jeweilige Thema wieder vorkommt — alte Themen stören also nicht.

**Die Blacklist wird geleert**, weil Sperrungen je Buch gelten. Was dauerhaft
draußen bleiben soll, gehört nach `stopwords.txt`, nicht in die Blacklist.

Danach: `GESAMT_RAETSEL` in `core.py` auf den neuen Umfang setzen, dann weiter
bei Abschnitt 2.

## Begriffe — verbindliche Bedeutung

Diese Wörter werden im ganzen Ablauf und in allen Ausgaben genau so verwendet.

| Begriff | Bedeutung |
|---|---|
| **Themenwortschatz** | alle Wörter eines Themas in `themes.json`, unabhängig von der Nähe. Summe aus Kern, Umfeld und Kolorit. |
| **Nähe** | Zahl 0 bis 1 je Wort. Sie kommt aus der Facette, in der das Wort steht, und bestimmt Füllgewicht, Wiederholungsdämpfung und Anspruch an die Frage. |
| **Kern** | Nähe ≥ 0,8. Echtes Fachvokabular des Themas. Nur aus der Handliste. Die Frage **muss** thematisch sein. |
| **Umfeld** | Nähe 0,45 bis 0,8. Randbereich, Eigennamen, thematisch anschlussfähige Alltagswörter. Thematische Frage erwünscht. |
| **Kolorit** | Nähe unter 0,45. Lose verwandt, meist maschinell gefunden. Thematische Frage nur, wenn sie nicht gezwungen wirkt. Wird bei Wiederholung wie ein Füllwort gedämpft. |
| **`kern=`** | Kennzahl in der Ausgabe von `book.py`: Zahl der Einträge mit Nähe ≥ 0,8. **Die aussagekräftige Zahl.** |
| **`them=`** | Zahl aller Einträge, die im Themenwortschatz stehen, Kolorit eingeschlossen. Lässt sich durch große Listen aufblähen, deshalb nachrangig. |
| **`selten=`** | Einträge aus dem Rückfallwortschatz. Je weniger, desto geläufiger das Rätsel. |
| **Grundwortschatz** | `words_v3.json`, Häufigkeitsrang unter 25.000. Die normalen Füllwörter. |
| **Rätselwortschatz** | `raetselwoerter.txt`: klassische Kreuzworträtselwörter mit fertiger Frage — SMUTJE, ASBEST, KAVALLERIE. Eigene Gewichtsstufe, unabhängig von der Häufigkeit. |
| **Rückfallwortschatz** | `fallback_v3.json`, Rang 25.000 bis 100.000. Notnagel, gering gewichtet. |
| **Vorgabewörter** | Wunschwörter des Projektleiters aus `plan.json`. Stehen außerhalb des Wettbewerbs und sind vor der Nachbesserung geschützt. |
| **Nutzungskonto** | `used_words.json`. Zählt, wie oft ein Wort im laufenden Buch schon vorkam; steuert die Wiederholungsdämpfung. |
| **Wiederholungsdämpfung** | Gewichtsabschlag nach Zahl der bisherigen Verwendungen (`REUSE_FILL`, `REUSE_THEMA` in `core.py`). |
| **Rationierung** | Bremst ein Thema, dessen Vorrat schneller schwindet als das Buch fortschreitet, damit auch die letzten Seiten noch frisches Fachvokabular haben (`rationierung()` in `core.py`). |
| **Sperrliste** | `stopwords.txt` dauerhaft und buchübergreifend, `blacklist.txt` nur für das laufende Buch. |

## 0. Einrichtung

```bash
cd /home/claude && unzip -o /mnt/user-data/uploads/skanvord_book.zip
cd book
pip install reportlab pyphen --break-system-packages -q
python -c "import core; print(len(core.build_lexicon()[0].words), 'Woerter im Lexikon')"
```

Beide Pakete gehören zur Einrichtung, ohne Rückfrage installieren:

* **reportlab** erzeugt das PDF. Ohne es läuft `render_book.py` nicht.
* **pyphen** liefert die deutsche Silbentrennung für `fitcheck.py`. Ohne es
  trennt das Skript hart nach Breite und schreibt „Klagelie-d" statt
  „Klage-lied" — es läuft also, aber die Trennstellen taugen nichts.

Die Prüfzeile muss rund 13.000 Wörter melden. Erscheint eine kleinere Zahl,
fehlt eine Datei aus dem Paket.

## 1. Feste Vorgaben

Entschieden und nicht neu zu verhandeln:

**Format.** A5 hochkant, Raster 17 × 12, Kästchen 11 mm.

**Schrift.** Nimbus Sans Narrow (URW, AFPL/GPL), liegt in `fonts/` bei. Das ist
ein freier Nachbau von Helvetica Narrow und damit dieselbe Entwurfslinie wie das
Vorbild CG Triumvirate Condensed Bold. Versalhöhe 0,718 em, der Grad folgt fest
daraus: 2 mm ÷ 0,718 = **7,90 pt**. Kein automatisches Verkleinern.

Für Überschriften liegt zusätzlich Nimbus Sans Bold bei (nicht kondensiert).

Die Dateien sind aus OTF nach TTF konvertiert, weil ReportLab keine
PostScript-Konturen einbettet.

Fragetexte stehen in der **fetten** Schnittvariante, linksbündig, senkrecht
mittig im Kästchen. Lösungsbuchstaben stehen in der **normalen** Schnittvariante
und allseitig zentriert.

**Fragetexte.** Höchstens vier Zeilen je Kästchen, nutzbare Zeilenbreite
**10,5 mm** (linker Einzug 0,45 mm, rechts nur eine minimale Reserve, weil der
Text linksbündig steht). Damit passen neun schmale Zeichen knapp — „Edelstein"
10,2 mm, „kostbarer" 10,4 mm — und sieben bis acht Zeichen zuverlässig.
Trenne selbst mit `\n` und setze Trennstriche von Hand:
`"Frei-\nheits-\nentzug"`. Passt eine Frage nicht, wird sie gekürzt — nie die
Schriftgröße geändert.

**Lösungswörter.** Umlaute als AE OE UE, ß als SS. Fragetexte dagegen normal
deutsch mit Umlauten.

**Aufbau.** Eine Frage je Frageblock. Pfeile außerhalb des Blocks, im ersten
Antwortkästchen an der zugewandten Kante. Fünf Typen: rechts, runter,
runter-rechts, rechts-runter, links-runter. Mindestlänge einer Antwort ist 4.

**Seitenaufbau.** Keine Überschrift, kein Umlauthinweis. Das Raster steht
waagerecht und senkrecht mittig auf der Seite. Die Seitenzahl steht fett und
größer als der Fragetext unten rechts, bündig mit der rechten Rasterkante.

**Pfeile** liegen bündig an der Kante des Kästchens an, in das die Antwort läuft.

**Lösungsseiten.** Überschrift LÖSUNGEN weiß auf schwarzem Balken, waagerecht
mittig und senkrecht mittig zwischen Seitenkante und Rasterbeginn. Darunter neun
Raster im 3×3-Feld, zeilenweise von links nach rechts. Über jedem Raster fett und
linksbündig „Seite X". Frageblöcke schwarz gefüllt, kein dicker Außenrahmen. Die
Seitenzählung läuft durch.

**Randregel.** In der linken Spalte und der obersten Zeile darf jede Zelle nur
Frageblock oder Wortanfang sein. Buchstaben mitten in einem Wort sind dort
unzulässig. Wortanfänge am Rand werden über abgewinkelte Pfeile erreicht. Der
Generator erzwingt das hart und repariert Verstöße nach dem Optimierungslauf.

**Kreuzungsrate.** Mindestens 58 % der Buchstabenzellen müssen zu zwei Wörtern
gehören (`CROSS_MIN` in `core.py`, ebenso als Straffunktion in `layout.py`).
Höhere Raten werden belohnt.

**Leere Frageblöcke.** Höchstens zwei je Rätsel, in der Regel null. `make_puzzle`
verwirft Raster mit mehr.

**Ausgabe.** Eine Datei `raetselbuch.pdf`: zuerst alle Rätselseiten mit Seitenzahl
unten mittig, danach die Lösungen zu je neun Rastern (3 × 3) pro Seite, über jedem
Raster die zugehörige Seitenzahl.

Das Verhältnis waagerecht zu senkrecht muss nur grob stimmen.

**Beugungsformen.** Partizipien, Superlative und Genitive sind unzulässig.
**Plurale und einfache Komparative sind zugelassen**, aber deutlich abgewertet
(Faktor 0,25 bzw. 0,35) — sie sollen vorkommen, aber nicht häufig. Die Frage muss
die Form dann mit ausdrücken:

* Plural: entweder ergibt er sich aus der Frage selbst („Vater und Mutter" →
  ELTERN), oder der Zusatz `(Pl.)` steht dabei.
* Komparativ: die Frage steht selbst in der Steigerungsform, etwa „dichter" →
  NÄHER.

`collect_clues.py` markiert solche Wörter mit `(Pl)` und `(Komp)`.

**Die Markierung ist unvollständig.** Sie erkennt nur Plurale, deren Singular im
Grundwortschatz steht. BEAMTE, ELTERN, LEUTE, GESCHWISTER und viele
substantivierte Adjektive rutschen durch. Besonders tückisch sind Wörter, deren
Ein- und Mehrzahl gleich lauten: „Staatsdiener" für BEAMTE liest sich wie ein
Singular und braucht deshalb zwingend das `(Pl.)`. **Prüfe die Form jeder Antwort
selbst.**

Zugelassen sind Substantive, Adjektive, Adverbien, Partikeln und gut erfragbare
Pronomen (ALLE, KEINER, NIEMAND, JEMAND, NICHTS, ETWAS) sowie bekannte Personen,
Länder, Städte und Flüsse. Schwer erfragbare Formen wie JEDE oder DEREN bleiben
draußen.

## 2. Themen einrichten (je Chat neu)

Der Projektleiter nennt Themen mit Gewichtungsfaktoren. `themes.json` ist im
Auslieferungszustand leer.

### 2a. Handliste — der einzige Schritt, der wirklich zählt

Die Handliste entsteht in zwei Durchgängen. Beide sind Pflicht.

**Erst die Direktliste, dann die Facetten.** Schreibe zuerst auf, was dir zum
Thema unmittelbar einfällt, ohne Ordnungsraster — das ist der unverstellte
Zugriff und liefert die geläufigsten und damit besten Rätselwörter. Diese Wörter
stehen in der Facettendatei **direkt hinter der Kopfzeile, vor der ersten
`[Facette]`**, und bekommen automatisch Nähe 1,0. `theme_facets.py` führt sie
unter „Direkt zum Thema" und meldet einen Mangel, wenn sie fehlen.

Erst danach die Facetten: sie sind das Werkzeug gegen die Erschöpfung des freien
Abrufs. Freies Assoziieren liefert immer dieselbe Ecke — bei Jura
Verfahrensbegriffe, nie ROBE, HAMMER oder WAAGE.

**Facettenraster** (themenunabhängig, passt auf Jura wie auf Segeln):

* Rollen und Personen
* Orte und Institutionen
* Gegenstände und Requisiten
* Tätigkeiten und Abläufe
* Erzeugnisse, Dokumente, Werke
* Fachsprache und Begriffe
* Abkürzungen und Kürzel
* Eigennamen, Orte, Marken
* Zeit, Fristen, Rhythmus
* **Kurzwörter** — Pflichtfacette, siehe unten
* Kolorit und Drumherum

```
# THEMA JURA GEWICHT 30
RICHTER ANWALT URTEIL GESETZ PARAGRAF KLAGE PROZESS
[Rollen und Personen] 1.0
KLAEGER ZEUGE SCHOEFFE BEISITZER RECHTSPFLEGER
[Requisiten und Symbolik] 0.6
ROBE TALAR HAMMER WAAGE SIEGEL STEMPEL JUSTITIA
[Kurzwoerter] 1.0
AKTE EIDE FRIST HAFT PFAND RAUB TAT NOTAR
[Kolorit] 0.35
STREIT UNRECHT WAHRHEIT ORDNUNG
```

**Pflichtfacette Kurzwörter.** Das Raster verlangt überwiegend Slots von vier bis
sieben Buchstaben, Fachvokabular ist aber lang. Deshalb gehört in jede
Facettendatei eine Facette, deren Name mit „Kurz" beginnt, und in der gezielt
nach Antworten mit **vier bis sechs Buchstaben** gesucht wird: Kurzformen,
Eigennamen, Orte, Kürzel, Alltagswörter mit Themenbezug. Nicht nebenbei
mitschreiben, sondern eigens danach suchen — die Frage lautet „welche kurzen
Wörter gehören zu diesem Thema", nicht „welche meiner Wörter sind kurz".

`theme_facets.py` prüft beides und meldet:

* `MANGEL: keine Direktliste`
* `MANGEL: keine Kurzwortfacette`
* `MANGEL: Kurzwortanteil unter 25 %`

Der Kurzwortanteil **der Handliste** soll mindestens ein Viertel betragen. Genau
darauf prüft `theme_facets.py`; gemessen wird die Facettendatei, nicht das
fertige Thema.

**Nach der Automatik gilt eine andere Zahl.** Die Stufen 2 bis 4 schütten fast
nur lange Zusammensetzungen dazu; ein Thema, dessen Handliste 30 % kurze Wörter
hatte, landet danach regelmäßig bei 15 bis 20 %. Das ist kein Verfall der
Handliste, sondern eine Eigenschaft der Automatik, und es wäre falsch, deswegen
nachzuarbeiten. `theme_stats.py` meldet deshalb nur noch, wenn **beides** zugleich
verfehlt wird: Quote unter 12 % **und** absolut weniger kurze Wörter als das Buch
braucht (`KURZ_JE_RAETSEL` × Rätselzahl, mindestens 40 je Thema). Zusätzlich
steht am Fuß der Bilanz die Gesamtzahl kurzer Wörter gegen den Bedarf des Buchs —
rund 25 kurze Slots je Rätsel. Ist diese Zahl erreicht, ist die Sache erledigt,
gleich wie die Einzelquoten aussehen.

**Umfang: so viel wie irgend möglich, es gibt keine Obergrenze.**

Ein breites Hauptthema wie Jura, Reisen oder Musik gibt mehrere Tausend sinnvolle
Wörter her. Dort sind **deutlich über 400 Handwörter** das Ziel, 600 bis 800 sind
besser, und es gibt keinen Punkt, an dem zu viele erreicht wären. Aber auch bei
engeren oder gering gewichteten Themen wird ausgereizt, was das Thema hergibt:
ein Nischenthema mit 250 möglichen Wörtern soll diese 250 auch bekommen und nicht
120, nur weil sein Gewicht klein ist. **Das Gewicht steuert, wie oft ein Thema
drankommt — nicht, wie gründlich es erschlossen wird.**

Die folgenden Zahlen sind reine **Untergrenzen**, unterhalb derer das Thema im
Rätsel nicht trägt:

| Themengewicht | Facetten mindestens | Handwörter mindestens |
|---|---|---|
| ≥ 25 (Leitthema) | 14 | 500, angestrebt deutlich mehr |
| 10 bis 20 | 10 | 300 |
| Nische (eine Stadt, eine Sportart) | 8 | 120, sofern das Thema nicht mehr hergibt |

**Der Modellaufwand dafür ist ausdrücklich erwünscht.** Die Handliste ist die
einzige Stelle im ganzen Ablauf, an der nicht gespart wird. Sie entsteht einmal
je Thema, ist die hochwertigste Quelle im System und trägt das ganze Buch.
Arbeite Facette für Facette und gehe je Facette mehrfach durch. Wenn dir zu einer
Facette nichts mehr einfällt, ist sie noch nicht fertig — wechsle die
Abrufrichtung („was liegt in einem Gerichtssaal", „woran erkennt man einen
Prozess von außen") statt aufzuhören. Die Token dafür sind gut angelegt; keine
Rechenzeit gleicht später eine dünne Handliste aus.

**Warum die Handliste allein zählt:** die drei nachgelagerten Automatikstufen
erzeugen fast ausschließlich Kolorit. Kernvokabular entsteht ausschließlich aus
der Handliste. Gemessen an Jura: 280 Handwörter ergaben nach allen vier Stufen
933 Wörter Themenwortschatz — aber weiterhin nur 263 Kernbegriffe. Der
Vervielfacher liegt bei rund 3,3, und er wirkt nur auf Kolorit. Für rund 1.300
Wörter Themenwortschatz braucht es etwa 400 Handwörter, für 2.000 etwa 600.

**Nähe gestaffelt vergeben — die Zwischenstufe ist kein Verlegenheitswert.**
Ein häufiger Fehler ist, fast alles auf 1,0 und den Rest auf 0,35 zu setzen. Dann
gibt es praktisch kein Umfeld, und der Generator behandelt einen entlegenen
Fachbegriff genauso vordringlich wie das Wort, das jeder mit dem Thema verbindet.
Das kostet Qualität an genau der Stelle, an der sie entsteht.

Richtwerte:

| Nähe | wofür | Beispiel Jura |
|---|---|---|
| 1,0 | was jeder sofort mit dem Thema verbindet | RICHTER, URTEIL, KLAGE |
| 0,8 – 0,9 | echtes Fachvokabular, etwas spezieller | BAULAST, ZEDENT, NOTFRIST |
| 0,6 – 0,7 | Randbereich, Eigennamen, anschlussfähige Alltagswörter | TALAR, JUSTITIA, KOMMISSAR |
| 0,45 – 0,55 | entfernt zugehörig, im Zweifel auch ohne Thema erfragbar | SIEGEL, MAPPE, ORDNUNG |
| — | **Obergrenze für Facetten: 0,95.** `theme_facets.py` kappt jeden höheren Wert. Nur die Direktliste vor der ersten `[Facette]` behält 1,0 und damit einen kleinen Vorsprung: was einem zum Thema unmittelbar einfällt, soll vor dem stehen, was erst über eine Facette dazukommt. | |
| unter 0,45 | Drumherum, Kolorit | STREIT, WAHRHEIT |

Das Füllgewicht wächst **quadratisch** mit der Nähe (`core.set_weights`). Der
Abstand zwischen 1,0 und 0,6 ist also kein feiner Unterschied, sondern der Faktor
drei — genau der Hebel, mit dem die guten Wörter vor den entlegenen landen.
Wer alles auf 1,0 setzt, verschenkt ihn.

**Entlegenes gehört ins Umfeld, nicht in den Kern — und Unbekanntes gar nicht
in die Liste.** Es gilt derselbe Maßstab wie für den Rätselwortschatz (Abschnitt
4a): was ein durchschnittlich belesener Erwachsener nicht kennt, gehört nicht
ins Buch. Drei ungarische und russische Hunderassen in einem Raster sind kein
Fachgewinn, sondern eine unlösbare Seite. Bei Rassen, Sorten, Ortsteilen und
Eigennamen deshalb nur das Geläufige aufnehmen — DACKEL, PUDEL, BEAGLE ja,
KOMONDOR, KUVASZ, BOLONKA nein. Im Zweifel: Nähe 0,5 statt 1,0, oder weglassen.

**Die Nähe je Facette entscheidet über drei Dinge:**

### 2a-1. Handlisten wiederverwenden

Die Handliste ist die eigentliche Arbeit an einem Thema und überlebt das Buch.
Sie liegt in `themen/` — dem einzigen Verzeichnis, das `neues_buch.py`
unangetastet lässt. Kommt dasselbe Thema wieder, wird die Datei zurückkopiert,
in der Kopfzeile das neue Gewicht gesetzt und `theme_build.py` laufen gelassen.

Alles außer der Handliste wird je Buch neu erzeugt. Der Grund: die drei
Automatikstufen ziehen aus dem Lexikon, und das wächst. Ein archivierter
fertiger Themenwortschatz wäre nach dem nächsten Wortschatz-Nachtrag veraltet;
der Neuaufbau kostet zwei Minuten.

**Wird das Thema enger gefasst, taugt die alte Handliste nicht unverändert.**
„Jura" und „Jura, aber nur allgemein bekannte Begriffe" sind zwei verschiedene
Themen. Dann gibt es zwei Wege:

* die Liste **neu schreiben**, wenn der Zuschnitt deutlich anders ist, oder
* die vorhandene **filtern** — Kopie anlegen, die nicht passenden Einträge
  streichen. Zu prüfen sind dabei nur die Kernbegriffe; Umfeld und Kolorit sind
  ohnehin Alltagswortschatz.

Das Ergebnis wird als **eigene Datei** abgelegt, etwa
`themen/facetten_JURA_ALLGEMEIN.txt`, mit einer Kommentarzeile zum Zuschnitt.
Das Original bleibt daneben stehen. Über die Zeit entsteht so eine kleine
Bibliothek statt einer Kette von Überschreibungen.

### 2b. Aufbaukette in vier Stufen

```bash
python theme_build.py facetten_JURA.txt
```

Das Skript führt hintereinander aus:

| Stufe | Skript | was es beisteuert | Nähe |
|---|---|---|---|
| 1 Handliste | `theme_facets.py` | echtes Fachvokabular, **Kern und Umfeld** | wie in der Datei |
| 2 Subsuche | `theme_subscan.py` | jedes Facettenwort als Saat im vorhandenen Wortschatz | Facettennähe × 0,42 |
| 3 Expander | `theme_expand.py` | Zusammensetzungen um Kernbegriffe, Stammfamilie mit Umlauttoleranz (KLAGE → KLÄGER) | 0,4 |
| 4 Kolorit | `theme_flex.py` | Beugungen und Ableitungen (RECHT → RECHTLICH, URTEIL → URTEILE) | 0,3 |

Die Stufen 2 bis 4 kosten nur Rechenzeit und lassen sich einzeln aufrufen
(`--add` nimmt auf, ohne `--add` wird nur angezeigt). Stufe 2 sucht nur am
Wortanfang und -ende sowie über den Wortstamm am Wortanfang; Treffer im
Wortinneren bleiben draußen, sonst fängt GESETZ auch ABGESETZT.

### 2c. Sichtprüfung und Stand

```bash
python theme_review.py JURA 4 6
python theme_drop.py JURA RECHTECK GERECHT
python theme_stats.py
```

Die Subsuche produziert Beifang über den Wortstamm (PROTOKOLL → PROTON). Weil
er nur als Kolorit ankommt, ist er nicht schlimm, aber die Sichtprüfung der
kurzen Wörter lohnt einmal je Thema.

`theme_stats.py` meldet je Thema die Stufen, den Anteil kurzer Wörter und die
**Reichweite**: wie oft müsste jedes Kernwort im Schnitt herhalten, um den
Bedarf des Buchs zu decken. Unter 1 sind Wiederholungen praktisch
ausgeschlossen, über 2 werden sie häufig — dann Facetten erweitern, nicht die
Automatik nochmals laufen lassen.

**Kurze Wörter sind der eigentliche Engpass.** Fachvokabular ist überwiegend
lang, die Raster brauchen aber Slots von vier bis sieben Buchstaben. Deshalb die
eigene Kurzwortfacette: Eigennamen, Orte, Abkürzungen, Alltagswörter mit
Themenbezug.

### 2d. Nähewerte über die ganze Skala staffeln

Wer nur drei Werte vergibt (0,95 für alle Fachfacetten, 0,35 für Kolorit), lässt
das Umfeld leer. Im Oma-Buch waren es beim ersten Aufbau 182 Umfeldwörter auf
5.532 Kernwörter — die Rationierung kann dann nicht mehr zwischen dem Wort, das
jeder mit dem Thema verbindet, und dem entlegenen Fachbegriff unterscheiden.

Bewährt hat sich diese Verteilung je Thema:

| Stufe | Nähe | wofür |
|---|---|---|
| Kern | 1,0 | Direktliste |
| Kern | 0,9 | zwei bis drei zentrale Facetten |
| Kern | 0,85 | Kurzwortfacette, weitere Fachfacetten |
| Kern | 0,8 | Fachvokabular zweiter Reihe |
| Umfeld | 0,7 | Zusatz-Kurzwortfacette, Randfacetten |
| Umfeld | 0,45–0,65 | Alltag, Geschichte, Brauchtum, Drumherum |
| Kolorit | 0,3 | Stimmungswörter |

Ergebnis im Oma-Buch nach der Umstellung: 4.963 Kern, 2.656 Umfeld, 11.802
Kolorit. Wichtig ist die Schwelle 0,8 — alles darunter zählt als Umfeld. Eine
Facette mit echtem Fachvokabular gehört auf 0,8 oder darüber, sonst verliert das
Thema seinen Kern.

## 3. Wunschwörter

Der Projektleiter liefert eine Liste, oft mit Fragevorschlägen in Klammern.
Trenne beides: die Wörter nach `wunschwoerter.txt` (eines je Zeile), die
Fragevorschläge direkt in `clues.json`.

```bash
python plan_book.py wunschwoerter.txt 50
```

Wörter über 17 Zeichen passen in kein A5-Raster und entfallen; das Skript meldet
sie. **Drei Buchstaben sind zulässig**, obwohl der Füllwortschatz erst bei vier
beginnt: `make_puzzle` zählt die dreibuchstabigen Vorgabewörter eines Rätsels und
lässt das Raster **genau so viele** Dreier-Slots anlegen — keinen mehr, keinen
weniger. Ein überzähliger Dreier-Slot wäre unfüllbar, ein fehlender machte das
Vorgabewort unplatzierbar; beide Abweichungen werden in `layout.evaluate` hart
bestraft, und Raster mit falscher Zahl werden verworfen. Gemessen kostet ein
dreibuchstabiges Vorgabewort keine zusätzliche Rechenzeit gegenüber einem
längeren. Kürzer als drei geht nicht. Ergebnis: `plan.json` im Format
`{"1": {"pflicht": [...], "weich": [...]}, ...}`.

**Wunschwörter gehören nicht in die Themenlisten.** Sie stehen ausschließlich in
`wunschwoerter.txt` und `plan.json`. Ein Wunschwort zusätzlich in eine
Facettendatei zu schreiben, ist ein Fehler mit zwei Folgen: das Wort kann in
einem anderen Rätsel als gewöhnliches Füllwort auftauchen und steht dann zweimal
im Buch, und die Themenbilanz zählt ein Wort mit, das gar nicht aus dem Thema
kommt. Prüfe die Facettendateien vor dem Aufbau gegen `wunschwoerter.txt` und
entferne Treffer. Auch das Umgekehrte gilt: Wunschwörter sind keine
Themenbelege — wer eine Handliste um sie herum baut, arbeitet an der Aufgabe
vorbei.

**Verteilung.** Die Wörter werden gleichmäßig über die **gesamte** Buchlänge
gestreut, nicht vorne zusammengedrängt: 25 Wunschwörter auf 50 Rätsel landen auf
Seite 1, 3, 5 … und nicht auf 1 bis 25. Das Skript meldet, welches das letzte
belegte Rätsel ist — steht dort nicht ungefähr die Gesamtzahl, stimmt etwas
nicht.

**Reihenfolge: zufällig, nicht nach Länge.** `plan_book.py` sortiert die Wörter
in Zeile 72 absteigend nach Länge (`words.sort(key=len, reverse=True)`) und
verteilt sie erst danach. Ergebnis: die längsten Wunschwörter liegen auf den
ersten Seiten, die dreibuchstabigen auf den letzten. Das ist aus zwei Gründen
unerwünscht.

Erstens ist es ein sichtbares Muster: das Buch fängt mit den schwersten Vorgaben
an und wird nach hinten leichter. Zweitens — und das wiegt schwerer — kostet ein
langes Vorgabewort Themenanteil (siehe Abschnitt 3c), sodass ausgerechnet die
ersten Seiten die schwächsten werden.

Deshalb nach `plan_book.py` die Zuordnung einmal durchmischen, mit festem Seed
zur Reproduzierbarkeit, und dabei bereits gebaute Seiten unangetastet lassen:

```python
import json, random
p = json.load(open("plan.json"))
ww = [p[str(i)]["pflicht"][0] for i in range(1, 51)]
fest = ww[:GEBAUT]                       # Seiten, die schon existieren
rest = ww[GEBAUT:]
random.seed(20260831)
random.shuffle(rest)
for i, w in enumerate(fest + rest, 1):
    p[str(i)] = {"pflicht": [w], "weich": p[str(i)].get("weich", [])}
json.dump(p, open("plan.json", "w"), ensure_ascii=False)
```

**Pflicht und weich.** Je Rätsel gelten höchstens zwei Wörter als Pflicht, alles
Weitere ist weich. `book.py` versucht zuerst alles zu platzieren und lässt weiche
Vorgaben einzeln fallen, sobald sie die Füllung blockieren; erst ganz zuletzt
fällt eine Pflichtvorgabe. So macht eine lange Wunschliste das Füllen nicht
unnötig schwer.

**Schutz vor der Nachbesserung.** `improve_theme` leert reihum Nicht-Themenwörter
und füllt sie neu. Ein Wunschwort ist per Definition kein Themenwort und wurde
dabei früher still überschrieben — das Protokoll meldete `vorgaben=1`, im
fertigen Rätsel stand das Wort nicht mehr. `book.py` übergibt die Vorgaben
deshalb als `schutz=`; geschützte Einträge werden weder geleert noch als Nachbarn
mitgeleert. Wer an dieser Stelle etwas ändert, muss das mitführen.

## 3c. Lange Wunschwörter kosten Themenanteil

Gemessen am Oma-Buch, Seite 1, gleiches Raster-Seedfenster, gleicher
Wortschatz:

| | mit NORDICWALKING (13) | ohne Vorgabewort |
|---|---|---|
| Einträge | 43 | 44 |
| Themenwörter | 21 (49 %) | 29 (66 %) |
| Kernbegriffe | 12 | 19 |

Die Ursache liegt im Raster, nicht in der Gewichtung. Ein Slot mit dreizehn
Zeichen verbraucht eine ganze Zeile oder Spalte; das Raster gleicht das mit
kurzen, stark verkreuzten Restslots aus. Und bei vier Buchstaben stehen nur rund
900 Wörter im ganzen Lexikon zur Verfügung — sind die Kreuzungsbuchstaben
gesetzt, passt oft **genau ein** Wort. Der Füller hat dort keine Wahl mehr, und
die Wahl, die er hat, trifft er in den ersten, noch freien Platzierungen.

Was hilft:

* **Verteilen statt bündeln.** Die Zufallsverteilung aus Abschnitt 3 sorgt
  dafür, dass keine Seite zwei lange Vorgaben trägt und der Buchanfang nicht der
  schwächste Teil wird.
* **Mehr Raster prüfen.** `make_puzzle` gibt zurück, sobald ein Raster
  überhaupt eine brauchbare Füllung liefert — bei Seite 1 waren das zwei
  betrachtete Layouts. Ein größeres `seed_range` liefert mehr Auswahl, kostet
  aber Laufzeit im gleichen Maß.
* **Kurze Themenwörter mit vier und fünf Zeichen.** Sie sind der Engpass, nicht
  der Themenwortschatz insgesamt. Ein Thema mit 400 Wörtern, davon 30 kurzen,
  trägt zum Ergebnis wenig bei.

Was **nicht** hilft: die Themengewichte anheben. Gemessen mit dem Faktor 2,15
über alle Themen sank der Themenanteil von 49 auf 42 %, die seltenen Wörter
stiegen von 9 auf 15. Grund: `fill.score` sortiert die Kandidaten eines Slots
absteigend nach Gewicht, und Themenwörter liegen ohnehin vorn — das schwächste
(Gewicht 4, Nähe 0,3: 4 × 0,3² × 6 = 2,16) schlägt bereits den
Rätselwortschatz (1,3). Ein gemeinsamer Faktor ändert die Reihenfolge nicht,
er lässt den Füller nur tiefer in den schwachen Rand greifen, wenn die guten
Kandidaten in Sackgassen führen.

## 3b. Wiederholungen im Buch

Ein Wort zweimal im Buch ist verschmerzbar, dreimal fällt auf, zweimal
hintereinander wirkt wie ein Fehler. Vier Regeln greifen ineinander:

| Regel | Wo | Wirkung |
|---|---|---|
| Dämpfung Füllwortschatz | `REUSE_FILL` | 2. Einsatz auf 4 %, 3. auf 1 % |
| Dämpfung Themenwörter | `REUSE_THEMA` | 2. Einsatz auf 4 %, 3. auf 1 % |
| Obergrenze, **alle Wörter** | `WORT_MAX = 3` | ab dem 4. Einsatz gesperrt |
| Punktabzug bei der Auswahl | `WIED_STRAFE = 1.5` | je Wiederholung in der Füllung |
| Sperrfenster | `SPERRE_SEITEN = 2` | **jede** Antwort der letzten zwei Seiten ist gesperrt |
| Kurzwortzuschlag | `KURZ_DAEMPFUNG = 0.25` | Themenwörter mit 4–6 Zeichen zusätzlich gedämpft |

Das Sperrfenster gilt für **jede** Antwort, gleich woher sie kommt: eine enge
Wiederholung stört unabhängig davon, ob das Wort aus einem Thema oder aus dem
Füllwortschatz stammt. Es sperrt rund neunzig Wörter von über zwanzigtausend,
engt die Füllung also nicht nennenswert ein. Die Obergrenze `THEMA_MAX` bleibt
dagegen auf Themenwörter beschränkt — der Füllwortschatz reguliert sich über
die Dämpfung selbst.

**Kurze Wörter werden härter gedämpft — alle, nicht nur Themenwörter.** Wörter
mit vier bis sechs Zeichen passen in fast jedes Muster und wiederholen sich
deshalb am häufigsten; genau für sie gibt es aber auch am ehesten Ersatz. Ab
dem zweiten Einsatz kommt der Faktor `KURZ_DAEMPFUNG = 0.05` obendrauf:

```
UREA      (Thema, kurz)   180,00  ->  0,3600
REINIGUNG (Thema, lang)   180,00  ->  7,2000
ANIS      (Fuellwort)       1,30  ->  0,0026
Median eines frischen Fuellworts: 1,43
```

**Das Gewicht allein genügt nicht.** War ein Wort für seinen Slot die einzige
Wahl, hilft kein noch so kleines Gewicht. Deshalb kostet jede Wiederholung
zusätzlich Punkte bei der Auswahl der Füllung (`WIED_STRAFE`): eine andere
Füllung, die den Slot anders löst, gewinnt dann den Vergleich.

**Gesperrt heißt gesperrt, nicht „Gewicht 0".** Ein Wort mit Gewicht 0 kann der
Füller weiterhin setzen, wenn es der einzige Kandidat für einen Slot ist. Und
`improve_theme`, die lokale Nachoptimierung in `book.py`, wählt überhaupt nicht
nach Gewicht, sondern nach Themenzugehörigkeit — sie holt also gerade die
Wörter zurück, die die Dämpfung mühsam herausgehalten hat. Deshalb legt
`set_weights` die Menge `lex.gesperrt` an, und **beide** fragen sie ab:
`fill.candidates` zieht sie von den Kandidaten ab, `improve_theme` ebenso.

Dass das nötig war, hat sich an UMAN gezeigt: Seite 10, 12 und 13, davon zwei
direkt aufeinanderfolgend, obwohl die Gewichtung das ausschloss. Der
Nachoptimierer hatte es jedes Mal wieder hereingeholt.

Das Fenster hängt **nicht** am Buchumfang. Bei fünfzig Seiten fällt eine
Wiederholung nach zwei Seiten genauso auf wie bei zehn.

Die Obergrenze wird wichtiger, je länger das Buch ist. Bei zehn Seiten hält
schon die Dämpfung die Quote klein; bei dreißig Seiten sammeln sich sonst
Wörter an, die fünf- oder sechsmal vorkommen, weil ihre Buchstabenfolge dem
Löser entgegenkommt (LILA: vier Zeichen, drei Vokale, kreuzt gut).

**Neue Fassungen werden angehängt, nie vorangestellt.** `render_book` wählt
`vs[k % len(vs)]` — die Fassung also nach der Zahl der bisherigen Einsätze. Wer
eine Fassung vorn einfügt, verändert damit die Frage auf **jeder bereits
fertigen Seite**. Angehängt wird sie erst beim nächsten Einsatz sichtbar, und
genau das ist gewollt. `fitcheck.py --eintragen` macht das inzwischen richtig;
wer von Hand in `clues.json` schreibt, muss darauf achten.

**Wiederholte Wörter brauchen verschiedene Fragen.** `render_book.py` wählt die
Fassung nach der Zahl der bisherigen Einsätze (`vs[k % len(vs)]`) — wenn es nur
eine Fassung gibt, steht dieselbe Frage zweimal im Buch. Das meldet der
Renderer unter „GLEICHE FRAGE MEHRFACH" mit der Zahl der benötigten Fassungen.
Diese Meldung ist abzuarbeiten, nicht zu übergehen.

## 3a. Kreuzungsrate

`CROSS_MIN` in `core.py` (0,58) und `MIN_CROSS` in `skanvord/layout.py` sind eine
**Untergrenze, kein Zielwert**. Angestrebt wird **knapp über 0,60**; Werte
zwischen 0,60 und 0,64 ergeben ein dichtes, sauber verzahntes Raster. Die
Erzeugung meldet den erreichten Wert je Rätsel als `kreuz=`.

Nicht absenken. Ein niedrigerer Wert macht das Füllen leichter und den
Themenanteil höher, das Rätsel wird aber luftig und beliebig. Wer mehr
Themenwörter will, vergrößert die Handliste (Abschnitt 2a) — nicht die
Kreuzungsrate senkt man, sondern den Vorrat hebt man.

## 4. Rätsel erzeugen

```bash
python book.py 1 10
python book.py 11 20
```

In Zehnerblöcken, sonst läuft der Aufruf in die Zeitgrenze. Je Rätsel etwa 30 bis
60 Sekunden. Scheitert ein Rätsel mit Vorgabewörtern, versucht das Skript es ohne
sie und meldet `vorgaben=0`.

`used_words.json` wird fortgeschrieben. Füllwörter fallen nach einer Verwendung
auf 10 % Gewicht und kehren praktisch nicht wieder.

Bei Themenwörtern greifen **zwei Regler ineinander**:

**Wiederholungskurve** — 100 %, dann 30 %, dann 10 %, danach 2 %. Sie fällt steil,
läuft aber nicht auf null: solange ein frisches Wort passt, gewinnt es; erzwingt
die Füllung es, ist eine Wiederholung möglich. So bleiben Wiederholungen selten,
ohne dass ein Rätsel daran scheitert.

**Rationierung je Thema** — verbraucht ein Thema mehr Wörter, als seinem Anteil am
Buchfortschritt entspricht, sinkt sein Gewicht, bis die anderen aufgeholt haben.
Ohne diese Bremse würde das schwerstgewichtete Thema zuerst leergeräumt und stünde
in der zweiten Buchhälfte nicht mehr zur Verfügung. Die Bremse arbeitet mit dem
Verhältnis aus verbrauchtem Anteil und Buchfortschritt und funktioniert deshalb
bei jedem Buchumfang.

**`used_words.json` niemals löschen.** In einem Test ergaben 115 Einträge 113 verschiedene Wörter.

## 4a. Rätselwortschatz — gegen zu leichte Bücher

`raetselwoerter.txt` enthält rund 1.020 klassische Kreuzworträtselwörter mit
fertiger Frage, je Zeile `WORT | Frage`: VIOLA, SMUTJE, ASBEST, KAVALLERIE,
ERDGAS, PHANTOM, TITISEE, STINKTIER. Wörter also, die jeder Löser kennt, die im
Alltagsdeutsch aber selten vorkommen und deshalb im reinen Häufigkeitswortschatz
untergehen.

**Warum die Liste nötig ist.** Das Grundgewicht eines Füllworts ist
`3,0 / (1 + Rang/1200)`. Ein Wort mit Rang 100 bekommt damit 2,8, eines mit Rang
20.000 nur 0,17 — die Auswahl kippt zwangsläufig zu den Allerweltswörtern, und
deren Fragen sind zwangsläufig banal. Das Niveau ist also **überwiegend eine
Frage der Wortauswahl, nicht der Formulierung**: zu HAUS oder JAHR lässt sich
keine kniffelige Frage schreiben, zu SMUTJE schreibt sie sich von selbst.

Zwei Stellschrauben in `core.py`:

* `RAETSEL_BASE` (1,6) — festes Gewicht für die Liste, unabhängig von der
  Häufigkeit. Entspricht etwa Rang 1.000: die Wörter kommen regelmäßig vor,
  beherrschen das Rätsel aber nicht.
* `HAEUFIG_GRENZE` (800) und `HAEUFIG_DAEMPFUNG` (0,75) — die allerhäufigsten
  Wörter werden leicht gebremst. Sie sind grammatisch bequem und drängen sich
  sonst in jedes Raster.

Wird es zu schwer, `RAETSEL_BASE` senken; wird es zu leicht, anheben. Bei 2,5
dominiert die Liste spürbar, bei 1,0 verschwindet sie fast.

**Das Niveau der Liste.** Angepeilt ist „kennt man, benutzt man aber selten" —
ERDGAS, ASBEST, KAVALLERIE, SMUTJE, ZEREBRUM. **Nicht** aufgenommen wird, was
man nachschlagen muss: Fachbegriffe der Seemannssprache jenseits des Bekannten,
entlegene Amtsbezeichnungen, seltene Fremdwörter. Wenn ein Eintrag einem
durchschnittlich belesenen Erwachsenen nichts sagt, gehört er nicht in die
Liste. Bereits aussortiert wurden aus diesem Grund unter anderem SPINNAKER,
DROSCHKE, ADLATUS, NUNTIUS, MADRIGAL und KLAFTER.

**Pflege.** Die Wörter gelangen über `core.load_raetselwoerter` zur Laufzeit in
den Grundwortschatz, auch wenn sie in `words_v3.json` fehlen. Die Fragen gehören
in den Cache:

```bash
python import_raetselwoerter.py              # nur prüfen
python import_raetselwoerter.py --schreiben  # in clues.json eintragen
```

Das Skript setzt den Zeilenumbruch selbst und meldet jede Frage, die auch
umgebrochen nicht ins Kästchen passt. Vorhandene Fragen werden nicht überschrieben.
Die Liste darf jederzeit wachsen — sie ist buchübergreifend und themenneutral.

## 4b. Ein einzelnes Wort ersetzen statt die Seite neu zu bauen

Findet die Wortprüfung ein unbrauchbares Wort, ist der vollständige Neubau die
**letzte** Stufe, nicht die erste. Ein Neubau kostet acht bis zehn Minuten, wirft
alle bereits geschriebenen Fragen der Seite weg und liefert ein anderes Raster,
das seinerseits neue Funde enthalten kann. Drei Stufen in dieser Reihenfolge:

**Stufe 1: den einen Slot neu belegen.** `ersetze_wort.py NR WORT` zeigt, welche
Wörter in den Slot passen, wenn nur die Kreuzungsbuchstaben stehen bleiben; mit
`--nimm ERSATZ` wird gesetzt und das Konto gepflegt. Dauert Sekunden. Bei kurzen,
stark verkreuzten Slots gibt es oft nur einen einzigen Kandidaten oder gar
keinen — bei vier Buchstaben stehen im ganzen Lexikon nur rund 900 Wörter.

**Stufe 2: die direkten Nachbarn einbeziehen.** `ersetze_wort.py NR WORT
--stufe2` leert den Slot samt seinen unmittelbaren Nachbarn und füllt neu —
dasselbe Verfahren, das `core.improve_theme` benutzt. Der Rest der Seite bleibt
stehen. Der Schalter erzwingt die Umgebungssuche auch dann, wenn Stufe 1
Kandidaten hätte.

**Stufe 3: die zweite Kreuzungsebene.** Läuft automatisch an, wenn Stufe 2
nichts findet: auch die Nachbarn der Nachbarn werden geleert, Gruppengröße bis
zehn, 600 Versuche, Zeitdeckel zehn Minuten. Erfahrungswert aus dem Oma-Buch:
Stufe 3 trägt bei Slots ab sechs Zeichen mit freien Positionen (ERGUSS, WEIBER,
KINDSTOD, IMPOTENT, MAINFRAME wurden so ersetzt), scheitert aber bei kurzen,
vollständig verkreuzten Slots fast immer (SUFF, WAGON, CMOS, STEISS, GHETTO).
Bei vier bis fünf Zeichen lohnt der Versuch selten.

**Achtung nach Stufe 2 und 3:** Sie tauschen bis zu zehn Wörter auf einmal und
prüfen dabei nur den Themenanteil, nicht die inhaltliche Eignung. Die
Ersatzwörter müssen danach genauso geprüft werden wie nach einem Neubau — im
Oma-Buch schleppte ein Stufe-3-Lauf das Wort REKTAL ein.

**Vorgabewörter sind geschützt.** `ersetze_wort.py` liest `plan.json` und lässt
das Pflichtwort der Seite unangetastet, weder als Ziel noch als mitgeleerten
Nachbarn. Ohne diesen Schutz hatte Stufe 2 einmal stillschweigend BINGO
ersetzt.

**Stufe 4: `rollback.py` und Neubau — mit Seed-Versatz.** `make_puzzle` ist bei
gleichem Konto deterministisch: Ein Neubau ohne Versatz liefert exakt dasselbe
Raster und damit dasselbe Problem. `book.py` kennt dafür die Umgebungsvariable

    SEED_VERSATZ=100 python book.py 22 22

Sie verschiebt das Rasterfenster. Bewährt hat sich, je Anlauf um 100 zu erhöhen.
Im Oma-Buch brauchte Seite 22 fünf Anläufe (Versatz 0, 100, 200, 300, 400), weil
jedes neue Raster einen anderen Grenzfall mitbrachte.

**Vor Stufe 3 den Projektleiter fragen.** Ein Neubau ist eine Entscheidung über
seine Zeit, und ob ein Wort wirklich raus muss, ist häufig Ermessenssache — im
Oma-Buch wurden STUNTMAN, ATZE, ABDECKER, ARSENAL und GUERILLA von mir gesperrt
und vom Projektleiter wieder freigegeben. In diesen Fällen war der Neubau ganz
umsonst.

**Achtung:** `rollback.py` löscht die Rätseldatei, nicht nur den Konto-Eintrag.
Nach einem Rollback ist die alte Seite unwiederbringlich weg, auch wenn sich
herausstellt, dass das beanstandete Wort doch in Ordnung war. Deshalb erst
fragen, dann rollen.

## 4c. Endgrenze und Nachbesserung in make_puzzle

Seit dem Umbau steckt die Nachbesserung in `make_puzzle`, nicht mehr in
`book.py`. Der Ablauf je Raster:

1. Bis zu `tries` Füllungen erzeugen. Jede vollständige Füllung unter
   `MIN_THEMA` (0,40) wird sofort verworfen — das ist nur eine Vorprüfung, sie
   greift nie mitten im Füllen, sondern immer erst am fertigen Raster.
2. Alle übrigen Füllungen werden gesammelt und nach Punktzahl sortiert.
3. Die beste wird mit `NACHBESSERN_LAEUFE` (8) Durchgängen `improve_theme`
   nachgebessert und gegen `MIN_THEMA_FINAL` (0,50) geprüft. Reicht sie nicht,
   ist die nächstbeste dran, bis `NACHBESSERN_MAX` (6).
4. Erst wenn keine der besten sechs Füllungen reicht, fällt das ganze Raster und
   der nächste Seed kommt dran.
5. Erreicht kein Raster die Endgrenze, wird das beste gesehene Ergebnis genommen
   (`rueckfall_genommen` in der Diagnose) — eine Seite soll nie ganz scheitern.

Wichtig ist die Reihenfolge: Die 50 Prozent gelten für das **nachgebesserte**
Ergebnis. Steht die Endgrenze schon in der Vorprüfung, verwirft der Füller
Kandidaten, die der Nachbesserer noch über die Linie gehoben hätte — das kostete
im Oma-Buch einmal fünfzig Minuten für eine einzige Seite.

`nachbesserung_rang=1` in der Diagnose heißt: die beste Füllung reichte sofort.
Das ist der Normalfall.

## 4d. Konto aus den Rasterdateien wiederherstellen

`used_words.json` kann auseinanderlaufen — etwa wenn eine ältere Sicherung
zurückgespielt wird, nachdem `ersetze_wort.py` bereits Wörter getauscht hat. Der
Zustand ist jederzeit aus den Rätseldateien rekonstruierbar:

```python
import json, pickle, glob, collections, sys
sys.path.insert(0, "skanvord"); import layout
neu = collections.Counter()
for f in sorted(glob.glob("puzzles/*.pkl")):
    lay, _ = pickle.load(open(f, "rb"))
    for e in lay.entries:
        neu[e.word] += 1
json.dump(dict(neu), open("used_words.json", "w"), ensure_ascii=False)
```

Diese Prüfung gehört nach jedem Abbruch eines Hintergrundlaufs und nach jeder
Wiederherstellung einer Sicherung. Sie ist billig und deckt still entstandene
Abweichungen sofort auf.

## 4e. Nach jeder fertigen Seite rendern

Nicht am Ende eines Blocks, sondern nach jeder abgeschlossenen Seite. Der
Projektleiter hat dann durchgehend ein aktuelles PDF und muss nicht auf das Ende
einer Reparaturkette warten. Kostet nur Sekunden.

## 5. Wortauswahl prüfen — VOR den Fragen

**Diese Reihenfolge ist verbindlich.** Erst die Wortliste vollständig prüfen und
bereinigen, dann erst Fragen schreiben. Jede nachträgliche Sperrung erzwingt eine
Neuberechnung der betroffenen Rätsel, damit eine neue Wortliste und damit neue
Fragen — geschriebene Fragen sind dann verloren. Das ist der teuerste Fehler, den
man in diesem Ablauf machen kann.

```bash
python collect_clues.py
```

`FEHLT` listet Wörter ohne Frage; `!` `+` `~` markieren die Themenstufe, `(Pl)`
und `(Komp)` die Form, `(Pl?)` einen Formverdacht.

### 5a. Was gesperrt wird — und was nicht

Sperren ist der teuerste Eingriff im ganzen Ablauf. Er ist nur für Wörter
gedacht, die in **keiner** denkbaren Frage funktionieren.

**Sperren:**

* Fragmente und Fehlbildungen: ANGELES (aus Los Angeles), SCHAFT, STRASS
* durchgerutschte Partizipien: VERSAGT, ABGEKLAERT
* Vulgäres, Herabwürdigendes, Belastendes — sofern nicht schon in `stopwords.txt`
* Wörter, deren einzige Frage den Wortstamm enthalten müsste

**Nicht sperren:**

* **Unmarkierte oder falsch markierte Plurale.** Das ist ein Formproblem, kein
  Sperrgrund. NÄGEL und LÄDEN sind völlig brauchbare Antworten, sie brauchen nur
  eine Frage in der Mehrzahl, notfalls mit dem Zusatz „(Pl.)". Korrektur gehört
  nach `formen.txt`, nicht in die Sperrliste.
* **Umgangssprachliches und leicht Derbes ohne Herabwürdigung.** VERSOFFEN, SUFF
  oder BLÖD sind salopp, aber weder vulgär noch beleidigend. Sie bleiben.
* **Unbequeme, aber erfragbare Allerweltswörter.** URIN, AIDS, SEIN, MEIN,
  PASSEND, TAUBSTUMM — hier entscheidet der Projektleiter über den Ton, nicht die
  Automatik. Im Zweifel nachfragen statt sperren.
* Wörter, die nur schwer zu umschreiben sind. Erst eine Formulierung versuchen.
* **Wörter mit Russlandbezug — ausnahmslos alle.** Sie werden **nicht**
  gesperrt. Sie bekommen eine negativ oder sarkastisch formulierte Frage — und
  zwar **als einzige**. Keine neutrale Fassung daneben, und **keine
  Themenbindung**: die Haltung gilt unabhängig davon, ob Ukraine im jeweiligen
  Buch ein Thema ist.

  Die Regel gilt für **jedes** Wort mit Russlandbezug, nicht nur für die
  Staatssymbole. Erfasst sind Staat und Herrschaft (RUSSLAND, MOSKAU, KREML,
  ZAR, SOWJET), Währung und Wirtschaft (RUBEL, GAZPROM), Geografie
  (SANKTPETERSBURG, SIBIRIEN, WOLGA, NEWA, URAL, BAIKAL), Sprache und Kultur
  (KYRILLISCH, BALALAIKA, MATRJOSCHKA, DATSCHA, SAMOWAR, TROIKA), Speisen
  (WODKA, BORSCHTSCH in russischer Lesart, PIROGGE) und Personennamen.

  Vorhandene Beispiele in `clues.json`: MOSKAU „Hauptstadt der Aggressoren",
  KREML „Sitz des Hauptfeindes", RUSSLAND „Land des Angriffskriegs", RUBEL
  „Währung des Aggressors".

  Ist ein Wort zusätzlich so entlegen, dass die Empfängerin es nicht lösen
  kann, gilt der normale Maßstab und es wird gesperrt — die sarkastische Frage
  rettet kein unbekanntes Wort. So geschehen mit NEWA im Oma-Buch.

  Was für die Schreibweise ukrainischer Namen gilt (Abschnitt 6a-2: KYJIW,
  nicht KIEW), gilt hier für den Ton.

### 5a-1. Vorabsperrung ganzer Fehlerklassen — vor dem ersten Rätsel

Erfahrung aus dem Buch für die Oma (Salzgitter-Bad, 50 Seiten): Wer erst beim
fertigen Rätsel prüft, sperrt ein Wort, baut die Seite neu, findet das nächste
Wort derselben Klasse, baut wieder neu. Fünf Anläufe für Seite 1 waren die
Folge. Billiger ist es, den **gesamten Wortschatz einmal vorab** nach Mustern zu
durchsuchen und die Klasse geschlossen zu sperren — vor `book.py`, nicht danach.

Quellen für den Suchlauf: `words_v3.json`, `fallback_v3.json`, `selten_v3.json`
und `raetselwoerter.txt`, abzüglich dessen, was `stopwords.txt` schon abdeckt.

Fünf Klassen haben sich als ergiebig erwiesen:

1. **Durchgerutschte Partizipien.** `wordcheck.ist_partizip` erkennt nur das
   GE-Muster. Formen mit Präfix ohne GE rutschen durch. Suchmuster:
   `^(VER|BE|ER|ENT|ZER|MISS|UEBER|UNTER|UM|AN|AUF|AUS|EIN|VOR|NACH|MIT|ZU|AB)`
   plus Endung `IERT|EBEN|OMMEN|ANGEN|UNDEN|ORBEN|OGEN|ETEN|AGEN|OSSEN|ICHEN|
   ALTEN|ANDEN|UNGEN|ORFEN|OCHEN|ETZT|ANNT|EIHT`. Ertrag: rund 78 Wörter
   (VERSCHWUNDEN, BESCHLOSSEN, ZURUECKGEZOGEN, ANERKANNT …). Das ist die mit
   Abstand größte Klasse.
2. **Anstößiges.** Stämme HURE, NUTTE, DIRNE, UNZUCHT, GEIL, EROT, SEX, NACKT,
   BUSEN, VAGIN, PENIS, ARSCH, PISS, KOT, ORGIE, ORGAS. HUREREI stammt aus dem
   Bibelwortschatz und taucht bei christlichen Themen zuverlässig auf.
3. **Belastendes.** Tod und Bestattung (TOT, LEICH, GRAB, SARG, STERB, TRAUER,
   WITWE, WAISE, URNE, BEGRAEB), Krieg und Waffen (KRIEG, WAFFE, GEWEHR,
   PISTOLE, BOMBE, GRANATE, PANZER, SOLDAT, GALGEN, HENKER), schwere Krankheit
   (Endungen OSE, ITIS, PATHIE, SKOPIE, AEMIE, ALGIE, PHOBIE, MANIE sowie
   PSYCH, NEUR, INFARKT, EMBOL, SKLEROS). Wieviel davon gesperrt wird, hängt
   von der Empfängerin ab und gehört dem Projektleiter vorgelegt — bei einer
   Empfängerin mit Kriegskindheit oder Vertreibungsgeschichte ist der Kriegsteil
   nicht optional.
4. **Anglizismen.** Muster auf Endungen und Bestandteile: SHOW, STYLE, CHECK,
   CLUB, TEAM, SHIRT, PARTY, JOB, CHAT, MAIL, ONLINE, COMPUTER, SMART, SERVER,
   DESIGN, FITNESS, TRAINING, DRINK, VIDEO. Achtung auf Fehltreffer: die
   deutsche Endung -BAR (BRAUCHBAR, DENKBAR) trifft das Muster BAR, NACHBAR und
   HAMBURGER treffen BAR und BURGER. Treffer immer sichten, nie blind sperren.
5. **Funktionswörter ohne eigenständige Bedeutung.** IRGEND, IHRIGE, SEINIGE,
   ZUMAL, ZUDEM, FERNER. Diese sind keine Partikeln im Sinne von Abschnitt 1,
   sondern Bruchstücke, die allein nicht erfragbar sind.

### 5a-2. Die eigenen Handlisten prüfen — nicht nur den Grundwortschatz

Tippfehler und Erfindungen in den selbst geschriebenen Facettendateien fallen
sonst erst im fertigen Raster auf. Prüfung: alle Handlistenwörter bis sieben
Zeichen gegen `words_v3` + `fallback_v3` + `selten_v3` + `raetselwoerter.txt` +
`alltag.txt` abgleichen und die Rückstände sichten. Zusammensetzungen und
Eigennamen stehen dort erwartungsgemäß nicht drin, Tippfehler aber auch nicht —
und die sind zwischen den Eigennamen gut zu erkennen.

Gefunden wurden auf diesem Weg: TOEL (verrutschtes TORJUBEL), GERoeLL (Umlaut
nicht umgesetzt), CEROBAN (Fehlbildung aus Ceranfeld), SAGALEY (frei erfundenes
Brettspiel), YAHTZEE und TREK (Anglizismen), BLEIB (Imperativ).

**Korrektur gehört in die Facettendatei, nicht nur in die Sperrliste** —
zusätzlich `theme_drop.py THEMA WORT`, sonst steht das Wort beim nächsten Buch
wieder in der Liste. Danach die korrigierte Datei nach `themen/` kopieren.

### 5a-3. Wunschwörter nach jedem Themenaufbau erneut prüfen

Die Automatikstufen holen Wunschwörter über Zusammensetzungen zurück: BROCKEN
aus BROCKENBAHN, DRACHE aus DRACHENBAUM, PFLAUME aus PFLAUMENBAUM, TUERKEI aus
TUERKENBUND, HOECKER aus HOECKERZAHN. Steht ein Wunschwort zusätzlich als
gewöhnliches Füllwort im Thema, taucht es doppelt im Buch auf.

Nach **jedem** `theme_build.py`-Durchgang `themes.json` gegen
`wunschwoerter.txt` abgleichen und Treffer mit `theme_drop.py` entfernen. Das
Entfernen aus den Facettendateien allein genügt nicht.

**Zwei Listen, zwei Zwecke:**

| Datei | Reichweite | wächst |
|---|---|---|
| `stopwords.txt` | dauerhaft, buchübergreifend, vorsorglich umfangreich (rund 650 Wörter) | selten, jede Ergänzung erzwingt Neuberechnung betroffener Rätsel |
| `blacklist.txt` | dieses Buch | mit jedem Durchgang um ein bis zwei Wörter je Rätsel |

Beide werden **zeilenweise** gelesen; eine Zeile, die mit `#` beginnt, ist
vollständig Kommentar. Die frühere Fassung las die Dateien mit `read().split()`
und verwarf nur Tokens, die selbst mit `#` anfingen — dadurch galten alle Wörter
der Kommentarzeilen („Dauerhaft", „gesperrt", „Sexuelles") als Sperrwörter, und
jede zeilenweise Zählung lieferte unsinnige Werte. Zuständig ist jetzt allein
`wordcheck.lade_sperrliste`.

### 5a-4. Entsperren wirkt nicht von allein

Ein Wort aus `stopwords.txt` zu streichen holt es **nicht** zurück:
`words_v3.json` und `fallback_v3.json` wurden einmalig mit einer früheren
Fassung der Sperrliste gebaut, das Wort steht dort gar nicht mehr. Ein Neubau
bräuchte die Quelldateien in `./wl/`, die nicht im Paket liegen.

Dafür gibt es `freigabe.txt`: ein Wort je Zeile, optional ein Häufigkeitsrang
dahinter (Vorgabe 15.000). `build_lexicon` fügt diese Wörter zur Laufzeit dem
Grundwortschatz hinzu. Die Sperrlisten haben Vorrang — was in `stopwords.txt`
oder `blacklist.txt` steht, bleibt draußen, auch wenn es in `freigabe.txt` steht.

Also immer beides tun: aus der Sperrliste streichen **und** in `freigabe.txt`
eintragen.

Beide Sperrlisten greifen **zur Laufzeit** in `build_lexicon`. Das ist wichtig:
`words_v3.json` lässt sich nur mit den Quelldateien in `./wl/` neu bauen, die
nicht im Paket liegen. Eine Ergänzung in `stopwords.txt` wirkt trotzdem sofort.

```bash
python blacklist_add.py ANGELES VERSAGT
python rollback.py 7 7
python book.py 7 7
```

**`rollback.py` ist zwingend**, bevor ein bereits erzeugtes Rätsel neu gebaut
wird. Sonst zählen die verworfenen Wörter im Nutzungskonto weiter mit und werden
bei der Neuerzeugung fälschlich gedämpft.

### 5a-5. Mitgerissene Substantive — keinpartizip.txt

`wordcheck.ist_partizip` erkennt Partizipien am Muster `[Vorsilbe]GE…T/EN`. Das
Muster trifft auch gewöhnliche Substantive: GERICHT, GESICHT, GEWALT, GEBIET,
GEBURT, GERÄT, GESUNDHEIT, GESELLSCHAFT, GEDICHT, GEWICHT und Dutzende weitere.
Sie wurden beim einmaligen Bau von `words_v3.json` verworfen und fehlten im
System vollständig — auch über eine Facettendatei ließen sie sich nicht
nachtragen, weil `theme_facets.py` dieselbe Prüfung anwendet. Für ein Thema wie
Jura ist das nicht hinnehmbar; ein Rätselbuch ohne GERICHT gibt es nicht.

Zuständig ist `keinpartizip.txt`, eine Zeile je Wort, optional ein Häufigkeitsrang
dahinter. Sie wirkt an zwei Stellen:

* `wordcheck.ist_partizip` gibt für diese Wörter `False` zurück — sie kommen
  über jede Facettendatei in jedes Thema.
* `core.build_lexicon` schlägt sie dem Grundwortschatz zu, genau wie
  `freigabe.txt`. Sie stehen damit auch als Füllwörter zur Verfügung.

Die Liste ist dauerhaft und buchübergreifend. Wer ein solches Wort vermisst,
trägt es dort ein — nicht in `freigabe.txt`, die ist für Wörter da, die einmal
gesperrt waren. Sperrlisten haben in beiden Fällen Vorrang.

Umgekehrt bleibt die Heuristik grob: kurze Partizipien wie GETAN rutschen durch,
weil das Muster erst ab sechs Zeichen greift. Die gehören in `stopwords.txt`.

### 5b. Formen korrigieren statt sperren

Die automatische Formerkennung in `build_wordlists.py` arbeitet über Endungen und
liegt in zwei Richtungen daneben:

* **falsch als Plural markiert:** KOHLE sieht aus wie KOHL + E, MASSE wie MASS + E
* **Plural nicht erkannt:** Umlautplural wie NÄGEL, LÄDEN, BÜCHER

Beides wird in `formen.txt` von Hand korrigiert, eine Zeile je Wort:

```
KOHLE SG
MASSE SG
NAEGEL PL
LAEDEN PL
```

`SG` löscht eine falsche Markierung, `PL` und `KOMP` tragen eine fehlende nach.
Die Datei wird von `core.load_formen` und `build_lexicon` gelesen und schlägt die
automatische Erkennung. Wirkung: das Füllgewicht sinkt (Plural 0,25, Komparativ
0,35) und `collect_clues.py` zeigt die Markierung an.

`(Pl?)` in der Ausgabe von `collect_clues.py` ist ein **Verdacht** aus der
Heuristik `wordcheck.plural_verdacht`, kein Befund. Prüfe das Wort und trage das
Ergebnis in `formen.txt` ein — dann ist die Frage beim nächsten Mal richtig
markiert.

### 5c. Zwei Wörter desselben Stamms in einem Raster

EKEL und EKLIG, BUND und BÜNDE, SZENE und SZENEN auf einer Seite sind ein
Mangel, und zwar einer, der sich nicht durch Sperren lösen lässt: beide Wörter
sind für sich einwandfrei, falsch ist nur ihr Zusammentreffen. Deshalb erledigt
das der Generator selbst.

`fill.py` führt je Raster einen Zähler über die Wortstämme und lässt pro Stamm
nur einen Eintrag zu (`stamm_sperre=True`, Vorgabe). Der Stamm kommt aus
`wordcheck.stamm`: die längste bekannte Endung abtrennen, das Schwa-E vor dem
Schlusskonsonanten tilgen, Umlaute auflösen. EKEL und EKLIG fallen damit beide
auf EKL, BUND und BÜNDE beide auf BUND, während LESER (LES) und LASER (LAS)
auseinanderbleiben.

Die Ableitung ist bewusst vorsichtig: lieber ein Paar übersehen als unverwandte
Wörter gegeneinander sperren. FRISEUR und FRISUR entgehen ihr zum Beispiel. Wer
so etwas im fertigen Raster findet, meldet es — gesperrt wird deswegen nichts.
`wordcheck.stamm_kollision(woerter)` prüft eine fertige Wortliste nach.

## 6. Fragen schreiben

`clues.json`: Wort → Liste von Varianten. Ein Eintrag ist entweder ein reiner Text
(themenneutral) oder ein Objekt mit Themenbindung:

```json
{"AKTE": ["Sammlung\nvon\nPapier",
          {"c": "Was der\nRichter\nliest", "t": "JURA"}]}
```

Beim Rendern werden Varianten bevorzugt, deren Thema im aktuellen `themes.json`
vorkommt; sonst die neutralen. Über das Buch hinweg rotieren sie: das n-te
Auftreten eines Wortes bekommt die n-te Variante. `VARIANTE` in Schritt 5 zeigt,
wo noch eine Formulierung fehlt.

### 6a. Der Ton: knappe Nominaldefinition, kein beschreibender Satz

Eine Kreuzworträtselfrage ist ein **Lexikoneintrag ohne Stichwort**, keine
Erklärung. Sie ist ein bis fünf Wörter lang, nennt die Sache und hört auf. Das
ist die Stelle, an der die Qualität eines Buchs entschieden wird — Raster und
Füllung sind Handwerk, die Fragen sind das Produkt.

**Sechs Regeln:**

1. **Nominal statt verbal.** Ein Substantiv wird mit einem Substantiv
   umschrieben. „Gratis nutzen lassen" beschreibt *leihen*, nicht LEIHE —
   richtig ist „Gratis-Nutzung".
2. **Keine Relativsätze, keine „Was …"-Konstruktionen.** „Was der Hammer trifft"
   für NÄGEL, „Wer den Nachlass bekommt" für ERBE — beides umständlich und
   unidiomatisch. Richtig: „Blechstifte (Pl.)", „Nachlassempfänger". Solche
   Konstruktionen gehören auf höchstens ein Zehntel der Fragen.
3. **Keine Zustandsbeschreibungen.** „Aktueller Zustand einer Sache" für STATUS,
   „Beschaffenheit der Gesichtshaut" für TEINT, „Begleitender Faktor" für
   UMSTAND — das sind Definitionen aus dem Wörterbuch, keine Rätselfragen.
   Richtig: „Stand der Dinge", „Hautbild", „Nebenbedingung".
4. **Keine Tätigkeitsumschreibung für Tätigkeitswörter.** „Sportlich an Felsen
   steigen" für KLETTERN ist zu lang und zu erklärend. „Alpine Fortbewegung"
   oder schlicht „Felsensport" trägt.
5. **Ein bis fünf Wörter.** Ein einziges Wort ist oft die beste Lösung und
   keineswegs zu wenig: „Kandidat" für ANWÄRTER, „Hautsalbe" für CREME,
   „Kurzwort" für AKRONYM. Umgekehrt sind Fragen mit drei Zeilen Fließtext fast
   immer ein Zeichen dafür, dass die kompakte Definition noch nicht gefunden
   ist.
6. **Der Wortstamm der Lösung darf nicht vorkommen.** „Wer erbt" für ERBE ist
   unzulässig. `render_book.py` meldet Verdachtsfälle unter
   FRAGE ENTHAELT DEN WORTSTAMM.

**Gegenüberstellung** (links tatsächlich vorgekommen, rechts der Zielton):

| Lösung | zu lang und beschreibend | richtig |
|---|---|---|
| STATUS | Aktueller Zustand einer Sache | Stand der Dinge |
| NÄGEL | Was der Hammer trifft (Pl.) | Blechstifte (Pl.) |
| AKRONYM | Wort aus Anfangsbuchstaben | Kurzwort |
| KLETTERN | Sportlich an Felsen steigen | Alpine Fortbewegung |
| LADEN | Geschäfte in der Stadt | Verkaufsraum |
| CREME | Pflegeprodukt für die Haut | Hautsalbe |
| TEINT | Beschaffenheit der Gesichtshaut | Hautbild |
| MASSE | Physikalische Gewichtsgröße | Gewicht in Kilogramm |

**Ausnahme: die Sprichwortanspielung.** Neben der Nominaldefinition ist ein
zweites Register zugelassen — die augenzwinkernde Anspielung auf ein bekanntes
Sprichwort oder eine feste Redewendung. „Fährt im Hühnerstall Motorrad" für OMA
ist keine Definition und verstößt gegen die Regeln 1 bis 4, funktioniert aber,
weil der Löser die Wendung erkennt und nicht nach einer Beschreibung sucht.

Dafür gelten drei Bedingungen:

* Die Wendung muss allgemein bekannt sein. Regionale oder milieugebundene
  Sprüche gehören nicht hierher.
* **Höchstens ein bis zwei solcher Fragen je Rätsel.** Sie leben davon, selten zu
  sein; als Dauerform wird das Buch beliebig.
* Die Breitenprüfung gilt unverändert. Umbruchvarianten durchprobieren, statt die
  Formulierung aufzugeben: `Fährt im / Hühner- / stall / Motorrad` passt,
  `Motorrad / im Hüh- / nerstall` nicht.

**Zum Niveau.** Die Rätsel sollen an einzelnen Stellen etwas kniffliger sein,
ohne insgesamt schwer zu werden. Das ist überwiegend eine Sache der
**Wortauswahl**, nicht der Formulierung: zu HAUS oder JAHR gibt es keine
kniffelige Frage, zu SMUTJE oder ASBEST schreibt sie sich von selbst. Dafür
sorgt der Rätselwortschatz aus Abschnitt 4a. Beim Formulieren heißt es: die
geläufige Definition wählen, aber nicht die allererste — „Feuerfester
Faserstoff" statt „Baustoff", „Reiterei" statt „Truppe".

**Weitere Punkte:**

* Die geläufige Definition schlägt die originelle Umschreibung. „Freiheitsentzug"
  für HAFT ist gut, „Zelle statt Freiheit" umständlich.
* Form und Numerus müssen stimmen: Mehrzahl mit „(Pl.)" kennzeichnen, wenn die
  Frage es nicht ohnehin ausdrückt; Komparative in der Steigerungsform fragen.
* Nicht zu speziell werden. „Region um Kyjiw" trifft OSTEUROPA nicht,
  „halb Europa, östlich" schon.
* Grammatisch sauber. „Männliche Sau" für EBER, nicht „Er ist eine Sau".
* Kein Kalauer um des Kalauers willen.

**Halb-Thematisierung.** Auch allgemeine Füllwörter sollen thematisch gefärbt
umschrieben werden. Der Cache enthält Fragen aus früheren Büchern mit anderen
Themen — **prüfe deren Ausrichtung**. Passt eine gespeicherte Frage nicht zum
aktuellen Thema, ergänze eine themengebundene Variante, statt die vorhandene zu
ändern.

### 6a-0. Synonyme im selben Raster

Zwei Wörter für dieselbe Sache auf einer Seite — ABORT und KLOSETT, WEG und
PFAD — sind kein Grund, das Rätsel zu verwerfen und neu zu bauen. Das kostet
die ganze Seite an Fragenarbeit und bringt wenig: der Generator kennt keine
Bedeutungen, das nächste Raster kann dasselbe wieder liefern.

Gelöst wird es in den **Fragen**. Sie dürfen kein gemeinsames Wort tragen, sonst
sieht die Seite aus wie ein Versehen:

* falsch: ABORT „Stilles Örtchen" **und** KLOSETT „Örtchen mit Spülung"
* richtig: ABORT „Stilles Örtchen" und KLOSETT „Toilette mit Spülung"

Es geht um das gemeinsame Stichwort, nicht um die Verwandtschaft der Antworten.
Zwei Fragen, die aus verschiedenen Richtungen kommen, stören niemanden.

Für gleiche Wort**stämme** gilt das nicht — die verhindert der Generator hart
(Abschnitt 5c).

### 6a-1. Themenwörter thematisch erfragen — auch Kolorit

Ein Wort, das aus einer Themenliste stammt, soll seine Frage auch aus dem Thema
beziehen. Das gilt **einschliesslich Kolorit**: bekommt ein Koloritwort eine
rein neutrale Frage, ist es im fertigen Buch kein Themenwort mehr, obwohl es als
solches ausgewaehlt wurde. Der Themenbezug ist der ganze Zweck der Auswahl.

Der Fehler liegt nie in der Themenbindung selbst, sondern in ihrer Ausfuehrung.
Zwei Muster, die nicht taugen:

* **Synonym plus angehaengter Themenbezug.** DUSCHRAUM als „Waschraum der
  Bergleute": Waschraum ist blosse Wortersetzung, „der Bergleute" nur
  drangeklebt. Besser ist ein Bild aus dem Thema, das ohne Synonym auskommt:
  „Letzte Station der Schicht".
* **Zu vage, um aufloesbar zu sein.** KONTRA als „Ansage gegen das Spiel" nennt
  das Thema, laesst aber offen, welches Spiel und welche Ansage gemeint ist.
  „Ansage beim Skat" benennt beides und bleibt gleich kurz.

Sachliche Fehler wiegen schwerer als schwache Bilder: LUEGE als „Unwahrheit vor
Gericht" ist falsch, weil die Luege vor Gericht die Falschaussage ist. Hier hilft
keine bessere Formulierung, sondern nur der Verzicht auf die Bindung — die
neutrale Frage „Unwahrheit" ist dann die richtige.

**Reihenfolge beim Schreiben:** erst eine thematische Fassung suchen, die
sachlich stimmt und ohne Synonymersatz auskommt. Erst wenn das nicht gelingt,
neutral formulieren. Die neutrale Frage ist die Ausnahme, nicht der Normalfall.

Als Massstab: MUSIK als Kernwort von SALZGITTERBAD bekam „Klang beim
Altstadtfest". Das traegt, weil das Altstadtfest tatsaechlich ein Ort fuer Musik
ist — aber es ist die Untergrenze des Brauchbaren.

### 6a-1a. Doppelte Fragen aus dem Fragen-Cache

`clues.json` wächst über Bücher hinweg. Zwei verschiedene Wörter können dabei
dieselbe alte Frage tragen. In Seite 1 standen NAHE und SIEG gemeinsam im
Raster, beide mit „Nebenfluss des Rheins" aus einem früheren Buch. Der Renderer
merkt das nicht.

Deshalb: beim Prüfen der Wortliste nicht nur auf fehlende Fragen achten, sondern
die **vorhandenen Fassungen des Rasters nebeneinander lesen**. Bei Dopplung eine
neue Fassung schreiben und voranstellen — solange die Seite noch nicht fertig
ist, ist Voranstellen zulässig.

### 6a-1b. Die Frage muss das Wort treffen, nicht nur streifen

Vier Fehler, die im Oma-Buch alle auf Seite 1 zugleich standen. Sie sehen
harmlos aus, weil `fitcheck.py` sie nicht erkennt — Breite, Wortstamm und
Klammerzusatz stimmen ja.

**1. Die Themenbindung darf nichts Falsches behaupten.** Ein allgemeines Wort
wird nicht dadurch zum Themenwort, dass die Frage das Thema nennt. PARK als
„Grünanlage in Salzgitter" behauptet eine Ortsbindung, die es nicht gibt — ein
Park ist überall ein Park. Ebenso SEEBAD als „Badeort am Schwarzen Meer": Seebäder
gibt es an jeder Küste. Beide bekamen die zutreffende allgemeine Frage.

Prüffrage: Wäre die Frage auch dann richtig, wenn das Thema im Buch gar nicht
vorkäme? Lautet die Antwort nein und ist die Einschränkung sachlich falsch, ist
die Bindung zu streichen.

**2. Die Frage darf nicht behaupten, das Wort sei etwas anderes.** KOPFHOERER
als „Radio am Krankenbett" ist schlicht falsch, ein Kopfhörer ist kein Radio.
Richtig ist „Lautsprecher dicht am Ohr". Der Fehler entsteht, wenn man vom
Verwendungszusammenhang statt vom Gegenstand her denkt.

**3. Fachbedeutungen brauchen das Thema in der Frage.** Ist ein Wort nur in
seiner fachlichen Bedeutung gemeint und ohne Kenntnis des Themas nicht zu
erraten, muss die Frage das Themenfeld erkennbar machen. Nicht durch Abdrucken
des Themennamens, sondern durch die Wahl der Begriffe: LORE als „Wagen im
Stollen" nennt den Bergbau nicht, ruft ihn aber auf; HUNT als „Förderwagen im
Bergbau" macht es ausdrücklich, weil das Wort sonst gar nicht zu finden wäre.
Je entlegener das Fachwort, desto deutlicher darf der Fingerzeig sein.

Bleibt das Wort auch mit Fingerzeig unlösbar, weil die fachliche Bedeutung
selbst unbekannt ist, gehört es mit `theme_drop.py` aus dem Thema und bekommt
die allgemein bekannte Bedeutung als Frage. So bei STOSS: im Bergbau die
seitliche Begrenzung einer Strecke, für alle anderen ein Aufprall. Ein
Fingerzeig auf den Bergbau hätte hier nicht geholfen, sondern nur in die Irre
geführt.

Die Unterscheidung: Kennt die Empfängerin das Wort in der Fachbedeutung
grundsätzlich, braucht sie nur den Hinweis auf das Feld — dann Fingerzeig.
Kennt sie die Fachbedeutung gar nicht, ist das Wort im Thema falsch aufgehoben
— dann `theme_drop.py`.

**4. Ein Synonym ist keine Frage.** UNHEILVOLL als „verhängnisvoll" ist blosse
Wortersetzung, nicht Definition. Wer das eine Wort nicht kennt, kennt das andere
auch nicht. Besser ist eine Umschreibung der Eigenschaft: „düster und drohend".
Dasselbe galt für DUSCHRAUM als „Waschraum" (Abschnitt 6a-1).

### 6a-2. Ukrainische Namen: Duden-Transkription aus dem Ukrainischen

Maßgeblich ist die **Duden-Transkription, angewandt auf die ukrainische
Namensform** — nicht auf die russische. Dieselbe Umschrift verwendet auch das
Auswärtige Amt in seiner Liste „Nach Duden transkribierte Schreibweise
ukrainischer Ortsnamen".

Daraus folgt beides zugleich, ohne Ausnahmeregel:

* Ausgangsform ist der ukrainische Name, nicht der russische: **KYJIW** (nicht
  Kiew), **LWIW**, **CHARKIW**, **DNIPRO**, **TSCHORNOBYL**.
* Die Duden-Regeln für die Lautwiedergabe gelten dabei vollständig. Dazu
  gehört, dass **с zwischen Vokalen als ss** wiedergegeben wird, damit es
  stimmlos gesprochen wird. Aus Одеса wird deshalb **ODESSA**, nicht Odesa —
  mit einem s spräche man im Deutschen ein langes e und ein weiches s.

ODESSA ist also keine Rückkehr zur russischen Form, sondern das Ergebnis
derselben Regel, die auch KYJIW hervorbringt. Wer unsicher ist, schlägt im
Duden nach oder in der genannten Liste des Auswärtigen Amtes.

### 6a-3. Sachliche Genauigkeit der Frage

Die Frage muss auf die Antwort führen und auf nichts anderes. Wiederkehrende
Fehler, jeder davon schon vorgekommen:

* **Grammatische Zahl.** Fragt die Frage nach einem Volk, lautet die Antwort
  AZTEKEN, nicht AZTEKE. Für den Einzelnen heißt es „Mann aus altem Mexiko".
  Dasselbe bei LIRE: das ist der Plural, also „Alte Münzen Italiens (Pl.)".
* **Die Frage muss eindeutiger auf die Antwort führen als auf ein anderes
  Wort.** „Ruf ohne Stimme" ist PFIFF, nicht PFEIFE. „Höhepunkt einer Sache"
  ist eher der Gipfel als der CLOU — dort trifft „Knackpunkt".
* **Keine Frage, die nur mit dem Thema im Kopf aufgeht.** Der Löser sieht das
  Thema nicht. „Warme Unterlage im Korb" für DECKE setzt voraus, dass man an
  einen Hundekorb denkt; „Warme Auflage fürs Bett" steht für sich. Ebenso
  „Kennzeichen unter der Haut" für CHIP — der Chip ist zuerst ein Schaltkreis.
* **Keine erfundenen Zuschreibungen.** SUSI ist ein Mädchenname, kein
  Nagetiername; HASSO ist ein Hundename wie Bello, aber „Rufname für den
  Hofhund" behauptet eine Festlegung, die es nicht gibt.
* **Vollständige Redewendungen.** „sich völlig grün" ergibt nichts, „sich grün
  sein" schon — und nur, wenn die Wendung wirklich geläufig ist.
* **Keine Fachfehler, auch nicht populäre.** MORD ist nicht „vorsätzliche
  Tötung" — Totschlag ist ebenfalls vorsätzlich, die Abgrenzung liegt bei den
  Mordmerkmalen. Wer ein Rechtsgebiet, eine Krankheit oder eine Technik
  erfragt, muss die Sache kennen oder die Frage so wählen, dass sie ohne
  Fachwissen richtig bleibt (etwa „Schwerstes Tötungsdelikt").
* **Nichts erfinden, um eine Prüfung zu bestehen.** BRAT hat keine Bedeutung
  als Kurzform von „Bratsche" — ich hatte sie erfunden, nachdem die erste
  Fassung an der Wortstammprüfung gescheitert war. Wenn eine Frage abgelehnt
  wird, ist die Antwort eine andere richtige Frage, nicht eine erfundene.
  Fällt zu einer Antwort nichts Richtiges ein, gehört sie gemeldet.
* **Veraltete Wörter kennzeichnen oder meiden.** RAIN für den Grasstreifen am
  Feldrand gibt es, ist aber selten; solche Antworten brauchen eine Frage, die
  das Alter miterzählt, oder sie gehören nicht ins Buch. Wo das Wort auch mit
  Zusatz nur noch historisch ist — ULAN für den Lanzenreiter —, gehört es
  gesperrt, nicht erfragt. Der Maßstab ist derselbe wie beim Rätselwortschatz
  (Abschnitt 4a): kennt man, benutzt man selten — nicht: hat man noch nie
  gehört.

### 6a-0a. Fragen auf die Buchthemen hin schreiben

Die Fragen entstehen nicht aus einer Datei, sondern werden geschrieben. Also
sind sie auch der Ort, an dem die Themen des Buchs sichtbar werden — und zwar
bei **allen** Antworten, nicht nur bei den Themenwörtern.

Vor jeder Seite lohnt ein Blick auf die Themenliste des Buchs. Kommt ein
Grundwort oder ein Koloritwort vor, das sich an ein Thema anlehnen lässt, wird
die Frage dorthin gedreht:

| Antwort | neutral | auf das Buch hin |
|---|---|---|
| STREIT | Zank und Hader | Zank vor Gericht |
| DECKE | Warme Auflage fürs Bett | Warmes im Hundekorb |
| SPIEGEL | Glas zum Betrachten | Blick beim Schminken |
| WURZEL | Teil der Pflanze | Was im Borschtsch steckt |

Zwei Grenzen: Die Frage muss **auch ohne Themenkenntnis lösbar** bleiben (siehe
6a-3) — der Löser sieht die Themenliste nicht. Und sie darf nicht gezwungen
wirken; bei Koloritwörtern lohnt es oft, bei Grundwörtern selten. Wo es passt,
macht es das Buch persönlich, und genau dafür wird es gemacht.

**Eine so gedrehte Frage wird themengebunden gespeichert.** Sie geht nur mit
dem Thema auf und wäre in einem anderen Buch ein Rätsel ohne Lösung. Deshalb
kommt sie nicht als schlichter Text nach `clues.json`, sondern als Objekt:

```json
"OFEN": [{"c": "Herz der\nSauna", "t": "SPA"}, "Wärme-\nquelle im\nZimmer"]
```

`render_book.variants` nimmt die gebundene Fassung, solange SPA im Buch steht,
und sonst die neutrale. **Jedes Wort behält mindestens eine neutrale Fassung** —
sonst steht es im nächsten Buch ohne Frage da.

**Jede thematisch gedrehte Frage wird gebunden — das ist Pflicht, nicht Kür.**
Sie ist der Grund, warum in einem Buch mit Thema Jura für TENOR „Kern des
Urteils" erscheint und in einem Musikbuch „Hohe Männerstimme". Ohne Bindung
nimmt der Renderer schlicht die erste Fassung der Liste, und das Buch bekommt
zufällig mal die eine, mal die andere.

Die Abgrenzung läuft nicht über die Wortart, sondern darüber, **wo der
Themenbezug sitzt**:

* **Binden**, wenn der Bezug im *Wortlaut der Frage* steckt und dort auch
  wegfallen könnte: KIEL „Feder zum Schreiben" (Bücher) neben „Längsbalken am
  Boot", STREU „Bodenbelag im Käfig", BLEI „Weiches Metall aus der Grube",
  METRO „Untergrundbahn in Paris" neben „Bahn unter der Stadt".
* **Nicht binden**, wenn der Bezug schon in der *Wortbedeutung* liegt und die
  Frage gar nicht anders lauten kann: MASKARA, DNIPRO, LUMOS, WELPE, ILSESTEIN.
  Eine Bindung wäre dort wirkungslos und nähme dem Wort im Zweifel die einzige
  Frage.

**Neutrale Fassung mitschreiben, wo das Wort auch außerhalb seines Themas
vorkommt.** Bei Alltagswörtern wie STEG, KREUZ, PARK, HAAR, ECKE gehört neben
die gebundene eine neutrale Fassung; sonst steht das Wort im nächsten Buch ohne
Frage da. Zwingend ist es nicht — fehlt sie, wird eine neue Frage geschrieben,
was nur Token kostet. Bei reinen Themenwörtern erübrigt sie sich.

### 6a-4. Klammerzusätze: Plural, Englisch, Abkürzung

Drei Fälle verlangen einen Zusatz in Klammern, sonst ist die Frage nicht
eindeutig lösbar:

| Fall | Zusatz | Beispiel |
|---|---|---|
| Plural | `(Pl.)` | BERGE — „Alpen und Anden (Pl.)" |
| englisches Wort, nicht fest eingedeutscht | `(engl.)` | GLOWUP — „Verschönerung (engl.)" |
| **fremdsprachiges Wort allgemein** | `(Ukr.)`, `(frz.)`, `(ital.)` … | DERUNY — „Kartoffelpuffer (Ukr.)" |
| Abkürzung | `(Abk.)` | STGB — „Strafgesetzbuch (Abk.)" |

Bei fremdsprachigen Wörtern genügt statt der Klammer auch die ausgeschriebene
Sprache in der Frage: SELO „Dorf auf Ukrainisch" braucht kein `(Ukr.)` mehr.
Entscheidend ist, dass die Herkunft überhaupt genannt wird — ohne sie ist
DERUNY nicht lösbar, weil das Wort im Deutschen nichts bedeutet.

Nicht gemeint sind englische Wörter, die im Deutschen fest eingebürgert sind:
STREIK, KEKS, SPORT, TRAINER brauchen nichts. MEALPREP, LEAVEIN, GLOWUP,
QUIDDITCH schon. Die Grenze ist Ermessenssache — im Zweifel kennzeichnen.
Abkürzungen werden immer gekennzeichnet, auch geläufige.

Gepflegt wird das in zwei Dateien: `kennzeichen.txt` (Wort und geforderter
Zusatz, `engl.` oder `Abk.`) und `formen.txt` für Plurale.

**Wie kennzeichen.txt gefüllt wird.** Von Hand, an drei Gelegenheiten:

1. **Beim Themenaufbau.** Die englischen Begriffe eines Themas stehen in der
   Handliste vor einem — MEALPREP, LEAVEIN, AGILITY, HALFTIMESHOW. Sie gehören
   im selben Arbeitsgang nach `kennzeichen.txt`, nicht später. Das ist die
   Hauptquelle; der Rest sind Nachträge.
2. **Beim Fragenschreiben.** `collect_clues.py` hängt den Pflichtzusatz direkt
   an das Wort in der FEHLT-Liste — `GLOWUP!(engl.)`. Damit steht er schon da,
   bevor die Frage formuliert wird, statt hinterher beanstandet zu werden.
3. **Als Netz.** Fällt beim Rendern ein unmarkiertes Wort auf, kommt es in die
   Datei und die Frage wird ergänzt.

Automatisch erkennen lässt sich das nicht zuverlässig: KEKS, STREIK und SPORT
sind englischen Ursprungs und brauchen nichts, LOOK und STORY brauchen es.
Die Entscheidung bleibt Ermessen.

**Geprüft** wird an zwei Stellen: `fitcheck.py --eintragen` weist eine Frage ohne
nötigen Zusatz zurück, `render_book.py` meldet sie unter „ZUSATZ FEHLT". Beides
sind Kontrollen, kein Ersatz dafür, den Zusatz gleich mitzuschreiben.

Meldet die Prüfung `(Pl.)` für ein Wort, das gar kein Plural ist — TÖPFER,
BETRÜGER, PAPIER —, liegt der Fehler in der Formerkennung, nicht in der Frage.
Dann gehört ein `WORT SG` nach `formen.txt` (Abschnitt 5b), keine Änderung an
der Frage.

### 6b. Zeilenumbruch und Breite — vor dem Rendern prüfen

Das Kästchen fasst höchstens vier Zeilen von rund neun schmalen Zeichen. Zu
breite Fragen werden beim Rendern **abgeschnitten** — im fertigen Buch steht dann
„Korn zum Auspflan" oder „Braunschweiger Schrift". Trennstriche setzt du selbst;
eine Zeile darf nur mit `-` enden, wenn dieser Bindestrich im Fragetext steht.

```bash
python fitcheck.py "Anzei-\nchen im\nProzess" "Hinweis\nvor Ge-\nricht"
python fitcheck.py --auto "Anzeichen im Prozess" "Hinweis vor Gericht"
```

Die erste Form prüft einen selbst gesetzten Umbruch, die zweite setzt ihn selbst
— mit sauberer Silbentrennung, sofern `pyphen` verfügbar ist, sonst hart nach
Breite. `--auto` meldet ZU LANG, wenn der Text auch umgebrochen nicht in vier
Zeilen passt; dann muss die Frage kürzer formuliert werden.

Entscheidend ist die **Breite, nicht die Zeichenzahl**: „Klagelied" mit neun
Buchstaben passt nicht in eine Zeile, „Stand der" mit neun schon. Schätzen führt
in die Irre, messen nicht.

Ausgabe `OK` oder `ZU BREIT` je Variante, ohne Rendern. Prüfe mehrere
Formulierungen in einem Aufruf und trage erst die passende ein. `render_book.py`
prüft dasselbe nochmals und listet unter PASST NICHT INS KAESTCHEN, was übrig
bleibt — dort sollte nichts mehr stehen.

Trage Fragen per kurzem Skript ein, das `clues.json` lädt, mit `update()` ergänzt
und zurückschreibt — gib die Datei nicht von Hand neu aus.

### 6b-1. Bereits umgebrochene Fragen nicht zweimal trennen

`umbrechen` löst vorhandene Trennstriche am Zeilenende auf, bevor es neu
umbricht. Ohne diesen Schritt wird eine schon fertige Frage zerstört: aus
`Schmerz-\nhaft` liest die Funktion zwei Wörter, trennt das erste noch einmal
und liefert `Schmer-\nz- haft` — ein zweiter Bindestrich mitten in der Zeile.

Zu erkennen ist der Schaden an einem Bindestrich, dem ein Leerzeichen folgt.
Prüfen lässt er sich mit einer Suche nach `"- "` in `clues.json`.

Getrennte Wörter mit Bindestrich im Satz (`Vor- und Zuname`) sind davon nicht
betroffen: aufgelöst wird nur ein Bindestrich unmittelbar vor einem
Zeilenumbruch.

### 6c. Der Regelweg: fitcheck.py --eintragen

Fragen werden nicht von Hand umgebrochen und dann geprüft, sondern in einem
Schritt geschrieben und eingetragen:

```
python fitcheck.py --eintragen "KEULE=Hinterlauf beim Hund" \
                                "MAULKORB=Schutz gegen Beißen" ...
```

Der Aufruf nimmt Rohtext ohne Umbrüche, setzt die Silbentrennung selbst
(pyphen, also korrekt getrennt statt nach Breite abgeschnitten), misst die
Kästchenbreite, sucht den Wortstamm der Lösung in der Frage und prüft den
Klammerzusatz. Nur was alle vier Prüfungen besteht, landet in `clues.json`;
der Rest wird mit Grund gemeldet und übersprungen. Abgelehnte Fragen werden neu
formuliert und im nächsten Aufruf mitgeschickt.

Der frühere Weg — Umbruch von Hand raten, mit `fitcheck.py` messen, bei „ZU
BREIT" neu raten, am Ende alles per Skript in `clues.json` schreiben — kostete
drei bis fünf Aufrufe je Seite. Es sind jetzt ein bis zwei. Alle Fragen einer
Seite gehören in **einen** Aufruf.

`fitcheck.py "..."` ohne Schalter bleibt für die reine Messung einzelner Texte
erhalten.

**`fitcheck.py --durchsehen`** nimmt sich die ganze `clues.json` vor: jede
Fassung wird neu umgebrochen, der Wortlaut bleibt unangetastet. Was auch dann
nicht in vier Zeilen passt, wird als `NEU FORMULIEREN` gemeldet.

Das ist **kein Routineschritt je Buch**, sondern eine Wartungsarbeit. Sie lohnt
nach einer Schriftänderung, nach einem Eingriff in `trennung.txt` oder wenn der
Renderer auffällig viele Altfragen beanstandet. Im Normalbetrieb genügt die
Prüfung beim Rendern, die nur die tatsächlich verwendeten Fragen betrifft.

### 6d. Fertige Seiten bleiben unangetastet

Eine Seite ist fertig, sobald ihr Raster in `puzzles/` liegt und die Fragen
geschrieben sind. Danach wird an ihr nichts mehr geändert — weder am Raster
noch an den Fragen, und auch nicht mittelbar.

Mittelbar heißt: die drei Wege, auf denen sich eine fertige Seite ungewollt
verändert, sind

1. eine **neue Fassung vorangestellt** statt angehängt (Abschnitt 3b),
2. eine **bestehende Fassung überschrieben oder gelöscht**, sodass die
   Rotation eine andere greift,
3. ein **Wort gesperrt**, das auf der Seite steht.

Nummer drei ist der teure Fall und verlangt den vollen Rückbau
(`blacklist_add.py` → `rollback.py` → `book.py`) samt neuer Fragen. Nummer eins
und zwei sind zu vermeiden, nicht zu reparieren.

Das PDF wird bei jedem Lauf vollständig neu geschrieben — das ist billig und
unschädlich, solange die Fragen stabil bleiben. Nur wenn sich eine Frage einer
fertigen Seite geändert hat, ist etwas schiefgelaufen; dann gehört der Grund
gesucht, nicht das PDF ersetzt.

## 7. Buch rendern

```bash
python render_book.py /mnt/user-data/outputs
```

Je Rätsel eine Prüfzeile, dann die Liste der Fragen, die nicht ins Kästchen
passen. Diese kürzen und erneut rendern. Wer vorher `fitcheck.py` benutzt hat
(Abschnitt 6b), findet hier nichts mehr vor — abgeschnittene Fragen im fertigen
PDF sind der auffälligste Qualitätsmangel überhaupt und vollständig vermeidbar.

Prüfe zusätzlich die Meldung FRAGE ENTHAELT DEN WORTSTAMM und beseitige jeden
Treffer.

## 8. Token-Disziplin

**Sieh dir keine gerenderten Seiten als Bild an.** Ein Vollseiten-PNG kostet ein
Vielfaches jeder Textausgabe. Alle Prüfungen laufen programmatisch: Überlauf,
Notrennungen, leere Blöcke, unversorgte Zellen. Ein Bild nur, wenn sich etwas aus
Zahlen nicht klären lässt — dann einmal und in niedriger Auflösung.

**Gib keine vollständigen Wortlisten aus.** Die Skripte melden nur, was Handlung
erfordert. `theme_scan.py` schreibt die Masse in eine Datei und zeigt nur die
knappen kurzen Wörter.

**Arbeite in Blöcken.** Ein Aufruf für zehn Rätsel, eine Sammelliste fehlender
Fragen, ein Renderlauf. Kein Dialog je Rätsel.

**Sichere den Stand.** Der Container wird zwischen Sitzungen zurückgesetzt. Packe
am Ende `clues.json`, `used_words.json`, `themes.json`, `plan.json`, `puzzles/`
und `blacklist.txt` in ein ZIP nach `/mnt/user-data/outputs`.

## 9. Dateien

```
book/
  core.py             Lexikon, Dämpfung, Erzeugung, Themen-Nachbesserung, Formkorrektur
  themes.py           lädt themes.json, rechnet Gewicht × Nähe
  theme_facets.py     importiert eine Facettendatei          (Stufe 1)
  theme_subscan.py    Subsuche mit jedem Facettenwort als Saat (Stufe 2)
  theme_expand.py     Zusammensetzungen und Stammfamilien     (Stufe 3)
  theme_flex.py       Beugungen und Ableitungen als Kolorit   (Stufe 4)
  theme_build.py      führt die vier Stufen nacheinander aus
  theme_scan.py       Scanner mit handgetippten Stichwörtern (Sonderfall)
  theme_add.py        übernimmt Wörter in ein Thema
  theme_drop.py       entfernt Wörter aus einem Thema
  theme_review.py     Sichtprüfung einer Themenliste nach Länge
  theme_stats.py      Bilanz der Themenlisten gegen den Buchbedarf
  plan_book.py        streut Wunschwörter über das ganze Buch (Pflicht/weich)
  book.py             Batch-Erzeugung, schreibt puzzles/NN.pkl
  collect_clues.py    meldet fehlende Fragen, Themenstufe und Formverdacht
  fitcheck.py         prüft Fragetexte auf Kästchenbreite, setzt auf Wunsch den Umbruch
  import_raetselwoerter.py  trägt die Fragen aus raetselwoerter.txt in clues.json ein
  render_book.py      rendert raetselbuch.pdf und prüft
  bookpdf.py          Seitenaufbau: Rätselseiten, 3×3-Lösungsseiten
  blacklist_add.py    Wörter sperren
  rollback.py         Nutzungskonto zurückrechnen vor Neuerzeugung
  wordcheck.py        Partizip-, Wortstamm- und Pluralprüfung, Sperrlistenparser
  fonts/              Nimbus Sans Narrow Bold und Regular, PT Sans Narrow
  themes.json         LEER — je Chat zu füllen
  wunschwoerter.txt   je Chat zu füllen
  formen.txt          Handkorrekturen der Formerkennung (PL | KOMP | SG)
  freigabe.txt        wieder zugelassene Wörter, die beim Listenbau herausfielen
  clues.json          Wort -> Varianten (dauerhaft, themenübergreifend)
  used_words.json     Nutzungskonto des laufenden Buchs
  blacklist.txt       für dieses Buch gesperrt
  stopwords.txt       dauerhaft gesperrt, rund 610 Wörter
  raetselwoerter.txt  klassischer Rätselwortschatz mit Fragen, rund 1.020 Einträge
  words_v3.json       Grundwortschatz, Häufigkeitsrang < 25.000
  fallback_v3.json    Rang 25.000 bis 100.000, nur als Notnagel
  build_wordlists.py  baut beide Listen neu (braucht Quelldateien in wl/)
  skanvord/           layout.py, fill.py, render2.py
```

## 9a. Leere Frageblöcke

Ein leerer Frageblock ist ein schwarzes Kästchen ohne Frage. Ob ein Raster
welche hat, steht schon vor dem Füllen fest — es ist eine Eigenschaft des
Layouts, nicht der Wortwahl. Deshalb lässt sich das Problem sauber lösen,
indem solche Raster gar nicht erst gefüllt werden.

`make_puzzle` sucht in vier Durchgängen:

| Durchgang | Seeds | leere Blöcke | Frühabbruch |
|---|---|---|---|
| 1 | die 8 regulären | 0 | nach 12 erfolglosen Füllversuchen |
| 2 | 32 weitere (`SEEDS_EXTRA`) | 0 | nach 12 |
| 3 | die 8 regulären | 0 | aus, volle `tries` |
| 4 | die 8 regulären | 1 | aus |

Durchgang 4 ist der Notausgang und greift praktisch nie: unter vierzig Rastern
ist fast immer eines ohne leeren Block. Er kostet nichts, solange er nicht
gebraucht wird, und verhindert, dass am Ende gar kein Rätsel entsteht.

Ein Raster zu erzeugen kostet rund elf Sekunden. Die 32 zusätzlichen Seeds
schlagen also mit etwa sechs Minuten zu Buche — aber nur in dem seltenen Fall,
dass die ersten acht nichts hergeben.

`render_book.py` gibt die Zahl je Seite als `leereBloecke=` aus. Steht dort
regelmäßig 1, ist die Layoutdichte (`DENSITY`) das Stellrad, nicht die Toleranz.

## 10. Laufzeit

Gemessen in einer Standardumgebung, A5-Raster 17×12, `CROSS_MIN` 0,58:

| Vorgang | Zeit |
|---|---|
| Lexikon bauen, Gewichte setzen | unter 1 s |
| viermal `improve_theme` | rund 4 s |
| `make_puzzle`, günstiges Raster | rund 50 s |
| `make_puzzle`, ungünstiges Raster | bis 6 min |
| Rätsel mit einem Vorgabewort | 2 bis 3 min |

**Die Streuung kommt aus dem Raster, nicht aus der Wortzahl.** `make_puzzle`
erzeugt der Reihe nach acht Raster und verwirft jedes, das die Prüfungen zu
Kreuzungsrate, Sättigung, Randbelegung und leeren Blöcken nicht besteht. Wie
viele Raster durchfallen und wie oft die Füllung an einem angenommenen Raster
scheitert, hängt am Zufallsstartwert. Ein Rätsel lief in 52 Sekunden, ein
anderes am selben Wortschatz in sechs Minuten.

**Warum überhaupt bis zu 45 Füllversuche je Raster?** Nicht wegen der
Machbarkeit — die erste gelungene Füllung ist bereits ein gültiges Rätsel. Sie
dienen der Auswahl: jeder Versuch startet mit anderem Zufall, nimmt einen
anderen Weg durch dieselben Slots und liefert eine andere Wortmischung. Bewertet
wird mit `2 × Kernbegriffe + 0,6 × übrige Themenwörter − 0,8 × seltene Wörter`.
Die erste Füllung ist im Schnitt eine mittelmäßige.

**Abbruch bei ausreichender Güte.** Sobald eine Füllung mindestens 30 %
Kernbegriffe und höchstens 12 % Wörter aus dem Rückfallwortschatz hat, wird sie
genommen und die Suche beendet — ein Vergleich mit weiteren Versuchen bringt
dann nichts mehr. Die Schwellen stehen als `GUT_KERN`, `GUT_SELTEN` und
`GUT_KERN_MIN` in `core.py`. Wird die Schwelle nie erreicht, entscheidet nach
`tries` Versuchen die beste Bewertung. Erreichbar ist die Schwelle nur mit einem
ausreichend großen Themenwortschatz — bei einer dünnen Handliste läuft jedes
Raster in die vollen 45 Versuche, was die lange Laufzeit der ersten Bücher
erklärt.

Ein früherer Ansatz, nach einer Reihe erfolgloser Versuche abzubrechen, brachte
gemessen nur sieben Prozent Zeitgewinn bei schlechterem Ergebnis und ist wieder
entfernt.

**Vorgabewörter.** `fill` probiert für jedes Vorgabewort passende Slots durch,
und jeder Platzierungsversuch zieht eine vollständige Füllung nach sich. Bei
acht Rasterkandidaten × 45 Füllversuchen × mehreren Slots waren das neun bis
zehn Minuten je Rätsel. `fill(..., forced_slots=3)` begrenzt die Slots je
Versuch; die Vielfalt kommt ohnehin aus den 45 Versuchen. Gemessen: 2 bis 3
statt 9 bis 10 Minuten.

Praktische Folge: rechne für ein 50-Rätsel-Buch mit ein bis zwei Stunden reiner
Rechenzeit und arbeite in Blöcken von zwei bis fünf Rätseln. Lange Läufe im
Vordergrund laufen in Zeitlimits — starte sie im Hintergrund und frage das
Protokoll ab:

```bash
(setsid nohup python book.py 1 5 > run.log 2>&1 < /dev/null &)
cat run.log
```

## 9b. Wann eine Füllung sofort angenommen wird

`make_puzzle` erzeugt bis zu `tries` Füllungen, bewertet jede und nimmt am Ende
die beste. Die Gütekriterien entscheiden nur, wann die Suche **vorzeitig**
abbricht — nie, was genommen wird. Eine zu niedrige Schwelle kostet also keine
Qualität durch falsche Auswahl, sondern durch zu frühes Aufhören.

**Untergrenze.** Eine Füllung mit weniger als `MIN_THEMA` = 40 % Themenwörtern
wird verworfen — sie wird nicht einmal als bester Kandidat gemerkt. Bleibt bis
zum Schluss keine bessere übrig, fällt das ganze Raster und der nächste Seed
kommt dran. Damit greift auch der Frühabbruch (`FRUEH_AUS`) bei einem Raster,
das zwar Füllungen liefert, aber nur schlechte.

Vier Bedingungen für die sofortige Annahme, alle müssen erfüllt sein:

| Kriterium | Konstante | Wert |
|---|---|---|
| Themenwörter insgesamt | `GUT_THEMA` | ≥ 65 % der Einträge |
| Kern **und Umfeld** zusammen | `GUT_KERN` | ≥ 56 % |
| Antworten mit 4–6 Zeichen | `GUT_KURZ` | ≤ 72 % |
| Wiederholungen | `GUT_WIED` | höchstens 1 |

Die Werte sind an der Verteilung der ersten zwanzig Seiten geeicht und treffen
grob deren oberes Fünftel: Themenanteil Median 60 %, 80-%-Quantil 64 %; Kern
und Umfeld Median 51 %, 80-%-Quantil 57 %; Kurzwortanteil Median 76 %,
30-%-Quantil 72 %. Wachsen die Werte im Lauf eines Buchs, gehören die Schwellen
nachgezogen — sonst bricht die Suche wieder zu früh ab.

**Seltene Wörter sind kein Kriterium.** Ein Wort aus dem Rückfallwortschatz ist
nicht schlechter als eines aus dem Grundwortschatz, nur ungewöhnlicher. In die
Bewertung (`score`) geht es weiterhin leicht negativ ein, für die sofortige
Annahme spielt es keine Rolle mehr.

**Der score** wiegt ab: `2,0 · Kern + 0,6 · Umfeld − 0,8 · selten −
5,0 · Wiederholungen − 0,15 · (kurze Antworten über dem Median)`. Der
Kurzwortabzug ist bewusst klein — kurze Wörter sind nicht schlecht, es sollen
nur nicht immer mehr werden.

## 9c. Slotlängen im Raster

Drei Viertel aller Slots haben vier bis sechs Zeichen. Das bestimmt den
Kurzwortanteil der Antworten — in einen Vierer passt nichts Längeres — und
mittelbar den Themenanteil, weil Themenvokabular überwiegend zusammengesetzt
und damit lang ist.

`layout.py` bestraft deshalb kurze Slots leicht: `STRAFE_L4 = 8.0` je
Vierer-Slot, `STRAFE_L5 = 2.0` je Fünfer. Gemessen an je sechs Layouts:

| Strafe | Einträge | 4er | kurz (4–6) | 7+ |
|---|---|---|---|---|
| ohne | 45,5 | 30,4 % | 76,2 % | 23,8 % |
| 6 / 1,5 | 44,2 | 26,4 % | 74,0 % | 26,0 % |
| 12 / 3 | 44,3 | 26,7 % | 71,8 % | 28,2 % |

Ein erster Versuch mit 2,0 / 0,5 blieb wirkungslos — zu schwach gegen die
übrigen Strafterme. Vorsicht nach oben: kurze Slots tragen die Kreuzungsrate,
zu harte Strafen kosten Einträge und lassen mehr Layouts an `CROSS_MIN`
scheitern.

## 10a. Warum Füllversuche scheitern

`book.py` gibt je Rätsel eine Diagnosezeile aus:

```
04 seed=149 n=45 kern=23 ... leer=0
   diag layouts=2 layouts_brauchbar=1 verworfen_saettigung=1
        fuellversuche=45 fuellung_gelungen=3 fuellung_knotengrenze=42
```

Zu lesen ist das so: von zwei erzeugten Rastern war eines brauchbar, das andere
zu gesättigt. Auf dem brauchbaren Raster liefen 45 Füllversuche, drei gelangen,
42 scheiterten. Erreicht eine Füllung die Güteschwelle (`GUT_KERN`,
`GUT_SELTEN`), steht zusätzlich `schwelle_bei_versuch=N` und die Suche bricht
dort ab — deshalb hat ein gutes Rätsel oft nur einen einzigen Versuch.

`fuellung_knotengrenze` und `fuellung_sackgasse` sind zu unterscheiden. Das
erste heißt: das Knotenbudget `MAX_NODES` war aufgebraucht, die Suche war noch
nicht fertig. Das zweite: die Suche war erschöpft, auf diesem Raster gibt es mit
diesem Wortschatz keine Belegung. Nur der erste Fall lässt sich mit mehr
Rechenzeit beheben.

**Frühabbruch enger Raster.** Hat ein Raster nach `FRUEH_AUS` = 12
Füllversuchen keine einzige gültige Belegung geliefert, wird es aufgegeben und
der nächste Seed genommen (`raster_frueh_aufgegeben` in der Diagnosezeile).
Ein Raster, das in zwölf Anläufen nichts liefert, liefert erfahrungsgemäß auch
in fünfundvierzig kaum etwas Brauchbares, und ein neues Layout kostet elf
Sekunden gegenüber dreiunddreißig weiteren Füllversuchen. Der Mechanismus
spart also Zeit, statt welche zu kosten. In den Durchgängen 3 und 4 ist er
ausgesetzt, damit ein schweres Raster am Ende doch noch seine vollen `tries`
bekommt.

Gemessen an einem schweren Raster (Rätsel 4) bringt eine Verdopplung von
`MAX_NODES` von 6000 auf 12000 dort **keine** höhere Erfolgsquote — die
Versuche brauchen ein Vielfaches, nicht das Doppelte. Solche Raster sind
schlicht eng; die Erfolgsquote liegt bei rund einem Zwanzigstel, und
`make_puzzle` fängt das über die Zahl der Versuche auf. Die Grenze steht
trotzdem auf 12000, weil sie bei mittelschweren Rastern hilft und die Kosten
nur dort anfallen, wo ohnehin nichts zu holen war.

## 10b. Die drei Wortschatzstufen

Das Lexikon entsteht zur Laufzeit aus mehreren Quellen. Die Zahlen sind
Größenordnungen, sie ändern sich mit den Themen:

| Stufe | Datei | Umfang | Gewicht |
|---|---|---|---|
| Grundwortschatz | `words_v3.json` | ~5.800 | nach Häufigkeit, bis 3,0 |
| Rückfall | `fallback_v3.json` | ~6.900 | 0,06 bzw. 0,012 |
| **Selten** | `selten_v3.json` | ~7.600 | 0,006 (`SELTEN_BASE`) |
| Themenwörter | `themes.json` | je nach Buch | quadratisch nach Nähe |
| Rätselwortschatz | `raetselwoerter.txt` | ~1.000 | 1,3 (`RAETSEL_BASE`) |
| Nachträge | `freigabe.txt`, `keinpartizip.txt` | ~150 | wie Grundwortschatz |

Die dritte Stufe enthält Wörter mit Häufigkeitsrang jenseits 100.000, die alle
Filter des Listenbaus bestehen — HEGEMONIE, PLEBISZIT, TÜFTLER, NEKTARINE,
INTERVALL, LEINÖL. Ihr Gewicht liegt unter dem schwächsten Rückfallgewicht:
sie sollen ein Raster nicht prägen, sondern nur retten, wenn ein Slot sonst
leer bliebe. In den Kennzahlen tauchen sie unter `selten=` auf.

Die Stufe ist gefiltert, aber **nicht nach Länge** — das Raster fasst
Antworten bis siebzehn Zeichen, und die Quelle liefert ohnehin höchstens
fünfzehn. Entfernt werden nur Fehlformen: durchgerutschte Partizipien
(VORAUSGEEILT, WARMGEHALTEN, VERFOCHTEN), Fachjargon auf -GRAMM, -SKOPIE,
-ITIS, Genitivformen auf -ENS (LEHRENS, NACHDENKENS), Steigerungs- und
Flexionsformen (DEUTSCHESTE, KONKRETERE). Von 7.791 Rohkandidaten bleiben
rund 7.270.

Ohne diese Reinigung landet Unsinn im Raster: LEHRENS hatte es im Test bis in
Seite 13 geschafft und erst dadurch fiel die ganze Genitivklasse auf.

Nicht aufgenommen wurden die rund 5.200 Kandidaten ganz ohne Häufigkeitsdaten.
Die Stichprobe war deutlich schlechter: Epoxischeibe, Adressoffset, Reglertyp,
schockfarben.

## 10c. Herkunftsanalyse — nur auf Anforderung

Wird eine Auswertung verlangt, hat sie **dieses** Format. Nicht von sich aus
erzeugen. Keine erläuternden Absätze zwischen den Zahlen — eine Tabelle, dann
die Zusatzzahlen, fertig.

**Eine Tabelle**, alle Quellen, Untergruppen eingerückt, jede Zeile mit dem
Anteil an **allen** Antworten (nicht am Zwischenwert):

```
Quelle                        Einsaetze   Anteil
Themenwortschatz                     80    59,7 %
  davon Kern                         61    45,5 %
  davon Umfeld                        1     0,7 %
  davon Kolorit                      18    13,4 %
Grundwortschatz (words_v3)           27    20,1 %
Raetselwortschatz                     3     2,2 %
Rueckfall (fallback_v3)              12     9,0 %
Dritte Stufe (selten_v3)              6     4,5 %
Nachtraege                            9     6,7 %
  davon alltag.txt                    6     4,5 %
  davon freigabe/keinpartizip         3     2,2 %
gesamt                              134   100,0 %
```

**Nachträge** sind Wörter, die in keiner der drei Wortlisten stehen und nur
über `alltag.txt`, `freigabe.txt` oder `keinpartizip.txt` ins Lexikon kommen.

Danach, ohne Zwischentext:

* **Themen**, absteigend: Einsätze und Anteil am Themenwortschatz.
* **Wiederholungen**: Zahl und Anteil an allen Antworten, dann je Wort die
  Seiten, die Gesamtzahl im Buch, die Quelle und die Wortlänge.
* **Kennzahlen je Seite**: `kern`, `them`, `selten`, Kreuzungsrate.

Der Bezug ist der, der verlangt wurde. Steht nichts dabei, gilt das ganze Buch.

**„Seltene Wörter"** (`selten=` in den Kennzahlen) sind Antworten, die weder zu
einem Thema gehören noch im Grundwortschatz stehen — also alles aus
`fallback_v3.json` und `selten_v3.json`. Der Wert misst, wie stark ein Rätsel
auf den schwachen Rand des Wortschatzes ausweichen musste.

## 11. Bekannte Schwächen

**Das Quellwörterbuch hat Lücken, die kein Filter verursacht.** `words_v3.json`
wurde einmalig aus dem igerman98-Hunspell-Wörterbuch gebaut (`index.dic` aus
`wooorm/dictionaries`, dazu die Frequenzlisten `de_50k.txt` und `de_full.txt`
von hermitdave). Der Bau liest ausschließlich **Lemmata** und wendet keine
Affixregeln an — gebeugte und abgeleitete Formen wie DECKE, EIDE, NÄGEL, LÄDEN
waren deshalb nie Kandidaten. Dazu kommen echte Lücken der Quelle: KATZE, AUGE,
DECKE und ZEITUNG fehlen dort als Lemma, auch in der großen Ausgabe mit 258.200
Einträgen; nur die Kompositionsstämme KATZEN, AUGEN, ZEITUNGS sind vorhanden.
Solche Fälle lassen sich nur über `freigabe.txt` schließen. Wer beim Prüfen
einer Wortliste ein geläufiges Wort vermisst, trägt es dort nach.

**Die Formerkennung arbeitet über Endungen** und liegt in beide Richtungen
daneben. Für Partizipien federt `keinpartizip.txt` das ab (Abschnitt 5a-2), für
Plurale und Komparative `formen.txt` (Abschnitt 5b). Beide Listen sind Handarbeit
und werden nie vollständig sein.

**Buchumfang einstellen.** `GESAMT_RAETSEL`, `ZIEL_KERN` und `ZIEL_UMFELD` in
`core.py` steuern Rationierung und Reichweitenrechnung. Bei einem anderen
Buchumfang als 50 dort anpassen.

**Kreuzungsrate und Themenanteil stehen im Zielkonflikt.** Bei hoher Kreuzungsrate
hat jeder Slot viele feste Buchstaben, die Kandidatenmenge schrumpft, und
Themenwörter passen seltener. Messwerte: ohne Kreuzungsuntergrenze rund 25 von
39 Einträgen thematisch, mit 58 % Untergrenze rund 15 von 48. Wer mehr Thema
will, senkt `CROSS_MIN` in `core.py` und die Strafschwelle `MIN_CROSS` in
`layout.py`. Der zweite Hebel sind größere Themenlisten, vor allem mit vier bis
sechs Buchstaben.

**Der Rückfallwortschatz** ist auf Häufigkeitsrang 25.000 bis 100.000 begrenzt
und durchläuft dieselben Filter wie der Grundwortschatz: keine Plurale, keine
Partizipien, keine Steigerungsformen, keine Pronomenformen, dazu `stopwords.txt`.
Sein Gewicht ist nach Seltenheit gestaffelt. Er ist damit deutlich sauberer als
früher, ersetzt die Sichtprüfung in Schritt 5 aber nicht — einzelne Wörter, die
in einem Rätselbuch nichts verloren haben, gehören auf die Sperrliste, und die
wächst mit jedem Buch.

**Raster mit hoher Kreuzungssättigung lassen sich kaum füllen.** Der Generator
filtert sie ab 0,66 vorab aus. Wer daran dreht, sollte wissen, dass jeder
gescheiterte Füllversuch rund 25 Sekunden kostet.
