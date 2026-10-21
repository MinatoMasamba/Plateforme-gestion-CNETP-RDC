# PLAN COMPLET — Clone Flutter de la plateforme CNE-ITP

> Trois espaces : **Expert**, **Coordination technique (CTC)**, **Copil (Pilotage)**
> Décisions validées : **une seule application Flutter** · **3 espaces par rôle**
> · **clone fonctionnel branché sur l'API** · cibles **Web + Windows**.
> Référence visuelle : `captures_ui/` (53 captures réelles) — index : `captures_ui/INDEX.md`.

---

## Sommaire
1. Contexte et objectif
2. Décisions structurantes
3. Références (visuel + code source)
4. Système de design
5. Architecture Flutter
6. Authentification et rôles
7. Cartographie détaillée des écrans
8. Couche API (existant + à créer)
9. Modèles et workflows métier
10. Phases de livraison
11. Tests et recette
12. Risques et points ouverts
13. Annexe — inventaire des captures

---

## 1. Contexte et objectif

La plateforme CNE-ITP est aujourd'hui une application Django avec des
interfaces web (templates Tailwind) et une PWA, organisées en trois espaces
de travail selon le rôle de l'utilisateur connecté :

- **Expert** → « Espace de travail » (`/app/`) : éditeur de normes et modules associés.
- **Coordination technique (CTC)** → « Secrétariat technique » (`/ctc/`).
- **Copil (Pilotage)** → Comité de Pilotage (`/pilotage/`) avec console globale et
  trois collèges (Bureau Directoire, Conseillers, ATF).

Objectif : reconstruire **à l'identique l'interface UI/UX** de ces trois espaces
en Flutter, de façon **fonctionnelle** (branchée sur le backend Django via API
JSON/JWT), pour **Web et Windows**.

---

## 2. Décisions structurantes

| Sujet | Décision |
|---|---|
| Structure | 1 application Flutter unique, 3 espaces routés par rôle |
| Périmètre | Clone fonctionnel connecté à l'API |
| Plateformes | Web (Chrome/Edge) + Windows desktop |
| État | Riverpod |
| Navigation | go_router (redirection par rôle) |
| HTTP | Dio + intercepteur JWT (refresh automatique) |
| Modèles | freezed + json_serializable |
| Icônes | `lucide_icons` |
| Police | Inter (`google_fonts`) + Copper Hewitt embarquée |
| Graphiques | `fl_chart` (remplace ECharts) |
| Stockage | `flutter_secure_storage` (tokens) + `shared_preferences` (préférences) |
| Notifications | in-app + polling (pas de FCM sur web/windows) |

---

## 3. Références

### 3.1 Référence visuelle (captures)
- `captures_ui/00_auth/` — 4 captures
- `captures_ui/01_expert/` — 9 captures
- `captures_ui/02_ctc/` — 13 captures
- `captures_ui/03_copil_console/` — 5 captures
- `captures_ui/04_copil_directoire/` — 5 captures
- `captures_ui/05_copil_conseillers/` — 12 captures
- `captures_ui/06_mobile/` — 5 captures
- Index détaillé : `captures_ui/INDEX.md`

### 3.2 Code source de référence
| Élément | Fichier |
|---|---|
| URLs web | `web/urls.py`, `config/urls.py` |
| Vue de redirection post-login | `web/views.py:312` (`_get_redirect_url`) |
| Contexte CTC (rôles, sidebar) | `web/ctc_views.py:223` (`get_ctc_context`) |
| Contexte Pilotage | `web/pilotage_views.py:674` (`get_pilotage_context`) |
| App Expert (SPA) | `templates/app/app.html` |
| Modules Expert JS | `templates/static/js/components/*.js` |
| App CTC (SPA) | `templates/ctc/app/app.html` + `templates/ctc/app/components/*` |
| Consoles CTC | `templates/ctc/composants/*` |
| Console Copil | `templates/pilotage/dashboard.html` |
| Apps Copil | `templates/pilotage/app/`, `app_conseillers/`, `app_atf/` |
| Design tokens | `templates/static/css/institutional-ui.css` |
| Charte RDC | `CHARTE_APPLIQUEE.md` |
| Modèles postes | `apps/governance/models.py:220` (`PosteNominatif`) |
| API | `api/v1/urls.py`, `api/v1/mobile/views.py`, `api/v1/auth/views.py` |
| JWT | `config/settings.py:178` et `:205` |

