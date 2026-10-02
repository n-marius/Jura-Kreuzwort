"""Kernfunktionen der Buchproduktion.

Zentrale Neuerungen gegenueber der Einzelraetsel-Fassung:
  * Wiederholungsdaempfung ueber ein buchweites Nutzungskonto (used_words.json)
  * Mindestantwortlaenge 4 (kurze Fuellwoerter sind die Hauptquelle von Wiederholungen)
  * Themengewichte deutlich angehoben
"""
import json, os, pickle, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "skanvord"))
sys.path.insert(0, HERE)

import layout as _layout
from layout import generate
from fill import Lexicon, fill
from themes import theme_map, _n, stufe
from wordcheck import lade_sperrliste

DATA = HERE
GRID_H, GRID_W = 17, 12
CELL_MM, CAP_MM, LINES_MAX = 11.0, 2.0, 4
DENSITY = 0.28
MIN_LEN = 4
FORMEN = {}          # Wort -> "PL" | "KOMP"


def load_form_overrides(path=None):
    """Handkorrekturen der Formerkennung aus formen.txt.

    Format je Zeile:  WORT PL | WORT KOMP | WORT SG
    SG loescht eine falsche Markierung (KOHLE ist kein Plural von KOHL,
    MASSE keiner von MASS). PL traegt eine fehlende nach (NAEGEL, LAEDEN).
    """
    path = path or os.path.join(DATA, "formen.txt")
    out = {}
    if not os.path.exists(path):
        return out
    for zeile in open(path, encoding="utf-8"):
        z = zeile.strip()
        if not z or z.startswith("#"):
            continue
        p = z.split()
        if len(p) >= 2 and p[1].upper() in ("PL", "KOMP", "SG"):
            out[_n(p[0])] = p[1].upper()
    return out


def load_freigabe(path=None):
    """Woerter, die zur Laufzeit in den Grundwortschatz zurueckgeholt werden.

    Format je Zeile:  WORT [rang].  Sperrlisten haben Vorrang.
    """
    path = path or os.path.join(DATA, "freigabe.txt")
    out = {}
    if not os.path.exists(path):
        return out
    for zeile in open(path, encoding="utf-8"):
        z = zeile.strip()
        if not z or z.startswith("#"):
            continue
        p = z.split()
        w = _n(p[0])
        if len(w) >= MIN_LEN:
            out[w] = int(p[1]) if len(p) > 1 and p[1].isdigit() else 15000
    return out


def load_raetselwoerter(path=None):
    """Klassischer Raetselwortschatz aus raetselwoerter.txt.

    Woerter, die jeder Loeser kennt, die im Alltag aber selten vorkommen -
    SMUTJE, ASBEST, KAVALLERIE. Ohne sie besteht ein Buch nur aus den
    haeufigsten Alltagswoertern und wirkt zu leicht. Sie werden dem
    Grundwortschatz zugeschlagen und in set_weights eigenstaendig gewichtet.
    Rueckgabe: Menge der Woerter (die Fragen stehen in clues.json).
    """
    path = path or os.path.join(DATA, "raetselwoerter.txt")
    out = set()
    if not os.path.exists(path):
        return out
    for zeile in open(path, encoding="utf-8"):
        z = zeile.strip()
        if not z or z.startswith("#") or "|" not in z:
            continue
        w = _n(z.split("|", 1)[0].strip())
        if MIN_LEN <= len(w) <= 17:
            out.add(w)
    return out


def load_formen():
    out = {}
    for f in ("words_v3.json", "fallback_v3.json"):
        for d in json.load(open(os.path.join(DATA, f), encoding="utf-8")):
            if d.get("form"):
                out[d["w"]] = d["form"]
    for w, v in load_form_overrides().items():
        if v == "SG":
            out.pop(w, None)
        else:
            out[w] = v
    return out

# Wie stark ein bereits verwendetes Wort abgewertet wird.
# 0 Verwendungen -> Faktor 1,0 | 1 -> 0,10 | 2 -> 0,02 | ab 3 -> praktisch aus.
# Fuellwoerter sollen sich im ganzen Buch moeglichst nicht wiederholen.
REUSE_FILL = {0: 1.0, 1: 0.12, 2: 0.03}

