# Feux du Cameroun, MODIS et VIIRS harmonisés

NASA Space Apps Challenge 2026, défi « Harmonisation des points chauds MODIS et VIIRS ».

Application web statique (une page, `index.html`, Leaflet par CDN, sans serveur) qui montre, pour tout
le Cameroun, un calendrier mois × année des points chauds de feu de 2012 à 2026. La vue principale est
l'**anomalie** de chaque mois par rapport à sa **médiane historique** (2012 à 2025). Une carte montre
les détections par cellule de 0,5° pour l'année et les mois choisis. Les valeurs affichées s'exportent
en CSV.

## Ouvrir l'application

Double-cliquer sur `index.html` (les données sont dans `donnees.js`, aucun serveur n'est nécessaire).
Le fond de carte et Leaflet viennent d'Internet ; sans connexion, le calendrier et l'export marchent
quand même. Autre possibilité : `python -m http.server 8000`, puis http://localhost:8000.

## Sources

- **NASA FIRMS** (Fire Information for Resource Management System), téléchargements par pays (Cameroun) :
  - MODIS Collection 6.1 (Aqua et Terra), 1 km : `DL_FIRE_M-C61`
  - VIIRS 375 m S-NPP : `DL_FIRE_SV-C2` ; NOAA-20 : `DL_FIRE_J1V-C2` ; NOAA-21 : `DL_FIRE_J2V-C2`
  - pour chacun, une archive (données définitives) et un fichier NRT (temps quasi réel).
- Citation : « We acknowledge the use of data and imagery from LANCE FIRMS operated by NASA's Earth
  Science Data and Information System (ESDIS) with funding provided by NASA Headquarters. »
  https://firms.modaps.eosdis.nasa.gov
- Fond de carte : © contributeurs OpenStreetMap.

Couvertures réelles des fichiers (vérifiées par `inspect_archives.py`) :

| Capteur | Archive | NRT |
|---|---|---|
| MODIS (Aqua, Terra) | 2012-01-20 → 2026-08-29 | 2026-09-09 → 2026-11-13 |
| S-NPP | 2012-01-20 → 2026-07-31 | 2026-08-01 → 2026-11-02 |
| NOAA-20 | 2018-04-01 → 2026-07-31 | 2026-08-01 → 2026-11-13 |
| NOAA-21 | 2023-03-01 → 2026-07-31 | 2026-08-01 → 2026-11-13 |

## Décisions

1. **Série principale : S-NPP seule, sans addition des capteurs.** S-NPP, NOAA-20 et NOAA-21 passent
   souvent au-dessus du même feu à quelques minutes d'intervalle : additionner leurs détections
   compterait deux ou trois fois le même feu. Plutôt qu'un dédoublonnage spatio-temporel (fragile et
   lent), S-NPP est figée comme série principale : c'est la seule série VIIRS qui couvre 2012 à 2026.
   NOAA-20 et NOAA-21 servent **seulement à vérifier** cette série (voir Résultats).
2. **Confiance « nominale et haute » sur une échelle commune.** VIIRS donne `l`/`n`/`h`. MODIS donne
   0-100, converti avec les seuils FIRMS : bas < 30, nominal 30-79, haut ≥ 80. Les détections basses
   sont écartées pour les deux capteurs.
3. **Archive : `type = 0` seulement** (feu de végétation présumé), ce qui écarte les volcans, les sources
   fixes terrestres et le large (torchères). Les fichiers NRT n'ont pas cette colonne : ils gardent
   tout. Effet mesuré sur l'archive S-NPP : 0,42 % des détections seulement.
4. **Calibration MODIS → équivalent S-NPP par année, jamais une constante.** Pour chaque année :
   facteur = détections S-NPP / détections MODIS, sur les mois complets pour les deux capteurs et non
   provisoires. Une année sans recouvrement prendrait le facteur de l'année la plus proche (signalé).
5. **Mois incomplets écartés, pas extrapolés.** Un mois n'a de valeur pour un capteur que s'il est
   couvert du premier au dernier jour : janvier 2012 (début le 20), novembre 2026 pour S-NPP (fin du
   NRT le 2 novembre), août et septembre 2026 pour MODIS (trou).
6. **Médiane historique** de chaque mois du calendrier sur 2012-2025 (167 mois de référence, sans les
   mois incomplets ni provisoires). Anomalie = (valeur − médiane) / médiane × 100.
7. **Données provisoires** : tout mois qui contient des données NRT, et les 5 derniers mois (juillet à
   novembre 2026). Ils sont hachurés et signalés par un bandeau ; l'année 2026 est marquée incomplète.
