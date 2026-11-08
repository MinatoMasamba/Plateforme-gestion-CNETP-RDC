# Plan d’implémentation — 5 espaces UI/UX du Secrétariat technique

Source : `prompt` (v2, 31/10/2026), matrice ST v3 du communiqué n° 003.
Statut : plan retenu pour la première passe.
Périmètre validé : **socle commun + architecture des 5 espaces + Coordination + Pôle 2**.
Hors périmètre de cette passe : modules métier des Pôles 1, 3 et 4, LiveKit, parité Flutter.
Les espaces P1, P3 et P4 restent visibles avec leurs menus et leurs indicateurs disponibles, mais les modules non développés affichent explicitement « Module à venir », sans fausses données.

---

## 1. Principes directeurs

- **Une seule application Django**, cinq espaces fonctionnels : Coordination, Pôle 1, Pôle 2, Pôle 3, Pôle 4.
- **Le chef de pôle supervise tout son pôle** ; le membre ne voit que son périmètre.
- **Les permissions sont appliquées côté serveur** : masquer un menu ne suffit pas.
- **Aucune donnée inventée** : les valeurs de démonstration sont remplacées ou signalées.
- **Traçabilité obligatoire** : qui, quand, sur quel objet, avec quel commentaire.
- **Statuts en couleur ET en texte**, un verbe par bouton, français simple.
- **Style Airy Minimalism et Soft Glassmorphism**, responsive ordinateur et téléphone.

---

## 2. État actuel et écarts principaux

| Sujet | Existant | Écart à combler |
|---|---|---|
| Rôles/postes | `apps/governance/st_matrix.py` : 19 postes, 5 organes, capacités | Menus encore liés à l’ancien modèle 19 sous-rôles / 4 pôles ; capacités `st_*` peu utilisées dans l’UI |
| Shell CTC | `templates/ctc/app/app.html`, sidebar, topbar, modules | Menu jusqu’à 14 entrées ; pas de « Mon travail du jour », pas de colonne droite, pas de barre d’aide |
| Circuit | `CTCProcessus` 5 étapes ; `Norme.status` | Pas de statuts d’affichage à 8 étapes + « Bloquée » avec motif |
| Audit | `AuditLog`, `build_traceability` | Matrice A.9 « qui lit l’audit de qui » non appliquée intégralement |
| Réunions | Backend `apps/meetings` + API complets | UI `reunions_view.html` = « Non disponible » |
| GED/PTN | `STRecord` non migré ; `st_can_manage_ptn` | Registre PTN, indexation, codification, versions à créer |
| Finances | `FinancialLine`, cotisations/jetons partiels | `financial_module.html` statique ; états réels à brancher |
| Pôles 1/2/4 | Quasi absents | Plans, livrables, indicateurs, formation, incidents, comptes, communication |
| Permissions | Contexte web + DRF grossier | Aucune permission DRF par pôle ; accès direct par hash encore possible |

Point bloquant à traiter dès le départ : la migration `0036` manque (`CTCMembership.is_active` + `STRecord`). Il faut la créer ou retirer le scaffold avant toute utilisation.

---

## 3. Méthode de travail — boucle obligatoire

Chaque lot suit la même boucle, sans passer au suivant tant que le lot n’est pas **PASS** :

1. **Implémentation verticale** : modèle/service + permission serveur + route + composant UI + tests ciblés.
2. **Vérification statique** : `manage.py check`, tests pytest du lot, `makemigrations --check`.
3. **Visualisation** : base de captures dédiée, serveur local, captures Playwright desktop `1440×900` et mobile `390×844` pour chaque poste concerné.
4. **Correction** : lecture des captures, liste d’écarts dans un `PASS_FAIL.md`, correction ciblée.
5. **Re-visualisation** : mêmes captures ; **PASS** si la checklist est intégralement respectée, sinon retour à l’étape 1 du lot. Maximum 3 itérations avant escalade.
6. **Après tous les lots** : parcours navigateur réel des 19 postes, tests négatifs d’URL/API, vérification mobile, console/network, puis **vérification finale** complète et rapport de recette.

### Checklist visuelle de PASS

