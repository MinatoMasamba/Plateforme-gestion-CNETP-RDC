# Navigation de l'espace CTC — interface web

Documentation de référence de la Coordination du Secrétariat technique (CTC) :
points d'entrée, structure de l'interface, navigation commune, navigation propre à
chaque rôle et inventaire des modules web.

Sources vérifiées : `web/ctc_views.py`, `web/urls.py`, `templates/ctc/app/app.html`,
`templates/ctc/app/components/`, `templates/ctc/composants/`, `apps/governance/models.py`.

---

## 1. Accès à l'espace

| Élément | Valeur |
|---|---|
| URL principale | `/ctc/` (route `web:ctc_dashboard`) |
| Vue | `CTCDashboardView` → `templates/ctc/app/app.html` |
| Authentification | session Django (`login_required`, redirection `/se-connecter/`) |
| Condition d'accès | posséder un `Expert` **et** une adhésion `CTCMembership` |
| Refus | redirection vers `/app/` (espace expert) avec message |
| Verrou global | si `PlatformFreeze` est actif, bandeau rouge et actions serveur suspendues (HTTP 423) |

L'espace CTC est distinct de l'espace expert (`/app/`) et de l'espace Pilotage.
Un même utilisateur peut avoir accès à plusieurs espaces selon ses adhésions.

---

## 2. Architecture de l'interface

L'interface est un **shell Django rendu côté serveur** : tous les modules sont inclus
dans `app.html`, la navigation ne fait que basculer leur visibilité (`window.switchView`).

```
┌──────────────────────────────────────────────────────────────┐
│ Bandeau institutionnel (RDC — Cabinet interministériel)      │
├──────────────────────────────────────────────────────────────┤
│ TOPBAR : titre, Annuaire & Mail, Réunion Meet, Espace Drive, │
│          notifications, profil / déconnexion                 │
├───────────────┬──────────────────────────────────────────────┤
│ SIDEBAR       │ MAIN — un seul `view-container` visible      │
│ Travail       │ #view-dashboard / #view-dossiers / ...       │
│ Supervision   │                                              │
│ Outils        │                                              │
│ Système       │                                              │
│ Profil        │                                              │
└───────────────┴──────────────────────────────────────────────┘
```

### 2.1 Routage par ancre

- La vue par défaut est `dashboard`.
- `window.switchView('dossiers')` cible `#view-dossiers` et met à jour le hash
  (`#dossiers`) via `history.replaceState`.
- Au chargement, `location.hash` est lu ; `hashchange` est écouté.
- La sidebar reçoit la vue active via `window.updateSidebarForTab`.

Identifiants de vues disponibles :

`dashboard`, `dossiers`, `assignations`, `ctc_requests`, `assistant_executif`,
`financial`, `statistiques`, `experts`, `tracabilite`, `homologations`,
`instructions`, `reunions`, `drive`, `archives`, `parametres`.

> **Important** : tous les conteneurs sont rendus pour tout membre CTC. Le menu
> n'est qu'un filtre d'affichage ; une visite directe par hash
> (`/ctc/#financial`, `/ctc/#assistant_executif`, ...) affiche le module même s'il
> n'est pas dans le menu du rôle. Les données et les actions restent filtrées ou
> refusées côté serveur.

### 2.2 Comportement mobile et tablette

| Seuil | Comportement |
|---|---|
| `< 768 px` | sidebar masquée ; bouton hamburger `Ouvrir le menu` ; overlay `mobile-dock` ; fermeture par clic extérieur ou `Échap` |
| `>= 768 px` | sidebar visible, redimensionnable de 256 à 480 px (poignée, largeur mémorisée dans `localStorage: ctc-sidebar-width`) |
| `< 640 px` | logo et sous-titre de la topbar masqués |
| `>= 1024 px` | raccourcis topbar « Annuaire & Mail », « Réunion Meet », « Espace Drive » visibles |

Le bouton hamburger porte le libellé accessible `aria-label="Ouvrir le menu"`.

### 2.3 Bandeau de verrouillage

