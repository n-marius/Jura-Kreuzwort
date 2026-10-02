# Dieses Buch: Schwedenrätsel für die Oma

**Lies zuerst diese Datei, dann `README.md`.** Die README beschreibt das
Werkzeug allgemein, diese Datei alles, was nur für dieses eine Buch gilt.

---

## 0. Das Wichtigste zuerst

**Dieses Buch wird fortgesetzt, nicht neu begonnen.** `neues_buch.py` darf
**nicht** laufen. Es würde `puzzles/`, `used_words.json`, `plan.json`,
`themes.json` und die Facettendateien löschen und 29 fertige Seiten vernichten.

Stand bei Übergabe: **Seiten 1 bis 29 sind fertig** — Raster gebaut, Wortlisten
geprüft, alle Fragen geschrieben, beide PDF erzeugt. Es fehlen die **Seiten 30
bis 50**.

Der nächste Schritt ist schlicht:

    python book.py 30 30

Danach Wortliste prüfen, Fragen schreiben, rendern. Genau so weiter bis 50.

---

## 1. Empfängerin und Grundhaltung

Das Buch ist ein Geschenk für die Großmutter des Projektleiters. Sie ist
hochbetagt, lebt in **Salzgitter-Bad**, hat **schlesische Wurzeln** und eine
Kriegs- und Vertreibungsgeschichte in der Familie.

Daraus folgt der Maßstab für jedes Wort: **Würde sie es lösen können, und würde
es sie freuen statt belasten?** Ein Wort kann sachlich korrekt und trotzdem
falsch sein — weil es Fachjargon ist, weil es an Krankheit oder Krieg rührt,
oder weil es schlicht kein Wort ist, das eine Frau ihres Alters verwendet.

---

## 2. Die 19 Themen und ihre Gewichte

| Thema | Gewicht | Zuschnitt |
|---|---|---|
| SALZGITTERBAD | 20 | Stadtteil und Stadt Salzgitter, Ortsteile, Solequelle, Industrie |
| HARZ | 20 | Berge, Bergbau, Sagen, Bahn, Orte, Wandern |
| PFLANZEN | 15 | Blumen, Bäume, Garten, Obst, Gemüse |
| CHRISTENTUM | 10 | allgemein bekannt, keine Theologenfachsprache |
| FUSSBALL | 10 | |
| KOCHEN | 10 | Kochen und Backen |
| KRANKENHAUS | 10 | **nur Laienperspektive**, keine Fachmedizin |
| NIEDERSACHSEN | 10 | |
| QUIZSHOW | 10 | deutsche Fernsehquizsendungen |
| REISEN | 10 | Deutschland, Europa, Türkei, Schwerpunkt Busreisen für Senioren |
| BERGWERK | 7 | Schwerpunkt Eisenerz |
| JURA | 7 | **nur sehr einfache, allgemein bekannte Begriffe** |
| NORDSEE | 7 | |
| BRETTSPIELE | 5 | nur deutsche Klassiker, nichts Modernes |
| HUNDE | 5 | **keine Rassenamen** |
| KOSMETIK | 5 | |
| SPA | 5 | |
| UKRAINE | 5 | **nur vor 2022 in Deutschland Bekanntes, keine Transliterationen** |
| SCHLESIEN | 4 | deutsche Ortsnamen, Küche, Vertreibung |

Die Gewichte stammen vom Projektleiter und sind **nicht** zu verändern. Ein
Versuch, sie gemeinsam mit Faktor 2,15 anzuheben, hat den Themenanteil
gesenkt statt gehoben (Begründung in README 3c).

---

## 3. Wunschwörter

50 Wunschwörter, je eines pro Seite als Pflichtvorgabe, bereits in `plan.json`
verteilt. Die Reihenfolge wurde einmalig durchgemischt (Seed 20260831), weil
`plan_book.py` sonst nach Länge sortiert und die schwersten Vorgaben auf die
ersten Seiten legt.

**Noch offen, Seiten 30 bis 50:**

30 HUPENTONI · 31 KNEIPP · 32 JAGST · 33 KUMQUAT · 34 JETTA · 35 FORTUNA ·
36 BAD · 37 SALESCH · 38 BONING · 39 KIEW · 40 DRACHE · 41 HORST · 42 MONACO ·
43 LITZEL · 44 TALSPERRE · 45 ELLI · 46 BOSKOP · 47 BROCKEN · 48 ELSASS ·
49 TSV · 50 HAINBACH

Alle 50 haben ihre Frage bereits in `clues.json`, meist wörtlich so, wie der
Projektleiter sie vorgegeben hat. **Diese Fragen sind nicht zu ändern.**
Persönliche Bezüge: MARIUS Enkel, VANESSA Enkelin, AGNESSA Schwiegerenkelin,
PETRA Tochter, ELLI Mutter, KARL Vater, LITZEL Geburtsname, CHERRY Hundename,
BABYSITTERIN erster Job, OKTOBER Hochzeitsmonat, DALBERSDORF Dorf in Polen.

