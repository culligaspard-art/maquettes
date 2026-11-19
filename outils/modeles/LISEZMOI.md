# Modèles de sites par métier

`python3 outils/modele.py chantier/<slug>` lit `chantier/<slug>/fiche.json` et écrit `src.html` et `site.json`. Ensuite `python3 outils/build.py chantier/<slug>` assemble le site, et `python3 outils/shots.py …` le contrôle, comme pour un site sur mesure.

## Familles

| famille | pour | ouverture « wow » |
|---|---|---|
| `beaute` | onglerie, institut, coiffure, barbier, esthétique | une forme (`forme`: `ongle` ou `miroir`) se remplit de couleur, reflet, puis s'ouvre sur le site |
| `emporter` | pizzeria, snack, burger, kebab, traiteur, food truck | la boîte s'ouvre, le plat tourne, vapeur |
| `patisserie` | boulangerie, pâtisserie, chocolatier, salon de thé, glacier | la nappe vichy s'ouvre sur une plaque ovale au nom de la maison |
| `restaurant` | restaurant, winstub, brasserie, bar, crêperie | rideau sombre, sceau (logo ou initiale), anneaux, ouverture en iris ; braises dans le hero |
| `artisan` | menuisier, charpentier, plombier, électricien, maçon, peintre, couvreur, carreleur, serrurier, paysagiste, garage | un plan se dessine (`dessin`: `toit` ou `plan`), le nom est tamponné, le plan glisse |
| `commerce` | boucherie, fromagerie, épicerie, primeur, caviste, fleuriste, cordonnerie, pressing, toiletteur, auto-école | le rideau métallique peint au nom du commerce se lève |

Les polices sont choisies automatiquement dans la famille, en évitant celles des 10 derniers sites du journal (`"polices": <indice>` pour forcer). Les couleurs viennent du logo, sinon de la photo principale (`"couleurs": {"principale": "#…", "accent": "#…"}` pour forcer : à faire dès qu'une couleur de marque est évidente).

## fiche.json

Champs obligatoires : `slug`, `famille`, `nom`, `activite`, `ville`, `adresse`, `cp_ville`, `tel` (format +33…), `tel_affiche`, `hero` (clé d'image), `photos` (liste), `horaires`.

```json
{
  "slug": "nom-du-commerce", "famille": "beaute", "forme": "ongle",
  "nom": "Nom du commerce", "activite": "Institut de beauté", "ville": "Ville",
  "adresse": "8 rue …", "cp_ville": "68600 Ville",
  "tel": "+33685565430", "tel_affiche": "06 85 56 54 30", "email": "…",
  "resa_url": null, "facebook": "https://…", "instagram": "https://…",
  "note": "4,6", "avis": 36, "preuve_extra": "recommandé à 96 % sur Facebook",
  "logo": "logo", "logo_blanc": "logo-blanc", "hero": "photo-principale", "hero_alt": "…", "hero_pos": "50% 40%",
  "accroche": "Institut de beauté à Ville", "titre_lignes": ["Arrêt", "Beauté"], "slogan": "Phrase tirée du commerce.",
  "offre_titre": "Les soins", "offre_intro": "…",
  "offre": [{"titre": "Onglerie", "texte": "…", "prix": "35 €"}],
  "offre_groupes": [{"titre": "Base tomate", "items": [{"titre": "…", "texte": "…", "prix": "11,00 €"}]}],
  "notes": [{"k": "Sans gluten", "v": "…"}],
  "photos": [{"img": "cle", "alt": "…", "titre": "…", "texte": "…", "pos": "50% 60%"}],
  "bloc2": {"titre": "La maison", "texte": "…", "img": "cle", "faits": [{"k": "1936", "v": "…"}]},
  "moment": {"titre": "La pizza du moment", "intro": "…", "items": [{"img": "cle", "titre": "…", "texte": "…"}]},
  "commande": {"titre": "Commander un gâteau", "texte": "…", "img": "cle"},
  "encart": {"titre": "Soirées à volonté", "texte": "…"},
  "zone": "Colmar et 30 km autour", "devis_texte": "…", "dessin": "toit",
  "nom_plaque": "Birké", "ruban": "depuis 1936", "kraft": "#D6B998",
  "horaires": {"lundi": [], "mardi": ["09:00-12:00", "14:00-18:30"], "mercredi": [], "jeudi": [], "vendredi": [], "samedi": [], "dimanche": []}
}
```

Champs utiles par famille :
- `beaute` : `forme`, `logo_blanc` (logo blanc pour l'ouverture), `offre`, `photos` (jusqu'à 7, la galerie), `bloc2` (bandeau sombre avec une photo).
- `emporter` : `offre_groupes` (la carte avec les prix), `notes`, `moment`, `etapes` (facultatif), `hero` = un plat vu de dessus si possible (il tourne).
- `patisserie` : `nom_plaque` (nom court sur la plaque), `ruban`, `photos` (6, la vitrine), `bloc2` (obligatoire, la maison), `commande`.
- `restaurant` : `offre` (plats), `encart`, `photos` (la 1re à côté de la carte, les 5 suivantes en mosaïque), `bloc2`, `resa_url`.
- `artisan` : `offre` (services), `photos` (réalisations), `zone`, `bloc2.faits`, `dessin`.
- `commerce` : `photos` (l'étal, 3 à 6 avec titre), `offre` (liste simple), `bloc2` (la maison), `hero_legende`.

Rien d'inventé : chaque texte vient d'une source publique du commerce, sinon il reste générique pour le métier.
- `nav_labels` : renomme les entrées du menu, par ex. `{"soins": "Les prestations"}`.
