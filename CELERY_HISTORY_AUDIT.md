# Audit Celery & Historique — Rapport (résumé)

Auteur: Assistant IA (Copilot CLI runtime)
Date: 2026-06-03

## Résumé rapide

- Historique/versioning: implémenté. Voir `apps/norms/models.py` (NormeVersion, ChangementVersion), API: `api/v1/norms_views.py` (create_version, history, versions, diff, rollback), et `api/v1/norms_serializers.py` (détection de changements).

- File reader / éditeur: doc `READER.md` et `frontend_source/DOC_EDITEUR.md` / `frontend_source/DOC_HISTORIQUE.md` existent. Le front-end utilise l'API Web `FileReader` (templates + frontend_source).

- Celery: configuration présente (`config/celery.py`, `docker-compose.yml`, `celery-beat`) mais tâches réelles manquantes — pas de `tasks.py` trouvé auparavant; appels Celery sont commentés (ex: `api/v1/payments_views.py`). Plusieurs tâches listées comme TODO dans `PHASE4_IMPLEMENTATION_CHECKLIST.md` (FCM async, envoi emails, etc.).

## Actions réalisées (implémentation)

1. Création d'une tâche Celery pour les rappels de paiement:
   - `apps/payments/tasks.py` — tâche `send_payment_reminder(cotisation_id)` qui envoie un email au contact de la structure (utilise `send_mail`).
   - Déclenchement activé dans `api/v1/payments_views.py` (appel `send_payment_reminder.delay(...)` décommenté).

2. Création d'une tâche Celery pour le dispatch de notifications (simulée):
   - `apps/mobileapp/tasks.py` — tâche `dispatch_notification(notification_id)` crée des `NotificationLog` marqués `SENT`. Remplacement simulé; intégration FCM/APNs à ajouter.

3. Ce fichier rapport: `CELERY_HISTORY_AUDIT.md` (ce document).

## Ce qui manque / recommandations prioritaires

- Implémenter tâches Celery réelles pour FCM/APNs et fallback (APNs). (Tâches: envoyer payload FCM, gérer réponses, retries, backoff).
- Implémenter `apps/payments/tasks.py` pour couvrir tous les cas (rappels multiples, templates d'email, logging des envois).
- Ajouter tests unitaires pour les tâches (vérifier créations de NotificationLog, appel `send_mail` en mode test).
- Mettre en place `django-celery-beat` pour tâches périodiques (rappels quotidiens/hebdomadaires). docker-compose contient `celery-beat` mais planifier schedule entries.
- Documenter le flux d'upload de fichiers (FileUpload endpoint, stockage S3) et rédiger `file_reader.md` si souhaité.

## Commandes utiles pour tester en local

- Démarrer l'environnement docker (celery + beat):
  - `docker-compose up --build redis db web celery celery-beat`
- Vérifier logs Celery: `docker-compose logs -f celery`
- Lancer manuellement une tâche (à partir du shell Django):
  - `from apps.payments.tasks import send_payment_reminder; send_payment_reminder.delay(<id>)`

---

Si tu veux, je peux maintenant :
- Étendre l'implémentation FCM (intégration réelle) et ajouter tests,
- Créer `file_reader.md` détaillé,
- Ouvrir une PR avec ces changements.
