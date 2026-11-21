# Audit de l’espace Expert Flutter

> Date : 18 novembre 2026
> Périmètre : `flutter_app/lib/features/expert/` et les endpoints `api/v1/` consommés.
> Référence de parité : espace expert web `templates/app/app.html` + `templates/static/js/norm-version-history.js`.
> Type : audit de parité, de bugs et de fonctionnalités manquantes, suivi de la mise en œuvre des correctifs.

## 1. Synthèse

L’espace Expert Flutter est fonctionnel et couvre les parcours principaux : éditeur de normes, sauvegarde de versions, votes, historique/diff/restauration, création de norme, messagerie, réunions, cotisations, processus ISO/légistique, profil, adhésions et notifications.

Points vérifiés :

- `flutter analyze lib/features/expert` : **aucun problème** après les correctifs.
- Tests ciblés Expert : **25/25 passent** (`test/expert_editor_test.dart` et `test/expert_modules_test.dart`), y compris focus responsive, sauvegarde, brouillons, vote, IA, groupes, ressources, messagerie, réunions et notifications.
- Les contrats d’API utilisés existent côté backend (experts, normes, réunions, ressources, messagerie, notifications, paiements).
- Recette visuelle régénérée sur base isolée : les onglets Réunions, Cotisations et Notifications sont lisibles en clair et en sombre, sur 1440 et 390 px.

Écarts principaux :

1. **Finances non cloisonnées** : l’écran affiche des cotisations, paiements et agrégats globaux à tous les experts. Le problème est d’abord backend (`CotisationViewSet`/`PaiementViewSet` non scopés), mais l’UI le rend visible.
2. **Réunions** : impossible de créer une réunion `SALLE` (LiveKit) ou de rejoindre la salle ; seul un lien externe peut être ouvert. Pas de quorum, de gestion d’invitations ni de lecteur de PV.
3. **Notifications** : pas de compteur de non-lues dans la barre, et « Ouvrir la réunion » ne fait qu’afficher l’onglet Réunions sans ouvrir la réunion.
4. **Pagination incomplète** : l’éditeur ne charge que 20 documents et l’historique que 10 versions, contre 100 côté web.
5. **Fonctions web absentes** : import/extraction de document, PDF de norme dans l’éditeur, verrouillage collaboratif, commentaires, édition riche, gestion des experts (statut/exclusion), CV/organisation, préférences de notifications.

## 2. État de mise en œuvre

Correctifs déjà appliqués :

- **P0 financier** : `CotisationViewSet` et le tableau de bord sont limités à la structure de l’expert (les coordinateurs CTC conservent le périmètre global) ; le nombre de structures est distinct. Tests `TestFinancialScoping` ajoutés dans `tests/test_payments_exports.py`.
- **P1 éditeur** : sauvegarde désactivée et bandeau lecture seule pour `PUBLISHED`/`ARCHIVED`, téléchargement PDF disponible.
- **P1 pagination** : documents, historique et notifications chargés par pages de 100.
- **P1 notifications** : badge des non-lues dans la barre (y compris mobile) et ouverture directe de la réunion depuis une notification.
- **P2 profil** : six préférences de notifications persistées, thème persistant via `SharedPreferences`, mise à jour du CV.
- **P2 experts** : actions Désactiver/Réactiver pour `ADMIN`/`COORD_CTC`.
- **P2 import** : import PDF/DOCX avec `extract_document`, préremplissage puis création de version.
- **Corrections visuelles** : contraste explicite des chips de période et de vote, dates de notifications formatées localement, libellés d’onglets compacts sans troncature à 1440 px, badge de notifications visible sur mobile, squelettes de chargement dans les modules.
- **Recette** : le script `scripts/check_expert_beta_browser.py` vérifie réellement le thème clair, retente le basculement et échoue explicitement si le thème ou le backend ne répond pas. Les anciennes captures claires dupliquées en sombre provenaient d’un basculement non appliqué, pas d’un bug de thème de l’écran Notifications.

Limites restantes :

- Parité LiveKit native impossible sans SDK : décision à formaliser (salle web `/app/salle/<id>/` ou maintien des liens externes).
- Gestion complète des experts par bureau CTM limitée par les permissions backend actuelles.
- Verrouillage collaboratif, commentaires, éditeur riche Quill et bouton d’installation réel restent à traiter.

