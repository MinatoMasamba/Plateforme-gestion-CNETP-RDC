# Rapport — Tests E2E « Parcours Utilisateurs » (CNETP)

- **Date** : 13/10/2026
- **Source du brief** : `prompt_test_2e2`
- **Environnement** : serveur local `http://127.0.0.1:8001` (base seedée `seed_e2e`, 14 comptes)
- **Méthode** : navigateur réel **Playwright/Chromium** (headless) + client Django pour confirmer les manques observés à l'écran. Captures dans `captures_test/`.
- **Profils utilisés** : `pilote1@cnetp.cd` (COPIL / Président, espace `/pilotage/bureau-directoire/`), `ctc1@cnetp.cd` (Secrétariat technique, `/ctc/`).

> Note de cadrage : l'application n'a pas de profil « Directeur général » distinct. Les scénarios A (DG) ont été joués avec le profil Président du Comité de Pilotage (pilote1), seul rôle disposant des pouvoirs de cadrage/instruction côté Pilotage. Le « Secrétariat technique » = CTC (`ctc1`). Les « sous-commissions » correspondent aux CTM (`CTM 1..8`).

---

## 1. Tableau des scénarios

| Scénario | Réussi ? | Clics | Temps | Blocage observé | Type de manque | Correction proposée | Corrigé ? |
|---|---|---|---|---|---|---|---|
| **A1** Instruction à un groupe | ❌ | — | — | Aucun écran de création d'instruction. Le modèle `Tache` (groupe, échéance, responsable, statut) existe mais **aucune interface de création** : seuls les endpoints de transition/configuration de tâches existantes sont branchés (`activity_task_transition`, `activity_task_configure`). 0 tâche seedée. | fonction absente | Écran « Instructions » (objet, destinataires, échéance) créant une `Tache` + statut « envoyée/lue/en cours/exécutée » | Non |
| **A2** Confier une norme à un groupe | ⚠️ | ~4-5 | ~1 min | Le cadrage (`NormeCadrage`, Bureau Directoire) et l'ordre de service vers la CTC existent, mais **aucun geste direct « affecter la norme X au groupe Y »**. Le lien norme→groupe (`Tache.norme`/`target_group`) n'a pas d'UI de création. | fonction présente mais introuvable | Bouton « Confier au groupe » dans le cadrage, matérialisant `Tache(norme, groupe, échéance, livrable)` | Non |
| **A3** Voir un groupe au travail | ✅ | ≤3 | <1 min | Écrans présents (`/pilotage/ctm/<n>/`, `/pilotage/groupes-travail/<pk>/activite/`, `/pilotage/activites/`) avec avancement, tâches en retard (`LATE`) et bloquées (`BLOCKED`). Mais **tout est vide** : 0 tâche, KPIs « Non configuré ». | information manquante à l'écran | Seed de tâches de démo + configuration des indicateurs | Non |
| **B1** Suivi du Secrétariat technique | ✅ | 2 | <1 min | Écran complet présent : `/pilotage/#panel-ctc` → « Supervision de l'équipe CTC » (répartition des opérations, contributions par collaborateur, état du circuit, journal « Qui a fait quoi », documents, dossiers CTC). | — (fonction présente) | Rien | — |
| **B2** Transmettre une norme au ST | ⚠️ | ~4 | ~1 min | Le circuit technique COPIL→CTC→CTM→experts existe (`CTCProcessus` : réception → indexation → examens → consultation → transmission). Mais **aucun bouton unique « transmettre au ST »** ; l'utilisateur doit deviner le chemin (cadrage → ordre de service → réception CTC). | fonction présente mais introuvable | Rendre le circuit visible pas-à-pas avec statut de transmission (frise) | Non |
| **B3** Commenter une norme / avis | ⚠️ | ~3 | <1 min | Commentaire simple possible (`NormeComment` + `/pilotage/norme/<pk>/commenter/`). Mais **pas de type d'avis** (favorable/réserve/défavorable), pas de motif structuré, **pas de notification au destinataire**. | fonction présente mais introuvable | Ajouter le type d'avis + motif + notification au responsable du dossier | Non |
| **B4** Signaler à la CTC un point non fait | ❌ | — | — | Aucun mécanisme de signalement COPIL→CTC. Les modèles voisins (`CTCOperationalRequest` = interne CTC, `PermissionRequest` = dérogation Pilotage, `ActivityDispute`/`ActivityAlert` = supervision d'activité) ne couvrent pas ce besoin. | fonction absente | « Signalement » (objet, norme/groupe, gravité) + accusé de réception + suivi de réponse | Non |
| **B5** Transmettre les comptes rendus à la CTC | ❌ | — | — | Le module « Réunions » CTC n'est qu'un **planificateur Meet** (lien visio + convocations). `ProcessusVerbaux` existe en modèle mais **aucune UI de dépôt** ; `generate_pv_pdf` non branché. | fonction absente | Dépôt de PV/CR rattaché à une réunion, visible CTC avec décisions/actions | Non |
| **C1** Rédiger/déposer le rapport de sous-commission | ❌ | — | — | Aucun modèle « Rapport », aucun espace « Rapports » par sous-commission (modèle, brouillon, dépôt, validation, historique). Les vues de sous-commission sont de la **supervision d'activité**, pas du dépôt de rapport. | fonction absente | Espace « Rapports » (modèle, brouillon, dépôt, validation, historique, statut) | Non |
| **C2** Consigner décisions et actions | ❌ | — | — | `Tache` (action + responsable + échéance) existe mais **pas de création via l'UI** et pas de rattachement à une réunion ; pas de modèle « décision » de réunion. | fonction absente | Saisie décisions + création d'actions rattachées à la réunion (responsable, échéance) | Non |
| **D1** Vue « Cette semaine » | ⚠️ | 2 | <1 min | `/pilotage/activites/` = « Supervision des sous-commissions » (KPIs, heatmap hebdo, tâches par sous-commission, exceptions/retards). Mais KPIs « **Non configuré** » (0 source), pas de filtre « normes actives par domaine », pas de notion « cette semaine » (période par défaut 28 j). | information manquante à l'écran | Configurer les indicateurs + filtre période/domaine « cette semaine » | Non |

Légende : ✅ réussi · ⚠️ partiel · ❌ échec/bloquant.

---

## 2. Top 5 des manques bloquants

1. **A1 / C2 — Aucune création d'instruction, de tâche ni d'action depuis l'interface.** Le modèle `Tache` est riche (groupe, échéance, responsable, statut, priorité) mais il n'existe **aucune vue de création** : uniquement des transitions/configurations de tâches déjà existantes. Résultat : le DG ne peut ni donner une instruction (A1), ni consigner des actions de réunion (C2). *(preuve : `captures_test/A3_ctm_detail.png` — vue de groupe vide, 0 tâche ; grep confirmant l'absence de `Tache.objects.create` dans les vues web)*.

2. **B4 — Aucun signalement formel vers la CTC.** Aucun écran « signaler qu'un point n'a pas été fait » avec accusé de réception. Les mécanismes existants (`CTCOperationalRequest`, `PermissionRequest`, `ActivityDispute`) répondent à d'autres besoins.

3. **B5 / C2 — Comptes rendus et PV non déposables.** Le module « Réunions » CTC ne fait que générer un lien Meet et des convocations. `ProcessusVerbaux` existe en base mais n'est jamais créé par une vue ; `generate_pv_pdf` n'est pas branché.

4. **C1 — Espace « Rapports » de sous-commission absent.** Aucun modèle ni écran de rapport (brouillon, dépôt, validation, historique). Les pages de sous-commission sont de la supervision, pas de la production de rapport.

5. **A2 / B2 — Circuits « norme → groupe » et « transmission ST » non matérialisés côté UI.** Les hubs `NormeCadrage` et `CTCProcessus` modélisent bien les étapes, mais l'utilisateur ne voit ni bouton « confier au groupe », ni frise de transmission lisible ; il doit deviner le chemin.

---

## 3. Corrigé pendant le test

Aucun. Conformément à la règle du brief (« ne construire que si petit et sans risque »), tous les manques relevés sont des **fonctions manquantes de portée structurante** (nouveaux écrans, nouveaux modèles, circuits), et non de simples liens/libellés/boutons. Aucune modification n'a donc été appliquée pour ne pas casser l'existant.

---

## 4. Ce qui reste (priorisé)

**Bloquant**
- Création d'instructions/tâches/actions depuis l'UI (A1, C2).
- Signalement formel vers la CTC avec accusé de réception (B4).
- Dépôt de comptes rendus/PV rattachés à une réunion (B5).
- Espace « Rapports » de sous-commission (C1).

**Important**
- Matérialiser l'affectation norme→groupe et la frise de transmission COPIL→CTC→CTM (A2, B2).
- Avis structurés sur norme (favorable/réserve/défavorable) + notification (B3).
- Configurer les indicateurs de supervision (KPIs « Non configuré ») et seed de données de démo (A3, D1).

**Confort**
- Filtre « cette semaine » / normes actives par domaine (D1).
- Libellés des KPIs d'activité (« Avancement / Production / Qualité / Engagement / Complétude » non configurés) à rendre compréhensibles.

---

## 5. Décisions à me soumettre

1. **Rôle « Directeur général »** : créer un rôle/profil distinct (ou confirmer que le Président du COPIL en tient lieu) pour porter les scénarios A.
2. **Circuit A2/B2** : confirmer le chemin officiel COPIL → Secrétariat technique → groupe → experts (et qui est l'émetteur légitime de l'ordre de service).
3. **Périmètre du signalement (B4)** : le signalement doit-il être un objet dédié, ou un cas particulier de « demande » (réutiliser `PermissionRequest`/`CTCOperationalRequest`) ?
4. **Rapports (C1)** : le « rapport de sous-commission » est-il le même objet que le PV de réunion, ou un document distinct avec son propre workflow de validation ?
5. **Notifications (B3)** : qui est notifié (responsable du dossier, CTC, groupe) et par quel canal (in-app, email) ?

---

## 6. Résumé (10 lignes)

- L'application excelle côté **supervision** : B1 (suivi CTC) et A3/D1 (synthèse d'activité) sont réels et riches.
- Mais la chaîne de **production** fait défaut : on ne peut créer ni instruction, ni tâche, ni action depuis l'UI (A1, C2).
- Aucun **signalement** formel COPIL→CTC avec accusé de réception (B4).
- Les **comptes rendus/PV** et les **rapports de sous-commission** n'ont aucun écran de dépôt (B5, C1).
- Les circuits norme→groupe et transmission ST existent en modèle mais pas en gestes clairs (A2, B2).
- Le commentaire de norme existe mais sans avis structuré ni notification (B3).
- Les indicateurs de supervision sont « Non configuré » faute de données/config (A3, D1).
- Aucune correction appliquée : tous les manques sont structurants, hors du périmètre « petit et sans risque ».
- Priorité : 1) création tâches/instructions, 2) signalement, 3) PV/CR, 4) rapports.
- Cinq décisions de rôles/circuits à trancher avant implémentation (liste en §5).