### 3.3 Procédure de (re)génération des captures
1. Lancer le serveur : `mon_env/bin/python manage.py runserver 127.0.0.1:8001 --noreload`
2. Créer des sessions Django ciblées par injection de cookie `sessionid`
   (`SessionStore` + `_auth_user_id` / `_auth_user_backend` / `_auth_user_hash`),
   sans modifier les mots de passe.
3. Script Playwright (Chromium `/usr/bin/google-chrome-stable`) : login par
   cookie, navigation `switchView` / `switchPilotagePanel`, captures
   `1440×900` et `390×844`.

Comptes utilisés (base locale) : Expert `kizito.matabaro@anat.gouv.cd` ;
CTC et Copil Président `minato1` ; Conseillers `stevetshitende6@gmail.com`.
Limite : aucun compte `ADMIN_TECH_FIN` → espace Copil **ATF** non capturé.

---

## 4. Système de design

### 4.1 Couleurs officielles RDC
| Nom | Hex |
|---|---|
| Bleu institutionnel | `#0095c9` |
| Jaune | `#fff24b` |
| Rouge | `#db3832` |

Bande tricolore en haut de page + « Ligne d'État » verticale de 3 segments égaux.

### 4.2 Palette institutionnelle (`institutional-ui.css`)
| Token | Clair | Sombre |
|---|---|---|
| `sidebar` | `#0f1b2d` | `#081321` |
| `page` | `#f4f8fc` | `#0b1220` |
| `card` | `#ffffff` | `#111d2d` |
| `border` | `#e3ebf2` | `#334155` |
| `text` | `#0f172a` | `#f8fafc` |
| `muted` | `#475569` | `#cbd5e1` |
| `accent` | `#2563eb` | `#60a5fa` |
| `sky` | `#74b9ff` | `#4886bb` |
| `cyan` | `#b7eaf7` | `#2c6172` |
| `lime` | `#d9ff25` | `#a2bd29` |

### 4.3 Palette app Expert (`templates/app/app.html`)
| Token | Clair | Sombre |
|---|---|---|
| `surface` | `#F3F4F6` | `#020204` |
| `surface-2` | `#FFFFFF` | `#06060c` |
| `surface-3` | `#F8FAFC` | `#0b0b10` |
| `text-primary` | `#0F172A` | `#e5eef8` |
| `text-muted` | `#475569` | `#94a3b8` |
| `border` | `#E2E8F0` | `rgba(255,255,255,.06)` |
| `blue-primary` | `#1E40AF` | `#2563eb` |
| `blue-accent` | `#1B3B8A` | `#3b82f6` |

### 4.4 Typographie
- Corps : **Inter** (300 → 900).
- Intitulés officiels : **Copper Hewitt** semi-bold (fallback Copperplate / Georgia).
- `theme-color` : `#0095c9`.

