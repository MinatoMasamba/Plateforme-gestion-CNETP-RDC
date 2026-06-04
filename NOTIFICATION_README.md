# Système de Notifications CNETP - Documentation Complète

## 🎯 Vue d'ensemble

Implémentation complète d'un système de notifications multi-canal pour la plateforme CNETP:

### Canaux supportés
- 📱 **Push Notifications** (Android, iOS, Web) via Firebase Cloud Messaging
- 📧 **Email** avec templates HTML responsifs
- 🔔 **Web** (optionnel avec WebSocket)

### Types de notifications
16 types couvrant tous les besoins:
- Normes (publiée, mise à jour, modifiée)
- Experts (invitations, ajouts à groupes)
- Réunions (invitations, rappels)
- Paiements (dues, reçus, en retard)
- Votes (ouverture, rappels)
- Amendements
- Messages
- Jetons
- Système

### Fonctionnalités principales
✅ Préférences fine-grained (par type + quiet hours + digests)  
✅ Tracking de livraison (SENT, FAILED, BOUNCED)  
✅ Signaux automatiques (créées quand événement système)  
✅ Retry automatique avec exponential backoff  
✅ Support multi-appareils par utilisateur  
✅ Digests quotidiens/hebdomadaires  
✅ Tests unitaires complets  
✅ Production-ready

## 📁 Fichiers importants

### Code source
```
apps/mobileapp/
├── models.py              # 5 modèles: Notification, NotificationLog, PushToken, etc.
├── tasks.py               # 2 tâches Celery: dispatch_notification, send_digest
├── signals.py             # Signaux Django pour auto-création
├── apps.py                # Configuration et signal registration
├── tests.py               # Tests unitaires
├── migrations/
│   └── 0002_extend_notification_types.py
└── templates/mobileapp/emails/
    ├── norm_published.html
    ├── payment_due.html
    ├── reunion_invite.html
    ├── expert_invite.html
    └── digest.html

config/settings.py         # Configuration NOTIFICATION_SETTINGS
api/v1/mobile_views.py     # API ViewSets
api/v1/mobile_serializers.py # Serializers
```

### Documentation
```
📖 NOTIFICATION_SYSTEM_SUMMARY.md      # Résumé exécutif complet
📖 NOTIFICATION_API_GUIDE.md           # API endpoints + exemples
📖 NOTIFICATION_DEPLOYMENT_GUIDE.md    # Déploiement + troubleshooting
```

## 🚀 Quick Start

### 1. Installer les dépendances
```bash
pip install firebase-admin>=6.0.0
pip install celery>=5.0.0
pip install redis>=4.0.0
```

### 2. Configurer l'environnement
```bash
# .env
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
CELERY_BROKER_URL=redis://localhost:6379/0
```

### 3. Appliquer les migrations
```bash
python manage.py migrate mobileapp
```

### 4. Démarrer les services
```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery worker
celery -A config worker -l info

# Terminal 3: Celery beat (optionnel, pour digests)
celery -A config beat -l info

# Optionnel: Redis
redis-server

# Ou avec Docker
docker-compose up -d
```

### 5. Tester
```bash
# Tests unitaires
pytest apps/mobileapp/tests.py -v

# Test manuel: enregistrer un token push
curl -X POST http://localhost:8000/api/v1/mobile/push-tokens/ \
  -H "Authorization: Bearer JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token":"TEST_TOKEN","device_type":"android","device_name":"Test"}'

# Créer une notification
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> from apps.mobileapp.models import Notification
>>> from apps.mobileapp.tasks import dispatch_notification
>>> User = get_user_model()
>>> user = User.objects.first()
>>> notif = Notification.objects.create(
...     user=user,
...     title='Test',
...     body='Test notification',
...     notification_type='NORM_PUBLISHED',
...     priority='HIGH'
... )
>>> dispatch_notification.delay(str(notif.id))
```

## 📊 Architecture

### Flux de base
```
Événement (norme publiée, expert invité, etc.)
    ↓ Signal Django
Créer Notification object
    ↓ Celery task (async)
Vérifier préférences + quiet hours
    ↓
┌─ Push (FCM) ─┐
│              │
└─ Email (SMTP)─┘
    ↓
NotificationLog créé (SENT/FAILED)
    ↓
Utilisateur reçoit
```