- Le poste arrive directement dans son espace ; le menu contient **5 à 7 entrées**.
- Les 4 blocs sont présents : *À traiter maintenant*, *En attente d’autres personnes*, *Échéances de la semaine*, *Derniers éléments traités*.
- Colonne droite alertes/échéances et bandeau bas aide/contact visibles sur desktop.
- Chef : tous les modules et statistiques de son pôle + audit du pôle. Membre : uniquement son périmètre.
- Statuts affichés **en couleur ET en texte** ; « Bloquée » affiche son motif.
- Aucun chiffre fictif non signalé ; chaque KPI ouvre la liste correspondante.
- Aucun débordement horizontal, aucun script en erreur, navigation mobile utilisable.
- Libellés français, un verbe par bouton, aucune donnée d’un autre pôle visible.

---

## 4. Plan par lots

### Étape 0 — Intégration du travail en cours (0,5–1 j)

- Revoir les 26 fichiers modifiés non commités : réunions, `api/v1/permissions.py`, `web/ctc_views.py`, sidebar, `prompt`.
- Lancer les tests ciblés existants (`test_st_matrix_v3`, réunions, permissions) avant de construire dessus.
- Créer la migration manquante `0036` (`CTCMembership.is_active`, `STRecord`, `STRecordRevision`, `STConfirmation`, `STAccessPolicy`) ou retirer le scaffold inutilisé après vérification.
- Baseline : captures actuelles, sauvegarde de base, branche dédiée.

### Étape 1 — Socle commun (3–4 j)

Fichiers principaux :
- `apps/governance/st_spaces.py` : définition des 5 espaces, rattachement des 19 postes, menus déclaratifs de 5 à 7 entrées, matrice d’audit A.9.
- `apps/governance/st_permissions.py` : garde serveur unique, capacités par poste, classes DRF par espace.
- `apps/governance/st_status.py` : 8 statuts + « Bloquée » avec motif, transitions tracées (auteur, date, commentaire), sans casser `Norme.transition_to`.
- `apps/governance/st_workday.py` : agrégateur des 4 blocs et de la colonne alertes/échéances, avec portée membre ou chef de pôle.
- Configuration provisoire des jetons de présence, paramétrable et libellée « règle provisoire à valider ».
- Notifications et journal d’audit réutilisés depuis `AuditLog` et les services existants.

Tests : `test_st_spaces.py`, `test_st_permissions.py`, `test_st_workday.py`, `test_st_status.py`, accès négatifs par URL et API.

### Étape 2 — Shell et 5 espaces (4–5 j)

- Refonte de `web/ctc_views.py::get_ctc_context` : retourne l’espace, le menu autorisé, les blocs du jour, les alertes et les indicateurs.
- Refonte de `templates/ctc/app/components/sidebar_module.html` : suppression du filtre dupliqué `sidebarAllowedViews`, menus fournis par le serveur.
- Topbar : nom, pôle, rôle, recherche globale, notifications.
- Nouveaux partiels : `workday_module.html`, `space_dashboard.html`, `alerts_rail.html`, `help_bar.html`, `status_badge.html`.
- Accueil générique du chef et accueil personnel du membre.
- Route d’espace explicite pour éviter l’accès par hash non contrôlé.
- Les espaces P1, P3 et P4 affichent leurs menus et leurs indicateurs disponibles ; les modules non développés affichent « Module à venir », jamais de valeurs inventées.

Gate : les 19 postes arrivent dans le bon espace, avec 5 à 7 entrées, les 4 blocs, la colonne droite et le bandeau bas.

### Étape 3 — Coordination (3–4 j)

- File de validation, *Valider / Renvoyer* avec commentaire obligatoire.
- Réception poste 6 avec accusé daté, boîte des demandes, registre des décisions.
- Arbitrage des retards, vue des 7 tomes, audit A.9, annuaire.
- Socle administratif des réunions pour les postes 6 et 7 : calendrier, convocation, invités, présences, PV manuel. Le backend existe déjà ; il s’agit de brancher l’UI, pas de le recréer.
- Tests : une validation de coordonnateur suffit ; renvoi sans perte de versions ; audit croisé ; accès non autorisé refusé.

### Étape 4 — Pôle 2 (5–6 j)

- Dossiers à indexer, GED, codification, versions, comparaison et restauration.
- Registre PTN sur `STRecord` : fiche, valeur, unité, source, version, tome, historique, export.
- Consolidation des avis par le chef de pôle, sans décision de faire monter ou redescendre la norme.
- Validation des fichiers PDF/PNG/JPG ≤ 10 Mo.
- Tests et gate visuel chef/membre.