### 4.5 Composants à porter
`TricolorBar`, `Armoirie` (logo `logo-cnetp.png` + ligne d'État), `AppTopbar`,
`AppSidebar` (redimensionnable, repliable, sections), `KpiCard` / `PremiumStat`,
`PremiumDonut`, `PremiumBars`, `StatusBadge`, `GlassCard`, `AccentCard`,
`AppToast`, `BottomNav`, `MobileDock`, `Modal` (directory, permission, groupes),
`Dropdown`, `ChartCard`, `EmptyState`, `DataTable` (responsive « stacked »).

Thème **sombre par défaut** + bascule clair/sombre persistée.

---

## 5. Architecture Flutter

```
flutter_app/
  lib/
    main.dart
    app.dart
    core/
      api/
        api_client.dart        # Dio, baseUrl, intercepteurs
        auth_interceptor.dart  # Bearer + refresh 401
        endpoints.dart
        api_exception.dart
      auth/
        auth_controller.dart   # état session (Riverpod)
        session.dart           # user, user_type, rôles
        role_router.dart       # redirection par rôle
      theme/
        app_colors.dart
        institutional_colors.dart
        app_theme.dart         # light/dark
        app_typography.dart
        app_spacing.dart
      routing/
        app_router.dart        # go_router + guards
        routes.dart
      storage/
        secure_storage.dart
        preferences.dart
      notifications/
        notification_service.dart  # polling + in-app
      widgets/                 # design system (§4.5)
    features/
      auth/                    # login, inscription, activation, reset
      expert/
        editor/                # éditeur de normes + vote + IA + partage
        history/
        experts_groups/
        meetings/
        financial/
        validation/            # bibliothèque / processus ISO
        legistique/
        notifications/
        profile/
      ctc/
        dashboard/
        dossiers/
        assignations/
        requests/
        executive_assistant/
        financial/
        statistics/
        homologations/
        instructions/
        meetings/
        drive/
        archives/
        settings/
        workflow/              # réception, indexation, revue, industriel, transmission
        consoles/              # consoles par pôle
      pilotage/
        console/               # panels de la console globale
        directoire/            # posts 1–5
        conseillers/           # posts 6–17
        atf/
        organisation/          # Phoenix
        activity/
        ia/
      shared/
        profile/
        notifications/
        messaging/
        directory/
```

Conventions : `feature/<écran>/<écran>_screen.dart`, `..._controller.dart`,
`..._repository.dart`, `..._model.dart`, widgets réutilisables dans
`core/widgets`.

---

## 6. Authentification et rôles

### 6.1 Flux
1. Login via `POST /api/v1/mobile/auth/login/` (email + mot de passe) →
   `{ user_type, user, access, refresh, session_id }`.
2. Stockage sécurisé des tokens ; `Authorization: Bearer <access>`.
3. Refresh via `POST /api/v1/mobile/auth/refresh/` ; rotation + blacklist
   (`ROTATE_REFRESH_TOKENS=True`, access 15 min, refresh 7 jours).
4. Logout via `POST /api/v1/mobile/auth/logout/`.
5. Redirection par rôle, reproduisant `_get_redirect_url` (`web/views.py:312`) :
   - Directoire → espace Directoire
   - Conseiller politique → espace Conseillers
   - ATF → espace ATF
   - autre membre Pilotage → console `/pilotage/`
   - membre CTC → `/ctc/`
   - sinon → `/app/`

### 6.2 Parcours d'accès
- Inscription publique + confirmation email par code
  (`register_public`, `confirm-email-code`, `resend-confirmation-code`).
- Activation expert par token (`activate_expert`).
- Réinitialisation de mot de passe (web : `/mot-de-passe-oublie/...`).

### 6.3 Autorisation
Le rôle côté client ne sert qu'à l'affichage/navigation ; **l'autorité reste le
serveur**. Chaque action métier doit être revalidée côté API.

---

## 7. Cartographie détaillée des écrans

### 7.1 Authentification (`00_auth/`)
| Écran | Capture | Source |
|---|---|---|
| Connexion expert | `01_login_expert.png` | `templates/expert/expert_auth/expert_login.html` |
| Connexion utilisateur | `02_login_user.png` | `templates/user_templates/user_login.html` |
| Inscription expert | `03_inscription_expert.png` | `templates/expert/expert_auth/expert_registration.html` |
| Inscription simple | `04_inscription_simple.png` | `templates/user_templates/user_registration.html` |

### 7.2 Espace Expert (`/app/`) (`01_expert/`)
L'éditeur est le cœur : sélection d'un document dans la sidebar, édition du
texte, vote, versionnage, conseil IA, partage vers le chat.

| Écran | Capture | Source |
|---|---|---|
| Éditeur de normes | `01_editeur.png` | `templates/app/app.html` |
| Historique | `02_historique.png` | `static/js/components/history.js` |
| Experts & groupes | `03_experts_groupes.png` | `static/js/components/experts.js` |
| Réunions & votes | `04_reunions_votes.png` | `static/js/components/meetings.js` |
| Cotisations & indemnités | `05_cotisations.png` | `static/js/components/financial.js` |
| Bibliothèque / Processus ISO | `06_bibliotheque_iso.png` | `static/js/components/validation.js` |
| Bureau légistique | `07_legistique.png` | `static/js/components/legistique.js` |
| Notifications | `08_notifications.png` | `templates/app/app.html` |
| Profil | `09_profil.png` | `templates/expert/profile.html` |

Éléments de l'éditeur à reproduire :
- En-tête document (code, famille, date, titre, description).
- Cartouche CTM (sous-commission) + « Voir Groupes (WGs) » (modal).
- Zone de texte + compteur caractères/mots.
- Panneau **Scrutin & Évaluation** : POUR / CONTRE / ABS, taux de consensus (75 %),
  registre d'émargement, statut de l'avis.
- **Journal des versions / commentaire** + sauvegarde.
- **Conseil Réglementaire IA** (analyser / appliquer / ignorer).
- **Partager & Débattre** (extrait de clause, expert destinataire, chat).
- Sidebar : documents récents, collaborateurs, mode ISO, poste actif, profil.
- Mobile : bottom-nav Normes / Historique / Groupes / Légistique / Profil.

### 7.3 Espace Coordination technique (`/ctc/`) (`02_ctc/`)
Sidebar dynamique par rôle (`get_ctc_context`) en 4 sections.

| Vue (`switchView`) | Capture | Composant source |
|---|---|---|
| `dashboard` | `01_dashboard.png` | `dashboard_module.html` |
| `dossiers` | `02_dossiers.png` | `dossiers_view.html` |
| `assignations` | `03_assignations.png` | `assignations_view.html` |
| `ctc_requests` | `04_demandes_a_traiter.png` | `ctc_requests_module.html` |
| `assistant_executif` | `05_assistant_executif.png` | `executive_assistant_module.html` |
| `financial` | `06_budget_comptabilite.png` | `financial_module.html` |
| `statistiques` | `07_statistiques.png` | `statistiques_view.html` |
| `homologations` | `08_homologations.png` | `homologations_view.html` |
| `instructions` | `09_instructions.png` | `instruction_module.html` |
| `reunions` | `10_reunions.png` | `reunions_view.html` |
| `drive` | `11_drive.png` | `drive_view.html` |
| `archives` | `12_archives.png` | `archives_view.html` |
| `parametres` | `13_parametres.png` | `parametres_module.html` |

Sections sidebar : **Travail**, **Supervision**, **Outils**, **Système**
+ variantes de `principal` selon sous-rôle (GAF → Budget ; Assistant Exécutif →
Assistant ; IT → + Drive).

Consoles par pôle (`templates/ctc/composants/`) : routage documentaire,
arbitrage des retards, traduction/alignement ISO, légistique CTC, enquête
publique, cadrage industriel, grand livre comptable, serveur SIG, administration
système, saisie massive, matrice impacts éco-environnementaux,
méthodologie/chronogramme.

### 7.4 Espace Copil — Console Globale (`/pilotage/`) (`03_copil_console/`)
| Panneau (`switchPilotagePanel`) | Capture |
|---|---|
| `panel-sc` — Supervision des sous-commissions | `01_dashboard_sc.png` |
| `panel-cadrage` — Cadrage Directoire | `02_cadrage_directoire.png` |
| `panel-reception` — Réception technique | `03_reception_technique.png` |
| `panel-adhesions` — Demandes d'adhésion | `04_demandes_adhesion.png` |
| `panel-requests` — Demandes de dérogation | `05_demandes_derogation.png` |

La console affiche : hero profil/collège, KPI de supervision
(SC / experts / à examiner / normes), liste des sous-commissions et de leurs
experts, accès Organisation (Phoenix), Activité des sous-commissions,
Assistant IA.

### 7.5 Espace Copil — Bureau Directoire (`04_copil_directoire/`)
Posts 1 à 5 (`switchView('post-N')`), chacun avec ses phases
(Cadrage / Contrôle technique / Quitus / Mandat / Réception).

| Poste | Capture |
|---|---|
| Poste 1 | `01_poste_1.png` |
| Poste 2 | `02_poste_2.png` |
| Poste 3 | `03_poste_3.png` |
| Poste 4 | `04_poste_4.png` |
| Poste 5 | `05_poste_5.png` |

### 7.6 Espace Copil — Conseillers (`05_copil_conseillers/`)
Posts 6 à 17 (`switchView('post-N')`) : phases de production, contrôle/validation,
sanction/vulgarisation, légistique, planification, rapports institutionnels.

| Postes | Captures |
|---|---|
| 6 à 17 | `06_poste_6.png` … `17_poste_17.png` |

### 7.7 Espace Copil — ATF (non capturé)
Aucun compte `ADMIN_TECH_FIN` en base locale. Prévoir : audit technique,
validation financière (FONER), contrôle laboratoire (BTC). À couvrir après
création d'un compte de test.

### 7.8 Variantes mobile (`06_mobile/`)
| Écran | Capture |
|---|---|
| Expert — éditeur | `01_expert_editor.png` |
| CTC — tableau de bord | `02_ctc_dashboard.png` |
| Copil — console globale | `03_copil_console.png` |
| Copil — directoire | `04_copil_directoire.png` |
| Copil — conseillers | `05_copil_conseillers.png` |

---

## 8. Couche API (existant + à créer)

### 8.1 Existant (JWT)
- Auth mobile : `POST /api/v1/mobile/auth/login|refresh|logout|register_public|
  activate_expert|confirm-email-code|resend-confirmation-code`.
- Notifications : `/api/v1/mobile/notifications/` (+ `unread_count`,
  `mark_all_as_read`, `mark_as_read`), préférences, push-tokens.
- Profil mobile : `/api/v1/mobile/profile/` (+ `dashboard`, `edit-data`, `update`).
- Public : `published_norms`, `ctm_composition`, `news`.
- Expert / général : `norms`, `norm-versions`, `norm-changes`, `experts`,
  `structures`, `ctm`, `wg`, `affectations`, `reunions`, `presences`,
  `reunion-votes`, `pv`, `cotisations`, `paiements`, `jetons`,
  `legistic-reviews`, `documents`, `documents-bridge`, `collaborators`,
  `messages`, `public-amendments`, `ia-agent/*`,
  `sidebar/experts`, `sidebar/documents`, `sidebar/meetings`, `sidebar/budgets`,
  `working-groups`, `tasks`, `document-history`, `expert-actions`,
  `dashboard/kpis`.

### 8.2 À créer (bloquant clone fonctionnel CTC / Copil)
Les actions CTC et Pilotage sont aujourd'hui des routes HTML (`/ctc/...`,
`/pilotage/...`). Créer des endpoints JSON dédiés :
- `GET  /api/v1/mobile/ctc/dashboard/`
- `GET  /api/v1/mobile/ctc/dossiers/` · `GET .../dossiers/{id}/`
- `POST .../dossiers/{id}/reception/`
- `POST .../dossiers/{id}/indexation/`
- `POST .../dossiers/{id}/validation-entree/`
- `POST .../reviews/{id}/decision/`
- `POST .../industriel/{id}/decision/`
- `POST .../dossiers/{id}/transmettre-pilotage/`
- `GET  /api/v1/mobile/pilotage/dashboard/`
- `GET/POST /api/v1/mobile/pilotage/permissions/`
- `POST /api/v1/mobile/pilotage/cadrage/{id}/action/`
- `POST /api/v1/mobile/pilotage/reception/{id}/`
- `GET  /api/v1/mobile/pilotage/activite/` · `organisation/`

