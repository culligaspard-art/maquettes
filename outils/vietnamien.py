"""Ajoute le sous-ensemble vietnamien des polices (ở, ố, ắ, đ…) à une page générée par modele.py.

    python3 outils/vietnamien.py chantier/<slug>

À lancer après modele.py et avant build.py, pour les commerces dont la carte a des noms vietnamiens.
"""
import json, re, sys
from pathlib import Path

PLAGE = ("U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,"
         "U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB")

d = Path(sys.argv[1])
sj = json.loads((d / "site.json").read_text(encoding="utf-8"))
s = (d / "src.html").read_text(encoding="utf-8")
ajouts = []
for f in list(sj["fonts"]):
    if f.get("subset") or f["key"].endswith("-vi"):
        continue
    k = f["key"] + "-vi"
    if not any(x["key"] == k for x in sj["fonts"]):
        sj["fonts"].append({**f, "key": k, "subset": "vietnamese"})
    m = re.search(r'@font-face\{[^}]*\{\{font:' + re.escape(f["key"]) + r'\}\}[^}]*\}', s)
    if m and "{{font:%s}}" % k not in s:
        r = m.group(0).replace("{{font:%s}}" % f["key"], "{{font:%s}}" % k)
        r = r[:-1] + ";unicode-range:" + PLAGE + "}"
        ajouts.append((m.group(0), r))
for old, new in ajouts:
    s = s.replace(old, old + new, 1)
(d / "site.json").write_text(json.dumps(sj, ensure_ascii=False, indent=1), encoding="utf-8")
(d / "src.html").write_text(s, encoding="utf-8")
print(f"{len(ajouts)} police(s) complétée(s) en vietnamien")