### Bases de données

**Notification**
- id (UUID)
- user_id
- title, body
- notification_type (16 types)
- priority (LOW, NORMAL, HIGH, URGENT)
- data (JSON)
- is_read, read_at
- created_at

**NotificationLog**
- id
- notification_id
- push_token_id
- status (PENDING, SENT, FAILED, BOUNCED)
- provider (FCM, APNs, EMAIL, SIMULATED)
- provider_response (JSON)
- error_message
- sent_at

**PushToken**
- id
- user_id
- token (unique)
- device_type (android, ios, web)
- device_name
- is_active
- last_used

**NotificationPreference**
- user_id (one-to-one)
- enable_* (8 booleans)
- quiet_hours_enabled, start, end
- digest_enabled, frequency

## 🔌 API Endpoints

### Push Tokens
```
POST   /api/v1/mobile/push-tokens/
GET    /api/v1/mobile/push-tokens/
GET    /api/v1/mobile/push-tokens/{id}/
POST   /api/v1/mobile/push-tokens/{id}/deactivate/
```

### Notifications
```
GET    /api/v1/mobile/notifications/
GET    /api/v1/mobile/notifications/{uuid}/
POST   /api/v1/mobile/notifications/{uuid}/mark_as_read/
POST   /api/v1/mobile/notifications/mark_all_as_read/
GET    /api/v1/mobile/notifications/unread_count/
```

### Préférences
```
GET    /api/v1/mobile/notification-preferences/list/
PUT    /api/v1/mobile/notification-preferences/update/
```

## 📱 Types de notification

| Type | Priorité | Pref | Description |
|------|----------|------|-------------|
| NORM_PUBLISHED | HIGH | enable_norm_updates | Norme publiée |
| NORM_UPDATE | NORMAL | enable_norm_updates | Mise à jour de norme |
| NORM_AMENDED | NORMAL | enable_amendments | Norme modifiée |
| EXPERT_INVITE | HIGH | enable_system | Invitation expert |
| EXPERT_ADDED_TO_WG | NORMAL | enable_system | Ajouté à WG |
| REUNION_INVITE | HIGH | enable_reunion_invites | Invitation réunion |
| MEETING_REMINDER | NORMAL | enable_reunion_invites | Rappel réunion |
| VOTE_OPEN | HIGH | enable_votes | Vote ouvert |
| VOTE_REMINDER | NORMAL | enable_votes | Rappel vote |
| AMENDMENT | NORMAL | enable_amendments | Nouvel amendement |
| PAYMENT_DUE | HIGH | enable_payments | Cotisation due |
| PAYMENT_RECEIVED | NORMAL | enable_payments | Paiement reçu |
| PAYMENT_OVERDUE | URGENT | enable_payments | Cotisation en retard |
| MESSAGE | NORMAL | - | Nouveau message |
| JETON | NORMAL | enable_system | Jeton de présence |
| SYSTEM | LOW | enable_system | Système |

## ⚙️ Configuration

### Firebase Cloud Messaging

1. Créer projet: https://console.firebase.google.com
2. Télécharger credentials JSON (Service Account)
3. Configurer:
```bash
export FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
# OU
export FIREBASE_CREDENTIALS_JSON='{"type":"service_account",...}'
```

### Email (SMTP)

```bash
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=your-email@gmail.com
export EMAIL_HOST_PASSWORD=your-app-password  # App password for Gmail
export DEFAULT_FROM_EMAIL=noreply@cnetp.cd
```

### Celery + Redis

```bash
# Docker
docker run -d -p 6379:6379 redis:7-alpine

# Variables d'env
export CELERY_BROKER_URL=redis://localhost:6379/0
export CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 🧪 Tests

```bash
# Tous les tests
pytest apps/mobileapp/tests.py -v

# Avec couverture
pytest apps/mobileapp/tests.py --cov=apps.mobileapp --cov-report=html

# Test spécifique
pytest apps/mobileapp/tests.py::TestNotificationSystem::test_create_notification -v
```

## 📈 Monitoring

### Vérifier Celery
```bash
# Logs
docker-compose logs celery

