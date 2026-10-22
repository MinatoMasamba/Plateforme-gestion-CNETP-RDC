# Audit de parité fonctionnelle UI/UX — Django ↔ Flutter

> Légende : ✅ fonctionnel (branché) · 🟡 visuel seulement (présent, sans action) · ❌ absent
> Date : 2026-10-21

## Synthèse
- **Fonctionnel** : auth (login/logout API, session, routage par rôle), navigation (onglets/vues/panneaux), sélection de document Expert + édition texte.
- **Tout le métier** (workflows, validations, formulaires, actions API) est **visuel ou absent**.
- Endpoint backend CTC (`dashboard/dossiers/assignations`) **prêt mais non branché**.
- Aucun bouton de **déconnexion** dans l'UI active ; **thème** non câblé (sauf login local).

---

## Global / Auth
| Fonction | Flutter |
|---|---|
| Login email/mot de passe (JWT réel) | ✅ |
| Bootstrap/rôle + redirection espace | ✅ |
| Logout (endpoint + nettoyage) | 🟡 (méthode existe, **aucun bouton UI**) |
| « Se souvenir de moi » | 🟡 |
| Mot de passe oublié | ❌ |
| Inscription expert / simple | ❌ |
| Confirmation email / activation token | ❌ |
| Bascule thème clair/sombre | ❌ (login local seulement ; copil non câblé) |

## Page racine
| Fonction | Flutter |
|---|---|
| Bouton « Se connecter » → /login | ✅ |
| « Ouvrir mon espace » si connecté | ✅ |
| « Découvrir le fonctionnement » | 🟡 |
| Stats du bandeau | 🟡 (valeurs figées) |

## Expert (`/app/`) — 9 onglets
| Module | Fonctions Django | Flutter |
|---|---|---|
| Éditeur | sélection doc, édition, compteur | ✅ |
| Éditeur | sauvegarde de version (POST) | 🟡 (recharge le doc) |
| Éditeur | votes POUR/CONTRE/ABS + émargement | 🟡 (aucun état) |
| Éditeur | Réinitialiser | ✅ (local) |
| Éditeur | IA Analyser / Appliquer / Ignorer | ❌ |
| Éditeur | Partager & débattre + chat | ❌ |
| Éditeur | CTM « Voir Groupes » (modal) | ❌ |
| Historique | filtres / comparer / restaurer | 🟡 / ❌ |
| Experts & Groupes | sélection WG/Expert, discuter, détacher, accepter | ❌ |
| Réunions & Votes | planifier, Meet, émargement, vote, PV, télécharger | ❌ |
| Cotisations | cotisations structures, pain.001, PDF, liquider, contester | ❌ |
| Processus ISO | renvoyer/promouvoir, portail public, télécharger | 🟡 / ❌ |
| Légistique | m'assigner, prêt pour enquête | 🟡 (accès restreint affiché) |
| Notifications | liste / lu | ❌ |
| Profil | formulaire (identité, CV, CTM/WG, coordonnées), enregistrer | ❌ (champs statiques) |
| Sous-modules | norm-reader, meeting-reader, norm-vote, pending/manage experts | ❌ |

## CTC (`/ctc/`)
| Vue | Fonctions Django | Flutter |
|---|---|---|
| Sidebar (4 sections) | navigation | ✅ |
| Tableau de bord | KPI + dossiers + assignations (réels) | 🟡 statique (endpoint prêt) |
| Dossiers normatifs | tableau, ouverture/lecture | ❌ |
| Mes Assignations | « Traiter » | ❌ |
| Demandes à traiter | examiner / approuver / refuser | ❌ |
| Assistant Exécutif | réception technique | ❌ |
| Budget & Comptabilité | lignes, actions rapides | ❌ |
| Suivi statistique | drill-down SC/CTM/groupes | ❌ |
| Homologations | liste | ❌ |
| Instructions | envoyer / annuler | ❌ |
| Réunions | liste | ❌ |
| Drive | upload / tous fichiers | ❌ |
| Archives | liste | ❌ |
| Paramètres | sauvegarde | ❌ |
| Workflow dossier | réception → indexation → validation → revue → industriel → transmission | ❌ |
| Consoles par pôle | routage doc., arbitrage, ISO, légistique, enquête, cadrage ind., grand livre, SIG, admin, saisie massive, matrice, méthodologie | ❌ |
| Annuaire / messagerie / notifications | ❌ |

## Copil (`/pilotage/`)
| Fonction | Flutter |
|---|---|
| Sidebar / panneaux | ✅ |
| Cartes SC (données réelles) | 🟡 figées (demoScGroups) |
| Clic carte SC → activité | ❌ |
| « Donner une instruction » | ❌ |
| Cadrage Directoire (open/validate/mandate/schedule/verify/quitus/final) | ❌ |
| Réception technique (accusé) | ❌ |
| Demandes d'adhésion (activer/refuser) | ❌ |
| Demandes de dérogation (approuver/refuser + réponse) | ❌ |
| Verrouillage plateforme (Président) | ❌ |
| Réponses récentes | ❌ |
| Directoire/Conseillers : postes réels + phases + groupes de cadrage | ❌ (squelette générique) |
| Espace ATF | ❌ |

---

## Priorités de mise en parité (ordre conseillé)
1. **Auth complet** : bouton logout, mot de passe oublié, inscription, confirmation.
2. **CTC** : brancher endpoint dashboard + tableaux dossiers/assignations + actions workflow.
3. **Copil** : brancher panneaux (cadrage, réception, adhésions, dérogations) + actions.
4. **Expert** : sauvegarde version, votes, IA, groupes, historique/diff, profil (formulaire).
5. **Modules secondaires** : réunions, cotisations, légistique, notifications, messagerie, IA.
6. **Postes nominatifs** (Directoire/Conseillers) + compte ATF.