# Themenwoerter: Wiederholung ist unerwuenscht, aber nicht verboten. Anders als
# beim Fuellwortschatz ist der Vorrat je Thema begrenzt, deshalb faellt die
# Kurve nicht ganz so steil. Zwei harte Regeln kommen dazu:
#
#   THEMA_MAX          hoechstens so oft im ganzen Buch (Gewicht 0 darueber)
#   Sperre der Vorseite  nie in zwei aufeinanderfolgenden Raetseln
#
# Beides greift in set_weights. Die Obergrenze ist wichtiger, je laenger das
# Buch wird: ohne sie waechst die Zahl der Mehrfachverwendungen mit dem Umfang.
REUSE_THEMA = {0: 1.0, 1: 0.12, 2: 0.03}
WORT_MAX = 3               # Hoechstzahl der Einsaetze - fuer JEDES Wort
THEMA_MAX = WORT_MAX       # alter Name, gleiche Bedeutung
KURZ_DAEMPFUNG = 0.50      # zusaetzlicher Faktor fuer JEDES Wort mit 4-6
#                            Buchstaben ab dem zweiten Einsatz. Kurze Woerter
#                            passen in fast jedes Muster und wiederholen sich
#                            deshalb am haeufigsten; fuer sie gibt es aber auch
#                            am ehesten Ersatz.
# Ein Themenwort von Seite N ist auf den naechsten SPERRE_SEITEN Seiten
# gesperrt: Einsatz auf S1 heisst gesperrt auf S2 und S3, ab S4 wieder frei.
# Das Fenster haengt nicht am Buchumfang.
SPERRE_SEITEN = 2

GESAMT_RAETSEL = 50        # Umfang des geplanten Buchs (nur fuer die Rationierung)
ZIEL_KERN = 20             # angestrebte Kernbegriffe je Raetsel
ZIEL_UMFELD = 8
REUSE_FLOOR = 0.002

# Klassischer Raetselwortschatz (raetselwoerter.txt): festes Grundgewicht,
# entspricht etwa einem Wort mit Haeufigkeitsrang 1400. Er soll regelmaessig
# vorkommen, aber das Raetsel nicht beherrschen - bei 1.6 draengte er sich vor
# die Themenwoerter.
RAETSEL_BASE = 1.3

# Dritte Wortschatzstufe (selten_v3.json). Deutlich unter dem schwaechsten
# Rueckfallgewicht (0.012): diese Woerter sollen nur greifen, wenn ein Slot
# sonst leer bliebe.
SELTEN_BASE = 0.006

# Die allerhaeufigsten Woerter leicht bremsen. Sie sind grammatisch bequem und
# draengen sich sonst in jedes Raster; ihre Fragen sind zwangslaeufig banal.
HAEUFIG_GRENZE = 800
HAEUFIG_DAEMPFUNG = 0.75

# Gebeugte Formen sind zugelassen, aber nachrangig: sie verlangen eine Frage,
# die die Form mit ausdrueckt (Plural "(Mz.)", Komparativ als Steigerung).
FORM_FAKTOR = {"PL": 0.25, "KOMP": 0.35}


# Pegelfaktor der Themengewichte.
#
# Die Gewichte aus themes.json wirken nicht nur relativ zueinander, sondern
# auch absolut gegenueber dem Fuellwortschatz: dessen Gewichte (RAETSEL_BASE,
# 2.5/(1+Rang/1200), SELTEN_BASE) sind feste Zahlen und skalieren nicht mit.
# Im ersten Band lag das Grundgewicht je Themenwort dadurch bei 19,2 gegen
# 41,2 im Vorgaengerbuch, und der Themenanteil fiel von 61 auf 49 Prozent.
# Der Ausgleich war ein gemeinsamer Faktor von 2,15 auf alle Themengewichte.
#
# Er steht hier und nicht in themes.json, weil theme_build.py beim Neubau
# eines Themas das Gewicht aus der Kopfzeile der Facettendatei zurueck-
# schreibt: ein in themes.json eingetragener Faktor verschwindet dort beim
# naechsten Themenaufbau spurlos. Die Vorgabewerte des Projektleiters bleiben
# so ausserdem in Kopfzeile und themes.json unveraendert lesbar.
GEWICHT_FAKTOR = 2.15

# Wunschwoerter frueherer Baende (altwoerter.txt). Haeufigkeitsrang, mit dem
# sie in den Grundwortschatz eingehen, wenn die Zeile keinen eigenen nennt.
# 4000 entspricht einem Wort des mittleren Bereichs: regelmaessig ziehbar,
# aber ohne Vorrang vor dem uebrigen Fuellwortschatz.
ALT_RANG = 4000


def load_ledger(path=None):
    path = path or os.path.join(DATA, "used_words.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {}


def save_ledger(led, path=None):
    path = path or os.path.join(DATA, "used_words.json")
    # Erst in eine Nebendatei schreiben, dann in einem Schritt ersetzen. Wird
    # der Lauf mitten im Schreiben abgebrochen, bleibt das alte Konto heil.
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(led, f, ensure_ascii=False, indent=0)
    # Unter Windows scheitert das Ersetzen, solange ein anderer Prozess die
    # Datei gerade zum Lesen offen hat. Das dauert nur Millisekunden.
    import time
    for _ in range(100):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.05)
    os.replace(tmp, path)


