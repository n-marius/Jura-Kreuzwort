#!/usr/bin/env python3
"""Setzt das Paket auf den Anfangszustand fuer ein neues Buch zurueck.

Das Paket traegt zweierlei mit sich: dauerhaftes Wissen, das mit jedem Buch
wertvoller wird, und den Zustand genau eines Buchs. Nur das Zweite wird
zurueckgesetzt.

WIRD GELOESCHT (Zustand eines Buchs)
  themes.json          Themenwortschatz - gehoert zu diesen Themen
  used_words.json      Einsatzkonto - zaehlt Wiederholungen in diesem Buch
  plan.json            Verteilung der Wunschwoerter auf die Seiten
  wunschwoerter.txt    Wunschwoerter dieses Buchs
  puzzles/*.pkl        die fertigen Raster
  facetten_*.txt       Handlisten (facetten_VORLAGE.txt bleibt)
  blacklist.txt        Sperrungen gelten je Buch, nicht dauerhaft
  raetselbuch.pdf      Ausgabe

BLEIBT (dauerhaftes Wissen, buchuebergreifend)
  clues.json           Fragen-Cache. Das ist das Wertvollste im Paket - jede
                       Frage, die einmal geschrieben wurde, spart beim
                       naechsten Buch Arbeit. Niemals loeschen.
  stopwords.txt        dauerhafte Sperrliste
  formen.txt           Handkorrekturen der Formerkennung
  freigabe.txt         nachtraeglich zugelassene Woerter
  keinpartizip.txt     Substantive im Partizipmuster
  kennzeichen.txt      Antworten mit Pflichtzusatz (engl./Abk.)
  words_v3.json        Grundwortschatz
  fallback_v3.json     Rueckfallwortschatz
  selten_v3.json       dritte Wortschatzstufe
  raetselwoerter.txt   klassischer Raetselwortschatz
  themen/              archivierte Handlisten. Sie sind die eigentliche
                       Arbeit an einem Thema und ueberleben das Buch -
                       siehe README 2a-1.
  alle .py-Dateien, fonts/

Aufruf:
  python neues_buch.py                 zeigt nur, was passieren wuerde
  python neues_buch.py --ja            fuehrt es aus
  python neues_buch.py --ja --archiv harry_potter
                                        legt vorher eine Kopie unter
                                        archiv/harry_potter/ ab

Nach dem Zuruecksetzen: GESAMT_RAETSEL in core.py auf den neuen Umfang
setzen, dann weiter bei Abschnitt 2 der README (Themen einrichten).
"""
import glob
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

LEEREN = {"themes.json": "{}", "used_words.json": "{}", "blacklist.txt": ""}
LOESCHEN = ["plan.json", "wunschwoerter.txt", "altwoerter.txt",
            "raetselbuch.pdf",
            "loesungsprobe.pdf"]
MUSTER = ["puzzles/*.pkl", "facetten_*.txt"]
BEHALTEN = {"facetten_VORLAGE.txt"}


def sammeln():
    """Alle betroffenen Pfade ermitteln, relativ zum Paketverzeichnis."""
    treffer = []
    for name in list(LEEREN) + LOESCHEN:
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            treffer.append(name)
    for m in MUSTER:
        for p in sorted(glob.glob(os.path.join(HERE, m))):
            if os.sep + "themen" + os.sep in p:
                continue                      # Archiv bleibt unangetastet
            name = os.path.relpath(p, HERE)
            if os.path.basename(name) not in BEHALTEN:
                treffer.append(name)
    return treffer


def main():
    ernst = "--ja" in sys.argv
    archiv = None
    if "--archiv" in sys.argv:
        i = sys.argv.index("--archiv")
        if i + 1 < len(sys.argv):
            archiv = sys.argv[i + 1]

    treffer = sammeln()
    if not treffer:
        print("Nichts zurueckzusetzen - das Paket ist bereits themenneutral.")
        return

    print(f"{len(treffer)} Datei(en) betroffen:")
    for name in treffer:
        art = "leeren" if name in LEEREN else "loeschen"
        print(f"  {art:9s} {name}")

    if not ernst:
        print("\nProbelauf. Mit --ja ausfuehren, bei Bedarf zusaetzlich")
        print("--archiv NAME, um vorher eine Kopie unter archiv/NAME/ abzulegen.")
        return

    if archiv:
        ziel = os.path.join(HERE, "archiv", archiv)
        os.makedirs(ziel, exist_ok=True)
        for name in treffer:
            q = os.path.join(HERE, name)
            z = os.path.join(ziel, name)
            os.makedirs(os.path.dirname(z), exist_ok=True)
            shutil.copy2(q, z)
        print(f"\nKopie abgelegt unter archiv/{archiv}/")

    # Handlisten ins Archiv retten, bevor sie geloescht werden.
    zarchiv = os.path.join(HERE, "themen")
    os.makedirs(zarchiv, exist_ok=True)
    gesichert = 0
    for name in treffer:
        if name.startswith("facetten_"):
            ziel = os.path.join(zarchiv, os.path.basename(name))
            if not os.path.exists(ziel):
                shutil.copy2(os.path.join(HERE, name), ziel)
                gesichert += 1
    if gesichert:
        print(f"\n{gesichert} Handliste(n) nach themen/ gesichert.")

    for name in treffer:
        p = os.path.join(HERE, name)
        if name in LEEREN:
            open(p, "w", encoding="utf-8").write(LEEREN[name] + "\n")
        else:
            os.remove(p)

    # clues.json nicht anfassen, aber zeigen, wie gross der Bestand ist -
    # das ist der Gewinn, den das neue Buch mitbekommt.
    cp = os.path.join(HERE, "clues.json")
    if os.path.exists(cp):
        c = json.load(open(cp, encoding="utf-8"))
        fassungen = sum(len(v) for v in c.values())
        print(f"\nclues.json bleibt: {len(c)} Woerter, {fassungen} Fassungen.")
    print("Zurueckgesetzt. Naechster Schritt: GESAMT_RAETSEL in core.py setzen,")
    print("dann Abschnitt 2 der README (Themen einrichten).")


if __name__ == "__main__":
    main()
