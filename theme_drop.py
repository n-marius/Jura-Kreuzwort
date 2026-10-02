"""Woerter aus einem Thema entfernen (und optional sperren).

  python theme_drop.py JURA RECHTECK GERECHT --sperren
"""
import sys, json, subprocess
from themes import _n, PATH

name = sys.argv[1].upper()
woerter = [_n(w) for w in sys.argv[2:] if not w.startswith("--")]
t = json.load(open(PATH, encoding="utf-8"))
ws = t[name]["woerter"]
weg = [w for w in woerter if ws.pop(w, None) is not None]
t[name].get("facetten", {}).pop
for w in weg:
    t[name].get("facetten", {}).pop(w, None)
json.dump(t, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(f"{name}: {len(weg)} entfernt, noch {len(ws)} Woerter")
if "--sperren" in sys.argv and weg:
    subprocess.run([sys.executable, "blacklist_add.py"] + weg)