Si la plateforme est verrouillée par le Président du Comité de Pilotage :
bandeau rouge en haut du shell, mention de l'auteur du verrouillage, et toutes les
actions CTC (réception, revue, transmission, instruction, demande) renvoient une
erreur serveur « Plateforme verrouillée ».

---

## 3. Résolution des rôles

Le sous-rôle CTC (`ctc_sub_role`) est dérivé de deux informations :

1. `CTCMembership.role` (16 valeurs possibles) ;
2. l'acronyme de la structure de l'expert (pour les rôles à double poste).

### 3.1 Table de correspondance

| Rôle CTCMembership | Acronyme structure | Sous-rôle résolu | Pôle |
|---|---|---|---|
| `COORDINATOR` | — | `coordonnateur_principal` | Direction des Opérations |
| `VICE_COORDINATOR` | — | `coordonnateur_adjoint` | Direction des Opérations |
| `EXECUTIVE` | — | `assistant_executif` | Direction des Opérations |
| `ISO_EXPERT` | `ACGT` | `veille_acgt` | Analyse & Ingénierie documentaire |
| `ISO_EXPERT` | autre / vide | `veille_sg` | Analyse & Ingénierie documentaire |
| `LEGAL` | — | `expert_juridique` | Analyse & Ingénierie documentaire |
| `ENVIRONMENTAL` | — | `sauvegardes_ci` | Analyse & Ingénierie documentaire |
| `PLANNER` | — | `planification_recons` | Analyse & Ingénierie documentaire |
| `ECONOMIST` | — | `economiste_foner` | Analyse & Ingénierie documentaire |
| `SCIENTIFIC` | — | `scientifique_inbtp` | Analyse & Ingénierie documentaire |
| `ACCOUNTANT` | — | `gaf` | Logistique, Communication & Relations extérieures |
| `ENQUIRY_MANAGER` | — | `responsable_enquetes` | Logistique, Communication & Relations extérieures |
| `INDUSTRIAL` | — | `liaison_fec` | Logistique, Communication & Relations extérieures |
| `COMMUNICATOR` | — | `communicateur` | Logistique, Communication & Relations extérieures |
| `CARTOGRAPHER` | `BEAU` | `sig_beau` | Bureau d'Appui Technique et Numérique |
| `CARTOGRAPHER` | `OVD` | `sig_ovd` | Bureau d'Appui Technique et Numérique |
| `CARTOGRAPHER` | autre | `sig_beau` | Bureau d'Appui Technique et Numérique |
| `DATA_ENTRY` | — | `operateur_saisie` | Bureau d'Appui Technique et Numérique |
| `IT_ADMIN` | `BTC` | `it_btc` | Bureau d'Appui Technique et Numérique |
| `IT_ADMIN` | autre / vide | `it_sg_itp` | Bureau d'Appui Technique et Numérique |

Soit **19 sous-rôles dérivés** répartis en 4 pôles. La matrice Phoenix du Secrétariat
technique décrit par ailleurs 24 postes (4 + 5 × 4) ; tous ne sont pas nécessairement
couverts par cette table.

### 3.2 Privilèges calculés

| Privilège | Sous-rôles concernés |
|---|---|
| `is_direction` | coordonnateur_principal, coordonnateur_adjoint, assistant_executif |
| `can_route_documents` | tous les rôles Direction |
| `can_arbitrate_delays` | coordonnateur_principal, coordonnateur_adjoint |
| `can_transmit_directoire` | coordonnateur_principal, coordonnateur_adjoint |
| `can_approve_ctc_requests` | assistant_executif |
| `can_translate_iso` | veille_acgt, veille_sg |
| `can_legistique_ctc` | expert_juridique |
| `can_eco_env_matrix` | economiste_foner, sauvegardes_ci |
| `can_methodologie_chronogramme` | planification_recons, scientifique_inbtp |
| `can_enquete_publique` | responsable_enquetes |
| `can_cadrage_industriel` | liaison_fec |
| `can_grand_livre` | gaf |
| `can_upload_maps` | sig_beau, sig_ovd |
| `can_admin_system` | it_btc, it_sg_itp |
| `can_fast_entry` | operateur_saisie |
| `readonly_logistique` / `must_use_amendment` | tous les rôles Analyse |
| `blocked_scientific_write` | tous les rôles Logistique |
| `blocked_political` | tous les rôles Numérique |

