# Méthode mathématique

Cameroon Fire Calendar — équipe WESH, Kenmoe Kahadjie Felix (NASA Space Apps 2026).

Ce document décrit chaque formule réellement présente dans le code, avec le fichier qui la porte, ce qu'elle calcule, pourquoi elle est préférée aux alternatives, et sa limite connue. Les chiffres cités ont été vérifiés contre `aggregats.json` et `python validate.py`.

## Notations

- Un mois : couple `(a, m)` avec `a` année et `m` mois (1 à 12).
- `N_s(a, m)` : nombre de détections du capteur `s` retenues ce mois-là (confiance nominale ou haute, archive type 0 seulement).
- Capteurs : S = Suomi NPP (VIIRS 375 m, série principale) ; M = MODIS (Aqua + Terra, Collection 6.1) ; N20, N21 = NOAA-20 et NOAA-21.

## 1. Échelle commune de confiance

**Fichier :** `harmonize.py`, fonctions `normalize_confidence` et `filter_detections`.

MODIS donne la confiance en entier de 0 à 100 ; VIIRS donne `l` (low), `n` (nominal), `h` (high). On ramène les deux à trois niveaux `{0, 1, 2}` :

- MODIS : `niveau = 0 si c < 30 ; 1 si 30 ≤ c < 80 ; 2 si c ≥ 80`
- VIIRS : `l → 0, n → 1, h → 2`

Puis on garde seulement `niveau ≥ 1` (nominale ou haute).

**Pourquoi.** Les deux capteurs ne codent pas la confiance de la même façon. Les seuils 30 et 80 sont ceux documentés par NASA FIRMS pour MODIS. Les détections de niveau bas sont majoritairement des faux positifs (fumées, eau chaude, réflexions), on les écarte pour ne pas biaiser les comptages.

**Limite.** Le seuil est binaire : une détection à 79 (MODIS) passe, une à 81 aussi, mais la seconde n'est pas beaucoup plus fiable.

## 2. Filtre d'archive : type 0 seulement

**Fichier :** `harmonize.py`, `filter_detections`.

Dans les fichiers d'archive, chaque détection a un champ `type` : 0 feu de végétation présumé, 1 volcan, 2 autre source statique, 3 offshore. On garde `type = 0`.

**Pourquoi.** On mesure l'activité des feux, pas celle des volcans ou des torchères. Mesuré sur l'archive S-NPP du Cameroun : 0,42 % des détections sont `type ≠ 0`.

**Limite.** Les fichiers NRT (near real time, temps quasi réel) n'ont pas de colonne `type`. Les mois NRT peuvent donc inclure quelques sources statiques — environ 0,4 % d'après la mesure ci-dessus. C'est l'une des raisons pour lesquelles les mois NRT sont marqués provisoires (voir §7).

## 3. Comptage mensuel et complétude

**Fichier :** `harmonize.py`, `monthly_counts` et `coverage_flags`.

Pour chaque capteur, on groupe les détections par `(a, m)` et on compte. Un mois est marqué complet pour un capteur si la couverture du capteur recouvre le mois entier (et, pour MODIS, ne tombe pas dans le trou du 30 août au 8 septembre 2026).

**Pourquoi.** Un mois à moitié couvert donnerait un chiffre non comparable aux autres années. On ne tire pas de valeur dans ce cas : un mois incomplet reste vide dans le calendrier et dans le CSV, il n'est **pas extrapolé**. C'est plus honnête que de normaliser par le nombre de jours : une activité très saisonnière (février contient la pointe) ne se ramène pas à un taux journalier.

## 4. Facteur de recalage MODIS → équivalent S-NPP, par année

**Fichier :** `harmonize.py`, `yearly_ratio` et `ratio_for`.

Pour chaque année `a` dont les deux capteurs ont au moins `MIN_CALIBRATION_MONTHS = 11` mois complets communs, on calcule

```
k_a = Σ_m N_S(a, m) / Σ_m N_M(a, m)
```

sur les mois complets pour les deux capteurs et non provisoires. L'équivalent MODIS d'un mois vaut `round(N_M(a, m) × k_a)`.

Une année partielle (par exemple 2026 avec six mois) prend le facteur de l'année calibrée la plus proche.

**Pourquoi un ratio de sommes et non une moyenne de ratios mensuels.** Un ratio de sommes pondère naturellement par le nombre de feux : les mois de haute saison, où les deux capteurs voient beaucoup, dominent le facteur ; les mois de saison humide, où un ratio mensuel peut être `3 / 1 = 3` ou `0 / 0` indéfini, ne déséquilibrent rien.

