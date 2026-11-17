#!/usr/bin/env python3
"""Assemble une maquette en un seul fichier HTML autonome (images WebP et polices intégrées).

Usage :
    python3 build.py chantier/<slug>        -> chantier/<slug>/dist/index.html

Le dossier du chantier contient :
    src.html    la page, avec ces repères :
                  {{img:nom}}    image de img/nom.jpg|.jpeg|.png|.webp, intégrée en WebP
                  {{font:cle}}   police déclarée dans site.json, intégrée en woff2
                  {{hours}}      lignes <tr> du tableau d'horaires
                  {{hours_js}}   horaires au format JS {0:[["18:00","21:00"]], ...} (0 = dimanche)
    img/        les photos (déjà recadrées si besoin)
    site.json   {"fonts": [{"key": "titre", "family": "grenze-gotisch", "weight": 600},
                           {"key": "texte", "family": "schibsted-grotesk", "variable": true},
                           {"key": "titre-it", "family": "bodoni-moda", "variable": true, "style": "italic"}],
                 "horaires": {"lundi": ["18:00-21:00"], "mardi": [], ...}}
"""
import base64, io, json, re, subprocess, sys, tarfile, tempfile
from pathlib import Path
from PIL import Image

CACHE = Path.home() / ".cache" / "maquettes-fonts"
JOURS = [("lundi", "Lundi", 1), ("mardi", "Mardi", 2), ("mercredi", "Mercredi", 3), ("jeudi", "Jeudi", 4),
         ("vendredi", "Vendredi", 5), ("samedi", "Samedi", 6), ("dimanche", "Dimanche", 0)]


def font_file(spec):
    fam, var, st = spec["family"], spec.get("variable", False), spec.get("style", "normal")
    name = f"{fam}-latin-wght-{st}.woff2" if var else f"{fam}-latin-{spec.get('weight', 400)}-{st}.woff2"
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / name
    if out.exists():
        return out
    pkg = f"@fontsource-variable/{fam}" if var else f"@fontsource/{fam}"
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(["npm", "pack", pkg, "--silent"], cwd=tmp, capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"Police introuvable sur npm : {pkg}")
        tgz = next(Path(tmp).glob("*.tgz"))
        with tarfile.open(tgz) as tf:
            try:
                tf.extract(f"package/files/{name}", tmp, filter="data")
            except KeyError:
                sys.exit(f"{name} absent de {pkg} (graisse ou sous-ensemble inexistant)")
        (Path(tmp) / "package" / "files" / name).replace(out)
    # copie locale en .ttf pour que les captures d'écran utilisent la vraie police
    try:
        from fontTools.ttLib import TTFont
        ttf_dir = Path.home() / ".fonts"; ttf_dir.mkdir(exist_ok=True)
        f = TTFont(out); f.flavor = None; f.save(ttf_dir / (out.stem + ".ttf"))
        subprocess.run(["fc-cache", "-f", str(ttf_dir)], capture_output=True)
    except Exception:
        pass
    return out


def img_uri(folder, name):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = folder / "img" / (name + ext)
        if p.exists():
            im = Image.open(p)
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
            buf = io.BytesIO()
            im.save(buf, "WEBP", quality=88 if ext == ".png" else 74, method=6)
            return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    sys.exit(f"Image manquante : img/{name}.jpg|png")


def heure(s):
    a, b = s.split(":"); return f"{int(a)}h{'' if b == '00' else b}"


def main():
    folder = Path(sys.argv[1]).resolve()
    conf = json.loads((folder / "site.json").read_text(encoding="utf-8"))
    fonts = {f["key"]: f for f in conf.get("fonts", [])}
    rows, js = [], {}
    for cle, nom, idx in JOURS:
        paires = [x.replace(" ", "").split("-") for x in conf.get("horaires", {}).get(cle, [])]
        if paires: js[idx] = paires
        txt = ", ".join(f"{heure(a)} – {heure(b)}" for a, b in paires) or "Fermé"
        rows.append(f'<tr data-day="{idx}"><th scope="row">{nom}</th><td>{txt}</td></tr>')

    s = (folder / "src.html").read_text(encoding="utf-8")
    cache = {}
    s = re.sub(r"\{\{img:([\w-]+)\}\}", lambda m: cache.setdefault(m.group(1), img_uri(folder, m.group(1))), s)
    def font(m):
        key = m.group(1)
        if key not in fonts: sys.exit(f"Police « {key} » non déclarée dans site.json")
        return "data:font/woff2;base64," + base64.b64encode(font_file(fonts[key]).read_bytes()).decode()
    s = re.sub(r"\{\{font:([\w-]+)\}\}", font, s)
    s = s.replace("{{hours}}", "\n          ".join(rows)).replace("{{hours_js}}", json.dumps(js))
    left = re.findall(r"\{\{[^}]+\}\}", s)
    if left: sys.exit(f"Repères non remplacés : {left}")
    for must in ('name="robots" content="noindex', "Maquette réalisée par Gaspard Culli"):
        if must not in s: sys.exit(f"Élément obligatoire absent : {must}")
    out = folder / "dist" / "index.html"; out.parent.mkdir(exist_ok=True)
    out.write_text(s, encoding="utf-8")
    print(out, round(len(s.encode()) / 1024), "Ko")


if __name__ == "__main__":
    main()
