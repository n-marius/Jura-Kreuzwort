# Stand nach dem Buch "Oma, Band 1" (Seiten 1-50 fertig, Druckdaten erzeugt)

Dieses Blatt ergaenzt README.md und BUCH_OMA.md. Es haelt fest, was in der
letzten Sitzung am Paket geaendert wurde, welche Regeln der Projektleiter
praezisiert hat und was beim naechsten Buch zu beachten ist.

## 1. Aenderungen am Code

### bookpdf.py - Druckformat
Frueher A5 (148 x 210 mm) ohne Beschnitt. Jetzt auf das Datenblatt der
Druckerei (WIRmachenDRUCK, Buch mit Softcover) umgestellt:

    TRIM_W, TRIM_H = 148 mm x 210 mm   Endformat
    BLEED          = 3 mm              Beschnitt ringsum -> Seite 154 x 216 mm
    BUND           = 2 mm              Versatz aus dem Falz

`_seitenanfang(c, seite)` legt den Nullpunkt jeder Seite auf die Ecke des
Endformats und verschiebt ungerade Seiten um BUND nach rechts, gerade nach
links. Jede Seite endet mit `c.restoreState()`. Alle Layoutmasse rechnen
weiterhin gegen das Endformat, nicht gegen das Datenformat.

Randmasse, die sich daraus ergeben: aussen 10 mm, innen 6 mm, oben und unten
11,5 mm. Der Sicherheitsabstand von 5 mm ist damit ueberall eingehalten. Die
Seitenzahl steht 6 mm ueber der Schnittkante (frueher 4,5 mm, das lag unter
dem Sicherheitsabstand).

### bookpdf.py - Pruefdruck
`--nur-loesungen` erzeugt nicht mehr die 3x3-Miniraster, sondern dieselben
Seiten in voller Groesse samt Fragen, zusaetzlich die Loesungsbuchstaben in
den Zellen (`draw(..., letters=grid, solution=True)`). Das Raetselbuch selbst
ist unveraendert und enthaelt die Miniraster als Loesungsteil.

### render_book.py - Seitenreihenfolge
Vor `build()` wird die Liste umsortiert:

    VORNE = [14, 20, 4, 2]

Das sind die Nummern der Rasterdateien, nicht die Buchseiten. Regel war:
vorne die Seite mit den meisten Salzgitter-Woertern, dann die Seiten mit den
Wunschwoertern. Anschliessend wird durchnummeriert, die gedruckte Seitenzahl
ist die neue Position, und die Loesungsseiten verweisen auf dieselbe Zaehlung.
**Fuer ein neues Buch ist VORNE anzupassen oder auf `[]` zu setzen.**

Achtung: Die Reihenfolge beeinflusst, welche Fragefassung ein mehrfach
verwendetes Wort bekommt (`seen`-Zaehler in render_book.py). Nach einer
Umsortierung immer neu rendern und die Meldung "GLEICHE FRAGE MEHRFACH"
beachten.

### stufe1_batch.py (neu)
Prueft Stufe 1 fuer viele Woerter auf einmal, laedt das Lexikon nur einmal.
Aufruf: `python stufe1_batch.py 12:WORT 31:ANDERES ...`. Macht genau das,
was `ersetze_wort.py` in Stufe 1 tut (Kreuzungsmuster, `lex.match` minus
belegte Woerter), und spart bei grossen Listen viel Zeit. Ersetzt nichts,
zeigt nur Kandidaten.

## 2. Praezisierte Regeln des Projektleiters

### Sperrlisten sauber trennen
- `blacklist.txt` - gilt nur fuer dieses Buch. Woerter, die hier nicht
  passen: zu schwer, unpassendes Register, Anglizismen, Fachjargon.
- `stopwords.txt` - gilt dauerhaft. Nur generell unzulaessige Formen:
  flektierte Adjektive, Superlative, Partizipien, Fehlbildungen, falsche
  Schreibungen, Vulgaeres.

Beispiel aus dieser Sitzung: AZETAT (falsche Schreibung) nach stopwords,
ACETAT (korrekt, aber zu fachlich) nach blacklist. NACHGEBURT und SAUBLOED
gehoeren in die blacklist, nicht in die stopwords - sie sind keine Formfehler.

### Vier Stufen vor dem Neubau
1. nur der Slot, 2. Slot und direkte Nachbarn, 3. zweite Kreuzungsebene,
4. **die KI sucht selbst** ein passendes Wort, ohne Lexikon.
Erst danach Rollback und Neubau, und immer erst nach Ruecksprache.

Zu Stufe 4: `ersetze_wort.py` prueft `--nimm` gegen `lex.match(muster)`
(Zeile 198) und lehnt alles ab, was nicht im Lexikon steht. Ein selbst
gefundenes Wort muss also vorher in eine Wortquelle aufgenommen werden -
der Projektleiter entscheidet, dann kommt es rein.

