# Console CNE-ITP — première page de référence : Experts

## Architecture conservée

La console reste rendue par Django, avec CSS et JavaScript natif. Aucune
bibliothèque UI ni étape de build supplémentaire n'est nécessaire. Les routes,
endpoints API, modèles, permissions, authentification et formulaires CRUD
existants sont conservés.

`console_experts.py` adapte uniquement la liste. Les indicateurs et le tableau
utilisent le queryset du ModelAdmin existant, afin de conserver son périmètre.
Les structures et les adhésions sont chargées depuis les données réelles ;
aucun chiffre de démonstration n'est utilisé.

## Socle visuel partagé

Les tokens sont centralisés dans `templates/static/css/console-admin.css` :

| Usage | Valeur claire |
| --- | --- |
| Fond | `#F4F8FC` |
| Surface | `#FFFFFF` |
| Navigation | `#101F35` |
| Accent | `#008FC5` |
| Bordure | `#DCE8F3` |
| Texte | `#13263E` |
| Texte secondaire | `#64748B` |
| Rayon des cartes | 18 à 20 px |
| Rayon des contrôles | 11 px |
| Échelle d'espacement | 4, 8, 12, 16, 24, 32 px |

Les surfaces de cadrage utilisent un flou léger avec transparence modérée dans
un bloc `@supports`. Le fallback est opaque. Les lignes du tableau restent
opaques. Les styles communs prennent également en charge le thème sombre,
le focus visible et `prefers-reduced-motion`.

La navigation conserve ses liens et dispose d'un rail compact sur tablette.
Le menu mobile gère le focus, Échap, le retour au bouton d'ouverture et
l'inactivité des liens lorsqu'il est fermé.

## Annuaire des experts

- Fil d'Ariane, titre, description et action de création explicite.
- Indicateurs réels : total, actifs, en attente, inactifs ou suspendus.
- Indicateur facultatif de profils à compléter : uniquement si des dossiers de
  suivi existent et si l'utilisateur possède `experts.view_profileupdate`.
  Le compte correspond aux états `NOT_STARTED`, `IN_PROGRESS` et
  `NEEDS_CORRECTION`, sans déduire la complétude à partir de champs manquants.
- Recherche existante, statut, structures multiples avec recherche locale,
  comité/affectation, période de nomination et réinitialisation.
- Badges actifs supprimables individuellement et conservation des raccourcis
  historiques de date et du lien `?status=PENDING`.
- Table en français : identité et email regroupés, structure, badge de statut,
  comité/affectation, date de nomination, présences et menu d'actions.
- Actions vers les fiches et formulaires existants, selon leurs permissions.
- En-tête fixe dans une zone défilable, sans élargir la page sur mobile.
- Pagination conservant les filtres, avec 25, 50 ou 100 lignes par page.
- État vide explicite et état de soumission « Chargement… ».

Le composant `partials/metric.html` et les tokens partagés peuvent être
réutilisés pour les autres pages de la console. Leur contenu métier n'a pas
été remplacé par une nouvelle interface dans cette première étape.

## Vérifications effectuées

```powershell
.\mon_env\Scripts\python.exe manage.py check
node --check templates/static/js/console.js
.\mon_env\Scripts\python.exe -m pytest apps/dashboard/test_console.py apps/dashboard/test_expert_directory.py -q --reuse-db
.\mon_env\Scripts\python.exe scripts/check_console_experts_browser.py --verify
```

Les 24 tests vérifient notamment les statistiques, les filtres combinés,
les structures multiples, les adhésions, les dates historiques, les
paramètres vides, la pagination et les permissions de lecture seule.

Le script Chromium vérifie les vues 1440, 1024 et 390 pixels, l'en-tête fixe,
les filtres, leurs badges, les menus d'actions au clavier, le menu mobile et
les thèmes. Les captures sont produites localement dans
`reports/console_experts_redesign/`.

Après déploiement, exécuter `collectstatic` et redémarrer le serveur applicatif
selon la procédure habituelle pour recharger les métadonnées WhiteNoise.