**Pourquoi par année et pas une seule constante.** Les facteurs vont de 4,008 (2012) à 4,693 (2025) et **montent** après 2020 (4,120 → 4,693). Une constante biaiserait toute comparaison entre les deux périodes. La hausse est probablement liée à la dégradation du capteur MODIS sur Terra (fin de vie), qui détecte moins de feux à nombre constant réel.

**Pourquoi un seuil de 11 mois.** 2012 commence le 20 janvier dans les archives FIRMS, soit 11 mois complets (février à décembre) : on veut inclure 2012. 2026 n'a que six mois complets (janvier à juin), ce qui donne un facteur de 5,942, bien hors de la plage 2012-2025 (3,951 à 4,693) ; on ne l'applique pas.

**Validation.** Voir §6 (test par année laissée de côté).

**Limite.** 2026 utilise 4,693 (facteur 2025) : c'est une estimation, pas une mesure sur l'année en cours. L'équivalent MODIS de 2026 est donc à lire avec cette convention en tête ; la table de calibration affiche `used = no` pour 2026 pour le signaler.

## 5. Médiane saisonnière et anomalie en pourcentage

**Fichier :** `harmonize.py`, `month_medians` et `anomaly_pct`.

Pour chaque mois calendaire `m ∈ {1, …, 12}`, on calcule la médiane

```
µ_m = médiane { N_S(a, m) : a ∈ 2012…2025, (a, m) mois de référence }
```

où un mois de référence est complet pour S-NPP, non provisoire, et antérieur à la dernière année (167 mois au total). Puis pour chaque mois affiché :

```
anomalie(a, m) = (N_S(a, m) − µ_m) / µ_m × 100
```

Si `µ_m = 0`, l'anomalie est indéfinie (affichée comme vide).

**Pourquoi la médiane et non la moyenne.** Les mois de haute saison ont des valeurs très étalées. Février 2023 vaut 90 395 détections contre une médiane de 55 432 ; une moyenne serait tirée vers le haut par cet événement et tous les autres mois paraîtraient « bas ». La médiane est robuste à ces pointes.

**Pourquoi exclure la dernière année de la référence.** On ne veut pas qu'une année en cours (ou tout juste finie) décide de son propre « niveau habituel ». La référence 2012-2025 décide ; 2026 est comparée à cette référence.

**Pourquoi pas en z-score.** Un z-score suppose une distribution approximativement normale. Les comptages de feux sont très skewés (concentration en haute saison) ; une anomalie en pourcentage reste lisible même pour un non-statisticien.

**Limite.** En saison des pluies, la médiane est faible (septembre : 104 détections). Quelques dizaines de détections donnent ±70 %, ce qui paraît spectaculaire mais ne l'est pas. L'application le dit dans le détail du mois (seuil `µ_m < 500`).

## 6. Erreur hors échantillon (leave-one-year-out)

**Fichier :** `validate.py`, fonctions `predictors`, `held_out_errors`.

Pour chaque année `a ∈ 2013…2025`, on prédit `k_a` sans utiliser `a`, par trois méthodes :

- **constant** : `Σ N_S(a', ·) / Σ N_M(a', ·)` sur toutes les années `a' ≠ a` ;
- **neighbours** : moyenne de `k_{a−1}` et `k_{a+1}` quand ils existent ;
- **trend** : régression linéaire de `(a', k_{a'})` sur `a' ≠ a` par moindres carrés — pente `Σ (x − x̄)(y − ȳ) / Σ (x − x̄)²`, puis prédiction `ȳ + pente × (a − x̄)`.

L'erreur relative est `|prédiction − k_a| / k_a`. On rapporte la moyenne et le maximum sur les 13 années.

Résultats (reproduits par `python validate.py`) :

| Méthode | Erreur moyenne | Erreur maximum |
|---|---|---|
| constant | 4,49 % | 10,03 % |
| neighbours | 3,25 % | 7,24 % |
| trend | 3,12 % | 6,60 % |

Une quatrième variante (Aqua seulement : MODIS restreint au satellite Aqua, même heure de passage que VIIRS) donne 2,48 % mais exige les fichiers bruts non versionnés.

**Pourquoi laisser l'année cible de côté.** Prédire le facteur d'une année avec les données de cette même année ne mesure pas la robustesse : on mesurerait l'ajustement, pas la généralisation. Laisser l'année hors du calcul simule l'ajout d'une année inconnue.