Réponses d'action normalisées :
```json
{ "ok": true, "status": "...", "current_stage": "...", "message": "...", "updated_at": "..." }
```
Chaque action doit être contrôlée côté serveur (rôle + état), et retourner
l'état courant du dossier.

### 8.3 Transverse
- **CORS** (`django-cors-headers`) pour le build web Flutter (origine distincte).
- Documentation OpenAPI déjà exposée (`/api/v1/schema/`, Swagger).

---

## 9. Modèles et workflows métier

### 9.1 CTC — circuit d'un dossier
`RECEPTION → GEOSPATIAL → MULTI_REVIEW → INDUSTRIAL → SIGNED_OUT`

Étapes à reproduire : réception, indexation, validation d'entrée, examens
multi-revues (acceptation/refus avec commentaire), consultation industrielle
FEC, signature/transmission au Pilotage. Un dossier n'avance que si le serveur
confirme l'étape précédente.

### 9.2 Copil — cadrage et réception
Actions de cadrage (`CADRAGE_FIELDS`) : `open`, `validate_onic`, `validate_btp`,
`formalize_mandate`, `schedule`, `verify_pv`, `quitus_onic`, `quitus_btp`,
`final_validate`. Accusé de réception CTC (étape 5) par Président/Rapporteur.

### 9.3 Postes nominatifs
17 postes (`PosteNominatif`) répartis par collège :
- Bureau Directoire : Président, Vice-Président, Secrétaire, Rapporteur (posts 1–5).
- Conseillers institutionnels/politiques (posts 6–17).
- ATF (Administrateurs Techniques et Financiers).
Chaque poste peut être vacant et possède des phases (phase1/phase2/phase3).