class _KontoSperre:
    """Dateisperre fuer used_words.json.

    Mehrere Ersetzungslaeufe duerfen gleichzeitig arbeiten. Damit dabei keine
    Eintraege verlorengehen, wird das Konto nur unter dieser Sperre gelesen,
    geaendert und zurueckgeschrieben. Die Sperre ist eine Datei, die exklusiv
    angelegt wird; bleibt sie nach einem Absturz liegen, gilt sie nach
    `stale` Sekunden als verwaist und wird entfernt.
    """

    def __init__(self, path, timeout=300, stale=900):
        self.lock, self.timeout, self.stale = path + ".lock", timeout, stale

    def __enter__(self):
        import time
        t0 = time.time()
        while True:
            try:
                fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    alter = time.time() - os.path.getmtime(self.lock)
                except OSError:
                    alter = 0.0
                if alter > self.stale:
                    try:
                        os.unlink(self.lock)
                    except OSError:
                        pass
                    continue
                if time.time() - t0 > self.timeout:
                    raise TimeoutError(
                        "used_words.json ist seit %.0f s gesperrt - laeuft noch "
                        "ein anderer Lauf? Notfalls %s von Hand loeschen."
                        % (self.timeout, self.lock))
                time.sleep(0.2)

    def __exit__(self, *exc):
        try:
            os.unlink(self.lock)
        except OSError:
            pass


def update_ledger(paare, path=None):
    """Traegt (altes Wort, neues Wort)-Paare im Nutzungskonto nach.

    Anders als save_ledger schreibt diese Funktion keinen im Speicher
    gehaltenen Gesamtstand zurueck, sondern liest den aktuellen Stand unter
    Sperre neu von der Platte und wendet nur die eigenen Aenderungen an.
    Dadurch koennen mehrere Ersetzungsprozesse nebeneinander laufen, ohne
    sich gegenseitig zu ueberschreiben.
    """
    path = path or os.path.join(DATA, "used_words.json")
    with _KontoSperre(path):
        led = load_ledger(path)
        for alt, neu in paare:
            if alt:
                led[alt] = led.get(alt, 1) - 1
                if led[alt] <= 0:
                    led.pop(alt, None)
            if neu:
                led[neu] = led.get(neu, 0) + 1
        save_ledger(led, path)
    return led


def build_lexicon():
    """Baut den Musterindex einmalig. Gewichte werden spaeter je Raetsel gesetzt."""
    global FORMEN
    # Beide Sperrlisten greifen zur Laufzeit. Das ist wichtig, weil
    # words_v3.json nur mit den Quelldateien in ./wl/ neu gebaut werden kann;
    # eine Ergaenzung in stopwords.txt wirkt sonst erst nach einem Neubau.
    bad = (lade_sperrliste(os.path.join(DATA, "blacklist.txt"))
           | lade_sperrliste(os.path.join(DATA, "stopwords.txt")))
    tm = theme_map()
    base = json.load(open(os.path.join(DATA, "words_v3.json"), encoding="utf-8"))
    rank = {d["w"]: d["rank"] for d in base}
    prim = {d["w"] for d in base}
    FORMEN = {d["w"]: d["form"] for d in base if d.get("form")}
    # Dritte Stufe: Woerter mit Haeufigkeitsrang jenseits 100.000, die alle
    # Filter des Listenbaus bestehen (selten_v3.json). Sie erweitern den
    # Vorrat um rund 60 Prozent und helfen dort, wo enge Raster an fehlenden
    # Kandidaten scheitern. Gewichtet werden sie sehr niedrig - der Fueller
    # greift nur zu, wenn nichts Besseres passt.
    seltd = {}
    _sp = os.path.join(DATA, "selten_v3.json")
    if os.path.exists(_sp):
        seltd = {d["w"]: d.get("rank", 999999)
                 for d in json.load(open(_sp, encoding="utf-8"))}
    fbd = {d["w"]: d.get("rank", 99999)
           for d in json.load(open(os.path.join(DATA, "fallback_v3.json"),
                                   encoding="utf-8"))}
    fb = set(fbd)
    rank.update(fbd)
    FORMEN.update({d["w"]: d["form"]
                   for d in json.load(open(os.path.join(DATA, "fallback_v3.json"),
                                           encoding="utf-8")) if d.get("form")})
    for w, v in load_form_overrides().items():      # Handkorrekturen
        if v == "SG":
            FORMEN.pop(w, None)
        else:
            FORMEN[w] = v
    # Wieder zugelassene Woerter (siehe freigabe.txt): sie fehlen im
    # Wortschatz, weil sie beim einmaligen Bau der Wortlisten gesperrt waren.
    for w, r in load_freigabe().items():
        if w not in bad and w not in rank:
            prim.add(w)
            rank[w] = r
    # Alltagstaugliche Themenwoerter (alltag.txt): stehen dauerhaft im
    # Wortschatz, unabhaengig davon, ob ihr Thema im Buch vorkommt.
    _ap = os.path.join(DATA, "alltag.txt")
    if os.path.exists(_ap):
        for zeile in open(_ap, encoding="utf-8"):
            z = zeile.strip()
            if not z or z.startswith("#"):
                continue
            t = z.split()
            w = t[0]
            if w not in bad and w not in rank:
                prim.add(w)
                rank[w] = int(t[1]) if len(t) > 1 and t[1].isdigit() else 12000
    # Wunschwoerter frueherer Baende (altwoerter.txt): sie stehen im Konto,
    # waren aber bisher nur ueber plan.json setzbar und dem Fueller damit
    # unbekannt. Hier kommen sie als gewoehnliche Woerter des Grundwortschatzes
    # dazu. Fuer ein voellig neues Buch genuegt es, die Datei zu loeschen.
    _wp = os.path.join(DATA, "altwoerter.txt")
    if os.path.exists(_wp):
        for zeile in open(_wp, encoding="utf-8"):
            z = zeile.strip()
            if not z or z.startswith("#"):
                continue
            t = z.split()
            w = t[0]
            if w not in bad and w not in rank:
                prim.add(w)
                rank[w] = int(t[1]) if len(t) > 1 and t[1].isdigit() else ALT_RANG
    # Substantive, die nur wegen der Partizip-Heuristik fehlen (keinpartizip.txt).
    from wordcheck import lade_keinpartizip
    for w, r in lade_keinpartizip().items():
        if w not in bad and w not in rank:
            prim.add(w)
            rank[w] = r
    raet = {w for w in load_raetselwoerter() if w not in bad}
    for w in raet:                       # zaehlen als Grundwortschatz
        prim.add(w)
        rank.setdefault(w, 20000)
    selt = {w for w in seltd if w not in bad and w not in rank and w not in tm}
    rank.update({w: seltd[w] for w in selt})
    words = (prim | set(tm) | fb | selt) - bad
    words = {w for w in words if len(w) >= MIN_LEN}
    lex = Lexicon(sorted(words), {})
    lex.raetsel = raet                   # eigene Stufe fuer set_weights
    lex.selten = selt                    # dritte Stufe, sehr niedrig gewichtet
    return lex, tm, prim, rank


