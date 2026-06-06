Module: mobile
==============
API mobile pour l'application Flutter: authentification, notifications push, profil et contenu public.

Contenu:
- serializers.py : PublicUserRegistrationSerializer, ExpertActivationSerializer, MobileLoginSerializer,
                   MobileUserDetailSerializer, PushTokenSerializer, NotificationPreferenceSerializer,
                   NotificationBasicSerializer, NotificationDetailSerializer, NotificationLogSerializer,
                   MobileNormSummarySerializer, MobileCalendarEventSerializer,
                   MobileExpertProfileSerializer, MobileSessionSerializer.
- views.py       : MobileAuthViewSet (register_public/activate_expert/login/logout/refresh_token/confirm-email),
                   PushTokenViewSet (CRUD + deactivate),
                   NotificationPreferenceViewSet (list/update),
                   NotificationViewSet (read-only + unread_count/mark_all_as_read/mark_as_read),
                   MobileProfileViewSet (profile/dashboard),
                   MobilePublicViewSet (published_norms/ctm_composition/news).

Endpoints principaux:
  POST       /api/v1/mobile/auth/register_public/
  POST       /api/v1/mobile/auth/activate_expert/
  POST       /api/v1/mobile/auth/login/
  POST       /api/v1/mobile/auth/logout/
  GET        /api/v1/mobile/auth/confirm-email/
  GET/POST   /api/v1/mobile/push-tokens/
  GET/PUT    /api/v1/mobile/notification-preferences/
  GET        /api/v1/mobile/notifications/
  GET        /api/v1/mobile/profile/dashboard/
  GET        /api/v1/mobile/public/published_norms/