---

## 10. Phases de livraison

### Phase 1 — Socle Flutter
- Projet Flutter (web + windows), thème clair/sombre, tokens (§4).
- Design system : topbar, sidebar, KPI, charts, badges, toast, mobile dock.
- Routing + guards par rôle, `AuthController`, refresh JWT, secure storage.
- **Livrable** : connexion + coquille vide des 3 espaces.

### Phase 2 — Espace Expert
- Éditeur de normes (header, texte, scrutin, versions, IA, partage).
- Historique, Experts & groupes, Réunions & votes, Cotisations,
  Bibliothèque/ISO, Légistique, Notifications, Profil.
- **Backend** : endpoints existants ; compléter si nécessaire.
- **Livrable** : espace Expert complet et fonctionnel.

### Phase 3 — Backend CTC / Copil
- Endpoints JSON §8.2 + sérialiseurs + permissions + tests.
- CORS.
- **Livrable** : API mobile stable, documentée, testée.

### Phase 4 — Espace CTC
- 13 vues + workflow complet (réception → transformation → transmission).
- Consoles par pôle.
- **Livrable** : CTC de bout en bout.

### Phase 5 — Espace Copil
- Console globale (5 panels), Directoire (5 postes), Conseillers (12 postes).
- Organisation (Phoenix), Activité, Assistant IA.
- **Livrable** : Copil complet ; ATF après création d'un compte de test.

