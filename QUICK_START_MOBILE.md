# 🚀 CNETP Mobile API - Quick Start Guide

## Django System Status
```
✅ System check: 0 issues
✅ All models migrated
✅ All endpoints registered
✅ Ready for production
```

---

## 📌 Quick Commands

### Activate Virtual Environment
```bash
cd /home/minato/projet
source mon_env/bin/activate
```

### Run Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```

### Run Django Check
```bash
python manage.py check
```

### Make Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 🔌 API Base URLs

```
Local Development:    http://localhost:8000/api/v1/mobile/
Production:           https://api.cnetp.cd/api/v1/mobile/
```

---

## 📱 Mobile App Usage Flow

### 1. **Public User Registration**
```bash
curl -X POST http://localhost:8000/api/v1/mobile/auth/register_public/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure123",
    "password_confirm": "secure123",
    "first_name": "John",
    "last_name": "Doe",
    "province": "Kinshasa",
    "profession": "Ingénieur"
  }'
```

Response (201 Created):
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "user_type": "public"
  },
  "access": "JWT_TOKEN",
  "refresh": "REFRESH_TOKEN"
}
```

### 2. **Expert Activation (Invite-Based)**
Admin sends activation email with token link:
```
https://cnetp.app/activate?token=SECURE_TOKEN
```

Expert completes registration:
```bash
curl -X POST http://localhost:8000/api/v1/mobile/auth/activate_expert/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "SECURE_TOKEN_FROM_EMAIL",
    "password": "newpassword123",
    "password_confirm": "newpassword123",
    "device_id": "device-uuid",
    "device_type": "android"
  }'
```

### 3. **Login**
```bash
curl -X POST http://localhost:8000/api/v1/mobile/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "expert@cnetp.cd",
    "password": "password123",
    "device_id": "device-uuid",
    "device_type": "android",
    "device_name": "Samsung Galaxy S21"
  }'
```

### 4. **Register Push Token (After Login)**
```bash
curl -X POST http://localhost:8000/api/v1/mobile/push-tokens/ \
  -H "Authorization: Bearer JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "FCM_DEVICE_TOKEN",
    "device_type": "android",
    "device_name": "My Phone"
  }'
```

### 5. **Get User Profile**
```bash
curl -X GET http://localhost:8000/api/v1/mobile/profile/profile/ \
  -H "Authorization: Bearer JWT_TOKEN"
```

### 6. **Get Dashboard**
```bash
curl -X GET http://localhost:8000/api/v1/mobile/profile/dashboard/ \
  -H "Authorization: Bearer JWT_TOKEN"
```

### 7. **List Notifications**
```bash
curl -X GET "http://localhost:8000/api/v1/mobile/notifications/?is_read=false" \
  -H "Authorization: Bearer JWT_TOKEN"
```

### 8. **View Published Norms (No Auth)**
```bash
curl -X GET http://localhost:8000/api/v1/mobile/public/published_norms/
```

---

## 🔐 Authentication Headers

All authenticated requests require:
```
Authorization: Bearer {JWT_ACCESS_TOKEN}
Content-Type: application/json
User-Agent: CNETP-Mobile/1.0 (Android|iOS)
X-Device-ID: device-uuid
```

---

## 📊 Database Models (Quick Reference)

| Model | Purpose | Key Fields |
|-------|---------|-----------|
| **ActivationToken** | Expert invitations | token, expert, expires_at, is_used |
| **PublicUser** | Public user profiles | user, province, profession, phone |
| **PushToken** | Device push tokens | user, token, device_type, is_active |
| **Notification** | System notifications | user, title, body, type, priority, is_read |
| **NotificationLog** | Push delivery tracking | notification, status, provider, sent_at |
| **NotificationPreference** | User preferences | user, enable_*, quiet_hours_* |
| **MobileSession** | Device sessions | user, device_id, device_type, expires_at |

---

## 🧪 Test Scenarios

### Test 1: Public Registration
1. Call `POST /mobile/auth/register_public/`
2. Verify `access` and `refresh` tokens returned
3. Call `GET /mobile/profile/profile/` with access token
4. Verify user profile returned with `user_type: "public"`

### Test 2: Expert Activation
1. (Admin) Create activation token for expert in Django admin
2. Expert clicks activation link with token
3. Call `POST /mobile/auth/activate_expert/` with token
4. Verify expert account activated
5. Call `POST /mobile/auth/login/` with email/password
6. Verify JWT tokens returned

### Test 3: Push Notifications
1. Expert logs in and registers push token
2. (Admin) Create notification from Django admin
3. Verify notification appears in `GET /mobile/notifications/`
4. Mark notification read: `POST /mobile/notifications/{uuid}/mark_as_read/`
5. Verify `is_read: true` in response

### Test 4: Notification Preferences
1. Get preferences: `GET /mobile/notification-preferences/list/`
2. Disable vote notifications: `PUT /mobile/notification-preferences/update/`
3. Verify `enable_votes: false` in response

### Test 5: Public Data
1. Call `GET /mobile/public/published_norms/` (no auth)
2. Call `GET /mobile/public/ctm_composition/` (no auth)
3. Verify both return data without authentication

---

## 🛠️ File Locations

```
Project Structure:
├── apps/mobileapp/                    ← Mobile app code
│   ├── models.py                      ← 7 models
│   ├── admin.py                       ← Admin registration
│   └── migrations/                    ← Database migrations
│
├── api/v1/
│   ├── mobile_serializers.py          ← 13 serializers
│   ├── mobile_views.py                ← 6 viewsets
│   └── urls.py                        ← Endpoint routing
│
├── config/settings.py                 ← Django settings
│
└── docs/
    ├── PHASE4_MOBILE_SUMMARY.md       ← Detailed overview
    ├── MOBILE_API_REFERENCE.md        ← Complete API docs
    ├── PHASE4_IMPLEMENTATION_CHECKLIST.md ← Tasks & checklist
    └── QUICK_START_MOBILE.md          ← This file
```

---

## 🔐 Security Notes

✅ **ActivationToken**
- Expires in 7 days
- Single-use (is_used flag)
- Uses cryptographically secure tokens

✅ **JWT Tokens**
- Access token: 15 minutes
- Refresh token: 7 days
- Automatic rotation recommended

✅ **Device Fingerprinting**
- Tracks device_id, user_agent, IP address
- Detects unauthorized device access
- 30-day session expiration

---

## 🚀 Deploy Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Activate virtual environment
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Configure SMTP (email service)
- [ ] Configure FCM credentials (Firebase)
- [ ] Configure APNs credentials (Apple)
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Run tests: `pytest`
- [ ] Run Django check: `python manage.py check`
- [ ] Start server

---

## 📞 Support

For detailed documentation:
- **Full API Reference**: See `MOBILE_API_REFERENCE.md`
- **Implementation Tasks**: See `PHASE4_IMPLEMENTATION_CHECKLIST.md`
- **Architecture Overview**: See `PHASE4_MOBILE_SUMMARY.md`

---

**Last Updated**: 2026-05-20
**Version**: 1.0
**Status**: Production Ready ✅

