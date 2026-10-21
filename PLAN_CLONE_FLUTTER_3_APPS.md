# Plan — Clone Flutter des 3 espaces CNE-ITP (Expert · Coordination technique · Copil)

> Décisions validées : **une seule application Flutter**, **3 espaces par rôle**,
> **clone fonctionnel branché sur l'API**, cibles **Web + Windows**.
> Référence visuelle : `captures_ui/` (53 captures réelles, voir `captures_ui/INDEX.md`).

---

## 0. Référence visuelle (étape réalisée)

Les interfaces des trois apps ont été lancées et photographiées depuis
l'application Django locale (`http://127.0.0.1:8001`) à l'aide de Chromium +
Playwright. Ces captures constituent la **vérité visuelle** à reproduire
pixel près dans Flutter.

- Inventaire complet : `captures_ui/INDEX.md`
- 53 captures : auth (4), Expert (9), CTC (13), Copil Console (5),
  Copil Directoire (5), Copil Conseillers (12), mobile (5).
- Comptes utilisés (base locale) :
  - Expert : `kizito.matabaro@anat.gouv.cd`
  - CTC (Coordonnateur) : `minato1`
  - Copil Directoire / Console (Président) : `minato1`
  - Copil Conseillers : `stevetshitende6@gmail.com`
- Limite connue : aucun compte `ADMIN_TECH_FIN` → espace Copil **ATF** non capturé.

### Procédure de (re)génération
1. `mon_env/bin/python manage.py runserver 127.0.0.1:8001 --noreload`
2. Créer des sessions Django pour les comptes cibles (injection de cookie
   `sessionid`, sans modifier les mots de passe) :
   `SessionStore` + `_auth_user_id` / `_auth_user_backend` / `_auth_user_hash`.
3. Script Playwright (`executablePath: /usr/bin/google-chrome-stable`) :
   login par cookie, navigation `switchView` / `switchPilotagePanel`,
   capture `1440×900` et `390×844`.

---

## 1. Architecture Flutter

```
flutter_app/
  lib/
    core/
      api/           # Dio, intercepteurs, refresh JWT, gestion erreurs
      auth/          # session, user_type, rôles (expert / ctc / pilotage)
      theme/         # tokens couleurs, typographie, light/dark
      routing/       # go_router + redirection par rôle
      storage/       # flutter_secure_storage (JWT), shared_preferences
      notifications/ # in-app + polling (pas de FCM sur web/windows)
      widgets/       # design system (voir §2)
    features/
      auth/
      expert/        # espace de travail
      ctc/           # secrétariat technique
      pilotage/      # console + directoire + conseillers + atf
      shared/        # profil, notifications, messagerie, annuaire
```

**Stack** : Riverpod (état), go_router (navigation), Dio (HTTP),
freezed + json_serializable (modèles), `lucide_icons`,
`google_fonts` (Inter), `fl_chart` (donut/bar), `flutter_secure_storage`.

---

## 2. Design system (à répliquer)

| Source web | Cible Flutter |
|---|---|
| Bleu `#0095c9`, Jaune `#fff24b`, Rouge `#db3832` | `ColorScheme` + extension `RdcColors` |
| Dark `#020204` / `#06060c` / `#0b1220` ; Light `#f4f8fc` / `#fff` | `ThemeData.dark/light` |
| Accent `#2563eb`, sky `#74b9ff`, cyan `#b7eaf7`, lime `#d9ff25` | extension `InstitutionalColors` |
| Inter / Copper Hewitt | `TextTheme` (Copper Hewitt embarquée + fallback Georgia) |
| Lucide | `lucide_icons` |
| Rayons 13/20/24 px, ombres douces, glassmorphism | constantes `Radius` / `Shadows` |

**Widgets** : `TricolorBar`, `Armoirie`, `AppTopbar`, `AppSidebar` (redimensionnable
et repliable), `KpiCard`/`PremiumStat`, `DonutChart`/`BarChart`,
`StatusBadge`, `GlassCard`, `AppToast`, `BottomNav`, `MobileDock`,
`Modal`, `Dropdown`, `ChartCard`.
Thème **sombre par défaut** + bascule clair/sombre.

---

## 3. Cartographie des écrans (réf. captures)