---

## 7. Lot 1 — Instructions & tâches (A1, A2, C2) — IMPLÉMENTÉ

Décisions actées : DG **confondu avec le Président du COPIL** (pas de nouveau rôle) ; modèle de données validé (table unique `Demande`).

**Construit** (migration additive uniquement, français, journalisation) :
- `apps/governance/models.py` : `Demande` (type INSTRUCTION/ACTION/SIGNALEMENT, émetteur, destinataire, groupe/sous-commission/norme, objet, message, échéance, gravité, statut) + `JournalDemande` (transition, acteur, horodatage). Flux : ENVOYÉE → LUE → EN_COURS → EXÉCUTÉE, transitions validées côté serveur.
- `web/production_views.py` : `InstructionDashboardView` (`/instructions/`), `instruction_create`, `demande_transition`. Permissions par rôle : émission réservée au Directoire, transition par Directoire/responsable/responsable de groupe. Notifications (`create_notification_for_user`) aux destinataires.
- `templates/pilotage/instructions.html` : liste + tiroir de création (type, groupe/responsable, norme, objet, message, échéance) + boutons de statut + journal. Lien « Instructions » ajouté au tableau de bord Pilotage.
- `apps/governance/admin.py` : admin `Demande` + inline `JournalDemande`.

**Résultat (rejoué dans Chrome/Playwright)** :

| Scénario | Résultat | Clics | Capture |
|---|---|---|---|
| A1 — instruction à un groupe | ✅ créée puis LUE→EN_COURS→EXÉCUTÉE (journal complet) | 3 | `A1_avant.png`, `A1_apres_creation.png`, `A1_transition_executee.png` |
| A2 — confier une norme à un groupe | ✅ instruction avec norme rattachée | 3 | `A2_apres_creation.png` |
| C2 — action vers un responsable | ✅ action confiée à un expert (visible côté expert, transition possible) | 3 | `C2_apres_creation.png` |

Vérification permissions : `expert1` voit uniquement son action (`TEST C2`), pas les instructions de groupe, et n'a pas le bouton de création.