## 3. Cartographie

| Onglet | Fichier principal | Endpoints |
|---|---|---|
| Éditeur | `widgets/expert_editor_tab.dart` | `norms/{id}/`, `votes/`, `vote/`, `create_version/`, `messages/contacts/`, `ia-agent/sessions/regulatory-advice/`, ressources mobile |
| Historique | `widgets/expert_history_tab.dart` | `norms/{id}/versions/`, `diff/`, `rollback-version/`, `pdf/` |
| Experts & Groupes / Adhésions | `widgets/expert_members_tab.dart` | `experts/`, `wg/`, `messages/contacts/`, `pending-*`, `admit-to-ctm/`, `reject/` |
| Réunions & Votes | `widgets/expert_meetings_tab.dart` | `mobile/expert/meetings/`, `details/`, `calendrier/`, `excuser/`, `checkin_presence/`, `vote/`, `close/`, `presences/{id}/` |
| Cotisations & Indemnités | `widgets/expert_financial_tab.dart` | `cotisations/`, `cotisations/dashboard/`, `paiements/`, `jetons/`, reçus PDF |
| Processus ISO / Légistique | `widgets/expert_workflow_tabs.dart` | `mobile/norms/`, `norms/{id}/pdf/` |
| Notifications | `widgets/expert_notifications_tab.dart` | `mobile/notifications/`, `mark_as_read/`, `mark_all_as_read/` |
| Profil | `widgets/expert_profile_tab.dart` | `experts/me/`, `experts/{id}/`, `my-affiliation/` |

Écran principal : `expert_screen.dart` (documents, activité, adhésions, thème, navigation, création de norme, ouverture d’une notification de norme).

## 4. Anomalies et bugs

### P0 — Données financières globales exposées

`api/v1/payments/views.py` :

- `CotisationViewSet.queryset = Cotisation.objects...` sans filtre par structure de l’expert.
- `PaiementViewSet.queryset = Paiement.objects...` sans filtre.
- `dashboard` calcule `total_paye` sur **tous** les paiements confirmés.

`widgets/expert_financial_tab.dart` affiche donc à un expert :

- toutes les cotisations de toutes les structures ;
- tous les paiements et reçus ;
- des libellés « Montant perçu » / « Reste à percevoir » qui laissent croire à des données personnelles.

Le web utilise aussi ces endpoints globaux : ce n’est pas une régression Flutter, mais une faille de cloisonnement à corriger côté API (puis éventuellement adapter les libellés).

Recommandation : filtrer par structure de l’expert (ou `user_ctm_scope`) pour les rôles non financiers, ou réserver l’écran aux rôles habilités. Ajouter des tests d’accès.

### P1 — Sauvegarde possible d’une norme publiée/archivée

- `expert_editor_tab.dart:62` calcule `_closed` pour `PUBLISHED`/`ARCHIVED`.
- Ce flag ne bloque que le vote (`:734`, `:748`), **pas** le bouton « Sauvegarder la version » (`:569-577`).
- Le backend refuse pourtant `create_version` sur ces statuts (`api/v1/norms/views.py`, action `create_version`).

Résultat : l’expert saisit un commentaire, clique, puis reçoit une erreur 400. La saisie est conservée par le brouillon local, mais le parcours est trompeur.

Recommandation : désactiver la sauvegarde et afficher un bandeau lecture seule lorsque `_closed` est vrai.

### P1 — Documents limités à la première page (20)

`expert_screen.dart:132-148` appelle `/api/v1/sidebar/documents/` sans `page` ni `page_size`. La pagination globale DRF vaut `PAGE_SIZE = 20` (`config/settings.py`), et aucun chargement de page suivante n’existe.

Le web charge `/api/v1/norms/?page_size=100` (`templates/app/app.html:7153`). Au-delà de 20 normes dans le périmètre, l’expert Flutter ne peut plus ouvrir les plus anciennes depuis la sidebar ; la recherche est également limitée aux 20 chargées (`_filteredDocuments`).

Recommandation : charger `/api/v1/norms/?page_size=100` comme le web, ou implémenter une pagination/scroll infini.

### P1 — Historique limité aux 10 dernières versions

`expert_history_tab.dart:71` appelle `/api/v1/norms/$id/versions/` sans paramètres. L’action backend applique `per_page=10` par défaut (`api/v1/norms/views.py`), et Flutter ne parcourt pas les pages.