Wunschwörter dürfen **nicht zusätzlich als Füllwort** im Buch stehen. Nach jedem
`theme_build.py` prüfen, ob die Automatik eines über ein Kompositum
zurückgeholt hat (README 5a-3).

---

## 4. Was gesperrt ist — und warum

`blacklist.txt` enthält rund 800 Wörter. Die Klassen, in der Reihenfolge ihrer
Wichtigkeit:

**Krebs und schwere Krankheit.** Der Kern der Vorgabe. Neben dem offensichtlichen
Vokabular ist auch **BLASE** gesperrt — der Projektleiter hat den Bezug zur
Blasenkrebserkrankung ausdrücklich genannt. Ebenso THROMBOSE, DARM, KATHETER war
kurz gesperrt und wurde wieder freigegeben.

**Schwere Alterskrankheiten.** DEMENZ, SCHLAGANFALL, HERZINFARKT, SENIL,
EPILEPSIE, KOLLAPS. Historisch distanzierte Krankheiten sind dagegen **erlaubt**:
EBOLA, CHOLERA, LEPRA, PEST, SEUCHE, MALARIA, TETANUS, POCKEN, TOLLWUT,
EPIDEMIE, PANDEMIE, QUARANTAENE, MIGRAENE, TYPHUS, TUBERKULOSE.

**Tod und Bestattung** einschließlich Umlautformen (SAERGE fiel durch ein
Suchmuster, das nur SARG kannte).

**Krieg und Waffen.** Wegen der Familiengeschichte. ARSENAL, GUERILLA, REKRUT,
GENERAL, SOLD sind dagegen **freigegeben** — der Projektleiter hat hier
mehrfach großzügiger entschieden als ich.

**Partizipien ohne GE.** `wordcheck.ist_partizip` erkennt sie nicht. Rund 180
sind gesperrt. Zwei Suchdurchgänge waren nötig: der erste verlangte drei Zeichen
zwischen Präfix und Endung und übersah dadurch ERRUNGEN (ER + R + UNGEN).

**Anglizismen, aber nur die nicht eingedeutschten.** Hier lag ich anfangs
deutlich zu streng; 98 Wörter mussten wieder freigegeben werden. **Erlaubt sind**
CITY, BRUNCH, DEAL, MONITOR, PUNK, SPAM, STRESS (deutsch), COMPUTER, LAPTOP,
HANDY, INTERNET, SOFTWARE, JEANS, DISCO, TEAM, CLUB, SHOW, SHOP, TICKET, COACH,
LIVE, MEETING, WORKSHOP, SMALLTALK, EVENT und Ähnliches. **Gesperrt bleiben**
Fach- und Werbejargon: BROWSER, SERVER, ACCOUNT, DEADLINE, FEEDBACK, PODCAST,
STREAMING, SETUP, RESET, TASK, USER, LAYOUT, DISPLAY, ROADMAP, MAINFRAME, CMOS,
BITSTROM sowie der Kosmetik-Werbewortschatz GLOWUP, EYELINER, LIPGLOSS.

Maßstab: **Würde die Oma das Wort im Alltag verwenden?**

**Sexuelles, Derbes, Abwertendes.** IMPOTENT, ERGUSS, WEIBER, EMANZE, SAEUE,
KONKUBINE war kurz gesperrt und wurde freigegeben, SUFF, TRINKER, MOBBING, SLIP.

**NS-Bezug.** GHETTO, ARISCH, HITLERJUGEND, NEONAZI.

**Russlandbezug ist nicht gesperrt**, bekommt aber **ausnahmslos eine
sarkastische Frage als einzige Fassung** (README 5a). STAATSDUMA und NEWA wurden
trotzdem gesperrt, weil sie für die Empfängerin unlösbar sind — die sarkastische
Frage rettet kein unbekanntes Wort.

**Fehler in den eigenen Handlisten.** TOEL (verrutschtes TORJUBEL), GERoeLL
(Umlaut nicht umgesetzt), CEROBAN, SAGALEY, FREIE (aus „Freie Bergstadt", die
Facettendatei trennt an Leerzeichen!), MONTEKALI, ABHYANGA, RASULBAD. Korrektur
gehört in die Facettendatei **und** per `theme_drop.py` ins Thema, sonst kommt
es beim nächsten Buch wieder.

### Freigegebene Einzelfälle

