"""Erzeugt freie Kreuzwortraetsel fuer eine Spanne von Seiten.

Aufruf:  python kr_book.py 1 10              Seiten 1 bis 10
         python kr_book.py --rollback 5 7    Seiten 5 bis 7 entfernen
                                             (Dateien und Wortkonto)

Wortschatz: ausschliesslich kr_config.WORTLISTE (Facettenformat), kein Lexikon,
keine Sperrlisten. Vorgaben je Seite aus plan.json wie bisher
({"3": {"pflicht": [...]}}). Fertige Seiten werden uebersprungen.
SEED_VERSATZ=100 python kr_book.py 4 4 baut eine Seite mit anderem Zufall neu.
"""
import sys, os, json, time, pickle, glob, re
import multiprocessing as mp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "skanvord"))
sys.path.insert(0, os.path.join(HERE, "kreuz"))
sys.path.insert(0, HERE)
os.chdir(HERE)

import kr_config as K
from core import REUSE_THEMA, WORT_MAX, SPERRE_SEITEN, KURZ_DAEMPFUNG
from themes import _n
from platzierung import erzeuge

SEED_VERSATZ = int(os.environ.get("SEED_VERSATZ", "0"))


def pfad(i):
    return os.path.join(K.PUZZLE_DIR, f"{i:03d}.pkl")


def lade_konto():
    return json.load(open(K.LEDGER, encoding="utf-8")) if os.path.exists(K.LEDGER) else {}


def _schreibe(pfad_, text=None, daten=None):
    """Erst in eine Nebendatei, dann in einem Schritt ersetzen: ein Abbruch
    mitten im Schreiben laesst die alte Datei heil. Unter Windows kurz
    wiederholen, falls die Datei gerade gelesen wird."""
    tmp = pfad_ + ".tmp"
    if daten is not None:
        with open(tmp, "wb") as f:
            f.write(daten)
    else:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
    for _ in range(100):
        try:
            os.replace(tmp, pfad_)
            return
        except PermissionError:
            time.sleep(0.05)
    os.replace(tmp, pfad_)


def speichere_konto(led):
    _schreibe(K.LEDGER, json.dumps(led, ensure_ascii=False, indent=0, sort_keys=True))


def lese_wortliste(pfad=None):
    """Facettendatei lesen. Rueckgabe (nah, abk): Wort -> Naehe, Menge der
    Abkuerzungen (Facettenname beginnt mit "Abk"). Latein siehe lese_latein(). Keine Lexikon- oder
    Sperrlisten-Abhaengigkeit: die Liste ist der gesamte Wortschatz."""
    nah, abk, naehe, facette = {}, set(), 0.85, ""
    for zeile in open(os.path.join(HERE, pfad or K.WORTLISTE), encoding="utf-8"):
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#"):
            continue
        m = re.match(r"\[(.+?)\]\s*([\d.]+)?", zeile)
        if m:
            facette, naehe = m.group(1), float(m.group(2) or 0.85)
            continue
        for w in zeile.split():
            w = re.sub(r"[^A-Z]", "", _n(w))
            if K.MIN_LEN <= len(w) <= K.MAX_LEN and naehe >= K.MIN_NAH:
                nah[w] = max(nah.get(w, 0), naehe)
                if facette.startswith("Abk"):
                    abk.add(w)
    return nah, abk


def lese_latein(pfad=None):
    """Woerter aus Facetten, deren Name mit "Latein" beginnt."""
    lat, facette = set(), ""
    for zeile in open(os.path.join(HERE, pfad or K.WORTLISTE), encoding="utf-8"):
        zeile = zeile.strip()
        m = re.match(r"\[(.+?)\]", zeile)
        if m:
            facette = m.group(1)
        elif zeile and not zeile.startswith("#") and facette.startswith("Latein"):
            lat |= {re.sub(r"[^A-Z]", "", _n(w)) for w in zeile.split()}
    return lat