---

## 4. Navigation commune à tous les rôles

### 4.1 Topbar

| Élément | Action | Visibilité |
|---|---|---|
| « Annuaire & Mail » | ouvre la modale **Annuaire de la Cellule (CTC)** | `>= 1024 px` |
| « Réunion Meet » | bascule vers `#reunions` | `>= 1024 px` |
| « Espace Drive » | bascule vers `#drive` | `>= 1024 px` |
| Cloche de notifications | bascule vers `#assistant_executif` si demandes en attente, sinon `#assignations` | si compteur > 0 |
| Bloc profil | ouvre le panneau identité (nom, poste ou pôle, structure) et « Se déconnecter » | toujours |
| Bandeau `RDC — Cabinet Interministériel de Co-Gouvernance` | informatif | toujours |

La cloche additionne `pending_ctc_requests_count` et `my_pending_reviews_count`.

### 4.2 Sidebar — sections permanentes

| Section | Entrée | Vue / hash |
|---|---|---|
| Supervision | Suivi statistique | `statistiques` |
| Supervision | Experts et affectations | `experts` |
| Supervision | Traçabilité | `tracabilite` |
| Supervision | Homologations | `homologations` |
| Outils | Instruction | `instructions` |
| Outils | Réunions | `reunions` |
| Système | Archives | `archives` |
| Système | Paramètres | `parametres` |
| Pied de sidebar | Profil de l'expert | `/profil/` (`web:expert_profile`) |

Ces sections sont ajoutées à la configuration de **tous** les sous-rôles.

### 4.3 Modales et composants transverses

| Composant | Déclencheur | Rôle |
|---|---|---|
| Annuaire CTC | topbar « Annuaire & Mail » | rechercher un membre, filtrer par pôle, écrire via client mail |
| Modale de permission | widget/console demandant un accès | créer une demande opérationnelle vers l'Assistant Exécutif |
| Agent IA | bouton flottant en bas à droite | assistant réglementaire contextuel (`widget_scope='ctc'`) |
| Notifications toast | actions asynchrones | confirmation/erreur |
| Modale CTM / groupes | incluse dans le shell | présente mais aucun déclencheur actif dans les modules actuels |
| Modale détail CTM | fichier présent mais non inclus | non montée dans l'interface actuelle |

---

## 5. Navigation par rôle

### 5.1 Direction des Opérations

#### `coordonnateur_principal` et `coordonnateur_adjoint`

- **Menu Travail** : Tableau de bord, Dossiers normatifs, Mes Assignations,
  Demandes à Traiter.
- **Supervision / Outils / Système** : menus communs.
- **Tableau de bord** :
  - carte « Mon rôle et mes droits » : Acheminement documentaire, Transmission au Pilotage ;
  - hub **Acheminement documentaire** (dossiers du circuit CTC, bouton
    « Transmettre » quand dossier industriel complet) ;
  - KPI, graphiques, travail attribué, dossiers, suivi statistique.
- **Dossiers normatifs** : bouton « Valider l'introduction » à l'étape
  `RECEPTION` lorsque l'indexation est terminée ; lecture seule sinon.
- **Actions serveur** : `validate_intake`, `transmettre-pilotage`, arbitrage des
  retards (privilège calculé), consultation des revues terminées.

#### `assistant_executif`

