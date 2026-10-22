# Index des captures d'interface — CNE-ITP

Captures générées le 2026-10-18 depuis l'application Django locale
(`http://127.0.0.1:8001`), viewport desktop `1440×900` et mobile `390×844`.
Ce sont les **références visuelles de vérité** pour le clone Flutter.

## 00 — Authentification
| Fichier | Écran | Source |
|---|---|---|
| `00_auth/01_login_expert.png` | Connexion expert | `templates/expert/expert_auth/expert_login.html` |
| `00_auth/02_login_user.png` | Connexion utilisateur | `templates/user_templates/user_login.html` |
| `00_auth/03_inscription_expert.png` | Inscription expert | `templates/expert/expert_auth/expert_registration.html` |
| `00_auth/04_inscription_simple.png` | Inscription simple | `templates/user_templates/user_registration.html` |

## 01 — App Expert « Espace de travail » (`/app/`)
| Fichier | Écran | Source |
|---|---|---|
| `01_expert/01_editeur.png` | Éditeur de normes | `templates/app/app.html` |
| `01_expert/02_historique.png` | Historique des versions | `static/js/components/history.js` |
| `01_expert/03_experts_groupes.png` | Experts & groupes | `static/js/components/experts.js` |
| `01_expert/04_reunions_votes.png` | Réunions & votes | `static/js/components/meetings.js` |
| `01_expert/05_cotisations.png` | Cotisations & indemnités | `static/js/components/financial.js` |
| `01_expert/06_bibliotheque_iso.png` | Bibliothèque / Processus ISO | `static/js/components/validation.js` |
| `01_expert/07_legistique.png` | Bureau légistique | `static/js/components/legistique.js` |
| `01_expert/08_notifications.png` | Notifications | `templates/app/app.html` |
| `01_expert/09_profil.png` | Profil expert | `templates/expert/profile.html` |

## 02 — App Coordination technique CTC (`/ctc/`)
| Fichier | Écran (vue `switchView`) |
|---|---|
| `02_ctc/01_dashboard.png` | `dashboard` |
| `02_ctc/02_dossiers.png` | `dossiers` |
| `02_ctc/03_assignations.png` | `assignations` |
| `02_ctc/04_demandes_a_traiter.png` | `ctc_requests` |
| `02_ctc/05_assistant_executif.png` | `assistant_executif` |
| `02_ctc/06_budget_comptabilite.png` | `financial` |
| `02_ctc/07_statistiques.png` | `statistiques` |
| `02_ctc/08_homologations.png` | `homologations` |
| `02_ctc/09_instructions.png` | `instructions` |
| `02_ctc/10_reunions.png` | `reunions` |
| `02_ctc/11_drive.png` | `drive` |
| `02_ctc/12_archives.png` | `archives` |
| `02_ctc/13_parametres.png` | `parametres` |

Sources : `templates/ctc/app/app.html` + `templates/ctc/app/components/*`.
Contexte de rôles : `web/ctc_views.py:223` (`get_ctc_context`).

## 03 — App Copil, Console Globale (`/pilotage/`)
| Fichier | Panneau (`switchPilotagePanel`) |
|---|---|
| `03_copil_console/01_dashboard_sc.png` | `panel-sc` (Supervision SC) |
| `03_copil_console/02_cadrage_directoire.png` | `panel-cadrage` |
| `03_copil_console/03_reception_technique.png` | `panel-reception` |
| `03_copil_console/04_demandes_adhesion.png` | `panel-adhesions` |
| `03_copil_console/05_demandes_derogation.png` | `panel-requests` |

Source : `templates/pilotage/dashboard.html`.

## 04 — App Copil, Bureau Directoire (`/pilotage/bureau-directoire/`)
Posts 1 à 5 (`switchView('post-N')`) — `templates/pilotage/app/`.

| Fichier | Poste |
|---|---|
| `04_copil_directoire/01_poste_1.png` | Poste 1 |
| `04_copil_directoire/02_poste_2.png` | Poste 2 |
| `04_copil_directoire/03_poste_3.png` | Poste 3 |
| `04_copil_directoire/04_poste_4.png` | Poste 4 |
| `04_copil_directoire/05_poste_5.png` | Poste 5 |

## 05 — App Copil, Conseillers (`/pilotage/conseillers/`)
Posts 6 à 17 (`switchView('post-N')`) — `templates/pilotage/app_conseillers/`.

| Fichier | Poste |
|---|---|
| `05_copil_conseillers/06_poste_6.png` … `17_poste_17.png` | Postes 6 à 17 |

## 06 — Variantes mobile (`390×844`)
| Fichier | Écran |
|---|---|
| `06_mobile/01_expert_editor.png` | Expert — éditeur (mobile) |
| `06_mobile/02_ctc_dashboard.png` | CTC — tableau de bord (mobile) |
| `06_mobile/03_copil_console.png` | Copil — console globale (mobile) |
| `06_mobile/04_copil_directoire.png` | Copil — directoire (mobile) |
| `06_mobile/05_copil_conseillers.png` | Copil — conseillers (mobile) |

## Note — Espace Copil ATF
Aucun compte de test avec le rôle `ADMIN_TECH_FIN` n'existe dans la base
locale. L'espace `/pilotage/atf/` n'a donc pas pu être capturé.