def wortschatz():
    return lese_wortliste()[0]


def gewichte(nah, led, gesperrt):
    out = {}
    for w, n in nah.items():
        k = led.get(w, 0)
        if k >= WORT_MAX or w in gesperrt:
            continue
        g = (0.3 + n) ** 2 * REUSE_THEMA.get(k, 0.0)
        if k and len(w) <= 6:
            g *= KURZ_DAEMPFUNG
        g *= K.KURZ_GEWICHT.get(len(w), 1.0)
        if g > 0:
            out[w] = g
    return out


def lade_wied():
    return json.load(open(K.WIED_DATEI, encoding="utf-8")) if os.path.exists(K.WIED_DATEI) else {}


def speichere_wied(d):
    _schreibe(K.WIED_DATEI, json.dumps(d, indent=0, sort_keys=True))


def _p(text):
    if K.FORTSCHRITT:
        print(f"    [{time.strftime('%H:%M:%S')}] {text}", flush=True)


def _arbeiter(args):
    """Ein Prozess baut seinen Anteil der Versuche (eigener Seed)."""
    woerter, gw, kw = args
    return erzeuge(woerter, gw, **kw)


def _parallel_erzeuge(pool, n_proz, woerter, gw, seed, versuche, kw):
    """Verteilt die Versuche auf n_proz Prozesse und nimmt das beste Ergebnis
    (hoechster Wert, bei Gleichstand der niedrigere Prozessindex)."""
    teile = [versuche // n_proz + (1 if i < versuche % n_proz else 0)
             for i in range(n_proz)]
    auftraege = [(woerter, gw, dict(kw, seed=seed * 7919 + i, versuche=t))
                 for i, t in enumerate(teile) if t > 0]
    if pool is None:
        ergebnisse = [_arbeiter(a) for a in auftraege]
    else:
        ergebnisse = pool.map(_arbeiter, auftraege)
    ergebnisse = [r for r in ergebnisse if r is not None]
    if not ergebnisse:
        return None
    return max(ergebnisse, key=lambda r: r[2]["wert"])


def rollback(a, b):
    led = lade_konto()
    wied = lade_wied()
    for i in range(a, b + 1):
        wied.pop(str(i), None)
    speichere_wied(wied)
    for i in range(a, b + 1):
        if os.path.exists(pfad(i)):
            lay, _ = pickle.load(open(pfad(i), "rb"))
            for e in lay.entries:
                led[e.word] = led.get(e.word, 0) - 1
                if led[e.word] <= 0:
                    del led[e.word]
            os.remove(pfad(i))
            print(f"{i:03d} entfernt")
    speichere_konto(led)