Le web demande explicitement `page=...&per_page=100` (`templates/static/js/norm-version-history.js:19`).

Conséquence : au-delà de 10 versions, les versions anciennes, le diff et la restauration ne sont plus accessibles. Le sélecteur de versions est de plus alimenté uniquement par ces 10 éléments.

### P1 — Notifications sans compteur ni navigation profonde

- Aucun appel à `/api/v1/mobile/notifications/unread_count/` dans l’espace Expert. Le web l’utilise (`app.html:5181`) pour le badge.
- `expert_screen.dart:231-234` : pour une notification de réunion, le callback fait seulement `setState(() => _tab = 3)`. Il n’ouvre ni la réunion ni ses détails.
- Le web route vers `openMeetingReader(meetingId)` et les modules `meeting-reader`/`norm-reader`.

Recommandation : ajouter le badge non-lus et transmettre l’ID de réunion à l’onglet pour ouvrir directement `_MeetingDetails`.

### P2 — Réunions : pas de salle LiveKit, pas de quorum

La création Flutter (`expert_meetings_tab.dart:60-150`) ne propose que :

- `mode = PRESENTIEL` si le lien est vide ;
- `mode = EXTERNE` sinon.

Le backend supporte `mode = SALLE` et les actions `rejoindre`, `ouvrir_salle`, `cloturer_salle`, `en_ligne`, `presences_detail`. Le web active la salle (`app.html:3049`, `:3067`, `:3093` → `/app/salle/{id}/`).

Conséquences Flutter :

- impossible de planifier une réunion dans la salle de la plateforme ;
- « Rejoindre la réunion » ouvre uniquement un lien externe (`s.open(...)`) ;
- pas de jeton LiveKit, pas de session de présence, pas de suivi en ligne ;
- pas de quorum ni de synthèse de présence ;
- pas de prévisualisation/téléchargement du PV, alors que le web affiche le PV et permet son aperçu.

### P2 — Gestion des experts absente

Le web propose `manage-experts` (`app.html:4988-5178`) : changement de statut (`PATCH /experts/{id}/`) et exclusion (`POST /experts/{id}/reject/`).

Flutter ne couvre que les **adhésions en attente** (`ExpertAdhesionsTab`). Un responsable ne peut ni suspendre/réactiver un expert ni l’exclure depuis l’application.

### P2 — Profil incomplet par rapport au web

`expert_profile_tab.dart` :

- l’interrupteur « Recevoir des notifications » (`:625-634`) est un simple état local, non chargé/enregistré via `/mobile/notification-preferences/` ;
- le thème (`expert_screen.dart:25`, `:242`) n’est pas persisté ;
- le bouton « Installer l’application » a `onPressed: () {}` (`:673`), donc inerte ;
- aucun lien/parcours « Actualiser mon CV et choisir ma nouvelle sous-commission », présent côté web (`app.html:4671` → `web:expert_organisation_update`).

### P2 — Import/extraction de document absent

La création manuelle d’une norme existe (`expert_screen.dart:37-106`). En revanche, aucun équivalent Flutter de l’import web avec `extract_document` : l’expert ne peut pas partir d’un PDF/DOCX pour créer le contenu.

### P2 — Éditeur sans PDF, verrouillage ni commentaires

Présents côté API, absents de l’éditeur Flutter :

- téléchargement PDF de la norme (`norms/{id}/pdf/`), utilisé seulement en légistique/validation ;
- verrouillage collaboratif (`lock/`/`unlock/`) : deux appareils Flutter peuvent sauvegarder en concurrence (dernier écrivain gagne) ;
- commentaires internes (`comments/`) ;
- éditeur riche : `flutter_quill` est dans `pubspec.yaml` mais utilisé uniquement côté CTC (`ctc_reports.dart`), l’éditeur Expert reste un `TextField` plein texte.

### P3 — Divers

