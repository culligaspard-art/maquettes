#!/usr/bin/env python3
"""Captures de contrôle d'une maquette.

Usage :
    python3 shots.py chantier/<slug>/dist/index.html chantier/<slug>/shots --ouvert 2026-11-17T19:10

--ouvert : date et heure où le commerce est ouvert (pour voir « Ouvert maintenant »).

Produit dans le dossier de sortie :
    planche-intro.jpg   6 images de la séquence d'ouverture (1,0 s à 3,6 s)
    bureau-1.jpg, bureau-2.jpg   la page entière sur ordinateur, en deux moitiés
    mobile.jpg          l'écran d'accueil mobile + la page entière découpée
et affiche le test de débordement horizontal à 375 et 1280 px (doit être False).
"""
import argparse, datetime as dt
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("html"); ap.add_argument("out"); ap.add_argument("--ouvert", required=True)
a = ap.parse_args()
url = Path(a.html).resolve().as_uri(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
fixed = dt.datetime.fromisoformat(a.ouvert)
CHROME = next((c for c in ("/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser") if Path(c).exists()), None)

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    def page(w, h, scale=1):
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=scale)
        pg = ctx.new_page(); pg.clock.set_fixed_time(fixed)
        pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:")) else r.abort())
        return pg
    pg = page(1440, 900); pg.goto(url, wait_until="commit"); t0 = 0; frames = []
    for t in (1000, 1450, 1650, 1900, 2300, 3600):
        pg.wait_for_timeout(t - t0); t0 = t
        p = out / f"_intro-{t}.png"; pg.screenshot(path=str(p)); frames.append(p)
    pg.screenshot(path=str(out / "_desktop.png"), full_page=True)
    for w in (1280, 375):
        p2 = page(w, 800); p2.goto(url); p2.wait_for_timeout(3000)
        print(f"débordement {w}px :", p2.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"))
    m = page(390, 844, 2); m.goto(url); m.wait_for_timeout(3400)
    m.screenshot(path=str(out / "_m-hero.png")); m.screenshot(path=str(out / "_m-full.png"), full_page=True)
    b.close()

W = 560; fr = [Image.open(f).convert("RGB") for f in frames]; fr = [f.resize((W, int(f.height * W / f.width))) for f in fr]
c = Image.new("RGB", (W * 3 + 20, fr[0].height * 2 + 10), "white")
for i, f in enumerate(fr): c.paste(f, ((i % 3) * (W + 10), (i // 3) * (f.height + 10)))
c.save(out / "planche-intro.jpg", quality=82)
d = Image.open(out / "_desktop.png").convert("RGB"); d = d.resize((900, int(d.height * 900 / d.width)))
half = d.height // 2; d.crop((0, 0, 900, half)).save(out / "bureau-1.jpg", quality=80); d.crop((0, half, 900, d.height)).save(out / "bureau-2.jpg", quality=80)
mh = Image.open(out / "_m-hero.png").convert("RGB").resize((390, 844))
f = Image.open(out / "_m-full.png").convert("RGB"); f = f.resize((390, int(f.height * 390 / f.width)))
parts = [f.crop((0, i * 1700, 390, min(f.height, (i + 1) * 1700))) for i in range((f.height + 1699) // 1700)]
c = Image.new("RGB", (390 * (len(parts) + 1) + 10 * len(parts), 1700), "white"); c.paste(mh, (0, 0))
for i, p in enumerate(parts): c.paste(p, ((i + 1) * 400, 0))
c.save(out / "mobile.jpg", quality=80)
for p in out.glob("_*.png"): p.unlink()
print("captures :", out)
