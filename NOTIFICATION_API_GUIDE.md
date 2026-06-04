# API Notifications - Documentation Complète

## Vue d'ensemble

Le système de notifications CNETP supporte:
- **Notifications push** (Android, iOS, Web)
- **Envoi par email**
- **Gestion des préférences** (quiet hours, digests, par type)
- **Tracking de livraison** (logs de statut)

## Types de notifications supportées

| Type | Description | Priorité | Canal |
|------|-------------|----------|-------|
| `NORM_PUBLISHED` | Norme publiée | HIGH | Push + Email |
| `NORM_UPDATE` | Mise à jour de norme | NORMAL | Push + Email |
| `NORM_AMENDED` | Norme modifiée | NORMAL | Push + Email |
| `EXPERT_INVITE` | Invitation expert | HIGH | Push + Email |
| `EXPERT_ADDED_TO_WG` | Ajouté à un WG | NORMAL | Push + Email |
| `REUNION_INVITE` | Invitation à réunion | HIGH | Push + Email |
| `MEETING_REMINDER` | Rappel de réunion | NORMAL | Push + Email |
| `VOTE_OPEN` | Vote ouvert | HIGH | Push + Email |
| `VOTE_REMINDER` | Rappel de vote | NORMAL | Push + Email |
| `AMENDMENT` | Nouvel amendement | NORMAL | Push + Email |
| `PAYMENT_DUE` | Cotisation due | HIGH | Push + Email |
| `PAYMENT_RECEIVED` | Paiement reçu | NORMAL | Push + Email |
| `PAYMENT_OVERDUE` | Cotisation en retard | URGENT | Push + Email |
| `MESSAGE` | Nouveau message | NORMAL | Push + Email |
| `JETON` | Jeton de présence | NORMAL | Push + Email |
| `SYSTEM` | Notification système | LOW | Push + Email |

## Niveaux de priorité

- `LOW`: Peut être ignorée pendant quiet hours
- `NORMAL`: Envoyée normalement
- `HIGH`: Toujours envoyée
- `URGENT`: Toujours envoyée, même pendant quiet hours

## Endpoints

### Push Tokens (Gestion des appareils)

#### Enregistrer un token push

```
POST /api/v1/mobile/push-tokens/
Authorization: Bearer JWT_TOKEN
Content-Type: application/json

{
  "token": "FCM_PUSH_TOKEN_FROM_DEVICE",
  "device_type": "android",
  "device_name": "Samsung Galaxy S21"
}

Response 201:
{
  "id": 1,
  "token": "FCM_PUSH_TOKEN_FROM_DEVICE",
  "device_type": "android",
  "device_name": "Samsung Galaxy S21",
  "is_active": true,
  "last_used": "2026-06-03T12:00:00Z"
}
```

#### Lister les tokens de l'utilisateur

```
GET /api/v1/mobile/push-tokens/
Authorization: Bearer JWT_TOKEN

Response 200:
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "token": "fcm_token_1",
      "device_type": "android",
      "device_name": "Phone 1",
      "is_active": true,
      "last_used": "2026-06-03T12:30:00Z"
    },
    {
      "id": 2,
      "token": "fcm_token_2",
      "device_type": "ios",
      "device_name": "iPhone",
      "is_active": true,
      "last_used": "2026-06-03T11:00:00Z"
    }
  ]
}
```

#### Détail d'un token

```
GET /api/v1/mobile/push-tokens/{id}/
Authorization: Bearer JWT_TOKEN

Response 200:
{
  "id": 1,
  "token": "fcm_token_1",
  "device_type": "android",
  "device_name": "Samsung Galaxy S21",
  "is_active": true,
  "last_used": "2026-06-03T12:30:00Z"
}
```

#### Désactiver un token

```
POST /api/v1/mobile/push-tokens/{id}/deactivate/
Authorization: Bearer JWT_TOKEN

Response 200:
{
  "message": "Token désactivé"
}
```

### Notifications

#### Lister les notifications

