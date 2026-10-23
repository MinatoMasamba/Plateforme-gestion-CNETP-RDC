# Centre d'intelligence CNE-ITP — conception

## Source et périmètre

La note Cabinet du 23 octobre 2026 sert de référence éditoriale : en-tête institutionnel, message essentiel, sections numérotées, points de vigilance et priorités. Ses chiffres sont une photographie distincte de la base locale et ne sont jamais recopiés comme données en direct. Le référentiel `reorganisation-2026-10-15` demeure `PROPOSED`.

Le rapport Ecosys RDC du 22 octobre 2026 sert de référence à une deuxième page : couverture institutionnelle, quatre indicateurs, définitions, chiffres clés, comparaison des SC, liste nominative filtrable et limites sur les courriels. Les 149/52/47/57 min du rapport source ne sont pas repris comme chiffres courants ; ils sont recalculés ou explicitement laissés sans mesure équivalente.

## Navigation

Tableau de bord statistique → Centre d'intelligence → Vue institutionnelle, Organisation, Experts, Production, Bibliothèque, Observations, Rapports. Une fiche SC mène aux GT et dossiers reliés. Un dossier mène à ses versions et observations. Le retour vers le tableau statistique reste permanent.

La rubrique Experts mène à `/dashboard/intelligence/activite-experts/`, page détaillée inspirée du rapport Ecosys.

## Wireframe

```text
┌─────────────────────────────────────────────────────────────┐
│ CNE-ITP · Centre d'intelligence       [← Tableau de bord]  │
├──────────────┬──────────────────────────────────────────────┤
│ Vue          │ REPUBLIQUE DEMOCRATIQUE DU CONGO             │
│ Organisation │ NOTE DE SITUATION · date d'extraction        │
│ Experts      │ Message essentiel / statut du référentiel   │
│ Production   │ [Experts] [SC] [GT] [Projets]                │
│ Bibliothèque │ Comparaison des sept SC : barres + tableau  │
│ Observations │ Dossiers / points de vigilance              │
│ Rapports     │                                              │
└──────────────┴──────────────────────────────[Interroger IA]─┘
```

## Maquette de référence

Fond ivoire très clair, rail bleu marine, feuille blanche centrale bordée d'un filet bleu pâle. Titres sérif pour la note, texte sans sérif pour les commandes et tableaux. Accent bleu réservé aux actions et aux barres. Sur mobile, les rubriques deviennent une navigation horizontale. Chaque graphique a son tableau de données et sa phrase de lecture.

## Règles de données

- Chiffres recalculés à chaque requête, date d'extraction visible.
- Affectation `MIGRATED` = rattachement migré ; `REVIEW` = à examiner ; `ChoixOrganisationExpert` = souhait ; `MandatOrganisation.ACTIVE` = mandat confirmé.
- Aucune attribution de norme à une SC par ressemblance de nom. Seuls les dossiers Phoenix et les rattachements documentaires explicites comptent.
- Activité SC calculée uniquement sur les agrégats journaliers explicitement liés à un GT cible. Absence de mesure ≠ absence de travail.
- Observations sans état de résolution dans le modèle `NormeComment` : affichage « état non suivi ».
- L'assistant répond à un catalogue de questions contrôlées ; il n'exécute ni SQL ni écriture.

Références UX consultées : GOV.UK Design System (hiérarchie et tableaux) et U.S. Web Design System (visualisations simples avec équivalent textuel).