Bei drei oder mehr Beanstandungen auf einer Seite gleich neu bauen, statt
einzeln zu tauschen.

### Russland- und Belarusbezug
Gilt fuer beide Laender gleich. Die Frage bekommt einen geografischen oder
sachlichen Anker, damit sie loesbar bleibt, und daneben die Spitze - nicht
ein blosses "des Aggressors" anstelle der Erklaerung. Aktueller Stand:

    URAL   Gebirge im Zarenreich
    UDSSR  Sowjetreich (Abk.)
    MINSK  Hauptstadt Belarus

### Fragen
- Drei Punkte in einer Frage bedeuten immer eine Ergaenzungsluecke:
  "LED; Leucht..." oder "...-Vitamin-Saft" oder "Im ... nehmen".
- Wird ein Wort getauscht, die alte Fassung aus `clues.json` loeschen,
  nicht danebenstehen lassen.
- Fremdsprachige Woerter brauchen den Vermerk: (engl.), (franz.), (lat.).
- Fragen erst schreiben, wenn die Woerter einer Seite endgueltig feststehen.

### Grenzfaelle vorlegen statt sperren
Der Projektleiter hat in dieser Sitzung rund ein Drittel der vorgeschlagenen
Sperrungen wieder aufgehoben, darunter DIABETES, ZOMBIE, GAMEBOY, WINDOWS,
SIFF, FUEHRER (als Reisefuehrer), SCANDIUM, ISOTOP, MESNER und OKAPI.
Massstab ist nicht, ob ein Wort mir gefaellt, sondern ob es ein typisches
Raetselwort ist oder die Empfaengerin es kennt. Im Zweifel vorlegen.

Ebenfalls entschieden: ESSEN und ESSIG duerfen gemeinsam auf einer Seite
stehen, ERDE darf viermal im Buch vorkommen.

## 3. Bekannte Schwaechen der Werkzeuge

- `ersetze_wort.py` prueft `WORT_MAX` nicht. So kam ERDE auf vier Einsaetze.
- Der Zeitdeckel in `stufe2` (Zeile 99) greift nur zwischen den Runden. Die
  Rekursion in `solve()` hat kein Knotenbudget, anders als der Fueller in
  `book.py`. Ein Lauf kann deshalb unbegrenzt weiterlaufen; deswegen immer
  mit `timeout` aufrufen.
- `wordcheck.stamm_kollision` erkennt weder Umlautplurale (NUSS/NUESSE,
  SATTEL/SAETTEL) noch Ableitungen auf -ER (ESSEN/ESSENER). Der Ersetzer
  prueft die Kollision offenbar gar nicht.
- `collect_clues.py` prueft nicht, ob die einzige Fassung eines Wortes an ein
  buchfremdes Thema gebunden ist. Solche Faelle (STAB, SAAL, SZENE, KOHL)
  faellt sonst erst `render_book.py` auf, das dann das Loesungswort selbst in
  die Zelle setzt. Vor dem Rendern lohnt ein Durchlauf ueber `clues.json`
  gegen die Themen des Buches.

## 4. Ein neues Buch beginnen

1. `puzzles/` leeren, `used_words.json` auf `{}` setzen.
2. `blacklist.txt` leeren oder auf die Faelle kuerzen, die auch im neuen Buch
   gelten sollen. `stopwords.txt` bleibt.
3. `plan.json` mit den neuen Vorgabewoertern schreiben.
4. Themen und Facetten auf den neuen Empfaenger anpassen, `themes.json` neu
   bauen.
5. `VORNE` in `render_book.py` anpassen oder leeren.
6. `clues.json` bleibt und ist der eigentliche Wert des Pakets - rund 2000
   gepruefte Fragen. Fassungen, die an Themen des alten Buches gebunden sind,
   werden im neuen Buch automatisch uebergangen; jedes Wort sollte deshalb
   mindestens eine neutrale Fassung haben.

## 5. Druckdaten

Zwei getrennte Dateien, nicht eine zusammengesetzte - die Formate sind
verschieden:

    Schwedenraetsel_Inhalt.pdf     56 Seiten, 154 x 216 mm
    Schwedenraetsel_Umschlag.pdf    2 Seiten, 305 x 216 mm (302 + 3 mm Bund)

Seite 1 des Umschlags ist die Aussenseite U4 - Ruecken - U1, Seite 2 sind die
leeren Innenseiten U2 und U3. Die Ruckenstaerke von 3 mm gilt fuer 56
Innenseiten; bei anderer Seitenzahl ist die Umschlagbreite nachzuziehen.

Beide Dateien sind in RGB angelegt, die Druckerei konvertiert nach CMYK.