- `_loadVersions()` avec `docId == null` modifie `_versions` sans `setState` (`expert_history_tab.dart`).
- Dialogues à largeur fixe : messagerie `SizedBox(780×650)` (`expert_messaging.dart:45`) et détails `SizedBox(width: 650)` (`expert_module.dart:127`). Ils sont contraints par le dialogue Flutter, mais restent peu adaptés aux petits écrans ; à valider sur 360-390 px.
- `ExpertResources` n’a pas de repli local fonctionnel en cas d’échec réseau : le cache local n’est lu que si les données distantes sont vides (`expert_resources.dart:52-56`), pas si l’appel échoue.
- `/expert` n’a pas de garde de rôle dans le routeur : tout utilisateur authentifié peut ouvrir la route, même si les endpoints renvoient ensuite des erreurs ou des listes vides.

## 5. Fonctionnalités qui fonctionnent

- Éditeur : chargement, brouillons locaux par document, commentaire obligatoire, sauvegarde, détection des modifications, restauration, compteur d’activité.
- Votes de norme : chargement, vote, synthèse, blocage si norme close.
- IA : demande, application des corrections, gestion des réponses obsolètes, changement de document.
- Historique : versions, diff, rollback, PDF (dans l’onglet légistique).
- Documents : création de projet de norme, sélection, partage, ressources synchronisées avec révision.
- Messagerie : contacts, conversation, non-lus, pièces jointes.
- Réunions : liste, filtres, agenda `.ics`, émargement, excuse, vote, clôture/PV, présence modifiable par les gestionnaires.
- Adhésions : accepter avec WG obligatoire, refuser avec motif.
- Profil : consultation, édition, changement de mot de passe, thème visuel immédiat.
- Notifications : liste, marquage lu / tout lu.

## 6. Plan d’action proposé

### P0

1. ✅ Cloisonner `CotisationViewSet`, `PaiementViewSet` et `dashboard` par structure/périmètre, ou restreindre l’onglet financier aux rôles habilités.

### P1

2. ✅ Désactiver la sauvegarde et afficher un état lecture seule pour `PUBLISHED`/`ARCHIVED`.
3. ✅ Charger 100 documents et 100 versions (ou paginer), comme le web.
4. ✅ Ajouter le compteur de notifications non lues et la navigation vers la réunion/la norme.
5. ⏳ Décider du périmètre réunions : parité complète `SALLE`/LiveKit ou maintien documenté des liens externes.

### P2

6. ✅ Gestion des experts : désactivation/réactivation. ⏳ Exclusion complète et filtrage par bureau CTM selon permissions backend.
7. ✅ Import/extraction de document PDF/DOCX.
8. ✅ Préférences de notifications persistées, thème persisté, CV. ⏳ Bouton d’installation réel et parcours complet d’organisation.
9. ⏳ PDF fait ; verrouillage collaboratif, commentaires et éditeur riche Quill restent à faire.
10. ⏳ Ajouter quorum, gestion d’invitations et lecteur de PV.

### P3

11. ⏳ Corriger `setState` de l’historique, rendre les dialogues adaptatifs, ajouter un repli local réel aux ressources, et ajouter une garde de rôle sur `/expert`.

## 7. Vérifications

Commandes utilisées :

```bash
cd flutter_app
/home/minato/flutter/bin/flutter analyze lib/features/expert
/home/minato/flutter/bin/flutter test \
  test/expert_editor_test.dart \
  test/expert_modules_test.dart

cd ..
./mon_env/bin/python -m pytest \
  tests/test_payments_exports.py::TestFinancialScoping \
  -q --no-header --nomigrations -p no:cacheprovider
```

Résultats : `flutter analyze` sans erreur ; **25 tests Flutter passent** ; **2 tests backend de cloisonnement financier passent**.

Recette visuelle :

```bash
./mon_env/bin/python scripts/prepare_expert_beta_review.py
EXPERT_REVIEW_TABS=3,4,7 ./mon_env/bin/python scripts/check_expert_beta_browser.py 8
```

Les captures `reports/expert_beta/8_tab{3,4,7}_{390,1440}_{dark,light}.png` confirment les chips lisibles, les dates locales, le badge mobile et l’absence de troncature du libellé sélectionné. Le serveur de recette doit écouter sur `127.0.0.1:1111` (URL API par défaut du build web) et le script vérifie désormais réellement le thème clair.

Limite : les tests Flutter mockent Dio ; ils valident les widgets et les payloads, pas l’intégration réelle avec Daphne/PostgreSQL. Les parcours LiveKit, notifications push et cloisonnement financier nécessitent des tests d’intégration ou E2E côté serveur.
