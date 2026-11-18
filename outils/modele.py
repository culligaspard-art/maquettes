#!/usr/bin/env python3
"""Génère src.html et site.json d'un commerce à partir de sa fiche et d'un modèle de métier.

Usage :
    python3 outils/modele.py chantier/<slug>
    python3 outils/build.py chantier/<slug>      # ensuite, comme pour un site sur mesure

La fiche chantier/<slug>/fiche.json décrit le commerce (voir outils/modeles/LISEZMOI.md).
Les images sont dans chantier/<slug>/img/ (nom sans extension = clé).
"""
import colorsys, hashlib, json, re, sys
from pathlib import Path

from jinja2 import ChainableUndefined, Environment, FileSystemLoader

ICI = Path(__file__).resolve().parent
MODELES = ICI / "modeles"

# ---------------------------------------------------------------- familles
# polices : (clé, paquet fontsource, variable, style, poids) ; le premier élément = titres
FAMILLES = {
    "beaute": {
        "nav": [("soins", "Les soins"), ("galerie", "En images"), ("horaires", "Horaires et accès")],
        "cta": "Prendre rendez-vous", "intro_ms": 2700,
        "polices": [
            [("titre", "bodoni-moda", True, "italic", None), ("texte", "jost", True, "normal", None)],
            [("titre", "playfair-display", True, "italic", None), ("texte", "outfit", True, "normal", None)],
            [("titre", "cormorant-garamond", True, "italic", None), ("texte", "figtree", True, "normal", None)],
            [("titre", "italiana", False, "normal", 400), ("texte", "karla", True, "normal", None)],
        ],
    },
    "emporter": {
        "nav": [("carte", "La carte"), ("commander", "Commander"), ("horaires", "Horaires")],
        "cta": "Commander", "intro_ms": 2700,
        "polices": [
            [("titre", "shrikhand", False, "normal", 400), ("texte", "barlow", False, "normal", 400), ("texte5", "barlow", False, "normal", 500), ("carte", "barlow-condensed", False, "normal", 600)],
            [("titre", "chango", False, "normal", 400), ("texte", "work-sans", True, "normal", None)],
            [("titre", "rammetto-one", False, "normal", 400), ("texte", "dm-sans", True, "normal", None)],
            [("titre", "caprasimo", False, "normal", 400), ("texte", "nunito-sans", True, "normal", None)],
        ],
    },
    "patisserie": {
        "nav": [("vitrine", "La vitrine"), ("maison", "La maison"), ("horaires", "Horaires")],
        "cta": "Appeler", "intro_ms": 2650,
        "polices": [
            [("titre", "yeseva-one", False, "normal", 400), ("script", "pinyon-script", False, "normal", 400), ("texte", "figtree", True, "normal", None)],
            [("titre", "abril-fatface", False, "normal", 400), ("script", "great-vibes", False, "normal", 400), ("texte", "nunito-sans", True, "normal", None)],
            [("titre", "gloock", False, "normal", 400), ("script", "parisienne", False, "normal", 400), ("texte", "outfit", True, "normal", None)],
        ],
    },
    "restaurant": {
        "nav": [("carte", "La carte"), ("lieu", "Le lieu"), ("horaires", "Horaires et accès")],
        "cta": "Réserver", "intro_ms": 2600,
        "polices": [
            [("titre", "fraunces", True, "normal", None), ("texte", "work-sans", True, "normal", None)],
            [("titre", "young-serif", False, "normal", 400), ("texte", "karla", True, "normal", None)],
            [("titre", "dm-serif-display", False, "normal", 400), ("texte", "dm-sans", True, "normal", None)],
            [("titre", "grenze-gotisch", False, "normal", 600), ("texte", "schibsted-grotesk", True, "normal", None)],
        ],
    },
    "artisan": {
        "nav": [("services", "Nos services"), ("realisations", "Réalisations"), ("devis", "Devis")],
        "cta": "Demander un devis", "intro_ms": 2700,
        "polices": [
            [("titre", "big-shoulders-display", True, "normal", None), ("texte", "manrope", True, "normal", None)],
            [("titre", "oswald", True, "normal", None), ("texte", "inter-tight", True, "normal", None)],
            [("titre", "archivo", True, "normal", None), ("texte", "familjen-grotesk", True, "normal", None)],
            [("titre", "anton", False, "normal", 400), ("texte", "dm-sans", True, "normal", None)],
        ],
    },
    "commerce": {
        "nav": [("produits", "Nos produits"), ("maison", "La maison"), ("horaires", "Horaires")],
        "cta": "Appeler", "intro_ms": 2600,
        "polices": [
            [("titre", "bricolage-grotesque", True, "normal", None), ("texte", "dm-sans", True, "normal", None)],
            [("titre", "dela-gothic-one", False, "normal", 400), ("texte", "karla", True, "normal", None)],
            [("titre", "ultra", False, "normal", 400), ("texte", "work-sans", True, "normal", None)],
            [("titre", "alfa-slab-one", False, "normal", 400), ("texte", "nunito-sans", True, "normal", None)],
        ],
    },
}
PAS_DE_RESA = {"emporter", "artisan", "commerce", "patisserie"}