def main(a, b):
    os.makedirs(K.PUZZLE_DIR, exist_ok=True)
    nah = wortschatz()
    print(f"Wortschatz {K.WORTLISTE}: {len(nah)} Woerter", flush=True)
    plan = json.load(open("plan.json", encoding="utf-8")) if os.path.exists("plan.json") else {}
    led = lade_konto()
    wied = lade_wied()
    versuche = int(os.environ.get("VERSUCHE", K.VERSUCHE))
    n_proz = max(1, int(os.environ.get("PARALLEL", K.PARALLEL)))
    pool = None
    if n_proz > 1:
        _p(f"Starte {n_proz} Rechenprozesse ...")
        pool = mp.get_context("spawn").Pool(n_proz)
    gescheitert, neu_n, neu_w, neu_kurz = [], 0, 0, 0
    try:
        for i in range(a, b + 1):
            if os.path.exists(pfad(i)):
                print(f"{i:03d} liegt schon vor - uebersprungen", flush=True)
                continue
            gesperrt = set()
            for k in range(max(1, i - SPERRE_SEITEN), i):
                if os.path.exists(pfad(k)):
                    gesperrt |= {e.word for e in pickle.load(open(pfad(k), "rb"))[0].entries}
            eintrag = plan.get(str(i), [])
            vorgaben = list(eintrag.get("pflicht", [])) if isinstance(eintrag, dict) else list(eintrag)
            gw = gewichte(nah, led, gesperrt)
            for v in vorgaben:
                gw.setdefault(v, 1.0)
            # Buchschnitt der Wiederholungen: liegt er ueber dem Ziel, darf diese
            # Seite hoechstens das Ziel erreichen, sonst bis WIED_MAX.
            ges_n = sum(v[0] for v in wied.values())
            ges_w = sum(v[1] for v in wied.values())
            grenze = K.WIED_ZIEL if ges_n and ges_w / ges_n > K.WIED_ZIEL else K.WIED_MAX
            kw = dict(H=K.RASTER_H, W=K.RASTER_W, stichprobe=K.STICHPROBE,
                      max_woerter=K.MAX_WOERTER, min_woerter=K.MIN_WOERTER,
                      kreuz_min=K.KREUZ_MIN, fuell_min=K.FUELL_MIN,
                      bonus_kreuz=K.BONUS_KREUZ, vorgaben=vorgaben,
                      bekannt=frozenset(w for w, n in led.items() if n > 0),
                      wied_ziel=K.WIED_ZIEL, wied_max=grenze,
                      wied_strafe=K.WIED_STRAFE, kurz_strafe=K.KURZ_STRAFE)
            t0 = time.time()
            res = None
            for anlauf in range(K.ANLAEUFE):
                _p(f"{i:03d} Start, Anlauf {anlauf + 1}/{K.ANLAEUFE}, {versuche} Versuche auf "
                   f"{n_proz} Prozessen")
                res = _parallel_erzeuge(pool, n_proz, list(gw), gw,
                                        i * 1009 + SEED_VERSATZ + 100 * anlauf,
                                        versuche, kw)
                if res is not None:
                    break
                _p(f"{i:03d} Anlauf {anlauf + 1} ohne brauchbares Raster")
            if res is None:
                gescheitert.append(i)
                print(f"{i:03d} FEHLGESCHLAGEN nach {K.ANLAEUFE} Anlaeufen ({time.time() - t0:.0f}s) - "
                      f"Lauf wird beendet. Die folgenden Seiten bauen auf dieser auf.", flush=True)
                break
            lay, grid, info = res
            _schreibe(pfad(i), daten=pickle.dumps((lay, grid)))
            n_wied = sum(1 for e in lay.entries if led.get(e.word, 0) > 0)
            for e in lay.entries:
                led[e.word] = led.get(e.word, 0) + 1
            speichere_konto(led)
            wied[str(i)] = [len(lay.entries), n_wied]
            speichere_wied(wied)
            neu_n += len(lay.entries)
            neu_w += n_wied
            ges_n = sum(v[0] for v in wied.values())
            ges_w = sum(v[1] for v in wied.values())
            print(f"{i:03d} FERTIG n={info['woerter']} zellen={info['zellen']} "
                  f"kreuz={info['kreuzrate']} fuell={info['fuellung']} "
                  f"wied={n_wied} ({100 * n_wied // max(1, info['woerter'])} %, "
                  f"Buch {100 * ges_w / ges_n:.1f} %) verworfen={info['verworfen']} "
                  f"{time.time() - t0:.0f}s [{time.strftime('%H:%M:%S')}]", flush=True)
    finally:
        if pool is not None:
            pool.terminate()
            pool.join()
    if neu_n:
        print(f"Neue Seiten zusammen: {neu_n} Woerter | Wiederholung {neu_w} "
              f"({100 * neu_w // neu_n} %)", flush=True)
    if gescheitert:
        print("gescheitert:", gescheitert)
    return 1 if gescheitert else 0


if __name__ == "__main__":
    if sys.argv[1] == "--rollback":
        rollback(int(sys.argv[2]), int(sys.argv[3]))
    else:
        raise SystemExit(main(int(sys.argv[1]), int(sys.argv[2])))