```
GET /api/v1/mobile/notifications/?is_read=false&notification_type=NORM_PUBLISHED&ordering=-created_at
Authorization: Bearer JWT_TOKEN

Query Parameters:
  - is_read: true|false (optionnel)
  - notification_type: NORM_PUBLISHED, PAYMENT_DUE, etc. (optionnel)
  - ordering: -created_at, created_at, -priority, priority (default: -created_at)
  - page_size: 10, 20, 50 (default: 20)

Response 200:
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid-1",
      "title": "Norme publiée: CNETP-CTM1-001",
      "body": "La norme de géotechnique a été publiée",
      "notification_type": "NORM_PUBLISHED",
      "priority": "HIGH",
      "data": {
        "norm_id": 123,
        "norm_title": "Norme de Géotechnique",
        "ctm_id": 1
      },
      "is_read": false,
      "read_at": null,
      "created_at": "2026-06-03T12:00:00Z"
    }
  ]
}
```

#### Détail d'une notification avec logs

```
GET /api/v1/mobile/notifications/{uuid}/
Authorization: Bearer JWT_TOKEN

Response 200:
{
  "id": "uuid-1",
  "title": "Norme publiée",
  "body": "La norme a été publiée",
  "notification_type": "NORM_PUBLISHED",
  "priority": "HIGH",
  "data": {...},
  "is_read": false,
  "read_at": null,
  "logs": [
    {
      "id": 1,
      "status": "SENT",
      "provider": "FCM",
      "provider_response": {"message_id": "abc123"},
      "error_message": null,
      "sent_at": "2026-06-03T12:00:05Z"
    },
    {
      "id": 2,
      "status": "SENT",
      "provider": "EMAIL",
      "provider_response": {},
      "error_message": null,
      "sent_at": "2026-06-03T12:00:06Z"
    }
  ],
  "created_at": "2026-06-03T12:00:00Z"
}
```

#### Marquer comme lue

```
POST /api/v1/mobile/notifications/{uuid}/mark_as_read/
Authorization: Bearer JWT_TOKEN

Response 200:
{
  "id": "uuid-1",
  "is_read": true,
  "read_at": "2026-06-03T12:30:00Z"
}
```

#### Marquer toutes comme lues

```
POST /api/v1/mobile/notifications/mark_all_as_read/
Authorization: Bearer JWT_TOKEN

Response 200:
{
  "message": "Toutes les notifications marquées comme lues",
  "count": 5
}
```

#### Nombre de notifications non lues

```
GET /api/v1/mobile/notifications/unread_count/
Authorization: Bearer JWT_TOKEN

Response 200:
{
  "unread_count": 3
}
```

### Préférences de notification

#### Récupérer les préférences

```
GET /api/v1/mobile/notification-preferences/list/
Authorization: Bearer JWT_TOKEN

Response 200:
{
  "enable_reunion_invites": true,
  "enable_votes": true,
  "enable_amendments": true,
  "enable_norm_updates": true,
  "enable_system": true,
  "enable_payments": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "20:00:00",
  "quiet_hours_end": "08:00:00",
  "digest_enabled": false,
  "digest_frequency": "DAILY"
}
```

#### Mettre à jour les préférences

```
PUT /api/v1/mobile/notification-preferences/update/
Authorization: Bearer JWT_TOKEN
Content-Type: application/json

{
  "enable_reunion_invites": true,
  "enable_votes": false,
  "enable_payments": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "21:00:00",
  "quiet_hours_end": "07:00:00",
  "digest_enabled": true,
  "digest_frequency": "DAILY"
}

Response 200:
{
  "enable_reunion_invites": true,
  "enable_votes": false,
  "enable_payments": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "21:00:00",
  "quiet_hours_end": "07:00:00",
  "digest_enabled": true,
  "digest_frequency": "DAILY"
}
```

## Statuts de livraison

Les notifications sont trackées via `NotificationLog`:

| Statut | Signification |
|--------|---------------|
| `PENDING` | En attente d'envoi |
| `SENT` | Envoyée avec succès |
| `FAILED` | Échec de l'envoi |
| `BOUNCED` | Rejectée par le provider |

### Providers

- `FCM`: Firebase Cloud Messaging (Android/iOS)
- `APNs`: Apple Push Notification service (iOS)
- `EMAIL`: Envoi par email
- `SIMULATED`: Mode test/simulation
- `WEBPUSH`: Notification web

## Exemples d'utilisation

### 1. Mobile: S'enregistrer pour les notifications

