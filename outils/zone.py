#!/usr/bin/env python3
"""Curseur de la tournée sur toute la France.

  python3 outils/zone.py ou-en-est        ville en cours, familles restantes, recherches Maps à lancer
  python3 outils/zone.py fait <famille>   marque la famille comme passée dans la ville en cours
  python3 outils/zone.py ville-epuisee    passe à la ville suivante même s'il reste des familles

Quand les 6 familles d'une ville sont passées, la ville suivante devient la ville en cours.
Le fichier outils/couverture.json garde l'état : le commiter à la fin de chaque lot.
"""
import json, sys, urllib.parse
from pathlib import Path

ICI = Path(__file__).resolve().parent
VILLES = json.loads((ICI / "villes.json").read_text())
ETAT = ICI / "couverture.json"

FAMILLES = {
    "beaute": ["coiffeur", "barbier", "institut de beauté", "onglerie", "esthéticienne"],
    "emporter": ["pizzeria", "kebab", "snack", "traiteur", "food truck", "burger"],
    "patisserie": ["boulangerie", "pâtisserie", "chocolatier", "glacier"],
    "restaurant": ["restaurant", "brasserie", "bar", "crêperie", "restaurant asiatique"],
    "artisan": ["menuisier", "charpentier", "plombier", "électricien", "couvreur", "peintre en bâtiment",
                "carreleur", "serrurier", "maçon", "garage automobile", "paysagiste"],
    "commerce": ["boucherie", "fromagerie", "épicerie fine", "primeur", "fleuriste", "caviste",
                 "cordonnerie", "toiletteur", "auto-école", "photographe"],
}


def charger():
    return json.loads(ETAT.read_text())


def sauver(e):
    ETAT.write_text(json.dumps(e, ensure_ascii=False, indent=2) + "\n")


def ville(e):
    return VILLES[e["index"] % len(VILLES)]


def avancer(e):
    v = ville(e)
    e["villes_terminees"].append(f'{v["dep"]}|{v["nom"]}')
    e["index"] += 1
    e["familles_faites"] = []


def ou_en_est(e):
    v = ville(e)
    reste = [f for f in FAMILLES if f not in e["familles_faites"]]
    print(f'Ville en cours : {v["nom"]} ({v["cp"]}, dép. {v["dep"]}, {v["pop"]} hab.) — {e["index"] + 1}/{len(VILLES)}')
    print("Familles restantes : " + (", ".join(reste) or "aucune"))
    for f in reste:
        print(f"\n[{f}]")
        for m in FAMILLES[f]:
            q = urllib.parse.quote_plus(f'{m} {v["nom"]} {v["cp"]}')
            print(f"  https://www.google.com/maps/search/{q}")
    s = VILLES[(e["index"] + 1) % len(VILLES)]
    print(f'\nVille suivante : {s["nom"]} ({s["cp"]})')


def main():
    e = charger()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ou-en-est"
    if cmd == "ou-en-est":
        ou_en_est(e)
    elif cmd == "fait":
        f = sys.argv[2]
        if f not in FAMILLES:
            sys.exit(f"Famille inconnue : {f}. Choix : {', '.join(FAMILLES)}")
        if f not in e["familles_faites"]:
            e["familles_faites"].append(f)
        if all(x in e["familles_faites"] for x in FAMILLES):
            avancer(e)
        sauver(e)
        ou_en_est(e)
    elif cmd == "ville-epuisee":
        avancer(e)
        sauver(e)
        ou_en_est(e)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
