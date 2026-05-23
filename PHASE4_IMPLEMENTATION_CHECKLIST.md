# Phase 4 - Mobile API Implementation Checklist

## ✅ Completed Tasks

### Core Infrastructure
- [x] Created `apps/mobileapp` Django app with proper configuration
- [x] Registered mobileapp in INSTALLED_APPS as `apps.mobileapp.apps.MobileappConfig`
- [x] Created all 7 mobile models with proper indexing and constraints

### Database Models (7 models, all migrated)
- [x] **ActivationToken** - Secure expert activation links (7-day expiration)
- [x] **PublicUser** - Public user profiles with mobile tracking
- [x] **PushToken** - FCM/APNs token storage (multi-device support)
- [x] **Notification** - Multi-type notification system with priority levels
- [x] **NotificationLog** - Push delivery tracking by provider
- [x] **NotificationPreference** - User notification settings with quiet hours
- [x] **MobileSession** - JWT session tracking with device fingerprinting

### Authentication Endpoints (4 endpoints)
- [x] `POST /mobile/auth/register_public/` - Public user auto-registration
- [x] `POST /mobile/auth/activate_expert/` - Expert activation with token validation
- [x] `POST /mobile/auth/login/` - JWT token generation for mobile
- [x] `POST /mobile/auth/logout/` - Session cleanup and invalidation

### Push Notification Endpoints (5 endpoints)
- [x] `POST /mobile/push-tokens/` - Register FCM/APNs token
- [x] `GET /mobile/push-tokens/` - List user's push tokens
- [x] `POST /mobile/push-tokens/{id}/deactivate/` - Deactivate device token
- [x] `GET /mobile/push-tokens/{id}/` - Get specific token details

### Notification Management Endpoints (5 endpoints)
- [x] `GET /mobile/notifications/` - List user's notifications with filtering
- [x] `GET /mobile/notifications/{uuid}/` - Get notification details with delivery logs
- [x] `POST /mobile/notifications/{uuid}/mark_as_read/` - Mark single notification as read
- [x] `POST /mobile/notifications/mark_all_as_read/` - Bulk mark all as read
- [x] `GET /mobile/notifications/unread_count/` - Get unread notification count

### Notification Preferences Endpoints (2 endpoints)
- [x] `GET /mobile/notification-preferences/list/` - Get user notification preferences
- [x] `PUT /mobile/notification-preferences/update/` - Update notification preferences

### User Profile Endpoints (2 endpoints)
- [x] `GET /mobile/profile/profile/` - Get authenticated user profile
- [x] `GET /mobile/profile/dashboard/` - Get user dashboard (expert or public)

### Public Data Endpoints (3 endpoints) - No Auth Required
- [x] `GET /mobile/public/published_norms/` - List published norms
- [x] `GET /mobile/public/ctm_composition/` - List CTMs and WGs
- [x] `GET /mobile/public/news/` - Get system news

### Serializers (13 serializers created)
- [x] PublicUserRegistrationSerializer
- [x] ExpertActivationSerializer
- [x] MobileLoginSerializer
- [x] MobileLogoutSerializer
- [x] PushTokenSerializer
- [x] NotificationSerializer
- [x] NotificationDetailSerializer
- [x] NotificationPreferenceSerializer
- [x] MobileUserProfileSerializer
- [x] MobileDashboardSerializer
- [x] PublishedNormMobileSerializer
- [x] CTMCompositionSerializer
- [x] NewsSerializer

### Viewsets (6 viewsets created)
- [x] MobileAuthViewSet
- [x] PushTokenViewSet
- [x] NotificationViewSet
- [x] NotificationPreferenceViewSet
- [x] MobileProfileViewSet
- [x] MobilePublicViewSet

### Routing Configuration
- [x] Updated `api/v1/urls.py` with all 6 mobile viewsets
- [x] Registered under `/api/v1/mobile/*` namespace
- [x] Proper permission classes assigned (IsAuthenticated, AllowAny as needed)

### Documentation
- [x] Created `PHASE4_MOBILE_SUMMARY.md`
- [x] Created `MOBILE_API_REFERENCE.md` (complete endpoint reference)
- [x] Created `PHASE4_IMPLEMENTATION_CHECKLIST.md` (this file)

