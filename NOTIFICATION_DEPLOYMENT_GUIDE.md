# Guide de déploiement - Système de Notifications

## Vue d'ensemble

Ce guide couvre le déploiement du système complet de notifications CNETP incluant:
- Notifications push mobiles (FCM/APNs)
- Envoi d'emails
- Gestion des préférences utilisateur
- Digests de notifications

## Prérequis

### Dépendances Python
```bash
pip install firebase-admin>=6.0.0
pip install celery>=5.0.0
pip install redis>=4.0.0
pip install django>=6.0
```

### Services externes

1. **Firebase Cloud Messaging (FCM)**
   - Créer un projet Firebase sur https://console.firebase.google.com
   - Télécharger les credentials JSON
   - Obtenir les tokens FCM pour les clients mobiles

2. **Serveur d'email (SMTP)**
   - Gmail, SendGrid, Mailgun, ou autre
   - Credentials d'authentification

3. **Redis**
   - Pour la queue Celery
   - Version 6.0+

## Configuration

### 1. Variables d'environnement (.env)

```env
# Firebase
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
# OU
FIREBASE_CREDENTIALS_JSON='{"type":"service_account","project_id":"...","private_key":"..."}'

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@cnetp.cd

# Notification Settings
NOTIFICATION_EMAIL_ENABLED=True
NOTIFICATION_FCM_ENABLED=True
NOTIFICATION_RETRY_ATTEMPTS=3
NOTIFICATION_RETRY_DELAY_SEC=60

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 2. Docker Compose (docker-compose.yml)

```yaml
version: '3.9'

services:
  redis:
    image: redis:7-alpine
    container_name: cnetp_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  celery:
    build: .
    container_name: cnetp_celery
    command: celery -A config worker -l info
    volumes:
      - .:/app
      - ./firebase-credentials.json:/app/firebase-credentials.json:ro
    environment:
      - DEBUG=False
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/1
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
      - EMAIL_HOST=${EMAIL_HOST}
      - EMAIL_PORT=${EMAIL_PORT}
      - EMAIL_HOST_USER=${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
    depends_on:
      redis:
        condition: service_healthy
      db:
        condition: service_healthy

  celery-beat:
    build: .
    container_name: cnetp_celery_beat
    command: celery -A config beat -l info
    volumes:
      - .:/app
    environment:
      - DEBUG=False
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/1
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - db

volumes:
  redis_data:
```

### 3. Configuration Django (config/settings.py)

Déjà mise à jour avec:
```python
NOTIFICATION_SETTINGS = {
    'EMAIL_ENABLED': config('NOTIFICATION_EMAIL_ENABLED', default=True, cast=bool),
    'FCM_ENABLED': config('NOTIFICATION_FCM_ENABLED', default=True, cast=bool),
    'RETRY_ATTEMPTS': config('NOTIFICATION_RETRY_ATTEMPTS', default=3, cast=int),
    'RETRY_DELAY_SEC': config('NOTIFICATION_RETRY_DELAY_SEC', default=60, cast=int),
}
```

## Installation & Migration

### 1. Appliquer les migrations

```bash
python manage.py migrate mobileapp
```

### 2. Créer les préférences de notification pour les utilisateurs existants

```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> from apps.mobileapp.models import NotificationPreference
>>> User = get_user_model()
>>> for user in User.objects.all():
...     NotificationPreference.objects.get_or_create(user=user)
```

### 3. Collecter les fichiers statiques

```bash
python manage.py collectstatic --noinput
```

## Déploiement sur Docker

### 1. Builder l'image

```bash
docker-compose build
```

### 2. Démarrer les services

```bash
docker-compose up -d
```

### 3. Vérifier que Celery fonctionne

```bash
docker-compose logs celery
```

Vous devriez voir:
```
[2026-06-03 12:00:00,000: INFO/MainProcess] celery@xxxxx ready.
```

## Utilisation

### 1. Enregistrer un token push (Mobile)

```bash
curl -X POST http://localhost:8000/api/v1/mobile/push-tokens/ \
  -H "Authorization: Bearer JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "FCM_TOKEN_FROM_DEVICE",
    "device_type": "android",
    "device_name": "Samsung Galaxy S21"
  }'
```

### 2. Créer une notification manuellement

```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> from apps.mobileapp.models import Notification
>>> from apps.mobileapp.tasks import dispatch_notification
>>> User = get_user_model()
>>> user = User.objects.first()
>>> notif = Notification.objects.create(
...     user=user,
...     title='Test Notification',
...     body='This is a test',
...     notification_type='NORM_PUBLISHED',
...     priority='HIGH',
...     data={'norm_id': 1}
... )
>>> dispatch_notification.delay(str(notif.id))
```

### 3. Configurer les préférences de notification

```bash
curl -X PUT http://localhost:8000/api/v1/mobile/notification-preferences/update/ \
  -H "Authorization: Bearer JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enable_norm_updates": true,
    "enable_payments": true,
    "quiet_hours_enabled": true,
    "quiet_hours_start": "20:00:00",
    "quiet_hours_end": "08:00:00",
    "digest_enabled": true,
    "digest_frequency": "DAILY"
  }'
