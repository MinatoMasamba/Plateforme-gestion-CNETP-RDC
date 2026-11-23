# Audit du poste CTC et proposition de dashboard orienté action

**Date de l'audit : 23 novembre 2026**

**Périmètre :** dépôt `Plateforme-gestion-CNETP-RDC`, surface principale `/ctc/`, comparaison `/app/` et Flutter.
**Principe de séparation :** le circuit historique `Norme.circuit_version=LEGACY` reste distinct du moteur Phoenix/ST v3. Phoenix complète les mandats, postes et espaces d'organisation ; il ne doit pas être traité comme une nouvelle version du circuit CTC legacy.

## Synthèse

| Statut | Conclusion |
| --- | --- |
| **Implémenté** | Contrôle d'accès serveur, mandats Phoenix actifs, périmètres de lecture par poste, workday ST v3, menus SSR, journalisation, versionnement GED, endpoint mobile CTC et rafraîchissement Flutter. |
| **Incomplet** | Deux accents de dashboard coexistent ; les KPI ne partagent pas encore une définition unique ; les erreurs/rate limits ne sont pas uniformes ; les filtres Experts/Demandes et le responsive Flutter sont partiels. |
| **Absent** | Contrat dashboard commun avec `workday`, `alerts` et `generated_at`; KPI actionnables partout ; écran de lecture global pour `/ctc/` sans hash implicite ; rollback général de workflow ; QR explicite dans l'annuaire CTC. |

