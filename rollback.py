"""Nutzungskonto zurueckrechnen, bevor Raetsel neu erzeugt werden.

  python rollback.py 3 7      (Raetsel 3 bis 7 aus used_words.json austragen)

Ohne diesen Schritt zaehlen verworfene Woerter weiter mit und werden bei der
Neuerzeugung faelschlich gedaempft.
"""
import sys, json, os, pickle
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skanvord"))
import layout                                   # noqa

a, b = int(sys.argv[1]), int(sys.argv[2])
led = json.load(open("used_words.json", encoding="utf-8"))
n = 0
for i in range(a, b + 1):
    f = f"puzzles/{i:02d}.pkl"
    if not os.path.exists(f):
        continue
    lay, _ = pickle.load(open(f, "rb"))
    for e in lay.entries:
        if e.word in led:
            led[e.word] -= 1
            if led[e.word] <= 0:
                del led[e.word]
    # Die Rasterdatei mitloeschen. Bleibt sie liegen und der anschliessende
    # Neubau bricht ab, sieht das alte Raster wie ein gueltiges aus - mit dem
    # gesperrten Wort noch darin, waehrend das Konto schon zurueckgesetzt ist.
    os.remove(f)
    n += 1
json.dump(led, open("used_words.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)
print(f"{n} Raetsel ausgetragen, Konto hat noch {len(led)} Woerter")