def rationierung(tm, ledger, fortschritt):
    """Bremst Themen, deren Vorrat schneller schwindet als das Buch fortschreitet.

    Ohne diese Bremse wird zuerst das schwerstgewichtete Thema leergeraeumt und
    steht in der zweiten Buchhaelfte nicht mehr zur Verfuegung. Verbraucht ein
    Thema mehr Woerter, als seinem Anteil am Buchfortschritt entspricht, sinkt
    sein Gewicht, bis die anderen Themen aufgeholt haben.
    """
    from collections import Counter
    pool, weg = Counter(), Counter()
    for w, (name, _g, nah) in tm.items():
        if nah >= 0.45:
            pool[name] += 1
            if ledger.get(w, 0) > 0:
                weg[name] += 1
    f = min(1.0, max(0.02, fortschritt))
    out = {}
    for name, p in pool.items():
        budget = max(1.0, p * f)
        v = weg[name]
        out[name] = 1.0 if v <= budget else max(0.05, (budget / v) ** 2)
    return out


def set_weights(lex, tm, prim, rank, ledger, fortschritt=1.0, vorseite=(),
                vorseiten=()):
    """Grundgewicht mal Wiederholungsdaempfung mal Rationierung.

    fortschritt = Raetselnummer / Gesamtzahl. Zwei Regler greifen ineinander:
    die Wiederholungskurve haelt Wiederholungen selten, die Rationierung sorgt
    dafuer, dass jedes Thema bis zur letzten Seite noch frische Woerter hat.

    vorseite = Woerter des unmittelbar vorhergehenden Raetsels. Themenwoerter
    daraus bekommen Gewicht 0: dasselbe Wort auf zwei aufeinanderfolgenden
    Seiten faellt jedem Loeser auf, waehrend ein Wiedersehen nach fuenf Seiten
    niemanden stoert. Grundwortschatz ist ausgenommen - dort regelt die
    Daempfung das allein.
    """
    # vorseiten: Woerter der letzten SPERRE_SEITEN Raetsel. vorseite bleibt als
    # Kurzform fuer ein einzelnes Raetsel erhalten.
    vorseite = set(vorseite) | {w for seite in vorseiten for w in seite}
    # Harte Sperre statt blossem Gewicht 0: ein Wort mit Gewicht 0 kann der
    # Fueller immer noch setzen, wenn es der einzige Kandidat fuer einen Slot
    # ist, und improve_theme greift ohnehin nicht auf das Gewicht zurueck,
    # sondern auf die Themenzugehoerigkeit. Nur eine Menge, die beide
    # abfragen, wirkt zuverlaessig.
    # Das Fenster gilt fuer JEDE Antwort, nicht nur fuer Themenwoerter: eine
    # enge Wiederholung stoert unabhaengig davon, woher das Wort kommt. Die
    # Obergrenze THEMA_MAX bleibt auf Themenwoerter beschraenkt, weil der
    # Fuellwortschatz gross genug ist, um sich selbst zu regeln.
    lex.gesperrt = set(vorseite) | {w for w, n in ledger.items()
                                    if n >= WORT_MAX}
    dros = rationierung(tm, ledger, fortschritt)
    for w in lex.words:
        n = ledger.get(w, 0)
        if w in tm:
            _, gew, nah = tm[w]
            base = gew * GEWICHT_FAKTOR * nah * nah * 6.0   # quadratisch:
            #                              Kolorit bleibt hinter Kern
            if nah >= 0.45:
                base *= dros.get(tm[w][0], 1.0)
                if n >= THEMA_MAX or w in vorseite:
                    dec = 0.0
                else:
                    dec = REUSE_THEMA.get(n, 0.0)
            else:
                dec = REUSE_FILL.get(n, REUSE_FLOOR)
        elif w in getattr(lex, "raetsel", ()):
            # Klassischer Raetselwortschatz: haeufigkeitsunabhaengig gewichtet,
            # damit er sich gegen die Allerweltswoerter durchsetzt, aber nicht
            # so stark, dass ein Raetsel nur aus solchen Woertern besteht.
            base = RAETSEL_BASE
            dec = REUSE_FILL.get(n, REUSE_FLOOR)
        elif w in prim:
            base = 2.5 / (1 + rank.get(w, 25000) / 1200)
            if rank.get(w, 25000) < HAEUFIG_GRENZE:
                base *= HAEUFIG_DAEMPFUNG
            dec = REUSE_FILL.get(n, REUSE_FLOOR)
        elif w in getattr(lex, "selten", ()):
            # Dritte Stufe (selten_v3.json): nur Lueckenfueller. Das Gewicht
            # liegt unter dem des Rueckfallwortschatzes, damit diese Woerter
            # ein Raster nicht praegen, sondern nur retten.
            base = SELTEN_BASE
            dec = REUSE_FILL.get(n, REUSE_FLOOR)
        else:
            r = rank.get(w, 99999)         # Rueckfall: je seltener, desto unwilliger
            base = 0.06 if r < 45000 else 0.012
            dec = REUSE_FILL.get(n, REUSE_FLOOR)
        # Zwei Regeln gelten fuer JEDES Wort, gleich aus welcher Quelle:
        # die Obergrenze und der Zuschlag fuer kurze Woerter.
        if n >= WORT_MAX or w in vorseite:
            dec = 0.0
        elif n and 4 <= len(w) <= 6:
            dec *= KURZ_DAEMPFUNG
        lex.weights[w] = base * dec * FORM_FAKTOR.get(FORMEN.get(w), 1.0)


