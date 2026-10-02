"""Baut ein Thema in einem Rutsch aus seiner Facettendatei auf.

  python theme_build.py facetten_JURA.txt

Vier Stufen, in dieser Reihenfolge:

  1 Handliste   theme_facets.py   die kuratierten Facetten, Naehe wie angegeben
  2 Subsuche    theme_subscan.py  jedes Facettenwort als Saat im Wortschatz
  3 Expander    theme_expand.py   Zusammensetzungen um die Kernbegriffe
  4 Kolorit     theme_flex.py     Beugungen und Ableitungen

Stufe 1 ist die einzige, die Modellaufwand kostet, und die einzige, die
wirklich neues Vokabular in das System bringt. Die Stufen 2 bis 4 sind reine
Rechenarbeit auf dem vorhandenen Wortschatz. Deshalb gilt: an Stufe 1 nicht
sparen, die Facettendatei ist die eigentliche Arbeit.

Danach lohnt eine einmalige Sichtpruefung der kurzen Woerter:
  python theme_review.py JURA 4 6
  python theme_drop.py JURA RECHTECK GERECHT
"""
import subprocess, sys, os, re

HERE = os.path.dirname(os.path.abspath(__file__))


def lauf(*args):
    print("$ python3", " ".join(args))
    r = subprocess.run([sys.executable] + list(args), cwd=HERE,
                       capture_output=True, text=True)
    out = (r.stdout or "").strip().splitlines()
    for zeile in out[:4]:                      # Kurzfassung, spart Ausgabe
        print("   ", zeile)
    if r.returncode:
        print("   FEHLER:", (r.stderr or "").strip()[-400:])
        sys.exit(1)


def main():
    pfad = sys.argv[1]
    kopf = open(os.path.join(HERE, pfad), encoding="utf-8").readline()
    m = re.match(r"#\s*THEMA\s+(\S+)", kopf, re.I)
    if not m:
        sys.exit("Erste Zeile muss '# THEMA NAME GEWICHT n' sein")
    name = m.group(1).upper()
    lauf("theme_facets.py", pfad)
    lauf("theme_subscan.py", pfad, "--add")
    lauf("theme_expand.py", name, "--naehe", "0.4")
    lauf("theme_flex.py", name, "--add")
    lauf("theme_stats.py")


if __name__ == "__main__":
    main()