- **Menu Travail** : Tableau de bord, **Assistant Exécutif**, Mes Assignations.
  (Pas d'entrée « Dossiers normatifs » ni « Demandes à Traiter » dans son menu.)
- **Tableau de bord** : badge « Demandes à traiter » ; hub d'acheminement
  documentaire (rôle Direction).
- **Module Assistant Exécutif** : réceptions du Secrétariat, demandes
  opérationnelles en attente, suivi des transmissions.
- **Dossiers normatifs** (accès direct) : bouton « Réceptionner » à l'étape
  `RECEPTION` tant que le dossier n'est pas enregistré.
- **Actions serveur** : `receive`, approbation/rejet des demandes opérationnelles.
  La cloche topbar pointe vers ce module.

### 5.2 Pôle Analyse & Ingénierie documentaire

Menu Travail commun : Tableau de bord, Dossiers normatifs, Mes Assignations,
Demandes à Traiter. Tous ont `readonly_logistique` et `must_use_amendment`.

| Sous-rôle | Widget du tableau de bord | Tâches / actions |
|---|---|---|
| `veille_acgt`, `veille_sg` | Conformité internationale & traduction | examen `ISOReview` : accepter/refuser, notes d'harmonisation |
| `expert_juridique` | Contrôle de légistique | examen `LegisticReview` : observations et validation CTC |
| `sauvegardes_ci` | Matrice impacts éco-environnementaux | examen `EcologicalReview` |
| `economiste_foner` | Matrice impacts éco-environnementaux | examen `EconomicReview` |
| `planification_recons` | Méthodologie & Chronogramme | validation `ScheduleReview` côté planificateur |
| `scientifique_inbtp` | Méthodologie & Chronogramme | validation `ScheduleReview` côté scientifique |

Les tâches attribuées apparaissent aussi dans **Mes Assignations** (catégorie
`personnelle`), avec lien direct vers la lecture du dossier.

### 5.3 Pôle Logistique, Communication & Relations extérieures

Tous les rôles de ce pôle ont `blocked_scientific_write`.

| Sous-rôle | Menu Travail spécifique | Widget / module | Actions |
|---|---|---|---|
| `gaf` | Tableau de bord, **Budget & Comptabilité**, Mes Assignations, Demandes à Traiter | Grand livre comptable | consultation financière (interface de démonstration, voir limites) |
| `responsable_enquetes` | menu commun | Modération de l'enquête publique (Art. 12) | modération des contributions d'enquête |
| `liaison_fec` | menu commun | Liaison industrielle (FEC) | consultation industrielle : accepter/refuser |
| `communicateur` | menu commun | Communication & vulgarisation | module annoncé « en développement » |

### 5.4 Bureau d'Appui Technique et Numérique

Tous les rôles de ce pôle ont `blocked_political`.

| Sous-rôle | Menu Travail spécifique | Widget / module | Actions |
|---|---|---|---|
| `sig_beau`, `sig_ovd` | menu commun | Serveur géospatial / SIG | dépôt et consultation cartographique |
| `operateur_saisie` | menu commun | Saisie massive & indexation | bouton « Finaliser l'indexation » à l'étape `RECEPTION` |
| `it_btc`, `it_sg_itp` | Tableau de bord, Dossiers normatifs, Mes Assignations, Demandes à Traiter, **Espace Drive** (configuration) | Administration système & dépôt | sauvegarde globale, réglages Drive, supervision technique |

> L'entrée « Espace Drive » est bien produite par le serveur pour les rôles IT,
> mais le filtre `sidebarAllowedViews` du template ne contient pas `drive` :
> elle n'apparaît donc **pas** dans la sidebar. Le module reste accessible par le
> raccourci topbar « Espace Drive » et par `#drive`.

### 5.5 Synthèse « Menu Travail » par rôle

| Rôle(s) | Entrées du menu Travail |
|---|---|
| coordonnateur_principal, coordonnateur_adjoint, veille_acgt, veille_sg, expert_juridique, sauvegardes_ci, planification_recons, economiste_foner, scientifique_inbtp, responsable_enquetes, liaison_fec, communicateur, sig_beau, sig_ovd, operateur_saisie | Tableau de bord · Dossiers normatifs · Mes Assignations · Demandes à Traiter |
| gaf | Tableau de bord · Budget & Comptabilité · Mes Assignations · Demandes à Traiter |
| assistant_executif | Tableau de bord · Assistant Exécutif · Mes Assignations |
| it_btc, it_sg_itp | Tableau de bord · Dossiers normatifs · Mes Assignations · Demandes à Traiter · Espace Drive (filtré de la sidebar) |

---

## 6. Inventaire des modules web

| Vue (`#hash`) | Libellé | Contenu | Données / état |
|---|---|---|---|
| `dashboard` | Tableau de bord | droits du poste, KPI, graphiques, travail attribué, dossiers, suivi statistique, hub Direction, outils métier | données serveur |
| `dossiers` | Dossiers normatifs | pipeline 5 étapes (`RECEPTION`, `GEOSPATIAL`, `MULTI_REVIEW`, `INDUSTRIAL`, `SIGNED_OUT`), filtres, actions par étape | données serveur |
| `assignations` | Mes Assignations | tâches personnelles, Pilotage, experts extérieurs ; recherche et filtre par catégorie | données serveur |
| `ctc_requests` | Demandes à Traiter | demandes opérationnelles en attente, tiroir d'examen, approuver/refuser | alimenté pour l'Assistant Exécutif |
| `assistant_executif` | Assistant Exécutif | réceptions, demandes, transmissions | données serveur |
| `financial` | Budget & Comptabilité | budget, engagements, lignes de dépenses | **valeurs statiques de démonstration** |
| `statistiques` | Suivi statistique | KPI, graphiques, sous-commissions, groupes, normes, lecture seule | données serveur |
| `experts` | Experts et affectations | annuaire, profils complets/incomplets, affectations, activité selon habilitation | données serveur |
| `tracabilite` | Traçabilité | journal des opérations (date, action, objet, référence, auteur, canal) | données serveur |
| `homologations` | Homologations | normes homologuées/publiées, preuve JO | données serveur |
| `instructions` | Instruction | instruction générale, instructions par CTM, création, lien rapport COPIL | données serveur |
| `reunions` | Réunions | écran « Non disponible » (service d'enregistrement non raccordé) | **placeholder** |
| `drive` | Espace Drive | stockage partagé, recherche, dossiers, synchronisation | selon configuration Drive |
| `archives` | Archives | normes archivées, recherche, filtre par date | données serveur |
| `parametres` | Paramètres | thème, notifications, sauvegarde (IT), intégrations et règles | données serveur + services |

### 6.1 Détail des droits par module

- **Dossiers normatifs** :
  - `assistant_executif` → « Réceptionner » ;
  - `operateur_saisie` → « Finaliser l'indexation » ;
  - `coordonnateur_principal` / `coordonnateur_adjoint` → « Valider l'introduction » ;
  - tous → « Lire ».
- **Assignations** : catégories `personnelle` (traitement CTC + examens),
  `pilotage` (réception Pilotage), `externe` (experts extérieurs).
- **Paramètres** :
  - notifications : tous les membres ;
  - sauvegarde globale : `can_admin_system` et base SQLite ;
  - bascule Drive auto : `can_admin_system` ;
  - cartes « Délégation », « ISO auto », « Anti-spam », « Debug » : selon le pôle,
    affichées comme non disponibles.
- **Experts** : la colonne Activité n'apparaît que si
  `expert_directory.can_view_contributions`.
- **Statistiques** : le panneau détaillé des sources de tâches n'apparaît que si
  `ctc_can_view_task_sources`.

Les modules non branchés doivent afficher explicitement une indisponibilité plutôt
qu'une valeur inventée.

---

## 7. Pages et routes hors shell

| Route | Nom | Accès | Usage |
|---|---|---|---|
| `/ctc/norme/<pk>/lecture/` | `web:ctc_norme_read` | membre CTC | lecture seule du dossier, versions, commentaires, PDF, impression, QR |
| `/ctc/norme/<pk>/qr/` | `web:ctc_norme_qr` | authentifié | QR de traçabilité |
| `/ctc/ctm/<number>/` | `web:ctc_ctm_detail` | membre CTC | détail CTM, WG, affectations, normes ; **aucun lien depuis le shell** |
| `/ctc/copil/rapport/` | `web:ctc_copil_rapport` | authentifié | dernier rapport COPIL (format A4) |
| `/ctc/copil/rapport/<pk>/` | `web:ctc_copil_rapport_detail` | authentifié | rapport COPIL ciblé |
| `/ctc/instructions/creer/` | `web:ctc_instruction_create` | membre CTC | POST de création d'instruction |
| `/ctc/demande-operationnelle/` | `web:ctc_operational_request` | membre CTC | POST de demande d'accès |
| `/ctc/approuver-demande/<pk>/` | `web:ctc_approve_request` | assistant_executif | POST approbation/rejet |
| `/ctc/methodologie/<pk>/` | `web:ctc_methodology_action` | planificateur / scientifique assigné | POST statut chronogramme |
| `/ctc/revue/<type>/<pk>/` | `web:ctc_review_action` | veille / écologique / économique | POST décision d'examen |
| `/ctc/consultation-industrielle/<pk>/` | `web:ctc_industrial_action` | liaison_fec | POST décision FEC |
| `/ctc/dossiers/<pk>/reception/` | `web:ctc_reception_action` | assistant / saisie / coordonnateur selon action | POST réception, indexation, validation |
| `/ctc/dossiers/<pk>/transmettre-pilotage/` | `web:ctc_transmit_pilotage` | coordonnateurs | POST transmission au Pilotage |
| `/ctc/parametres/notifications/` | `web:ctc_notification_settings` | membre CTC | préférences de notification |
| `/ctc/parametres/sauvegarde/` | `web:ctc_backup` | can_admin_system | sauvegarde vérifiée |
| `/ctc/parametres/drive/` | `web:ctc_drive_settings` | can_admin_system | activation de la synchronisation |
| `/api/ctc/contexte/` | `web:ctc_context_api` | membre CTC | contexte de privilèges JSON |
| `/api/v1/legistic-reviews/<id>/validate-ctc/` | API validation | expert_juridique | action du widget légistique |

---

## 8. Parcours types

### 8.1 Réception d'un dossier (Direction)

1. `assistant_executif` : `#dossiers` → « Réceptionner ».
2. `operateur_saisie` : `#dossiers` → « Finaliser l'indexation ».
3. `coordonnateur_principal` / `_adjoint` : `#dossiers` → « Valider l'introduction ».
4. Le dossier passe à `GEOSPATIAL` ou `MULTI_REVIEW` et les examens sont créés.

### 8.2 Examens parallèles (Analyse)

1. Chaque analyste ouvre son widget sur `#dashboard` ou `#assignations`.
2. Il accepte/refuse son examen (`ISOReview`, `LegisticReview`,
   `EcologicalReview`, `EconomicReview`, `ScheduleReview`).
3. Quand tous les examens sont terminés, les coordonnateurs sont notifiés.

### 8.3 Consultation industrielle et sortie (Logistique / Direction)

1. `liaison_fec` traite la consultation industrielle dans son widget.
2. Le coordonnateur utilise le hub « Acheminement documentaire » pour
   « Transmettre » le dossier complet au Pilotage (`SIGNED_OUT`).
3. Le Président et le Rapporteur du Pilotage sont notifiés.

### 8.4 Demande d'accès (tous les membres)

1. Un membre ouvre la modale de permission et saisit ressource + motif.
2. La demande est transmise à l'`assistant_executif` (notification).
3. L'Assistant Exécutif approuve ou rejette depuis `#assistant_executif` ou
   `#ctc_requests`.
4. Le demandeur reçoit la décision en notification.

---

## 9. Limites et incohérences connues

1. **Accès direct par hash** : le menu filtre l'affichage, pas la route. Un membre
   peut ouvrir un module hors de son menu (`#assistant_executif`, `#financial`, ...).
   Les actions restent protégées côté serveur, mais l'écran peut être vide ou
   hors périmètre.
2. **Espace Drive absent de la sidebar IT** : `drive` manque dans
   `sidebarAllowedViews` de `sidebar_module.html` ; l'entrée est donc filtrée.
3. **Budget & Comptabilité statique** : montants codés en dur (USD), pas de
   rattachement serveur.
4. **Réunions non disponibles** : écran placeholder.
5. **Demandes à Traiter** : la liste `pending_ctc_requests` n'est alimentée que
   pour l'`assistant_executif` ; les autres rôles voient une page vide.
6. **Assignations « Experts extérieurs »** : `my_external_assignments` n'est jamais
   fourni par le contexte ; le filtre `externe` reste vide.
7. **Console d'arbitrage des retards** : le privilège `can_arbitrate_delays` est
   calculé, mais aucun module dédié n'est monté dans le shell.
8. **Modale CTM / groupes** : incluse dans le DOM mais aucun déclencheur actif.
9. **Modale détail CTM** : fichier `ctm_detail_modal.html` non inclus.
10. **Détail CTM** : route `/ctc/ctm/<number>/` fonctionnelle mais non liée depuis
    l'interface du shell.
11. **Numérotation des rôles** : 19 sous-rôles dérivés dans le code, alors que la
    documentation du module en annonce 20 et que Phoenix décrit 24 postes.

---

## 10. Fichiers de référence

| Fichier | Rôle |
|---|---|
| `web/ctc_views.py` | contexte de privilèges, actions, routes de l'espace |
| `web/urls.py` | déclaration des routes `web:ctc_*` |
| `templates/ctc/app/app.html` | shell, liste des vues, routeur par hash |
| `templates/ctc/app/components/sidebar_module.html` | menus, filtre des vues, mobile, redimensionnement |
| `templates/ctc/app/components/topbar_module.html` | raccourcis, notifications, profil |
| `templates/ctc/app/components/dashboard_module.html` | widgets conditionnels par privilège |
| `templates/ctc/app/components/*.html` | modules de vue |
| `templates/ctc/composants/*.html` | sous-widgets métier et consoles |
| `apps/governance/models.py` | `CTCMembership`, `PosteNominatifCTC`, rôles |

---

## 11. Cinq espaces ST v3 (passe du 31 octobre 2026)

Lorsqu'un mandat ST v3 est actif (`STAccessPolicy` + `MandatOrganisation`), le shell ne présente plus les anciens menus par sous-rôle : il affiche l'espace du poste et un menu de 5 à 7 entrées.

| Espace | Postes | Accueil |
|---|---|---|
| Coordination | 1 à 7 | `#coordination` |
| Pôle 1 — Planification et suivi | 8 et 9 | `#espace_p1` |
| Pôle 2 — Documentation, codification et PTN | 10 à 12 | `#espace_p2` |
| Pôle 3 — Juridique, administratif et financier | 13 à 16 | `#espace_p3` |
| Pôle 4 — Appui techniques et Formation | 17 à 19 | `#espace_p4` |

Les cinq identifiants d'accueil partagent un seul conteneur serveur `view-coordination` ; le routeur les ramène tous vers l'accueil de l'espace courant. Les modules propres aux espaces sont ajoutés progressivement. Les modules non encore raccordés affichent un écran « Module à venir » et non des valeurs fictives.

### Accueil commun

- Bloc « À traiter maintenant »
- Bloc « En attente d'autres personnes »
- Bloc « Échéances de la semaine »
- Bloc « Derniers éléments traités »
- Colonne alertes et échéances
- Bandeau bas aide et contact du Pôle 4

### Modules raccordés dans cette passe

- Coordination : file de validation, retards, demandes, réunions administratives.
- Pôle 2 : dossiers à indexer, registre des PTN (versions et confirmation).
- Transversal : recherche globale, audit, mes demandes, organisation du ST.

### Vérification visuelle

```bash
mon_env/bin/python scripts/prepare_five_spaces_db.py --source db.sqlite3 --dest /tmp/five_spaces.sqlite3 --manifest reports/5_espaces/roles.json
SQLITE_NAME=/tmp/five_spaces.sqlite3 DEBUG=True mon_env/bin/python manage.py runserver 127.0.0.1:1113 --noreload
SQLITE_NAME=/tmp/five_spaces.sqlite3 mon_env/bin/python scripts/capture_five_spaces.py --base-url http://127.0.0.1:1113 --out reports/5_espaces
```

Le rapport `reports/5_espaces/INDEX.md` donne le PASS/FAIL par poste, vue et format.