# Knotengrenze je Fuellversuch. Bei 6000 scheiterten regelmaessig 40 von 45
# Versuchen an der Grenze statt an fehlenden Woertern; ein teurerer, aber
# erfolgreicher Versuch ist billiger als sieben abgebrochene.
MAX_NODES = 12000
FRUEH_AUS = 12       # erfolglose Fuellversuche, nach denen ein Raster faellt
SEEDS_EXTRA = 32     # zusaetzliche Seeds, bevor ein leerer Block geduldet wird
SAT_MAX = 0.78       # Slot-Saettigung, ab der Fuellversuche kaum gelingen
CROSS_MIN = 0.58     # geforderte Kreuzungsrate


# Ab wann eine Fuellung gut genug ist, um die Suche sofort zu beenden.
# Anteile, bezogen auf die Zahl der Eintraege im Raster.
# Sofortige Annahme einer Fuellung nur bei einem herausragenden Ergebnis -
# grob das obere Fuenftel dessen, was die Suche ueberhaupt liefert. Wird die
# Schwelle nicht erreicht, laeuft die Suche alle tries durch und nimmt am Ende
# die beste Fuellung nach score. Die Schwelle entscheidet also nur, wann
# aufgehoert wird, nie was genommen wird.
# Gemessen an den ersten zwanzig Seiten: Themenanteil Median 60 %,
# 80-%-Quantil 64 %; Kern und Umfeld zusammen Median 51 %, 80-%-Quantil 57 %;
# Kurzwortanteil Median 76 %, 30-%-Quantil 72 %. Die Schwellen liegen jeweils
# am oberen beziehungsweise unteren Fuenftel dieser Verteilungen.
GUT_KERN = 0.56            # Kern UND Umfeld zusammen, mindestens 56 %
GUT_THEMA = 0.65           # Themenwoerter insgesamt, mindestens 65 %
GUT_KURZ = 0.72            # hoechstens 72 % Antworten mit 4-6 Zeichen
WIED_ZIEL = 0.10           # angestrebter Anteil bereits verwendeter Woerter
#                            je Raetsel. Unterhalb dieses Werts gilt eine
#                            Fuellung als gut genug, um die Suche zu beenden.
WIED_MAX = 0.15            # harte Obergrenze: Fuellungen darueber werden gar
#                            nicht erst als Kandidat gemerkt.
GUT_WIED = 1               # alter Festwert, nur noch als Untergrenze fuer
#                            sehr kleine Raster (siehe _versuch)
GUT_KERN_MIN = 6           # untere Schranke fuer kleine Raster
MIN_THEMA = 0.40           # Vorpruefung: so schwache Fuellungen kommen gar
                           # nicht erst in die Auswahl fuer die Nachbesserung
