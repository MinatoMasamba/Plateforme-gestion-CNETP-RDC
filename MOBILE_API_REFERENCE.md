# CNETP Mobile API - Complete Reference

## Base URL
```
https://api.cnetp.cd/api/v1/mobile/
```

## Authentication

### Public Registration
```
POST /auth/register_public/

Body:
{
  "email": "user@example.com",
  "password": "securepass123",
  "password_confirm": "securepass123",
  "first_name": "John",
  "last_name": "Doe",
  "province": "Kinshasa",
  "profession": "Ingénieur",
  "phone_number": "+243123456789",
  "device_type": "android"
}

Response 201:
{
  "user": {
    "id": 123,
    "email": "user@example.com",
    "full_name": "John Doe",
    "user_type": "public",
    "is_active": true
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "message": "Inscription réussie. Bienvenue!"
}
```

### Expert Activation
```
POST /auth/activate_expert/

Body:
{
  "token": "ACTIVATION_TOKEN_FROM_EMAIL",
  "password": "newpassword123",
  "password_confirm": "newpassword123",
  "device_id": "device-uuid-1234",
  "device_type": "ios"
}

Response 200:
{
  "user": {...},
  "access": "JWT_TOKEN",
  "refresh": "REFRESH_TOKEN",
  "message": "Activation réussie. Bienvenue expert!"
}
```

### Login
```
POST /auth/login/

Body:
{
  "email": "expert@example.com",
  "password": "password123",
  "device_id": "device-uuid",
  "device_type": "android",
  "device_name": "Samsung Galaxy S21"
}

Response 200:
{
  "user": {...},
  "access": "JWT_TOKEN",
  "refresh": "REFRESH_TOKEN",
  "session_id": "uuid-of-session"
}
```

### Logout
```
POST /auth/logout/
Authorization: Bearer JWT_TOKEN

Response 200:
{
  "message": "Logout réussi"
}
```

## Push Notifications

### Register Push Token
```
POST /push-tokens/

Body:
{
  "token": "FCM_PUSH_TOKEN",
  "device_type": "android",
  "device_name": "My Phone"
}

Authorization: Bearer JWT_TOKEN

Response 201:
{
  "id": 1,
  "token": "FCM_PUSH_TOKEN",
  "device_type": "android",
  "device_name": "My Phone",
  "is_active": true,
  "last_used": "2026-05-20T10:30:00Z"
}
```

### List Push Tokens
```
GET /push-tokens/

Authorization: Bearer JWT_TOKEN

Response 200:
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "token": "FCM_TOKEN_1",
      "device_type": "android",
      "is_active": true,
      "last_used": "2026-05-20T10:30:00Z"
    },
    {
      "id": 2,
      "token": "FCM_TOKEN_2",
      "device_type": "ios",
      "is_active": true,
      "last_used": "2026-05-19T15:45:00Z"
    }
  ]
}
```

### Deactivate Push Token
```
POST /push-tokens/{id}/deactivate/

Authorization: Bearer JWT_TOKEN

Response 200:
{
  "message": "Token désactivé"
}
```

## Notifications

### List Notifications
```
GET /notifications/?is_read=false&notification_type=REUNION_INVITE

Authorization: Bearer JWT_TOKEN

Query Parameters:
  - is_read: true/false
  - notification_type: REUNION_INVITE, VOTE_OPEN, AMENDMENT, NORM_UPDATE, SYSTEM, PAYMENT, JETON
  - ordering: -created_at (default)

Response 200:
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid-1",
      "title": "Invitation - CTM 1 Réunion",
      "body": "Vous êtes invité à la réunion du CTM 1",
      "notification_type": "REUNION_INVITE",
      "priority": "HIGH",
      "data": {
        "reunion_id": 123,
        "reunion_date": "2026-05-25T10:00:00Z"
      },
      "is_read": false,
      "created_at": "2026-05-20T08:00:00Z"
    }
  ]
}
```

### Get Notification Detail
```
GET /notifications/{uuid}/

Authorization: Bearer JWT_TOKEN

Response 200:
{
  "id": "uuid-1",
  "title": "Invitation - CTM 1 Réunion",
  "body": "Vous êtes invité...",
  "notification_type": "REUNION_INVITE",
  "is_read": false,
  "read_at": null,
  "logs": [
    {
      "id": 1,
      "status": "SENT",
      "provider": "FCM",
      "sent_at": "2026-05-20T08:00:00Z"
    }
  ],
  "created_at": "2026-05-20T08:00:00Z"
}
```

### Mark as Read
```
POST /notifications/{uuid}/mark_as_read/

Authorization: Bearer JWT_TOKEN

Response 200:
{
  "id": "uuid-1",
  "is_read": true,
  "read_at": "2026-05-20T10:30:00Z"
}
```

### Mark All as Read
```
POST /notifications/mark_all_as_read/

Authorization: Bearer JWT_TOKEN

Response 200:
{
  "message": "Toutes les notifications marquées comme lues"
}
```