---

## 📋 Pending Tasks (Phase 5+)

### Immediate Priorities
- [ ] **File Upload Endpoint** - Expert file submissions (photos, PDFs)
  - [ ] Create FileUpload model
  - [ ] POST /mobile/files/upload/
  - [ ] GET /mobile/files/
  - [ ] Integrate AWS S3 or cloud storage
  
- [ ] **Rate Limiting** - Prevent abuse
  - [ ] Add throttling to auth endpoints
  - [ ] Add throttling to file upload
  - [ ] Configure per-user rate limits

- [ ] **Email Service** - Activation links delivery
  - [ ] Configure SMTP backend (SendGrid, Postmark)
  - [ ] Create email templates
  - [ ] Test activation email workflow

### Push Notification Integration
- [ ] **Firebase Cloud Messaging (FCM)**
  - [ ] Create FCM project and obtain credentials
  - [ ] Implement FCM sender service
  - [ ] Create Celery task for async FCM dispatch
  
- [ ] **Apple Push Notification Service (APNs)**
  - [ ] Obtain Apple developer certificates
  - [ ] Implement APNs sender service
  - [ ] Create fallback for APNs delivery failures

- [ ] **Notification Templates**
  - [ ] Create templates for all notification types (REUNION_INVITE, VOTE_OPEN, etc.)
  - [ ] Implement dynamic template rendering
  - [ ] Test multi-language support (FR/LN)

### Offline Support
- [ ] **Caching Strategy**
  - [ ] Implement ETag headers for published norms
  - [ ] Add Last-Modified headers
  - [ ] Document cache control policies
  
- [ ] **Offline Queue**
  - [ ] Create SyncQueue model for delayed operations
  - [ ] Implement queue processing logic
  - [ ] Handle conflict resolution

### Performance & Monitoring
- [ ] **Response Time Optimization**
  - [ ] Add database query optimization
  - [ ] Implement pagination for large result sets
  - [ ] Add caching layer (Redis)

- [ ] **Error Tracking**
  - [ ] Integrate Sentry for crash reporting
  - [ ] Implement error logging middleware
  - [ ] Create error dashboard

- [ ] **Analytics**
  - [ ] Track user login/logout events
  - [ ] Track feature usage (norms viewed, votes cast)
  - [ ] Create analytics dashboard

---

## 🔐 Security Checklist

- [x] JWT token generation implemented
- [x] ActivationToken uses cryptographically secure tokens (secrets.token_urlsafe)
- [x] One-time use activation tokens (is_used flag)
- [x] Token expiration (7 days for ActivationToken, 15 min for JWT access)
- [x] Password hashing via Django auth
- [x] MobileSession tracks device fingerprinting
- [x] Device ID validation for multi-device detection
- [ ] **TODO**: Rate limiting for auth attempts
- [ ] **TODO**: CORS configuration for mobile app domain
- [ ] **TODO**: SSL/TLS certificate configuration
- [ ] **TODO**: Database encryption at rest (sensitive fields)
- [ ] **TODO**: Audit logging for sensitive operations
- [ ] **TODO**: Two-factor authentication for experts (optional enhancement)

---

## 🧪 Testing Requirements

### Unit Tests Needed
- [ ] ActivationToken generation and validation
- [ ] Expert activation workflow (token expiration, reuse prevention)
- [ ] Public user registration with duplicate email prevention
- [ ] JWT token generation and refresh
- [ ] Notification filtering and pagination
- [ ] Permission checks for mobile endpoints
- [ ] MobileSession device fingerprinting
- [ ] Push token deactivation logic

### Integration Tests Needed
- [ ] Full registration → activation → login flow for experts
- [ ] Public registration → login flow
- [ ] Multi-device login (same user, different devices)
- [ ] Notification delivery tracking (FCM/APNs)
- [ ] Notification preferences enforcement
- [ ] Quiet hours notification suppression
- [ ] Pagination and filtering for large datasets

### End-to-End Tests Needed
- [ ] Mobile app can register public user
- [ ] Mobile app can activate expert with email link
- [ ] Mobile app can login and receive JWT token
- [ ] Mobile app can receive push notifications
- [ ] Mobile app properly displays user dashboard
- [ ] Mobile app can view published norms
- [ ] Mobile app respects notification preferences