MIN_THEMA_FINAL = 0.50     # Endgrenze: gilt fuer das nachgebesserte Ergebnis
NACHBESSERN_MAX = 6        # hoechstens so viele Fuellungen je Raster nachbessern
NACHBESSERN_LAEUFE = 8     # Durchgaenge je Fuellung
KURZ_STRAFE = 0.15         # Punktabzug je Antwort mit 4-6 Zeichen ueber dem
#                            Median. Klein gehalten: kurze Woerter sind nicht
#                            schlecht, es sollen nur nicht noch mehr werden.
WIED_STRAFE = 1.0          # Punktabzug je Wiederholung bei der Auswahl. Hoeher
#                            als zwei Kernbegriffe (je 2.0): eine Wiederholung
#                            wiegt schwerer als zwei fehlende Themenwoerter.


def make_puzzle(lex, tm, prim, seed_range, forced=None, tries=50,
                required=(), density=DENSITY, diag=None, ledger=None):
    """Erzeugt ein Raetsel. Rueckgabe (layout, grid, info) oder None.

    tries  Hoechstzahl der Fuellversuche je Raster. Sie dienen NICHT der
           Machbarkeit — die erste gelungene Fuellung ist bereits ein gueltiges
           Raetsel — sondern der Auswahl: jeder Versuch startet mit anderem
           Zufall und liefert eine andere Wortmischung, bewertet nach
           Kernbegriffen, Themenwoertern und seltenen Woertern.

    Abbruch erfolgt, sobald eine Fuellung alle vier Guetekriterien
    erreicht. Dann ist kein Vergleich mehr noetig: ein Raetsel mit 30 %
    Kernbegriffen und wenig Seltenem ist das Ziel, und laenger zu suchen kostet
    nur Rechenzeit. Wird die Schwelle nie erreicht, entscheidet nach tries
    Versuchen die beste Bewertung.
    """
    # Dreibuchstabige Vorgabewoerter: der Fuellwortschatz beginnt bei vier
    # Buchstaben, also darf das Raster genau so viele Dreier-Slots haben, wie
    # Vorgabewoerter dieser Laenge zu setzen sind - keinen mehr, keinen weniger.
    forced3 = sum(1 for w in (forced or ()) if len(w) == 3)
    _layout.MIN_LEN = 3 if forced3 else MIN_LEN
    seed_range = list(seed_range)
    weiter = list(range(seed_range[-1] + 1, seed_range[-1] + 1 + SEEDS_EXTRA))
    # Vier Durchgaenge, von streng nach nachgiebig. Ein leerer Frageblock ist
    # ein schwarzes Kaestchen ohne Frage; die ersten drei Durchgaenge lassen
    # keinen zu. Erst wenn 8 + SEEDS_EXTRA Raster keines ohne liefern - das ist
    # selten - wird einer geduldet.
    #
    #   (Seeds,        max_leer, frueh)
    #   frueh = Zahl erfolgloser Fuellversuche, nach der ein Raster aufgegeben
    #   und der naechste Seed genommen wird. Das ist der Frueherkennungs-
    #   mechanismus fuer zu enge Raster: er kostet nichts, er spart. Der letzte
    #   Durchgang setzt ihn aus, damit ein schweres Raster am Ende doch noch
    #   seine vollen tries bekommt und nie gar kein Raetsel herauskommt.
    for seeds, max_leer, frueh in ((seed_range, 0, FRUEH_AUS),
                                   (weiter,     0, FRUEH_AUS),
                                   (seed_range, 0, None),
                                   (seed_range, 1, None)):
        erg = _versuch(seeds, max_leer, forced, forced3, density,
                       required, tries, lex, tm, prim, diag, frueh, ledger)
        if erg:
            return erg
    return None