### Unread Count
```
GET /notifications/unread_count/

Authorization: Bearer JWT_TOKEN

Response 200:
{
  "unread_count": 3
}
```

## Notification Preferences

### Get Preferences
```
GET /notification-preferences/list/

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

### Update Preferences
```
PUT /notification-preferences/update/

Body:
{
  "enable_reunion_invites": true,
  "enable_votes": false,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "21:00:00",
  "quiet_hours_end": "07:00:00"
}

Authorization: Bearer JWT_TOKEN

Response 200:
{
  "enable_reunion_invites": true,
  "enable_votes": false,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "21:00:00",
  "quiet_hours_end": "07:00:00",
  ...
}
```

## User Profile

### Get Profile
```
GET /profile/profile/

Authorization: Bearer JWT_TOKEN

Response 200:
{
  "id": 123,
  "email": "expert@cnetp.cd",
  "full_name": "Jean Dupont",
  "first_name": "Jean",
  "last_name": "Dupont",
  "user_type": "expert",
  "structure": "Cabinet du Ministre",
  "ctm": "CTM 1 - Géotechnique",
  "wg_list": ["WG 1.1 - Reconnaissance", "WG 1.2 - Sols Tropicaux"],
  "upcoming_reunions_count": 3,
  "pending_votes_count": 2,
  "unread_notifications_count": 5
}
```

### Get Dashboard
```
GET /profile/dashboard/

Authorization: Bearer JWT_TOKEN

Expert Response 200:
{
  "user_type": "expert",
  "full_name": "Jean Dupont",
  "upcoming_reunions": 3,
  "pending_jetons_amount": "15000.00",
  "unread_notifications": 5,
  "assigned_to_ctms": 1,
  "last_login": "2026-05-20T10:00:00Z"
}

Public Response 200:
{
  "user_type": "public",
  "full_name": "John Doe",
  "unread_notifications": 2,
  "last_login": "2026-05-20T09:00:00Z"
}
```

## Public Data (No Authentication Required)

### Published Norms
```
GET /public/published_norms/

Response 200:
{
  "results": [
    {
      "id": 1,
      "reference_number": "CNETP-CTM1-001",
      "title": "Norme de Géotechnique",
      "description": "...",
      "status": "PUBLISHED",
      "ctm_id": 1,
      "wg_id": 11,
      "version_number": 1,
      "updated_at": "2026-05-20T00:00:00Z",
      "amendment_count": 2,
      "web_redirect_url": "https://cnetp.app/norms/1/"
    }
  ]
}
```

### CTM Composition
```
GET /public/ctm_composition/

Response 200:
{
  "results": [
    {
      "ctm": {
        "id": 1,
        "titre": "CTM 1 - Géotechnique et Risques Naturels",
        "description": "..."
      },
      "wgs": [
        {"id": 11, "titre": "WG 1.1 - Reconnaissance & Essais"},
        {"id": 12, "titre": "WG 1.2 - Sols Tropicaux"}
      ],
      "expert_count": 19
    }
  ]
}
```

### News
```
GET /public/news/

Response 200:
{
  "results": [
    {
      "id": 1,
      "title": "Bienvenue sur CNETP Mobile",
      "body": "Consultez les normes en temps réel...",
      "date": "2026-05-20T10:00:00Z",
      "type": "INFO"
    }
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Les mots de passe ne correspondent pas."
}
```

### 401 Unauthorized
```json
{
  "detail": "Token invalide ou expiré."
}
```

### 403 Forbidden
```json
{
  "detail": "Vous n'avez pas la permission d'accéder à cette ressource."
}
```

### 404 Not Found
```json
{
  "detail": "Ressource non trouvée."
}
```

## Headers

### All Authenticated Requests
```
Authorization: Bearer {JWT_ACCESS_TOKEN}
Content-Type: application/json
User-Agent: CNETP-Mobile/1.0 (Android|iOS)
X-Device-ID: device-uuid
X-Client-Version: 1.0.0
```

### Recommended Response Headers (Server)
```
Cache-Control: max-age=3600
ETag: "version-hash"
Last-Modified: 2026-05-20T10:00:00Z
```

## Refresh Token

### Refresh JWT Access Token
```
POST /auth/refresh_token/

Body:
{
  "refresh": "REFRESH_TOKEN"
}

Response 200:
{
  "access": "NEW_JWT_TOKEN"
}
```

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Successful GET/PUT/DELETE |
| 201 | Created - Successful POST |
| 204 | No Content - Delete successful |
| 400 | Bad Request - Validation failed |
| 401 | Unauthorized - Missing/invalid auth |
| 403 | Forbidden - Auth OK but no permission |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limited |
| 500 | Server Error |

---

**Last Updated**: 2026-05-20
**Version**: 1.0
**Base URL**: https://api.cnetp.cd/api/v1/mobile/