Damit sie nicht erneut gesperrt werden: ABDECKER, ARSENAL, GUERILLA, REKRUT,
GENERAL, STUNTMAN, ATZE, EBOLA, KATHETER, SKALPELL, GRAEUELTAT, KONKUBINE,
NOTDURFT, ZERSTOERT, BELEUMUNDET, ERRUNGEN, PEAK, FREAK, POTENZ (Frage „Kraft
und Wirkung", nichts Sexuelles), SOLD, LETAL, HAREM, VAMPIR, TENNE, EILE, EINS.

---

## 5. Fragen: der Ton dieses Buchs

Es gelten die allgemeinen Regeln aus README 6. Für dieses Buch zusätzlich:

* **Themenwörter thematisch erfragen, auch Kolorit.** Bekommt ein Themenwort
  eine neutrale Frage, ist es im Buch kein Themenwort mehr.
* **Die Bindung darf nichts Falsches behaupten.** PARK als „Grünanlage in
  Salzgitter" war falsch, ein Park ist überall ein Park. SEEBAD als „Badeort am
  Schwarzen Meer" ebenso.
* **Kein Synonym als Frage.** DUSCHRAUM als „Waschraum", UNHEILVOLL als
  „verhängnisvoll" — beides verworfen.
* **Fachbedeutungen brauchen einen Fingerzeig aufs Feld**, ohne den Themennamen
  abzudrucken: LORE „Wagen im Stollen". Ist die Fachbedeutung selbst unbekannt,
  gehört das Wort per `theme_drop.py` aus dem Thema — so geschehen bei STOSS.
* **Sachliche Genauigkeit vor schöner Formulierung.** LUEGE als „Unwahrheit vor
  Gericht" war falsch; vor Gericht ist die Lüge eine Falschaussage.

`clues.json` stammt aus dem Vorgängerbuch und enthält **Altlasten**: Fassungen,
die an Themen jenes Buchs gebunden sind (BRAUNSCHWEIG, BUECHER, KATYPERRY,
ERNAEHRUNG, HARRYPOTTER, SELBSTENTWICKLUNG, BERGSTEIGEN). Beim Fragenschreiben
prüfen und umhängen — bisher betroffen waren PARK, ORGEL, ECKE, HARZ, KAMM,
OPFER, STEG, KREUZ, TITEL, KEULE, RUHE, TIPP, STIL, GERSTE, BIRNE, KERZE,
UKRAINE („Land am Dnipro" — verbotene Transliteration!), KIWI, LUKE („Decköfnung"
mit Tippfehler).

Ebenso prüfen: Steht dieselbe Frage schon bei einem **anderen** Wort? Der
Renderer meldet nur Mehrfachverwendung desselben Worts. NAHE und SIEG trugen
beide „Nebenfluss des Rheins", TRAINER hätte dieselbe Frage bekommen wie COACH.

---

## 6. Ablauf je Seite

1. `python book.py NN NN` — rund zehn Minuten.
2. **Wortliste vollständig prüfen**, mit Thema, Stufe und vorhandener Frage.
   Jedes Wort einzeln gegen den Maßstab aus Abschnitt 1.
3. Auffälliges: `blacklist_add.py`, dann `ersetze_wort.py` Stufe 1, 2, 3
   (README 4b). **Vor einem Neubau den Projektleiter fragen** — er hat mehr als
   ein Dutzend meiner Sperrungen wieder aufgehoben, und `rollback.py` löscht die
   Seite endgültig.
4. Nach Stufe 2 oder 3 die **getauschten Ersatzwörter erneut prüfen**.
5. Fragen schreiben mit `fitcheck.py --eintragen`, Themenbindungen setzen.
6. `collect_clues.py` — meldet fehlende Fragen.
7. `render_book.py OUT` und `render_book.py OUT --nur-loesungen`. Meldet
   Mehrfachverwendungen ohne Zweitfassung, fehlende Klammerzusätze und
   Wortstammtreffer. Alles abarbeiten, bis nichts mehr kommt.
8. Formfehler der Automatik nach `formen.txt`: Bisher nötig für BOXER, RUNE,
   ALTER, STAENDER, EBENE, TIERART, ASTER, TAETER, ENGE, PFEILER, DRUECKER,
   IRAKER, KEILER, SCHALE, WESTEN, FARMER, STIFTER, TIBETER, OSTEN, RAEUBER.

**Berichten** an den Projektleiter: Themenanteil, Kern, **Rätselwortschatz**
(nicht die seltenen Wörter — das war ausdrücklich gewünscht), dazu nur die
Probleme, nicht jede geschriebene Frage.

---

## 7. Zahlen zum Stand

29 Seiten: 1.292 Einträge, 795 Themenwörter (62 %), 594 Kernbegriffe (46 %),
171 aus dem Rätselwortschatz. Konto 1.221 verschiedene Wörter.

Themenanteil je Seite zwischen 45 und 81 Prozent. Die Ausreißer nach unten haben
fast immer ein langes Vorgabewort (README 3c).

Erwartbar für die letzten Seiten: Der Themenwortschatz reicht bis 50 (Reichweite
0,20 Einsätze je Kernwort), aber die Wiederholungsdämpfung wird enger. Wörter,
die zweimal im Buch stehen, brauchen zwei Fragefassungen; bisher sind es rund
60 von 1.221.

---

## 8. Umgebung

`pip install reportlab pyphen --break-system-packages` ist nötig, wenn der
Container neu aufgesetzt wurde.

Hintergrundläufe überleben einen Neustart der Umgebung nicht. Nach jedem
abgebrochenen Lauf das Konto gegen die Rasterdateien prüfen (README 4d). Blöcke
von mehr als zwei Seiten sind unzuverlässig; einzelne Aufrufe sind sicherer.

Nie `book.py` und `ersetze_wort.py` gleichzeitig laufen lassen — beide schreiben
`used_words.json`.

`sicherung/` enthält eine Kopie von Seite 25 samt Konto und Fragen.