def _versuch(seed_range, max_leer, forced, forced3, density, required,
             tries, lex, tm, prim, diag=None, frueh=None, ledger=None):
    """Ein Durchgang der Layoutsuche mit fester Obergrenze fuer leere Bloecke.

    diag: optionales dict, in dem mitgezaehlt wird, warum Layouts und
    Fuellungen verworfen wurden (siehe book.py, Zeile "diag=").
    """
    def z(k, n=1):
        if diag is not None:
            diag[k] = diag.get(k, 0) + n

    rueckfall = None                       # bestes Ergebnis unter der Endgrenze
    for s in seed_range:
        lay, info = generate(GRID_H, GRID_W, density, iters=20000, seed=s,
                             required=tuple(required), slots3=forced3)
        z("layouts")
        if forced3 and sum(1 for e in lay.entries if e.length == 3) != forced3:
            z("verworfen_slots3")
            continue                       # Raster passt nicht, naechster Seed
        if info["uncovered"]:
            z("verworfen_unbedeckt")
            continue
        cnt = {}
        for e in lay.entries:
            for cell in e.cells():
                cnt[cell] = cnt.get(cell, 0) + 1
        sat = sum(sum(1 for cell in e.cells() if cnt[cell] >= 2) / e.length
                  for e in lay.entries) / len(lay.entries)
        letters = {(r, cc) for r in range(GRID_H) for cc in range(GRID_W)} - lay.blocks
        ratio = sum(1 for v in cnt.values() if v >= 2) / max(1, len(letters))
        rand_ok = all((r, 0) in lay.blocks or any(e.r == r and e.c == 0
                                                  for e in lay.entries)
                      for r in range(GRID_H)) and \
                  all((0, cc) in lay.blocks or any(e.r == 0 and e.c == cc
                                                   for e in lay.entries)
                      for cc in range(GRID_W))
        leer = len(lay.blocks - {e.clue_rc for e in lay.entries})
        if sat > SAT_MAX:
            z("verworfen_saettigung"); continue
        if ratio < CROSS_MIN:
            z("verworfen_kreuzrate"); continue
        if not rand_ok:
            z("verworfen_rand"); continue
        if leer > max_leer:
            z("verworfen_leerblock"); continue
        z("layouts_brauchbar")
        kandidaten = []
        n_e = len(lay.entries)
        schwelle_kern = max(GUT_KERN_MIN, GUT_KERN * n_e)
        schwelle_thema = GUT_THEMA * n_e
        led = ledger or {}
        for fs in range(tries):
            try:
                ok, grid, fst = fill(lay, lex, forced=forced, seed=fs,
                                     max_nodes=MAX_NODES)
            except TimeoutError:
                z("fuellung_abbruch"); ok = False
            z("fuellversuche")
            if not ok:
                z("fuellung_knotengrenze" if len(fst) > 2 and fst[2]
                  else "fuellung_sackgasse")
                if frueh and not kandidaten and fs + 1 >= frueh:
                    # Nach frueh Versuchen keine einzige gueltige Fuellung:
                    # das Raster ist zu eng. Weitersuchen kostet nur Zeit,
                    # der naechste Seed ist billiger.
                    z("raster_frueh_aufgegeben")
                    break
                continue
            z("fuellung_gelungen")
            kern = sum(1 for e in lay.entries
                       if e.word in tm and tm[e.word][2] >= 0.8)
            # Fuer die Annahmeschwelle zaehlen Kern und Umfeld zusammen: das
            # Umfeld ist thematisch ebenso brauchbar, nur weniger zentral.
            nah = sum(1 for e in lay.entries
                      if e.word in tm and tm[e.word][2] >= 0.45)
            kurz = sum(1 for e in lay.entries if 4 <= len(e.word) <= 6)
            th = sum(1 for e in lay.entries if e.word in tm)
            rare = sum(1 for e in lay.entries if e.word not in tm and e.word not in prim)
            # Wiederholungen kosten schon bei der Auswahl Punkte. Ohne das
            # entscheidet nur das Gewicht, und das hilft nicht, wenn ein Wort
            # fuer einen Slot ohnehin die einzige Wahl war - dann gewinnt jetzt
            # eine andere Fuellung, die den Slot anders loest.
            wied = sum(1 for e in lay.entries if led.get(e.word, 0) > 0)
            score = (2.0 * kern + 0.6 * (th - kern) - 0.3 * rare
                     - WIED_STRAFE * wied
                     - KURZ_STRAFE * max(0, kurz - 0.76 * n_e))
            # Untergrenze: eine Fuellung mit weniger als MIN_THEMA
            # Themenwoertern ist unbrauchbar. Sie wird gar nicht erst als
            # bester Kandidat gemerkt - bleibt bis zum Schluss keine andere
            # uebrig, faellt das ganze Raster und der naechste Seed kommt dran.
            if th < MIN_THEMA * n_e:
                z("fuellung_zu_wenig_thema")
                if frueh and not kandidaten and fs + 1 >= frueh:
                    z("raster_frueh_aufgegeben")
                    break
                continue
            if wied > max(GUT_WIED, WIED_MAX * n_e):
                z("fuellung_zu_viele_wiederholungen")
                continue
            kandidaten.append((score, [e.word for e in lay.entries],
                               dict(grid), th, rare))
            if (nah >= schwelle_kern and th >= schwelle_thema
                    and kurz <= GUT_KURZ * n_e
                    and wied <= max(GUT_WIED, WIED_ZIEL * n_e)):
                z("schwelle_erreicht")
                if diag is not None:
                    diag["schwelle_bei_versuch"] = fs + 1
                break                      # gut genug, kein Vergleich noetig
        if not kandidaten:
            z("layouts_ohne_fuellung")
            continue
        # Nachbesserung: die beste Fuellung zuerst. Kommt sie nicht ueber die
        # Endgrenze, ist die naechstbeste dran. Erst wenn keine der besten
        # NACHBESSERN_MAX Fuellungen reicht, faellt das ganze Raster.
        kandidaten.sort(key=lambda k: -k[0])
        for rang, (sc, ws, g0, th0, rare0) in enumerate(kandidaten[:NACHBESSERN_MAX]):
            bth, bgrid, bwords = th0, g0, list(ws)
            for k in range(NACHBESSERN_LAEUFE):
                for e, w in zip(lay.entries, ws):
                    e.word = w
                g2, th2 = improve_theme(lay, lex, tm, ledger or {},
                                        seed=s * 10 + k, schutz=forced or ())
                if th2 > bth:
                    bth, bgrid = th2, g2
                    bwords = [e.word for e in lay.entries]
            z("nachbesserungen")
            for e, w in zip(lay.entries, bwords):
                e.word = w
            rare2 = sum(1 for e in lay.entries
                        if e.word not in tm and e.word not in prim)
            info = dict(seed=s, entries=n_e, thematisch=bth, selten=rare2,
                        vorgaben=len(forced or []),
                        kreuzrate=round(ratio, 2), leer=leer)
            if bth >= MIN_THEMA_FINAL * n_e:
                if diag is not None:
                    diag["nachbesserung_rang"] = rang + 1
                return lay, bgrid, info
            z("endgrenze_verfehlt")
            if rueckfall is None or bth > rueckfall[0]:
                rueckfall = (bth, lay, bgrid, list(bwords), info)
    # Kein Raster hat die Endgrenze erreicht. Lieber das beste gesehene
    # Ergebnis als gar keine Seite.
    if rueckfall is not None:
        z("rueckfall_genommen")
        _, lay, g, ws, info = rueckfall
        for e, w in zip(lay.entries, ws):
            e.word = w
        return lay, g, info
    return None