Le dépôt contient déjà la matière première de la cible : `build_workday()` produit `todo`, `waiting`, `deadlines`, `recent`, `alerts` et `generated_at` ([`st_workday.py`](../apps/governance/st_workday.py#L83-L230)). Le problème principal est donc de sélection, composition et parité des surfaces, pas d'ajouter un moteur métier.

## 20 réponses

### Bloc 1 — Vues, rôles et permissions

1. **Inventaire par rôle, mandat et poste ST — Incomplet.**
   - Legacy : seize rôles CTC sont stockés dans `CTCMembership` ([`models.py`](../apps/governance/models.py#L359-L386)).
   - ST v3 : dix-neuf profils métier sont dérivés des postes de la matrice ; le poste détermine menus, mission et outils ([`st_spaces.py`](../apps/governance/st_spaces.py#L251-L275)).
   - Les menus couvrent ST, Pôles 1 à 4 et leurs spécialisations ; certains modules restent explicitement « à venir » ([`st_spaces.py`](../apps/governance/st_spaces.py#L70-L177), [`app.html`](../templates/ctc/app/app.html#L160-L213)).
   - Écart : il n'existe pas encore une vue ou un test unique présentant la matrice exhaustive rôle/mandat × vue réellement implémentée.

2. **Masquage UI contre permissions serveur — Implémenté, à compléter endpoint par endpoint.**
   - `get_ctc_context()` exige une adhésion legacy ou un mandat actif et calcule les capacités ([`ctc_views.py`](../web/ctc_views.py#L241-L391)).
   - ST v3 autorise les vues par `st_allowed_views`; le shell refuse une vue non autorisée par 403 ([`ctc_views.py`](../web/ctc_views.py#L927-L958), [`st_spaces.py`](../apps/governance/st_spaces.py#L200-L231)).
   - Les menus ne sont pas une habilitation. `st_spaces.py` l'explicite, et chaque écriture doit revalider le mandat, le périmètre et l'état du dossier.
   - `visible_tasks`, `visible_processus` et `visible_meetings` imposent le périmètre de lecture par poste ([`st_permissions.py`](../apps/governance/st_permissions.py#L6-L55)).

3. **Redirection post-connexion et première action — Incomplet.**
   - La redirection globale est `/`, pas une destination CTC calculée par rôle ([`settings.py`](../config/settings.py#L308)).
   - `/ctc/` choisit ensuite `st_space_home`, `st_initial_view`, un hash ou `dashboard` ([`app.html`](../templates/ctc/app/app.html#L400-L452)).
   - La première action n'est donc pas stable : une URL sans hash ouvre l'espace ST v3, tandis qu'un hash `#dashboard` force le dashboard générique observé sur la page auditée.

4. **Sidebar, topbar, routes et hash — Implémenté avec redondances.**
   - La navigation est groupée Travail, Supervision, Outils et Système dans le cas legacy ; ST v3 remplace ce menu par cinq à sept entrées de poste ([`ctc_views.py`](../web/ctc_views.py#L373-L410), [`st_spaces.py`](../apps/governance/st_spaces.py#L70-L177)).
   - `switchView()` vérifie la liste autorisée, synchronise le hash, gère le retour navigateur via `hashchange` et conserve une vue SSR active ([`app.html`](../templates/ctc/app/app.html#L400-L452)).
   - Redondance : « Tableau de bord » (générique) et espace `coordination`/`espace_pN` (workday) peuvent coexister dans le DOM. Une seule page d'accueil doit subsister après la refonte.

### Bloc 2 — Experts et groupes

5. **Listes, fiches experts, QR et statut — Incomplet.**
   - Les lignes exposent nom, email, structure, SC, affectation, complétude, dernière connexion, contributions et détail de profil ([`ctc_experts.py`](../web/ctc_experts.py#L80-L137), [`experts_view.html`](../templates/ctc/app/components/experts_view.html#L16-L67)).
   - Les cinq états de présence/affectation sont : affectation validée, proposée, choix exprimé, non affecté, profil incomplet.
   - Aucun QR ni QR de fiche d'expert n'est présent dans les composants CTC inspectés. Statut : **absent**.

6. **Relation Expert, CTM/SC, WG, mandats et postes ST — Implémenté côté données.**
   - L'annuaire relie `Expert`, `AffectationSousCommission`, choix d'organisation, organe SC, groupes de l'organe, postes et mandats actifs ([`ctc_experts.py`](../web/ctc_experts.py#L47-L153)).
   - `MandatOrganisation` rattache exclusivement un expert à un poste ou à un groupe cible, avec version, dates, capacité et statut ([`phoenix_models.py`](../apps/governance/phoenix_models.py#L337-L380)).
   - Écart : la vue ne matérialise pas encore un parcours unique « expert → mandat/poste → SC/CTM → WG → dossiers ».

7. **Recherche, filtres et tris — Incomplet.**
   - Recherche locale nom/email/structure et filtres affectation, SC et complétude sont actifs ([`experts_view.html`](../templates/ctc/app/components/experts_view.html#L25-L35), [`experts_view.html`](../templates/ctc/app/components/experts_view.html#L100-L117)).
   - Manquent : tri utilisateur, pagination, recherche par spécialité/téléphone/statut de profil/mandat, critère « poste ST » et distinction explicite CTM/SC/WG.

8. **Actions rapides et protections — Incomplet.**
   - L'annuaire est intentionnellement en lecture seule ; la protection principale est le serveur.
   - Les actions du circuit exigent, selon les cas, rôle, étape, affectation, commentaire, version courante et absence de décision dupliquée ([`ctc_views.py`](../web/ctc_views.py#L1248-L1333), [`st_operations.py`](../apps/governance/st_operations.py#L216-L230)).
   - Écart : la disponibilité des boutons n'est pas centralisée dans un contrat d'action et tous les handlers legacy n'ont pas la même mécanique anti-double soumission.

### Bloc 3 — Normes et documents

9. **Étapes, statuts legacy, ST v3 et affichages — Implémenté, vocabulaire double assumé.**
   - Legacy : `RECEPTION`, `GEOSPATIAL`, `MULTI_REVIEW`, `INDUSTRIAL`, `SIGNED_OUT` dans le circuit CTC.
   - ST v3 : `process_status()` dérive des libellés opérationnels à partir des dates, de l'étape, du statut norme et des tâches bloquées ([`st_status.py`](../apps/governance/st_status.py)).
   - Les dossiers non legacy sont redirigés vers Phoenix pour certaines opérations, et ne doivent pas passer par les actions legacy ([`ctc_views.py`](../web/ctc_views.py#L1434-L1439), [`ctc_views.py`](../web/ctc_views.py#L1530-L1535)).

10. **Versions, diff, rollback, restauration et traçabilité — Incomplet.**
    - La GED vérifie la version de base, incrémente la version, journalise l'auteur et permet une restauration traçable depuis une indexation antérieure ([`st_ged.py`](../apps/governance/st_ged.py#L181-L249)).
    - La décision d'une version est réservée à la dernière indexation et refuse les doubles décisions ([`st_ged.py`](../apps/governance/st_ged.py#L258-L273)).
    - Comparaison/restauration documentaire : **implémentées**. Rollback général d'un workflow ou d'une norme : **non établi**.

11. **Soumission, revue, commentaire, approbation et doubles soumissions — Incomplet.**
    - Plusieurs endpoints valident décision, commentaire, rôle, étape et prérequis. Les vues JSON retournent une erreur explicite en cas d'action refusée ([`ctc_views.py`](../web/ctc_views.py#L1248-L1544)).
    - Phoenix/ST v3 bloque une révision obsolète et une confirmation répétée ([`st_operations.py`](../apps/governance/st_operations.py#L137-L230)).
    - Écart : absence de politique uniforme `request_id`/idempotence couvrant tous les flux legacy et mobiles.

12. **Exactitude des KPI et écarts de périmètre — Incomplet.**
    - Le workday calcule réellement ses files, jusqu'à 12 éléments affichés mais avec compte complet, et distingue échéances bloquées/en retard ([`st_workday.py`](../apps/governance/st_workday.py#L83-L230)).
    - `build_space_dashboard()` calcule dossiers, tâches, records confirmés, réunions et membres selon le périmètre du poste ([`st_workday.py`](../apps/governance/st_workday.py#L233-L284)).
    - Le dashboard mobile ST v3 utilise ces KPI, mais son dashboard legacy appelle `build_ctc_statistics()` global et sa liste `group_norm_rows` est vide en ST v3 ([`ctc_views.py`](../api/v1/mobile/ctc_views.py#L61-L136)).
    - Conséquence : les quatre KPI visibles ne sont pas encore interchangeables entre web legacy, espace ST v3 et Flutter.

### Bloc 4 — Données, API et états UI

13. **SSR, DRF, polling Flutter, cache et fraîcheur — Incomplet.**
    - Web : données rendues côté serveur dans le shell ; `generated_at` est produit dans le workday et affiché ([`workday_module.html`](../templates/ctc/app/components/workday_module.html#L1-L18)).
    - API : endpoint Dashboard CTC mobile authentifié, filières dossiers/assignations/demandes séparées ([`ctc_views.py`](../api/v1/mobile/ctc_views.py#L16-L166)).
    - Flutter : quatre requêtes concurrentes au chargement puis poll toutes les 30 secondes, notifications toutes les 60 secondes ([`ctc_screen.dart`](../flutter_app/lib/features/ctc/ctc_screen.dart#L40-L96)).
    - Absents : `generated_at` dans le JSON mobile, cache versionné et indicateur de fraîcheur.

14. **Chargement, vide, 403/429/500/503, JWT et récupération — Incomplet.**
    - Flutter a un état initial, une erreur avec nouvelle tentative et des états vides de listes ([`ctc_screen.dart`](../flutter_app/lib/features/ctc/ctc_screen.dart#L84-L147)).
    - Un échec silencieux conserve l'ancien écran sans signaler la donnée périmée, exactement le cas qui masque les 429 observés dans le navigateur Flutter.
    - Le rafraîchissement JWT est prévu dans le client mobile.
    - Le web a des erreurs génériques par formulaire, mais pas une politique visuelle commune 403/429/500/503.

15. **Validations et prévention des actions invalides — Implémenté partiellement.**
    - Les opérations ST valident champs obligatoires, montants positifs et devise/date ; les modèles appellent `full_clean()` et protègent les révisions obsolètes ([`st_operations.py`](../apps/governance/st_operations.py#L137-L205)).
    - Les interfaces désactivent les boutons pendant les requêtes ([`ctc_requests_module.html`](../templates/ctc/app/components/ctc_requests_module.html)).
    - Écart : commentaires et échéances ne sont pas toujours obligatoires/rendus; la validation n'est pas homogène entre les formulaires SSR et Flutter.

16. **PDF, DOCX, CSV, PV, reçus, exports et pièces privées — Partiel mais fondé sur des modules dédiés.**
    - Les exports et téléchargements de preuves sont protégés par authentification et contrôle d'accès.
    - Les pièces Phoenix restent privées ; le service GED refuse les accès hors périmètre, version obsolète ou fichier non autorisé.
    - Le statut « PV » et « reçu » n'est pas uniforme dans tous les postes : ces formats existent selon le module, pas comme capacité globale du dashboard.

### Bloc 5 — Qualité visuelle et amélioration

17. **CSS/Tailwind, composants premium et palette Flutter — Implémenté avec dette de duplication.**
    - `app.html` charge Tailwind/CDN, CSS institutionnel et CSS CTC ; les composants ajoutent aussi des règles/classes locales.
    - La palette officielle est respectée (`#0095c9`, `#fff24b`, `#db3832`) dans les feuilles partagées.
    - Flutter reproduit visuellement le dashboard premium, mais sous un arbre de widgets séparé ([`ctc_dashboard.dart`](../flutter_app/lib/features/ctc/widgets/ctc_dashboard.dart)).
    - Écart : risque de dérive entre template HTML, règles inline et widgets Flutter ; consolider les tokens avant d'ajouter de nouveaux blocs.

18. **Mobile, tablette, desktop, rail/sidebar et tableaux — Incomplet.**
    - Le web gère sidebar/drawer, cartes KPI responsive et tableaux empilés.
    - Flutter possède des seuils compacts et des tests à 390, 1024 et 1440 px.
    - Le test `ctc_dashboard_test.dart` échoue actuellement à 390 px : `Row` de [`ctc_completion.dart`](../flutter_app/lib/features/ctc/widgets/ctc_completion.dart#L195) déborde de 116 px, suivi d'un timeout.
    - 768 px n'est pas couvert par la cible de tests demandée ; ce point reste à ajouter.

19. **Surcharge, colonnes, texte, actions et redondances — Incomplet.**
    - Le dashboard générique montre avant le travail : rôle/droits, quatre KPI globaux, deux graphiques, groupes, outils et statistiques secondaires ([`dashboard_module.html`](../templates/ctc/app/components/dashboard_module.html#L1-L55)).
    - Le navigateur audit montre 25 normes, 35 groupes et un long palmarès avant les assignations ; ce n'est pas une file de décision.
    - La table Demandes conserve sept colonnes, deux filtres désactivés et « échéance non configurée » ([`ctc_requests_module.html`](../templates/ctc/app/components/ctc_requests_module.html#L1-L6)).
    - L'écran ST v3 est plus proche de la cible, car il inclut déjà le workday avant les panneaux de supervision ([`space_home.html`](../templates/ctc/app/components/space_home.html#L35-L58), [`member_workspace.html`](../templates/ctc/app/components/member_workspace.html#L1-L37)).

20. **Cinq priorités et proposition — Définies.**

    1. **P0 — Unifier la page d'accueil.** Choisir `workday_module.html` comme zone principale pour tous les postes ; ne conserver qu'un dashboard.
    2. **P0 — Unifier les règles d'action et de périmètre.** Sérialiser les actions disponibles depuis le backend, sans déduire une permission depuis un bouton affiché.
    3. **P0 — Corriger 390 px et les états réseau.** Débordement Flutter, 429/stale, 403, 500, 503, reprise et retry.
    4. **P1 — Introduire le contrat commun web/mobile.** `schema_version`, `generated_at`, `scope`, `kpis`, `workday`, `alerts`, listes paginées.
    5. **P1/P2 — Déplacer statistiques et outils.** Graphiques repliables, filtres réellement actifs, liste en cartes, tests 390/768/1440 et tests clavier.

## Matrice synthétique des rôles, vues, permissions et données

| Population | Vues principales | Capacités/actions | Données visibles | Limite structurante |
| --- | --- | --- | --- | --- |
| Coordination ST v3, postes 1–5 | `coordination`, dossiers, demandes, retards, réunions | routage, décision, arbitrage selon action ; lecture d'audit ST/pôles | tous les processus dans le périmètre ST, demandes, tâches et membres | chaque action doit revalider le workflow |
| Assistant exécutif, poste 6 | `assistant_executif`, assignations, demandes, dossiers, rapports | réception, examen des demandes | processus en `RECEPTION`, demandes opérationnelles | non habilité à l'administration générale |
| P1, postes 8–9 | espace P1, planning, livrables, statistiques, alertes selon poste | supervision/suivi, pas décision documentaire globale | tâches de pôle, dossiers selon poste, réunions | plusieurs modules restent à venir |
| P2, postes 10–12 | espace P2, indexation, GED, PTN, consolidation/versions | saisie, indexation, confirmation selon chef/poste | queue indexation/restauration, records PTN | périmètre personnel pour le poste 11 |
| P3, postes 13–16 | espace P3, juridique, finance, cotisations, états | confirmation/audit pour co-chefs ; saisie finance pour chargés | examens juridiques, records finance, dépenses | aucun audit de coordination général |
| P4, postes 17–19 | espace P4, comptes, sauvegardes, travaux, formation, communication, usagers | capacités métier postées ; système pour le poste 18 | tâches/poste, incidents, travaux, réunions | menus non équivalents à droits d'écriture |
| Legacy reviewer/analyse | dashboard, dossiers, assignations, outils du rôle | revue assignée, avis, méthode/ISO selon rôle | étape `MULTI_REVIEW` ou étapes du rôle | rôle et affectation nominatifs requis |
| Legacy direction | dashboard, dossiers, demandes, routage, statistiques | arbitrage, transmission | toutes étapes CTC legacy | transmission après avis et étapes requises |

La source commune de périmètre est `get_ctc_context()` + `st_permissions.py`. Le contrat de rendu doit rester dérivé du backend, jamais codé seulement dans la sidebar.

## Dashboard cible

### Hiérarchie

1. **En-tête de poste**
   - mission, pôle, poste, statut du mandat ;
   - synchronisation « mis à jour à … » ;
   - au plus trois actions autorisées.
2. **Bande d'alertes**
   - retards ;
   - blocages ;
   - demandes en attente ;
   - échéances dans moins de 48 h.
3. **Quatre KPI cliquables**
   - à traiter ;
   - bloqué/en retard ;
   - attente d'un tiers ;
   - échéances de la semaine.
4. **Mon travail**
   - `todo` ;
   - `waiting` ;
   - `deadlines` ;
   - `recent`.
5. **Ligne d'action**
   - type, référence, titre, statut, responsable/attente, échéance, action principale ;
   - un lien secondaire « historique ».
6. **Supervision**
   - membres, files de validation et charge par poste ;
   - visible uniquement pour les superviseurs.
7. **Statistiques**
   - après le travail ;
   - repliables ;
   - limitées aux données utiles au poste.

### États

| État | Rendu |
| --- | --- |
| Vide légitime | message « Aucun élément ne vous attend », avec date de vérification |
| Aucun résultat filtré | message distinct + bouton « Réinitialiser les filtres » |
| 401 / JWT expiré | renouveler une fois ; sinon retour à l'authentification |
| 403 | poste/mandat insuffisant, destination d'accueil et module demandé |
| 423 / plateforme verrouillée | motif, auteur, date ; actions désactivées |
| 429 | conserver les données, afficher « Limite atteinte », retry temporisé, ne pas relancer quatre requêtes en boucle |
| 500 / 503 | erreur explicite, données fraîchement datées si disponibles, retry |
| Action en cours | un seul envoi, bouton local désactivé, progression visible |
| Action réussie | mise à jour de l'élément localement puis synchronisation ; ne pas vider tout l'écran |
| Donnée périmée | heure de dernière synchronisation et bannière compacte |

### Responsive

- **390 px :** cartes, une colonne, une action principale, filtres repliables ; pas de `Row` non flexible.
- **768 px :** deux colonnes seulement pour les blocs courts ; tableau remplacé par cartes prioritaires.
- **1440 px :** file principale large, alertes et supervision en colonne latérale ; graphiques repliés par défaut.
- Navigation : drawer accessible, focus restauré à la fermeture, labels lisibles, scroll principal unique.

## Contrat commun web/Flutter

Le web peut continuer à rendre le JSON comme contexte SSR, tandis que Flutter le consomme via DRF. La forme logique doit être identique.

```json
{
  "schema_version": 1,
  "generated_at": "2026-11-23T08:45:00+01:00",
  "scope": {
    "role": "coordination",
    "post_code": "ST-V3-01",
    "pole": "ST",
    "mandate_id": 12,
    "organisation_version": "2026"
  },
  "capabilities": {
    "view_dossiers": true,
    "route_documents": true,
    "approve_requests": false
  },
  "freshness": {
    "status": "fresh",
    "retry_after": null
  },
  "kpis": {
    "todo": 6,
    "blocked_or_overdue": 2,
    "waiting": 4,
    "deadlines_7d": 3
  },
  "workday": {
    "todo": [],
    "waiting": [],
    "deadlines": [],
    "recent": []
  },
  "alerts": [],
  "statistics": {
    "collapsed": true,
    "status_distribution": []
  },
  "dossiers": {
    "count": 0,
    "next": null,
    "results": []
  },
  "assignations": {
    "count": 0,
    "next": null,
    "results": []
  },
  "actions": [
    {
      "id": "processus.validate",
      "label": "Valider l'entrée",
      "target_type": "processus",
      "target_id": 6,
      "requires_comment": true,
      "method": "POST",
      "href": "/ctc/dossiers/6/validation/"
    }
  ]
}
```

Règles :

- tous les compteurs et listes sont calculés pour le même `scope` ;
- l'URL de l'action n'est pas une permission implicite : l'endpoint réapplique les contrôles ;
- les dates sont ISO 8601, avec timezone ;
- les collections vides sont stables (`[]`), les objets absents ne changent pas selon le rôle ;
- le serveur limite les listes ; les endpoints détaillés gardent la pagination ;
- les erreurs exposent `code`, `detail`, `retryable`, `retry_after` sans révéler de données hors périmètre.

## Backlog priorisé

### P0 — sécurité, exactitude et blocages

1. **Remplacer le dashboard générique par le workday comme accueil unique.**
   - `templates/ctc/app/components/dashboard_module.html`
   - `templates/ctc/app/components/space_home.html`
   - `templates/ctc/app/components/member_workspace.html`
   - `templates/ctc/app/app.html`
2. **Centraliser un builder de payload dashboard web/mobile.**
   - `apps/governance/st_workday.py`
   - `web/ctc_views.py`
   - `api/v1/mobile/ctc_views.py`
3. **Uniformiser les contrôles des actions, doubles soumissions et plateforme verrouillée.**
   - `apps/governance/st_operations.py`
   - `web/ctc_views.py`
   - `api/v1/mobile/ctc_views.py`
4. **Corriger le débordement Flutter à 390 px et remplacer le poll silencieux.**
   - `flutter_app/lib/features/ctc/widgets/ctc_completion.dart`
   - `flutter_app/lib/features/ctc/ctc_screen.dart`
5. **Ajouter les états 403/423/429/500/503 et l'indicateur de fraîcheur web/mobile.**
   - templates CTC, client Flutter API et widgets de dashboard.

### P1 — expérience actionnable et parité

1. Activer les filtres Demandes (type, statut, échéance, priorité), ajouter pagination et action principale.
2. Ajouter tri, pagination et filtres poste/ST/spécialité dans Experts ; conserver la lecture seule.
3. Produire `workday`, `alerts`, `generated_at`, scope et actions dans le dashboard mobile.
4. Réduire les appels Flutter : une requête dashboard agrégée, refresh conditionnel après mutation, backoff exponentiel.
5. Déplacer statistiques et outils derrière des panneaux repliables.
6. Tester explicitement le périmètre par poste pour dashboard, dossiers, assignations, demandes et actions.

### P2 — cohérence visuelle et parcours

1. Rationaliser les styles inline, CSS institutionnel/CTC et tokens Flutter.
2. Ajouter tests 390/768/1440 sur dashboard, dossiers, demandes, sidebar et drawers.
3. Ajouter des repères d'accessibilité : focus, Escape, lecteur d'écran, contrastes et états de boutons.
4. Aligner `/app/` sur la terminologie et les liens profonds CTC sans fusionner les moteurs.
5. Ajouter tri/export contextuel uniquement lorsque le module possède une politique de confidentialité validée.

## Validation exécutée

| Vérification | Résultat |
| --- | --- |
| `manage.py check` | **Réussi** — aucune anomalie |
| Tests ciblés ST/workday/mandats/mobile | **52 réussis** |
| Fichiers testés | `tests/test_st_spaces.py`, `tests/test_st_space_isolation.py`, `tests/test_st_matrix_v3.py`, `tests/test_mobile_ctc_requests.py` |
| Flutter `ctc_dashboard_test.dart` | **10 réussis, 1 échec** : overflow de 116 px à 390 px dans `ctc_completion.dart`, puis timeout |
| Navigateur web `/ctc/#dashboard` | **Observé** : rôle/droits et statistiques globales précèdent les éléments de travail |
| Navigateur Flutter | **Observé** : série de 429 lors du polling ; écran bloqué sur l'ancienne session/authentification |
| Ruff ciblé | **Non exécuté** : `ruff` non installé dans l'environnement actif |
| `flutter analyze` | **1 info préexistante**, hors périmètre CTC : accolades manquantes autour d'un `if` dans `flutter_app/lib/features/expert/expert_screen.dart`; aucune erreur CTC |

## Décisions recommandées

- Ne créer **ni modèle, ni migration, ni service métier parallèle** dans le premier lot.
- Exposer `build_workday()` comme source du centre de commande ST.
- Conserver Phoenix et CTC legacy séparés dans les calculs et les tests.
- Faire du dashboard un **contrat de lecture/action autorisée**, non une vitrine de tous les modules.
- Ne passer à la migration des vues détaillées qu'après validation des 390/768/1440 px et des erreurs réseau.