**Pourquoi tester trois méthodes.** La méthode publiée utilise le facteur de chaque année (meilleure que toutes celles-ci sur les mois complets). Les trois alternatives montrent ce qui se passerait si on devait prédire : la différence entre constant (4,49 %) et trend (3,12 %) justifie la montée documentée du facteur dans le temps, et la variante Aqua seulement (2,48 %) donne une piste d'amélioration pour une future itération.

**Limite.** Ce test porte sur les années entières. Pour une année partielle comme 2026, aucune de ces méthodes n'est appliquée telle quelle : 2026 utilise le facteur 2025 (la méthode « année précédente »), choix conservateur à défaut de mesure sur l'année courante.

## 7. Contrôle croisé avec NOAA-20 et NOAA-21

**Fichier :** `harmonize.py`, bloc `verification` dans `build`.

Sur les mois complets pour S-NPP et le capteur comparé (et non provisoires), on calcule :

- la **corrélation de Pearson** `r(S, X)` entre les séries mensuelles ;
- le **rapport des totaux** `Σ N_X / Σ N_S`.

Résultats (`aggregats.json`) :

| Capteur | Mois | Corrélation avec S-NPP | Rapport au total S-NPP |
|---|---|---|---|
| NOAA-20 | 93 | 0,999 | 0,996 |
| NOAA-21 | 34 | 0,998 | 0,961 |

**Pourquoi pas additionner S, N20 et N21.** Les trois capteurs VIIRS passent au-dessus du Cameroun à des heures voisines et détectent très souvent le même feu. Les additionner compterait deux ou trois fois chaque feu. La corrélation à 0,999 montre que les séries sont essentiellement la même information ; on prend S-NPP comme référence (plus longue couverture, 2012-aujourd'hui) et on s'en sert des deux autres uniquement comme contrôle.

**Pourquoi la corrélation de Pearson et pas Spearman.** On compare des grandeurs dans la même unité (nombre de détections) ; Pearson mesure la cohérence proportionnelle, qui est ce qu'on veut : si S voit 50 000 et N20 voit 49 800, on veut que ça passe le test.

## 8. Grille spatiale

**Fichier :** `harmonize.py`, `grid_counts`.

Pour la carte, on regroupe les détections S-NPP par cellule de `0,5°` de côté, par mois :

```
cell(latitude, longitude) = (⌊lat / 0,5⌋ × 0,5 , ⌊lng / 0,5⌋ × 0,5)
```

**Pourquoi cette taille de cellule.** 0,5° au Cameroun vaut environ 55 km à l'équateur. Plus fin que ça, les cellules sont peu peuplées en saison humide ; plus grossier, la carte perd l'information régionale (Nord vs Adamaoua vs Sud). On ne publie aucune détection individuelle (seulement des sommes) pour que le dépôt ne rejoue pas FIRMS.

## 9. Règle des mois provisoires

**Fichier :** `harmonize.py`, variable `provisional`.

Un mois est marqué **provisoire** s'il contient des données NRT **ou** s'il fait partie des cinq derniers mois de la couverture. Les mois provisoires sont hachurés dans la page, exclus de la référence historique, et signalés dans l'export CSV.

**Pourquoi cinq mois.** NASA republie périodiquement les archives, et les cinq derniers mois peuvent encore recevoir des mises à jour (consolidation des détections NRT en archive, corrections de géolocalisation). Un mois NRT clairement, mais aussi un mois d'archive très récent, ne sont donc pas des valeurs définitives.

## Classes de couleur (affichage uniquement)

L'affichage utilise la palette Cividis en 8 classes, avec des bornes différentes selon la vue :

- **Vue « anomalie »** : classes fixes aux seuils −60, −30, −10, +10, +30, +60, +100 %, lisibles directement (un rouge ne vient pas d'un quantile, il vient d'un vrai +60 %).
- **Vue « détections »** : classes par quantiles sur les valeurs disponibles, pour utiliser toute la palette sur une distribution très étalée.

**Pourquoi Cividis.** Palette ordonnée en luminance, lisible en niveaux de gris et avec le daltonisme. Vérifiée par `check_palette.py` : niveaux de gris de 30 à 224, au moins 22 d'écart entre deux classes voisines.

## Points à vérifier

- Le script `harmonize.py` complet n'a pas été exécuté dans cette itération (les fichiers FIRMS bruts ne sont pas versionnés). L'édition de `aggregats.json` applique le nouveau `ratio_for`, mais une regénération complète en local, à partir du dossier `data/`, est recommandée avant la soumission finale.
- La variante « Aqua seulement » (2,48 %) est documentée mais non publiée : elle exige de republier `data/modis/` séparé en Aqua et Terra, qu'on ne versionne pas.