def clue_store(path=None):
    path = path or os.path.join(DATA, "clues.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {}


def save_clues(c, path=None):
    path = path or os.path.join(DATA, "clues.json")
    json.dump(c, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)


# --------------------------------------------------------------------------
# Nachbesserung: Fuellwoerter nachtraeglich durch Themenwoerter ersetzen
# --------------------------------------------------------------------------
def improve_theme(lay, lex, tm, ledger, rounds=1200, seed=0, group_max=7,
                  schutz=()):
    """Lokale Suche: kleine Bereiche neu belegen und dabei Themenwoerter bevorzugen.

    Ein zufaellig gewaehlter Nicht-Themen-Eintrag wird samt seinen direkten
    Nachbarn geleert und neu gefuellt. Uebernommen wird nur, wenn die Zahl der
    Themenwoerter steigt (oder gleich bleibt und ein seltenes Wort verschwindet).
    """
    import random
    rng = random.Random(seed)
    E = lay.entries
    cellmap = {}
    for i, e in enumerate(E):
        for cell in e.cells():
            cellmap.setdefault(cell, []).append(i)
    neigh = {i: sorted({j for cell in E[i].cells() for j in cellmap[cell] if j != i})
             for i in range(len(E))}

    def build_grid(words):
        g = {}
        for e, w in zip(E, words):
            if w:
                for cell, ch in zip(e.cells(), w):
                    g[cell] = ch
        return g

    def theme_count(words):
        """Kernbegriffe zaehlen doppelt - Kolorit soll die Zahl nicht aufblasen."""
        return sum((2 if tm[w][2] >= 0.8 else 1) for w in words if w in tm)

    schutz = set(schutz)
    words = [e.word for e in E]
    best_n = theme_count(words)

    for _ in range(rounds):
        cands = [i for i, w in enumerate(words) if w not in tm and w not in schutz]
        if not cands:
            break
        i = rng.choice(cands)
        nb = [j for j in neigh[i] if words[j] not in schutz]
        rng.shuffle(nb)
        group = [i] + nb[:group_max - 1]
        trial = list(words)
        for j in group:
            trial[j] = None
        g = build_grid(trial)
        used = {w for w in trial if w}

        def solve(k):
            if k == len(group):
                return True
            j = group[k]
            pat = [g.get(cell) for cell in E[j].cells()]
            cs = lex.match(pat) - used - getattr(lex, "gesperrt", set())
            if not cs:
                return False
            order = sorted(cs, key=lambda w: (-(80.0 if (w in tm and tm[w][2] >= 0.8)
                                                else (30.0 if w in tm else 0.0))
                                              - lex.weights.get(w, 0.0)
                                              + rng.random() * 3))[:30]
            for w in order:
                changed = []
                for cell, ch in zip(E[j].cells(), w):
                    if cell not in g:
                        g[cell] = ch
                        changed.append(cell)
                trial[j] = w
                used.add(w)
                if solve(k + 1):
                    return True
                used.discard(w)
                trial[j] = None
                for cell in changed:
                    del g[cell]
            return False

        if solve(0):
            n = theme_count(trial)
            rar = sum(1 for w in trial if w not in tm and w not in lex.weights)
            if n > best_n or (n == best_n and rng.random() < 0.15):
                words, best_n = list(trial), n
    for e, w in zip(E, words):
        e.word = w
    return build_grid(words), best_n