### A. Espace Expert — `/app/` (`01_expert/`)
Onglets : **Éditeur de normes** (header document, textarea + compteur,
panneau Scrutin POUR/CONTRE/ABS + consensus 75 %, registre d'émargement,
journal de version, panneaux « Conseil Réglementaire IA » et
« Partager & Débattre », modal groupes WG), **Historique**,
**Experts & Groupes**, **Réunions & Votes**, **Cotisations & Indemnités**,
**Bibliothèque / Processus ISO**, **Bureau Légistique**, **Notifications**.
Sidebar : documents récents, collaborateurs, mode ISO, poste actif, profil.
Mobile : bottom-nav Normes / Historique / Groupes / Légistique / Profil.

### B. Espace Coordination technique — `/ctc/` (`02_ctc/`)
Sidebar 4 sections (`web/ctc_views.py:332`) : **Travail** (Tableau de bord,
Dossiers normatifs, Mes Assignations, Demandes à traiter), **Supervision**
(Suivi statistique, Homologations), **Outils** (Instruction, Réunions),
**Système** (Archives, Paramètres), + Assistant Exécutif, Budget &
Comptabilité, Espace Drive selon rôle.
Workflow dossier : `RECEPTION → GEOSPATIAL → MULTI_REVIEW → INDUSTRIAL → SIGNED_OUT`.
Consoles par pôle : routage documentaire, arbitrage retards, traduction ISO,
légistique, enquête publique, cadrage industriel, grand livre comptable,
SIG, admin système, saisie massive, matrice impacts, méthodologie.

### C. Espace Copil — `/pilotage/` (`03_` à `05_`)
- **Console Globale** : panels Supervision SC, Cadrage Directoire,
  Réception technique, Demandes d'adhésion, Demandes de dérogation
  + liens Organisation (Phoenix), Activité, Assistant IA.
- **Bureau Directoire** (posts 1–5) : Cadrage, Contrôle, Quitus, Mandat,
  Réception technique (phases 1/2/3).
- **Conseillers** (posts 6–17) : Légistique, Planification, rapports
  institutionnels, phases de production/contrôle/sanction.
- **ATF** : audit technique, validation financière, contrôle labo
  (non capturé — compte manquant).
Contexte de rôles : `web/pilotage_views.py:674` (`get_pilotage_context`).

### D. Auth (`00_auth/`)
Connexion expert, connexion utilisateur, inscription expert, inscription simple,
activation expert, confirmation email, réinitialisation mot de passe.

---

## 4. Couche API — écarts backend (clone fonctionnel)

Existant : JWT (`rest_framework_simplejwt`), `api/v1/auth`, `mobile/auth`,
`norms`, `sidebar/*`, `documents-bridge`, `meetings`, `payments`,
`validation`, `messaging`, `dashboard/kpis`.

**À créer avant les écrans CTC / Copil** (les actions sont aujourd'hui en HTML) :
- `api/v1/mobile/ctc/dashboard|dossiers|dossiers/{id}|reception|indexation|
  validation-entree|reviews/{id}/decision|industriel/{id}/decision|
  transmettre-pilotage`
- `api/v1/mobile/pilotage/dashboard|permissions|cadrage|reception|activite|organisation`
- Sérialiseurs, permissions par rôle, tests.
- **CORS** (`django-cors-headers`) pour le build web Flutter.

---

## 5. Phases de livraison

1. **Socle Flutter** : thème (§2), design system, routing par rôle, auth JWT.
2. **Espace Expert** : tous les écrans (API déjà prête).
3. **Backend** : endpoints mobiles CTC + Copil + tests.
4. **Espace CTC** : 13 vues + workflow de bout en bout.
5. **Espace Copil** : console + directoire + conseillers + activité/organisation.
6. **Finitions** : notifications in-app (polling), messagerie, responsive,
   tests E2E, validation pixel-perfect contre `captures_ui/`.

---

## 6. Points d'attention
- Notifications : polling `mobile/notifications` + fallback in-app (web/windows).
- Charts : ECharts → `fl_chart` (donut, barres).
- Responsive : reproduire les breakpoints desktop / mobile (dock, bottom-nav).
- Sécurité : JWT en secure storage ; le rôle côté client n'est qu'un affichage,
  l'autorité reste le serveur.