```

## Signaux et événements système

Les notifications sont créées automatiquement à partir de signaux Django:

### Normes publiées

Quand une norme est publiée, tous les experts du WG reçoivent une notification:
```
Type: NORM_PUBLISHED
Priorité: HIGH
Canal: Push + Email
```

### Invitations d'experts

Quand un expert est invité à un WG:
```
Type: EXPERT_INVITE
Priorité: HIGH
Canal: Push + Email
```

### Cotisations dues

Quand une cotisation arrive à échéance:
```
Type: PAYMENT_DUE
Priorité: HIGH
Canal: Push + Email
```

### Réunions prévues

Quand une réunion est programmée:
```
Type: REUNION_INVITE
Priorité: HIGH
Canal: Push + Email
```

### Messages

Quand un message est reçu:
```
Type: MESSAGE
Priorité: NORMAL
Canal: Push + Email
```

## Gestion des préférences

### Types de notification paramétrables

- `enable_norm_updates`: Mises à jour de normes
- `enable_payments`: Rappels de paiement
- `enable_reunion_invites`: Invitations à réunion
- `enable_votes`: Ouverture de votes
- `enable_amendments`: Nouveaux amendements
- `enable_system`: Notifications système

### Horaires silencieux

Les utilisateurs peuvent configurer des plages horaires sans notifications:

```python
prefs.quiet_hours_enabled = True
prefs.quiet_hours_start = "20:00"  # 20h
prefs.quiet_hours_end = "08:00"    # 8h du matin
```

Pendant ces heures, seules les notifications URGENT et HIGH sont envoyées.

### Digests

Les utilisateurs peuvent recevoir un digest quotidien ou hebdomadaire:

```python
prefs.digest_enabled = True
prefs.digest_frequency = 'DAILY'  # ou 'WEEKLY'
```

## Monitoring & Debugging

### Logs Celery

```bash
docker-compose logs -f celery
```

### Vérifier les tâches en attente

```bash
python manage.py shell
>>> from apps.mobileapp.models import Notification, NotificationLog
>>> # Notifications non traitées
>>> Notification.objects.filter(created_at__lt=timezone.now() - timedelta(minutes=5))
>>> # Logs d'erreur
>>> NotificationLog.objects.filter(status='FAILED')
```

### Redis info

```bash
redis-cli info
```

## Troubleshooting

### Firebase credentials introuvable

```
Error: Firebase init failed: Service account credentials not found
```

Solution:
1. Vérifier le chemin FIREBASE_CREDENTIALS_PATH
2. Ou définer FIREBASE_CREDENTIALS_JSON

### Celery ne démarre pas

```bash
# Vérifier Redis
redis-cli ping
# Vérifier les logs
docker-compose logs celery
# Redémarrer
docker-compose restart celery
```

### Emails non envoyés

1. Vérifier les credentials SMTP
2. Vérifier les logs: `docker-compose logs web`
3. Tester SMTP manuellement:

```python
from django.core.mail import send_mail
send_mail('Test', 'Test body', 'from@example.com', ['to@example.com'])
```

### Notifications FCM échouées

Vérifier:
1. Le token FCM est valide
2. Firebase est initialisé correctement
3. Les logs: `NotificationLog.objects.filter(status='FAILED')`

## Performance

### Optimisation Celery

```python
# config/settings.py
CELERY_TASK_ALWAYS_EAGER = False  # Production
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
```

### Indexes de base de données

Les modèles ont des indexes sur:
- `Notification.user, is_read`
- `Notification.user, notification_type`
- `NotificationLog.status, sent_at`
- `NotificationLog.push_token, status`
- `PushToken.user, is_active`

### Batch processing

Pour envoyer des notifications à de nombreux utilisateurs:

```python
from apps.mobileapp.tasks import dispatch_notification
from apps.mobileapp.models import Notification

# Créer les notifications en batch
notifications = [
    Notification(
        user=user,
        title='Title',
        body='Body',
        notification_type='NORM_PUBLISHED'
    )
    for user in users
]
Notification.objects.bulk_create(notifications)

# Dispatcher en async
for notif in notifications:
    dispatch_notification.delay(str(notif.id))
```

## Maintenance

### Nettoyer les anciennes notifications

```python
from django.utils import timezone
from datetime import timedelta
from apps.mobileapp.models import Notification

# Supprimer les notifications de plus de 90 jours
old_date = timezone.now() - timedelta(days=90)
Notification.objects.filter(created_at__lt=old_date).delete()
```

### Archiver les logs de notification

```python
from apps.mobileapp.models import NotificationLog

# Archiver les logs de plus de 30 jours
old_date = timezone.now() - timedelta(days=30)
NotificationLog.objects.filter(created_at__lt=old_date).delete()
```

## Support & Questions

Pour toute question ou problème:
1. Vérifier les logs: `docker-compose logs`
2. Consulter la documentation: `MOBILE_API_REFERENCE.md`
3. Vérifier les tests: `pytest apps/mobileapp/tests.py`