### Phase 6 — Finitions
- Notifications in-app (polling + fallback), messagerie, annuaire.
- Responsive/desktop-window, accessibilité.
- Recette pixel-perfect contre `captures_ui/`.
- **Livrable** : version candidate.

---

## 11. Tests et recette

Scénarios obligatoires :
- inscription publique + confirmation email ; activation expert ;
- connexion + refresh JWT + déconnexion ;
- réception complète d'un dossier CTC ; acceptation d'un examen ;
  refus avec commentaire ; blocage si validation manquante ;
  transmission au Pilotage ; accusé de réception Président/Rapporteur ;
- cadrage Directoire (phases) ;
- notification in-app et compteur non lu ;
- lecture hors connexion (cache) ;
- non-fuite entre rôles (un expert ne voit pas les données CTC, etc.).

Recette visuelle : comparer chaque écran Flutter à sa capture de référence.

---

## 12. Risques et points ouverts

| Risque / point | Mitigation |
|---|---|
| Actions CTC/Copil encore en HTML | Créer les endpoints JSON (phase 3) avant les écrans |
| Espace ATF sans compte de test | Créer un compte `ADMIN_TECH_FIN` de test |
| Pas de FCM web/windows | Polling `mobile/notifications` + in-app |
| ECharts → fl_chart | Porter donut/barres, valider le rendu |
| CORS web | Ajouter `django-cors-headers` |
| Charts/KPI dépendants de données | Prévoir états vides et chargement |
| Sécurité fine par objet/champ | Contrôles serveur systématiques |

---

## 13. Annexe — inventaire complet des captures (53)

```
00_auth/01_login_expert.png
00_auth/02_login_user.png
00_auth/03_inscription_expert.png
00_auth/04_inscription_simple.png
01_expert/01_editeur.png
01_expert/02_historique.png
01_expert/03_experts_groupes.png
01_expert/04_reunions_votes.png
01_expert/05_cotisations.png
01_expert/06_bibliotheque_iso.png
01_expert/07_legistique.png
01_expert/08_notifications.png
01_expert/09_profil.png
02_ctc/01_dashboard.png
02_ctc/02_dossiers.png
02_ctc/03_assignations.png
02_ctc/04_demandes_a_traiter.png
02_ctc/05_assistant_executif.png
02_ctc/06_budget_comptabilite.png
02_ctc/07_statistiques.png
02_ctc/08_homologations.png
02_ctc/09_instructions.png
02_ctc/10_reunions.png
02_ctc/11_drive.png
02_ctc/12_archives.png
02_ctc/13_parametres.png
03_copil_console/01_dashboard_sc.png
03_copil_console/02_cadrage_directoire.png
03_copil_console/03_reception_technique.png
03_copil_console/04_demandes_adhesion.png
03_copil_console/05_demandes_derogation.png
04_copil_directoire/01_poste_1.png
04_copil_directoire/02_poste_2.png
04_copil_directoire/03_poste_3.png
04_copil_directoire/04_poste_4.png
04_copil_directoire/05_poste_5.png
05_copil_conseillers/06_poste_6.png
05_copil_conseillers/07_poste_7.png
05_copil_conseillers/08_poste_8.png
05_copil_conseillers/09_poste_9.png
05_copil_conseillers/10_poste_10.png
05_copil_conseillers/11_poste_11.png
05_copil_conseillers/12_poste_12.png
05_copil_conseillers/13_poste_13.png
05_copil_conseillers/14_poste_14.png
05_copil_conseillers/15_poste_15.png
05_copil_conseillers/16_poste_16.png
05_copil_conseillers/17_poste_17.png
06_mobile/01_expert_editor.png
06_mobile/02_ctc_dashboard.png
06_mobile/03_copil_console.png
06_mobile/04_copil_directoire.png
06_mobile/05_copil_conseillers.png
```