# ---------------------------------------------------------------- couleurs
def hx(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c))) for c in rgb)

def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return hx(tuple(a[i] * (1 - t) + b[i] * t for i in range(3)))

def lum(h):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return .2126 * ch(r) + .7152 * ch(g) + .0722 * ch(b)

def contraste(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + .05) / (lb + .05)

def couleur_dominante(img_path):
    """Teinte saturée la plus présente d'une image (logo de préférence)."""
    from PIL import Image
    im = Image.open(img_path).convert("RGBA").resize((96, 96))
    import numpy as np
    a = np.asarray(im).reshape(-1, 4)
    px = [tuple(int(v) for v in p[:3]) for p in a if p[3] > 200]
    seaux = {}
    for r, g, b in px:
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if s < .28 or l < .12 or l > .88:
            continue
        k = int(h * 24)
        seaux.setdefault(k, []).append((r, g, b))
    if not seaux:
        return None
    k = max(seaux, key=lambda k: len(seaux[k]))
    pts = seaux[k]
    return hx(tuple(sum(p[i] for p in pts) / len(pts) for i in range(3)))

def assombrir_pour_texte_blanc(c):
    while contraste(c, "#FFFFFF") < 4.6:
        c = mix(c, "#000000", .08)
    return c

def palette(fiche, dossier):
    c = dict(fiche.get("couleurs") or {})
    if fiche.get("famille") == "restaurant":
        c.setdefault("accent", "#F08A3C")
    if "principale" not in c:
        src = None
        for k in (fiche.get("logo"), fiche.get("hero")):
            if k:
                for ext in (".png", ".jpg", ".jpeg", ".webp"):
                    p = dossier / "img" / f"{k}{ext}"
                    if p.exists():
                        src = p
                        break
            if src:
                d = couleur_dominante(src)
                if d:
                    c["principale"] = d
                    break
        c.setdefault("principale", "#B3402A")
    p = c["principale"]
    c.setdefault("encre", mix(p, "#140C08", .82))
    c.setdefault("fond", mix(p, "#FFFFFF", .94))
    c.setdefault("fond2", mix(p, "#FFFFFF", .86))
    c.setdefault("sombre", mix(p, "#0B0806", .78))
    c.setdefault("accent", c.get("accent") or mix(p, "#F2C14E", .55))
    # bouton principal lisible en blanc
    c["bouton"] = assombrir_pour_texte_blanc(p)
    c["bouton_survol"] = mix(c["bouton"], "#000000", .15)
    c["doux"] = mix(c["encre"], c["fond"], .32)
    c["trait"] = "rgba(%d,%d,%d,.16)" % rgb(c["encre"])
    c["accent_encre"] = "#FFFFFF" if contraste(c["accent"], "#FFFFFF") >= 4.5 else c["encre"]
    c["sur_sombre"] = mix(c["fond"], c["sombre"], .18)
    c["sur_sombre_doux"] = mix(c["fond"], c["sombre"], .38)
    return c

# ---------------------------------------------------------------- polices
def nom_css(paquet):
    return " ".join(w.capitalize() for w in paquet.split("-")).replace("Dm ", "DM ").replace("Ibm", "IBM")

def choisir_polices(famille, slug, journal):
    jeux = FAMILLES[famille]["polices"]
    recents = "\n".join(journal.strip().splitlines()[-10:]) if journal else ""
    depart = int(hashlib.md5(slug.encode()).hexdigest(), 16) % len(jeux)
    for i in range(len(jeux)):
        jeu = jeux[(depart + i) % len(jeux)]
        if nom_css(jeu[0][1]) not in recents:
            return jeu
    return jeux[depart]

# ---------------------------------------------------------------- horaires
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