```swift
// iOS/Swift
import FirebaseMessaging

// Obtenir le token FCM
Messaging.messaging().token { token, error in
    if let error = error {
        print("Error fetching FCM token: \(error)")
    } else if let token = token {
        // Envoyer à l'API
        registerPushToken(token: token, deviceType: "ios")
    }
}

func registerPushToken(token: String, deviceType: String) {
    let url = URL(string: "https://api.cnetp.cd/api/v1/mobile/push-tokens/")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let body = [
        "token": token,
        "device_type": deviceType,
        "device_name": UIDevice.current.name
    ]
    request.httpBody = try? JSONSerialization.data(withJSONObject: body)
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        if let error = error {
            print("Error registering token: \(error)")
        } else {
            print("Token registered successfully")
        }
    }.resume()
}
```

### 2. Mobile: Récupérer les notifications

```swift
func fetchNotifications() {
    let url = URL(string: "https://api.cnetp.cd/api/v1/mobile/notifications/?is_read=false")!
    var request = URLRequest(url: url)
    request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        if let data = data {
            let decoder = JSONDecoder()
            if let notifications = try? decoder.decode(NotificationsResponse.self, from: data) {
                // Afficher les notifications
                self.notifications = notifications.results
            }
        }
    }.resume()
}
```

### 3. Backend: Créer une notification programmatiquement

```python
from django.contrib.auth import get_user_model
from apps.mobileapp.models import Notification
from apps.mobileapp.tasks import dispatch_notification

User = get_user_model()

# Créer une notification pour un utilisateur
user = User.objects.get(email='expert@example.com')
notification = Notification.objects.create(
    user=user,
    title='Nouvelle norme publiée',
    body='La norme CNETP-CTM1-001 est maintenant disponible',
    notification_type='NORM_PUBLISHED',
    priority='HIGH',
    data={
        'norm_id': 123,
        'norm_title': 'Norme de Géotechnique',
        'ctm_id': 1
    }
)

# Dispatcher asynchroniquement
dispatch_notification.delay(str(notification.id))
```

### 4. Backend: Notifier plusieurs utilisateurs

```python
from apps.mobileapp.models import Notification
from apps.mobileapp.tasks import dispatch_notification

users = get_relevant_users()  # Votre logique
title = 'Nouvelle norme'
body = 'Une norme a été publiée'

for user in users:
    notification = Notification.objects.create(
        user=user,
        title=title,
        body=body,
        notification_type='NORM_PUBLISHED',
        priority='HIGH'
    )
    dispatch_notification.delay(str(notification.id))
```

## Gestion des erreurs

### Erreurs courantes

#### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```
Solution: Inclure le header `Authorization: Bearer JWT_TOKEN`

#### 404 Not Found
```json
{
  "detail": "Not found."
}
```
Solution: Vérifier l'UUID de la notification

#### 400 Bad Request
```json
{
  "field": ["This field is required."]
}
```
Solution: Vérifier tous les champs requis

## Limites et quotas

- Notifications push: Illimitées
- Emails: Limité par votre provider SMTP
- Rate limit API: 1000 requêtes/heure par utilisateur
- Taille max payload: 4KB pour FCM

## Performance

### Latence typique

- Notification push: 1-5 secondes
- Email: 10-30 secondes
- Digest: Traité en batch de nuit

### Optimisation

- Utiliser `is_read=false` pour les listes
- Paginer les résultats (20-50 par page)
- Utiliser les digests pour les notifications groupées

## Webhook de notification (futur)

Pour recevoir des événements de livraison:

```
POST /api/v1/mobile/notifications/webhooks/
{
  "url": "https://yourapp.com/webhooks/notification",
  "events": ["SENT", "FAILED", "BOUNCED"],
  "active": true
}
```

## Signaux système (administrateur)

Les signaux Django créent automatiquement les notifications pour:

1. **Norme publiée** → Tous les experts du WG
2. **Expert invité** → Expert invité
3. **Cotisation due** → Expert concerné
4. **Réunion programmée** → Experts participants
5. **Vote ouvert** → Votants éligibles
6. **Message reçu** → Destinataire

## Support

Pour plus d'information:
- Consulter: `NOTIFICATION_DEPLOYMENT_GUIDE.md`
- Tests: `pytest apps/mobileapp/tests.py`
- Logs: `docker-compose logs celery`