---

## 📱 Frontend Mobile App Requirements

### Authentication Flow
```
Startup Screen
    ↓
[Public Signup] ← → [Expert Login]
    ↓                    ↓
Register Account    Email + Password
Confirm Email
Activate Account
    ↓
Login Screen
    ↓
Main Dashboard
```

### Deep Linking URLs
- `cnetp://activate-expert?token=ACTIVATION_TOKEN` - Expert activation link
- `cnetp://norm/{norm_id}` - View norm details (opens web if editable)
- `cnetp://reunion/{reunion_id}` - View reunion details
- `cnetp://vote/{vote_id}` - Vote redirect to web app
- `cnetp://notification/{notification_id}` - Open notification details

### Offline Capabilities
- [ ] Cache published norms locally
- [ ] Cache user profile
- [ ] Queue notifications when offline
- [ ] Sync when connection restored

### Push Notification Handling
- [ ] Request user permission on first launch
- [ ] Handle notification tapped → open appropriate screen
- [ ] Respect quiet hours locally (in addition to server-side)
- [ ] Show notification badge count

---

## 📊 Database Schema Verification

Run these queries to verify all models are migrated:

```sql
-- Check all tables exist
SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%mobileapp%';

-- Expected tables:
-- - mobileapp_activationtoken
-- - mobileapp_publicuser
-- - mobileapp_pushtoken
-- - mobileapp_notification
-- - mobileapp_notificationlog
-- - mobileapp_notificationpreference
-- - mobileapp_mobilesession

-- Check indexes
SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%mobileapp%';

-- Expected indexes (at minimum):
-- - idx_notification_user_is_read
-- - idx_notification_user_type
-- - idx_notificationlog_status_sent_at
-- - idx_pushtoken_user_is_active
```

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (unit, integration, E2E)
- [ ] Database migrations created and tested
- [ ] Environment variables configured (.env)
- [ ] Static files collected
- [ ] Email service configured and tested
- [ ] FCM/APNs credentials obtained and configured
- [ ] AWS S3 (or alternative) configured for file uploads
- [ ] Redis configured for caching/sessions
- [ ] Backup procedure documented

### Deployment Steps
- [ ] Tag release in git
- [ ] Build Docker image
- [ ] Push Docker image to registry
- [ ] Update deployment configs
- [ ] Run database migrations
- [ ] Restart web server
- [ ] Run smoke tests
- [ ] Monitor error tracking (Sentry)
- [ ] Monitor API response times

### Post-Deployment
- [ ] Verify mobile app can connect
- [ ] Test expert activation workflow
- [ ] Test push notification delivery
- [ ] Monitor API logs for errors
- [ ] Verify database backups
- [ ] Document any issues in postmortem

---

## 📞 Support & Troubleshooting

### Common Issues

**1. Activation token not received in email**
- Check email service configuration in settings.py
- Verify SMTP credentials
- Check spam folder
- Review Django logs for email sending errors

**2. FCM token registration fails**
- Verify FCM project is created and credentials configured
- Check device FCM token format (should be valid FCM format)
- Review FCM admin console for errors

**3. JWT token expired**
- Mobile app should use refresh token to get new access token
- Verify token expiration settings (15 min for access, 7 days for refresh)
- Ensure refresh token sent in request body

**4. Notification not received on device**
- Verify push token is registered and active
- Check notification preferences (quiet hours, notification type enabled)
- Verify FCM/APNs delivery logs in database
- Check mobile app logs for notification handling errors

---

## 📚 Related Documentation

- `PHASE4_MOBILE_SUMMARY.md` - Comprehensive Phase 4 overview
- `MOBILE_API_REFERENCE.md` - Complete endpoint documentation
- `README.md` - Project overview
- `API_DOCUMENTATION.md` - Full API documentation (web + mobile)
- `ARCHITECTURE.md` - System architecture overview

---

**Last Updated**: 2026-05-20
**Status**: Phase 4 Implementation Complete, Phase 5 Planning Underway
**Next Phase**: File upload, FCM/APNs integration, offline support