8. **Palette « cividis »** (8 classes), lisible par les daltoniens et ordonnée en niveaux de gris.
   Vérifiée par `check_palette.py` (gris de 30 à 224, écart d'au moins 22 entre deux classes) et par
   une capture de la page en niveaux de gris. Chaque case porte aussi sa valeur en chiffres.

## Limites

- **Trou MODIS du 30 août au 8 septembre 2026** (aucune donnée, ni archive ni NRT) : août et septembre
  2026 n'ont pas de valeur MODIS. Signalé dans l'application. La série S-NPP n'est pas touchée.
- **Facteur 2026 = 5,94, calculé sur 6 mois** (janvier à juin). Il sort nettement de la plage
  2012-2025 (3,95 à 4,69) : à lire avec prudence (année incomplète, possible effet de la fin de vie de
  Terra). L'équivalent MODIS 2026 en dépend.
- **Saison des pluies** (juin à septembre) : la médiane tombe sous 500 détections, parfois sous 300 ;
  quelques dizaines de détections suffisent alors à donner ±70 %. L'application le rappelle dans le
  détail du mois.
- Une détection n'est pas un feu : un grand feu donne plusieurs pixels, un petit feu sous les nuages
  n'en donne aucun. Les comptes mesurent l'activité détectée, pas des surfaces brûlées.
- Les fichiers NRT n'ont pas la colonne `type` : les mois NRT peuvent compter quelques sources fixes
  en plus (de l'ordre de 0,4 % d'après l'archive).
- Les erreurs de géolocalisation au bord du pays (fenêtre FIRMS par pays) ne sont pas corrigées.

## Résultats clés

- **Facteur S-NPP/MODIS** : 4,01 (2012) → 4,69 (2025), moyenne 4,30, écart-type 0,23 (14 années
  complètes). Il **augmente** depuis 2020 (4,12 → 4,69) : une constante unique biaiserait la
  comparaison entre les deux époques, d'où le facteur par année.
- **Vérification de la série principale** sur les mois de référence : NOAA-20 corrélation 0,999 avec
  S-NPP (93 mois), rapport 1,00 ; NOAA-21 corrélation 0,998 (34 mois), rapport 0,96. La série S-NPP
  est donc stable et cohérente avec les deux autres VIIRS, sans doublons ajoutés.
- **Saisonnalité** : la saison des feux va de novembre à mars (médianes : janvier 52 007, février
  55 432, décembre 42 407 détections) ; juillet à septembre en compte moins de 250.
- **Total annuel S-NPP** : de 153 503 (2013) à 208 332 (2020), le maximum ; 189 714 en 2025.
- **2026** : janvier (−25 %) et février (−32 %), les mois les plus actifs, sont sous la médiane ; mars
  (+42 %) au-dessus. Juillet à novembre 2026 sont provisoires.

## Reproduire

Prérequis : Python 3.13 (pandas n'a pas encore de version pour 3.15) et pandas.

```
pip install pandas
python test_harmonize.py      # 10 tests sur données synthétiques
python inspect_archives.py    # contrôle des fichiers réels de data/ (dates, satellites, confiance, trous)
python harmonize.py           # écrit aggregats.json, grille.json et donnees.js
python check_palette.py       # palette en niveaux de gris
```

`data/` (archives FIRMS brutes, non versionnées) : télécharger depuis
https://firms.modaps.eosdis.nasa.gov/download/ les archives « Country : Cameroon » MODIS C6.1 et VIIRS
S-NPP, NOAA-20, NOAA-21, et les extraire dans `data/modis`, `data/snpp`, `data/noaa20`, `data/noaa21`.
Aucune clé API n'est utilisée.

## Fichiers

| Fichier | Rôle |
|---|---|
| `index.html` | application (carte, calendrier, export CSV) |
| `donnees.js` | agrégats chargés par la page (même contenu que les deux JSON) |
| `aggregats.json` | mois × année : S-NPP, MODIS, équivalent S-NPP, facteur, NOAA-20/21, médiane, anomalie, provisoire, complétude |
| `grille.json` | détections S-NPP par cellule de 0,5° et par mois (carte) |
| `harmonize.py` | chargement, confiance commune, filtres, calibration, médianes, anomalies |
| `test_harmonize.py` | tests unitaires |
| `inspect_archives.py` | inspection des fichiers réels |
| `check_palette.py` | vérification de la palette en niveaux de gris |

## Licence des données

Données NASA FIRMS : libres d'utilisation avec citation (voir ci-dessus). Fond de carte OpenStreetMap :
ODbL.
