from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from decimal import Decimal
from datetime import timedelta

from apps.mobileapp.models import (
    ActivationToken, EmailConfirmationCode, PublicUser, PushToken,
    Notification, NotificationPreference, MobileSession
)
from apps.mobileapp.tasks import send_email_confirmation_code, _send_email_confirmation_code_now
from apps.experts.models import Expert
from .serializers import (
    PublicUserRegistrationSerializer, EmailConfirmationCodeSerializer,
    ResendConfirmationCodeSerializer, ExpertActivationSerializer,
    MobileLoginSerializer, MobileUserDetailSerializer,
    PushTokenSerializer, NotificationPreferenceSerializer,
    NotificationBasicSerializer, NotificationDetailSerializer,
    MobileNormSummarySerializer, MobileCalendarEventSerializer,
    MobileExpertProfileSerializer, MobileSessionSerializer
)
from ..throttles import MobileAuthThrottle

User = get_user_model()


class MobileAuthViewSet(viewsets.ViewSet):
    """Vue d'authentification mobile"""
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny],
            throttle_classes=[MobileAuthThrottle])
    def register_public(self, request):
        """Inscription utilisateur public"""
        serializer = PublicUserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'user': MobileUserDetailSerializer(user).data,
            'email': user.email,
            'requires_email_confirmation': True,
            'message': "Inscription réussie. Un code de confirmation vous a été envoyé par email."
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny],
            throttle_classes=[MobileAuthThrottle])
    def activate_expert(self, request):
        """Activation expert via token"""
        serializer = ExpertActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        device_id = request.data.get('device_id', 'unknown')
        device_type = request.data.get('device_type', 'android')
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        expires_at = timezone.now() + timedelta(days=30)
        MobileSession.objects.create(
            user=user,
            device_id=device_id,
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )

        return Response({
            'user': MobileUserDetailSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'message': 'Activation réussie. Bienvenue expert!'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny],
            throttle_classes=[MobileAuthThrottle])
    def login(self, request):
        """Login mobile"""
        serializer = MobileLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # La confirmation par code ne concerne que les utilisateurs publics
        # (register_public) ; les experts passent par leur propre flux
        # d'activation par token (activate_expert / confirm_email).
        if hasattr(user, 'public_profile') and not user.email_confirmed:
            try:
                send_email_confirmation_code.delay(user.id)
            except Exception:
                _send_email_confirmation_code_now(user.id)

            return Response({
                'error_code': 'EMAIL_NOT_CONFIRMED',
                'message': "Votre email n'est pas confirmé. Un nouveau code de confirmation vous a été envoyé.",
                'email': user.email,
            }, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)

        device_id = request.data.get('device_id', 'unknown')
        device_type = request.data.get('device_type', 'android')
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        expires_at = timezone.now() + timedelta(days=30)
        session = MobileSession.objects.create(
            user=user,
            device_id=device_id,
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )

        if hasattr(user, 'public_profile'):
            user.public_profile.last_login_mobile = timezone.now()
            user.public_profile.save()

        user_data = MobileUserDetailSerializer(user).data

        return Response({
            'user_type': user_data['user_type'],
            'user': user_data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'session_id': str(session.id)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout mobile — blackliste le refresh token et ferme la session."""
        refresh_token_str = request.data.get('refresh')
        if refresh_token_str:
            try:
                token = RefreshToken(refresh_token_str)
                token.blacklist()
            except (TokenError, InvalidToken):
                pass

        MobileSession.objects.filter(
            user=request.user, is_active=True
        ).update(is_active=False)

        return Response({'message': 'Logout réussi'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny],
            url_path='refresh', throttle_classes=[MobileAuthThrottle])
    def refresh_token(self, request):
        """Obtenir un nouvel access token via le refresh token."""
        refresh_token_str = request.data.get('refresh')
        if not refresh_token_str:
            return Response(
                {'error': 'Le champ "refresh" est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token_str)
            data = {
                'access': str(token.access_token),
                'refresh': str(token),
            }
            return Response(data, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response(
                {'error': 'Refresh token invalide ou expiré.', 'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny],
            url_path='confirm-email')
    def confirm_email(self, request):
        """Confirmer l'email d'un expert via le token reçu par email."""
        token_str = request.query_params.get('token')
        if not token_str:
            return Response(
                {'error': 'Paramètre "token" manquant.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            activation = ActivationToken.objects.select_related('expert__user').get(
                token=token_str
            )
        except ActivationToken.DoesNotExist:
            return Response(
                {'error': 'Token invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if timezone.now() > activation.expires_at:
            return Response(
                {'error': 'Token expiré. Contactez l\'administrateur pour un nouveau lien.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = activation.expert.user
        if not user.email_confirmed:
            user.email_confirmed = True
            user.save(update_fields=['email_confirmed'])

        return Response({
            'message': 'Email confirmé avec succès.',
            'expert_name': user.get_full_name(),
            'email': user.email,
            'next_step': 'Activez votre compte via l\'application Flutter avec votre token.',
            'flutter_deep_link': f'cnetp://activate-expert?token={token_str}',
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny],
            url_path='confirm-email-code', throttle_classes=[MobileAuthThrottle])
    def confirm_email_code(self, request):
        """Confirmer l'email d'un utilisateur simple/public via le code reçu par email."""
        serializer = EmailConfirmationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        device_id = request.data.get('device_id', 'unknown')
        device_type = request.data.get('device_type', 'android')
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        expires_at = timezone.now() + timedelta(days=30)
        MobileSession.objects.create(
            user=user, device_id=device_id, device_type=device_type,
            ip_address=ip_address, user_agent=user_agent, expires_at=expires_at
        )

        return Response({
            'message': 'Email confirmé avec succès. Bienvenue !',
            'user': MobileUserDetailSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny],
            url_path='resend-confirmation-code', throttle_classes=[MobileAuthThrottle])
    def resend_confirmation_code(self, request):
        """Renvoyer un nouveau code de confirmation par email."""
        serializer = ResendConfirmationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user

        try:
            send_email_confirmation_code.delay(user.id)
        except Exception:
            # Broker indisponible : envoi synchrone en repli (sans passer par Celery)
            _send_email_confirmation_code_now(user.id)

        return Response({
            'message': 'Un nouveau code de confirmation a été envoyé par email.',
        }, status=status.HTTP_200_OK)

    @staticmethod
    def _get_client_ip(request):
        """Récupérer l'IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PushTokenViewSet(viewsets.ModelViewSet):
    """Gestion des tokens push"""
    queryset = PushToken.objects.all()
    serializer_class = PushTokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.push_tokens.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Désactiver un token push"""
        token = self.get_object()
        token.is_active = False
        token.save()
        return Response({'message': 'Token désactivé'})


class NotificationPreferenceViewSet(viewsets.ViewSet):
    """Préférences de notification"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='list')
    def list_prefs(self, request):
        """Récupérer les préférences — GET /notification-preferences/list/"""
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        return Response(NotificationPreferenceSerializer(prefs).data)

    @action(detail=False, methods=['patch', 'put'], url_path='update')
    def update_prefs(self, request):
        """Mettre à jour les préférences — PATCH /notification-preferences/update/"""
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(prefs, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Notifications pour mobile"""
    serializer_class = NotificationBasicSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['notification_type', 'is_read', 'priority']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NotificationDetailSerializer
        return NotificationBasicSerializer

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Nombre de notifications non lues"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': count})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Marquer toutes les notifications comme lues"""
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

        return Response({'message': 'Toutes les notifications marquées comme lues'})

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Marquer une notification comme lue"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response(NotificationDetailSerializer(notification).data)


class MobileProfileViewSet(viewsets.ViewSet):
    """Profil utilisateur pour mobile"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Récupérer le profil utilisateur"""
        serializer = MobileExpertProfileSerializer(request.user) if request.user.is_expert \
            else MobileUserDetailSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Tableau de bord mobile"""
        if request.user.is_expert:
            try:
                expert = Expert.objects.get(user=request.user)

                upcoming_reunions = expert.presences.filter(
                    reunion__date__gte=timezone.now(),
                    reunion__status__in=['PLANNED', 'IN_PROGRESS']
                ).count()

                pending_jetons = expert.jetons.filter(status='PENDING').aggregate(
                    total=models.Sum('montant')
                )['total'] or Decimal('0')

                unread_notifs = request.user.notifications.filter(is_read=False).count()

                affectations = expert.governance_affectations.count()

                return Response({
                    'user_type': 'expert',
                    'full_name': request.user.get_full_name(),
                    'upcoming_reunions': upcoming_reunions,
                    'pending_jetons_amount': str(pending_jetons),
                    'unread_notifications': unread_notifs,
                    'assigned_to_ctms': affectations,
                    'last_login': expert.user.last_login
                })
            except Expert.DoesNotExist:
                pass

        return Response({
            'user_type': 'public',
            'full_name': request.user.get_full_name(),
            'unread_notifications': request.user.notifications.filter(is_read=False).count(),
            'last_login': request.user.last_login
        })

    @action(detail=False, methods=['get'], url_path='edit-data')
    def edit_data(self, request):
        """Données complètes pour l'édition du profil — GET /mobile/profile/edit-data/"""
        user = request.user
        data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone or '',
            'province': user.province or '',
            'bio': user.bio or '',
        }
        if user.is_expert and hasattr(user, 'expert_profile'):
            expert = user.expert_profile
            cv_url = request.build_absolute_uri(expert.cv.url) if expert.cv else ''
            data.update({
                'specialties': expert.specialties or '',
                'mobile_money_number': expert.mobile_money_number or '',
                'whatsapp_number': expert.whatsapp_number or '',
                'bank_account': expert.bank_account or '',
                'bank_name': expert.bank_name or '',
                'structure_name': expert.structure.name if expert.structure else '',
                'appointment_date': str(expert.appointment_date) if expert.appointment_date else '',
                'appointment_decree_number': expert.appointment_decree_number or '',
                'cv_url': cv_url,
                'cv_filename': expert.cv.name.split('/')[-1] if expert.cv else '',
            })
        return Response(data)

    @action(detail=False, methods=['patch'], url_path='update')
    def update_profile(self, request):
        """Mettre à jour le profil — PATCH /mobile/profile/update/"""
        user = request.user

        # Champs User
        user_fields = []
        for field in ('first_name', 'last_name', 'phone', 'province', 'bio'):
            value = request.data.get(field)
            if value is not None:
                setattr(user, field, value.strip() if isinstance(value, str) else value)
                user_fields.append(field)

        if user_fields:
            user.save(update_fields=user_fields)

        # Champs Expert
        if user.is_expert and hasattr(user, 'expert_profile'):
            expert = user.expert_profile
            expert_fields = []
            for field in ('specialties', 'mobile_money_number', 'whatsapp_number',
                          'bank_account', 'bank_name'):
                value = request.data.get(field)
                if value is not None:
                    setattr(expert, field, value.strip() if isinstance(value, str) else value)
                    expert_fields.append(field)
            # Fichier CV
            cv_file = request.FILES.get('cv')
            if cv_file:
                expert.cv = cv_file
                expert_fields.append('cv')
            if expert_fields:
                expert.save(update_fields=expert_fields)

        # Retourner les données de edit-data pour synchroniser le client
        data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'email': user.email,
            'phone': user.phone or '',
            'province': user.province or '',
            'bio': user.bio or '',
            'user_type': 'expert' if user.is_expert else 'public',
        }
        if user.is_expert and hasattr(user, 'expert_profile'):
            expert = user.expert_profile
            cv_url = request.build_absolute_uri(expert.cv.url) if expert.cv else ''
            data.update({
                'specialties': expert.specialties or '',
                'mobile_money_number': expert.mobile_money_number or '',
                'whatsapp_number': expert.whatsapp_number or '',
                'bank_account': expert.bank_account or '',
                'bank_name': expert.bank_name or '',
                'cv_url': cv_url,
                'cv_filename': expert.cv.name.split('/')[-1] if expert.cv else '',
            })
        return Response(data)


class MobilePublicViewSet(viewsets.ViewSet):
    """Données publiques accessibles sur mobile"""
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def published_norms(self, request):
        """Normes publiées (lecture seule)"""
        from apps.norms.models import Norme

        norms = Norme.objects.filter(status='PUBLISHED').values(
            'id', 'reference_number', 'title', 'description',
            'status', 'ctm_id', 'wg_id', 'updated_at'
        )

        result = []
        for norm in norms:
            norm['version_number'] = 1
            norm['amendment_count'] = 0
            norm['web_redirect_url'] = f"https://cnetp.app/norms/{norm['id']}/"
            result.append(norm)

        return Response(result)

    @action(detail=False, methods=['get'])
    def ctm_composition(self, request):
        """Composition des CTM"""
        from apps.governance.models import CTM, WG

        ctms = CTM.objects.all().values('id', 'name', 'description')
        result = []

        for ctm_data in ctms:
            ctm = CTM.objects.get(id=ctm_data['id'])
            wgs = WG.objects.filter(ctm=ctm).values('id', 'name')

            result.append({
                'ctm': ctm_data,
                'wgs': list(wgs),
                'expert_count': ctm.member_experts.count()
            })

        return Response(result)

    @action(detail=False, methods=['get'])
    def news(self, request):
        """Actualités (placeholder)"""
        return Response([
            {
                'id': 1,
                'title': 'Bienvenue sur CNETP Mobile',
                'body': 'Consultez les normes en temps réel et recevez des notifications',
                'date': timezone.now(),
                'type': 'INFO'
            }
        ])