### Étape 5 — Boucle visualisation + web (2–3 j)

1. Étendre ou créer `scripts/prepare_five_spaces_db.py` pour générer un mandat matrice v3 par poste.
2. Créer `scripts/capture_five_spaces.py` : captures PC/mobile par espace, chef et membre, avec contrôles automatiques (4 blocs, menu 5–7, colonne droite, bandeau bas, débordement, erreurs console).
3. Sorties dans `reports/5_espaces/` : captures, `INDEX.md`, `manifest.json`, `PASS_FAIL.md`.
4. **Correction → re-capture** jusqu’au PASS, lot par lot.
5. **Vérification navigateur Playwright** : parcours des 19 postes, URL directes, POST non autorisés, mobile, clavier.
6. **Recherche de références UX** : confrontation aux principes de tableaux de bord (NN/g), accessibilité WCAG 2.2 AA, GOV.UK Design System et densité Material 3. Document `docs/REVUE_UX_5_ESPACES.md` : ce qui est adopté, ce qui est écarté, notamment sur le contraste du Soft Glassmorphism.
7. Nouvelle capture après ajustements UX, puis PASS final.

### Étape 6 — Recette finale (1 j)

```bash
mon_env/bin/python manage.py check
mon_env/bin/python manage.py makemigrations --check --dry-run
mon_env/bin/python -m pytest -q
ruff check .
git diff --check
```

Puis rapport de recette et mise à jour de `docs/NAVIGATION_CTC_WEB.md`.

---

## 5. Critères de PASS

- Chaque poste voit uniquement son espace et son menu ; les accès directs par URL ou API sont refusés côté Django.
- Chef : tous les modules, statistiques et audit de son pôle. Membre : son travail, ses échéances, ses statistiques.
- Les 4 blocs et la colonne droite sont présents sur les 5 accueils.
- Les 8 statuts + « Bloquée » sont affichés en couleur et en texte, avec motif.
- Aucun chiffre fictif non signalé ; chaque indicateur ouvre sa liste.
- Desktop et mobile sans débordement, sans erreur console, libellés français, un verbe par bouton.
- Tests, `check`, `makemigrations --check`, `ruff` et `git diff --check` passent.
- Captures finales et `PASS_FAIL.md` fournis.

---

## 6. Livrables

- Migration `0036` et modèles du socle.
- Services d’espaces, permissions, statuts, travail du jour.
- Shell refondu + accueils chef/membre des 5 espaces.
- Modules Coordination et Pôle 2 fonctionnels.
- Jeu de tests dédié.
- Scripts de capture et rapport visuel.
- `docs/REVUE_UX_5_ESPACES.md` et le présent plan.

---

## 7. Risques et parades

- **Deux modèles d’organisation coexistent** → matrice v3 comme source de vérité, couche de compatibilité pour les anciens rôles.
- **8 statuts vs 5 étapes existantes** → statut de présentation + modèle de transition, sans réécrire `Norme.status`.
- **Audit contradictoire dans le prompt** → matrice A.9 explicite et testée : le chef lit les membres, ses propres actions sont lues par l’autorité désignée.
- **Données fictives** → remplacement ou mention « valeurs de démonstration » obligatoire.
- **`app.html` très volumineux** → ajout de partiels ciblés, pas de réécriture globale.
- **Règle des jetons absente** → règle provisoire simple, paramétrable et signalée.
- **LiveKit** → hors première tranche, dépendance aux credentials et à la validation métier.
- **Travail en cours non commité** → revue puis intégration, sans écrasement.

---

## 8. Durée estimée

**16 à 20 jours** pour la première passe.

Je ne passerai au lot suivant qu’après un PASS visuel et technique du lot courant ; aucun commit ne sera fait sans demande explicite.

---

## 9. État d’exécution au 31 octobre 2026

La première passe est implémentée : socle, architecture des cinq espaces, Coordination et Pôle 2. Le rapport de recette est dans `reports/RAPPORT_IMPLEMENTATION_5_ESPACES.md`.

Les modules des Pôles 1, 3 et 4 restent des écrans « Module à venir ». LiveKit et la parité Flutter restent hors périmètre.