# Redis CLI
redis-cli -n 0 keys "*"

# Django shell
python manage.py shell
>>> from apps.mobileapp.models import NotificationLog
>>> NotificationLog.objects.filter(status='FAILED').count()
```

### Dashboard Flower (optionnel)
```bash
pip install flower
celery -A config flower --port=5555
# http://localhost:5555
```

## 🐛 Troubleshooting

### "Firebase init failed"
```
❌ Firebase credentials not found
✅ Vérifier FIREBASE_CREDENTIALS_PATH ou FIREBASE_CREDENTIALS_JSON
```

### "Celery worker not connected"
```
❌ Connection refused
✅ Vérifier Redis: redis-cli ping
✅ Redémarrer: docker-compose restart celery
```

### "Notifications non envoyées"
```
1. Vérifier les logs:
   docker-compose logs celery
   
2. Vérifier les erreurs:
   python manage.py shell
   >>> from apps.mobileapp.models import NotificationLog
   >>> NotificationLog.objects.filter(status='FAILED')
   
3. Vérifier tokens actifs:
   >>> from apps.mobileapp.models import PushToken
   >>> PushToken.objects.filter(is_active=True).count()
```

### "Emails non reçus"
```
1. Tester SMTP:
   python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Body', 'from@ex.com', ['to@ex.com'])
   
2. Vérifier credentials dans settings
3. Vérifier logs: tail -f logs/django.log
```

## 🔐 Sécurité

- ✅ Authentification JWT sur tous endpoints
- ✅ Permissions par utilisateur (voit que ses données)
- ✅ Firebase credentials en variables d'env (jamais en code)
- ✅ CSRF protection
- ✅ SQL Injection prevention (ORM Django)
- ✅ Rate limiting (optionnel)

## 🎓 Exemples d'utilisation

### Créer une notification (Backend)

```python
from apps.mobileapp.models import Notification
from apps.mobileapp.tasks import dispatch_notification

# Créer
notification = Notification.objects.create(
    user=user,
    title='Titre',
    body='Contenu',
    notification_type='NORM_PUBLISHED',
    priority='HIGH',
    data={'norm_id': 123}
)

# Dispatcher (asynchrone)
dispatch_notification.delay(str(notification.id))
```

### Lister les notifications (API)

```bash
curl -X GET "http://localhost:8000/api/v1/mobile/notifications/?is_read=false" \
  -H "Authorization: Bearer JWT_TOKEN"
```

### Configurer les préférences (API)

```bash
curl -X PUT http://localhost:8000/api/v1/mobile/notification-preferences/update/ \
  -H "Authorization: Bearer JWT_TOKEN" \
  -d '{
    "enable_payments": true,
    "quiet_hours_enabled": true,
    "quiet_hours_start": "20:00:00",
    "quiet_hours_end": "08:00:00",
    "digest_enabled": true,
    "digest_frequency": "DAILY"
  }'
```

### Mobile: S'enregistrer pour les notifications

```swift
// iOS
Messaging.messaging().token { token, error in
    if let token = token {
        // Envoyer à l'API
        registerPushToken(token: token, deviceType: "ios")
    }
}
```

```kotlin
// Android
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        // Envoyer à l'API
        registerPushToken(token, "android")
    }
}
```

## 📚 Documentation supplémentaire

- **API complète**: `NOTIFICATION_API_GUIDE.md`
- **Déploiement**: `NOTIFICATION_DEPLOYMENT_GUIDE.md`
- **Résumé**: `NOTIFICATION_SYSTEM_SUMMARY.md`

## ✅ Checklist de production

- [ ] Firebase configuré
- [ ] SMTP configuré
- [ ] Redis en cours d'exécution
- [ ] Celery worker démarré
- [ ] Migrations appliquées
- [ ] Tests passants
- [ ] Email test envoyé
- [ ] Token FCM test enregistré
- [ ] Notification test créée
- [ ] Logs Celery vérifiés
- [ ] Docker Compose validé

## 🎉 Prêt pour production!

Toutes les fonctionnalités sont implémentées, testées et documentées.

---

Pour plus d'informations, consultez la documentation complète dans les fichiers `.md` de ce répertoire.
