"""Traegt die Fragen aus raetselwoerter.txt in clues.json ein.

  python import_raetselwoerter.py            (nur pruefen)
  python import_raetselwoerter.py --schreiben (eintragen)

Die Woerter selbst kommen ueber core.load_raetselwoerter in den Wortschatz;
dieses Skript kuemmert sich nur um die Fragen. Der Zeilenumbruch wird mit
fitcheck.umbrechen gesetzt, also gemessen und mit sauberer Silbentrennung.
Vorhandene Fragen in clues.json bleiben erhalten - die neue Frage wird nur
angehaengt, wenn das Wort noch keine hat.
"""
import sys, json, os
from fitcheck import passt, umbrechen
from themes import _n
from wordcheck import lade_sperrliste

HERE = os.path.dirname(os.path.abspath(__file__))


def lies(pfad=None):
    """-> {WORT: Frage}  (Frage noch ohne Umbruch)"""
    pfad = pfad or os.path.join(HERE, "raetselwoerter.txt")
    out = {}
    for zeile in open(pfad, encoding="utf-8"):
        z = zeile.strip()
        if not z or z.startswith("#") or "|" not in z:
            continue
        w, f = z.split("|", 1)
        out[_n(w.strip())] = f.strip().replace("\\n", " ")
    return out


def main():
    schreiben = "--schreiben" in sys.argv
    roh = lies()
    bad = (lade_sperrliste(os.path.join(HERE, "stopwords.txt"))
           | lade_sperrliste(os.path.join(HERE, "blacklist.txt")))
    clues = json.load(open(os.path.join(HERE, "clues.json"), encoding="utf-8"))
    neu, hatte, schlecht, gesperrt, stamm = 0, 0, [], [], []
    for w, f in roh.items():
        if w in bad:
            gesperrt.append(w)
            continue
        # Wortstamm der Loesung darf in der Frage nicht vorkommen
        st = w[:5] if len(w) > 5 else w[:3]
        if st in _n(f):
            stamm.append((w, f))
            continue
        u = umbrechen(f)
        if not passt(u):
            schlecht.append((w, f))
            continue
        if clues.get(w):
            hatte += 1
            continue
        clues[w] = [u]
        neu += 1
    print(f"{len(roh)} Eintraege | neu {neu} | Frage war schon da {hatte} "
          f"| gesperrt {len(gesperrt)} | passt nicht {len(schlecht)} "
          f"| Wortstamm verraten {len(stamm)}")
    for w, f in stamm:
        print("  WORTSTAMM:", w, "=", f)
    for w, f in schlecht:
        print("  PASST NICHT:", w, "=", f)
    if gesperrt:
        print("  GESPERRT, uebergangen:", " ".join(gesperrt))
    if schreiben:
        json.dump(clues, open(os.path.join(HERE, "clues.json"), "w",
                              encoding="utf-8"), ensure_ascii=False, indent=0)
        print("clues.json geschrieben, jetzt", len(clues), "Woerter")
    else:
        print("(nur Pruefung — mit --schreiben eintragen)")


if __name__ == "__main__":
    main()
