# Plan — Console d’administration CNE-ITP

## Objectif

Créer une console d’administration sous `/dashboard/administration/` permettant de
consulter et gérer l’ensemble des modèles des applications locales, avec un accès
réservé aux superusers et aux membres d’un groupe dédié.

## Décisions

- Groupe par défaut : `Administrateurs CNE-ITP`, configurable via
  `CONSOLE_ACCESS_GROUP`.
- Superusers toujours autorisés ; les membres du groupe n’ont pas besoin d’être
  `is_staff`.
- Le groupe reçoit les droits CRUD sur les modèles locaux, sauf `core.delete_user`.
- Les journaux d’audit et les modèles sensibles (jetons, codes, sessions) sont en
  lecture seule dans la console.
- Aucune suppression physique d’utilisateur : désactivation du compte et suspension
  du profil expert. La réactivation peut restaurer le statut expert précédent.
- Phoenix est modifiable dans la console uniquement ; l’admin Django conserve
  `PhoenixReadOnlyAdmin`.
- Aucune migration de schéma : le groupe est synchronisé via `post_migrate`.
- Journalisation : `LogEntry` pour toutes les actions, `AuditLog` en complément pour
  les PK entiers et les actions utilisateur.
- Thème : dashboard COPIL (`templates/pilotage/dashboard.html`) pour l’habillage et
  dashboard conseiller (`templates/pilotage/conseiller/dashboard.html`) pour les
  graphiques ECharts.
- Périmètre v1 : CRUD par modèle + liens croisés ; pas d’inlines ni d’actions
  groupées.

## Architecture

### Nouveaux modules

- `apps/dashboard/console_permissions.py` : accès, décorateur, synchronisation du
  groupe.
- `apps/dashboard/console_registry.py` : registre des modèles, admin génériques,
  sous-classes Phoenix et normes, modèles en lecture seule.
- `apps/dashboard/console_changelist.py` : `ConsoleChangeList`, filtres, pagination.
- `apps/dashboard/console_forms.py` : formulaires génériques et formulaires
  utilisateur.
- `apps/dashboard/console_views.py` : accueil, explorateur, CRUD, utilisateurs,
  audit.
- `apps/dashboard/console_urls.py` : routes namespace `console`.
- `apps/dashboard/console_audit.py` : journalisation `LogEntry` / `AuditLog`.
- `apps/dashboard/templatetags/console_tags.py` : helpers d’affichage.
- `apps/core/account_services.py` : désactivation/réactivation utilisateur.
- `templates/static/css/console-admin.css` : thème COPIL.
- `templates/static/js/console.js` : navigation, graphiques ECharts, confirmations.
- `apps/dashboard/test_console.py` : tests.

### Fichiers modifiés

- `config/settings.py` : `CONSOLE_ACCESS_GROUP`, context processor.
- `apps/dashboard/apps.py` : hook `post_migrate`.
- `apps/dashboard/context_processors.py` : `console_access`.
- `apps/dashboard/urls.py` : inclusion des routes console.
- `apps/core/admin.py` : suppression utilisateur bloquée.
- `templates/base.html` : lien console.
- `apps/dashboard/templates/dashboard/dashboard.html` et `intelligence.html` :
  lien console.
- `web/views.py` : redirection des administrateurs console.

## Routes

- `console:home`
- `console:models`
- `console:model_list`
- `console:model_create`
- `console:model_detail`
- `console:model_edit`
- `console:model_delete`
- `console:users`
- `console:user_create`
- `console:user_detail`
- `console:user_edit`
- `console:user_password`
- `console:user_deactivate`
- `console:user_reactivate`
- `console:audit`

## Sécurité

- Décorateur `console_required` sur toutes les vues.
- Vérification des permissions modèle pour chaque action.
- Suppression `User` interdite côté console et côté admin Django.
- Dernier superuser actif et auto-désactivation protégés.
- Seuls les superusers peuvent éditer un superuser ou gérer les groupes.
- Champs sensibles masqués dans les détails.
- Confirmation et aperçu des suppressions en cascade.

## Tests

- Accès : superuser, membre du groupe, anonyme, non-membre.
- CRUD générique, suppression protégée, filtres et recherche.
- Phoenix modifiable dans la console, admin Django inchangé.
- Modèles UUID journalisés via `LogEntry` uniquement.
- Désactivation/réactivation, dernier superuser, `UserAdmin`.
- Création idempotente du groupe.
- Audit.

## Commandes de validation

```powershell
.\mon_env\Scripts\python.exe -m pytest apps\dashboard\test_console.py
.\mon_env\Scripts\python.exe -m ruff check apps\dashboard apps\core config web
```