def verifier_horaires(h):
    for j in JOURS:
        for plage in h.get(j, []):
            if not re.fullmatch(r"\d{2}:\d{2}-\d{2}:\d{2}", plage):
                sys.exit(f"Horaire mal formé pour {j} : « {plage} » (attendu HH:MM-HH:MM)")

# ---------------------------------------------------------------- rendu
def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    dossier = Path(sys.argv[1])
    fiche = json.loads((dossier / "fiche.json").read_text(encoding="utf-8"))
    fam = fiche.get("famille")
    if fam not in FAMILLES:
        sys.exit(f"Famille inconnue « {fam} ». Choix : {', '.join(FAMILLES)}")
    for k in ("slug", "nom", "activite", "ville", "adresse", "cp_ville", "tel", "tel_affiche", "hero", "photos", "horaires"):
        if not fiche.get(k):
            sys.exit(f"Champ manquant dans fiche.json : {k}")
    verifier_horaires(fiche["horaires"])
    imgs = {p.stem for p in (dossier / "img").glob("*")}
    cles = [fiche["hero"]] + [p["img"] for p in fiche["photos"]] + ([fiche["logo"]] if fiche.get("logo") else [])
    for extra in ("bloc2", "commande"):
        if fiche.get(extra, {}).get("img"):
            cles.append(fiche[extra]["img"])
    for it in (fiche.get("moment") or {}).get("items", []):
        cles.append(it["img"])
    manquantes = sorted({k for k in cles if k not in imgs})
    if manquantes:
        sys.exit(f"Images manquantes dans img/ : {', '.join(manquantes)}")

    journal = (ICI / "journal-design.md").read_text(encoding="utf-8") if (ICI / "journal-design.md").exists() else ""
    polices = choisir_polices(fam, fiche["slug"], journal)
    if fiche.get("polices"):  # forcer un jeu précis : liste d'indices de FAMILLES[fam]["polices"]
        polices = FAMILLES[fam]["polices"][int(fiche["polices"])]
    c = palette(fiche, dossier)

    faces, fonts_json, roles = [], [], {}
    for cle, paquet, var, style, poids in polices:
        fonts_json.append({"key": cle, "family": paquet, **({"variable": True} if var else {"weight": poids}), **({"style": style} if style != "normal" else {})})
        faces.append({"key": cle, "css": nom_css(paquet), "style": style, "poids": "100 900" if var else str(poids)})
        roles.setdefault(cle.rstrip("0123456789"), nom_css(paquet))

    resa = fiche.get("resa_url")
    cfg = FAMILLES[fam]
    if resa:
        cta = {"href": resa, "label": fiche.get("resa_label") or "Réserver", "ext": True}
    elif fam == "artisan" and fiche.get("email"):
        cta = {"href": "#devis", "label": cfg["cta"], "ext": False}
    else:
        cta = {"href": "tel:" + fiche["tel"], "label": cfg["cta"] if fam != "restaurant" else "Appeler", "ext": False}

    dest = fiche.get("maps_dest") or f'{fiche["nom"]}, {fiche["adresse"]}, {fiche["cp_ville"]}'
    from urllib.parse import quote
    itin = "https://www.google.com/maps/dir/?api=1&destination=" + quote(dest)

    env = Environment(loader=FileSystemLoader(str(MODELES)), autoescape=True, undefined=ChainableUndefined,
                      block_start_string="[%", block_end_string="%]",
                      variable_start_string="[[", variable_end_string="]]",
                      comment_start_string="[#", comment_end_string="#]",
                      trim_blocks=True, lstrip_blocks=True)
    env.globals["img"] = lambda k: "{{img:%s}}" % k
    f = dict(fiche)
    f.setdefault("description", f'{fiche["activite"]} à {fiche["ville"]}. {fiche["adresse"]}, {fiche["cp_ville"]}.')
    nav = [(i, l) for i, l in cfg["nav"] if not (i == "maison" and not fiche.get("bloc2"))]
    html = env.get_template(f"{fam}.html.j2").render(
        f=f, c=c, faces=faces, roles=roles, famille=fam, nav=nav, cta=cta, itin=itin,
        intro_ms=cfg["intro_ms"])
    html = re.sub(r"\n\s*\n+", "\n", html)
    (dossier / "src.html").write_text(html, encoding="utf-8")
    (dossier / "site.json").write_text(json.dumps({"fonts": fonts_json, "horaires": fiche["horaires"]}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{dossier}/src.html : famille {fam}, titres {roles.get('titre')}, texte {roles.get('texte')}, couleur {c['principale']}")

if __name__ == "__main__":
    main()
