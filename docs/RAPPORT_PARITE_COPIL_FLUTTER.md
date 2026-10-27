# Contrôle de correspondance COPIL : web et Flutter

## Références consultées avant correction

- Captures fournies dans `Pictures/Screenshots/copil` : Directoire Flutter,
  organisation web, COPIL et Secrétariat technique, thèmes clair et sombre.
- Templates `templates/pilotage/dashboard.html`, `templates/pilotage/app/`,
  `templates/pilotage/organisation.html` et leurs composants.
- Visualisation Chromium du serveur Django local sur le port 1111.

## Corrections réalisées

- En-tête Pilotage : bande tricolore, logo, navigation à gauche, actions à
  droite sur une même ligne, dimensions et variante compacte.
- Directoire : fonctions du titulaire connecté, suppression du sélecteur
  générique des cinq postes et du bloc de présentation absent du template,
  navigation par fonction et accès à l'organisation et à la supervision.
- Organisation : navigation COPIL / Secrétariat technique / sous-commissions /
  journal, tableaux et compteurs issus de la version courante, surfaces et
  espacements adaptés aux références.
- Actions d'organisation : formulaires de modification, ajout de poste et
  nomination issus des formulaires web Phoenix ; validations et journalisation
  conservées. Les ressources Phoenix restent distinctes des actions historiques.
- Panneaux Pilotage : dossiers réels, actions de cadrage, réception, adhésion
  et dérogation avec état d'envoi et restitution des erreurs serveur.
- Cartes de sous-commissions cliquables, profil personnel modifiable,
  consultation des instructions et accès aux sessions de l'assistant IA.
- Le volet global « Donner une instruction » reproduit l'état « Non disponible »
  du template web ; il ne simule pas un envoi.
- URL API locale par défaut : `http://127.0.0.1:1111`, surcharge
  `--dart-define=API_BASE_URL=...`. Origines Flutter locales autorisées sur 8082.

## Vérifications

- Analyse statique ciblée de l'espace Pilotage et des modifications API/routage.
- 9 tests Flutter : alignement de l'en-tête à 1440, 1024 et 390 pixels, volet
  d'instruction, fonctions du titulaire, organisation, profil/compteurs API et
  transmission des valeurs d'un formulaire.
- 6 tests API : permissions, demandes réelles, validation et persistance des
  réponses, conflits, formulaires d'organisation et journalisation.
- 3 tests Phoenix existants : formulaires et exports, renouvellement de mandat,
  correction des dates affichées sans réécriture des horodatages d'audit.
- `manage.py check` et compilation Flutter web.
- Script Chromium : `scripts/check_copil_browser.py --flutter` ; serveur web sur
  1111 et build Flutter servi sur 8082. Captures locales dans
  `reports/copil_parity/`.

La comparaison visuelle porte sur les écrans cités, à viewport identique.
Elle ne constitue pas une mesure automatisée d'identité pixel par pixel de
toutes les pages, des graphiques de l'assistant ou des écrans spécialisés des
autres collèges. Aucun appel réel au fournisseur IA n'est nécessaire aux tests.
