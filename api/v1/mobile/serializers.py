from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from apps.mobileapp.models import (
    ActivationToken, EmailConfirmationCode, PublicUser, PushToken,
    Notification, NotificationLog, NotificationPreference, MobileSession
)
from apps.experts.models import Expert

User = get_user_model()


# ============ Authentication & Registration ============

class PublicUserRegistrationSerializer(serializers.Serializer):
    """Inscription d'un utilisateur public"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    province = serializers.CharField(max_length=100)
    profession = serializers.CharField(max_length=255, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    device_id = serializers.CharField(max_length=255, required=False)
    device_type = serializers.ChoiceField(choices=['ios', 'android', 'web'], default='android')

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")

        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_expert=False
        )

        PublicUser.objects.create(
            user=user,
            province=validated_data['province'],
            profession=validated_data.get('profession', ''),
            phone_number=validated_data.get('phone_number', '')
        )

        NotificationPreference.objects.create(user=user)

        from apps.mobileapp.tasks import send_email_confirmation_code, _send_email_confirmation_code_now
        try:
            send_email_confirmation_code.delay(user.id)
        except Exception:
            # Broker indisponible : envoi synchrone en repli (sans passer par Celery)
            _send_email_confirmation_code_now(user.id)

        return user


class EmailConfirmationCodeSerializer(serializers.Serializer):
    """Confirmation de l'email via le code reçu par email"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable.")

        if user.email_confirmed:
            raise serializers.ValidationError("Cet email est déjà confirmé.")

        try:
            confirmation = EmailConfirmationCode.objects.filter(
                user=user, is_used=False
            ).latest('created_at')
        except EmailConfirmationCode.DoesNotExist:
            raise serializers.ValidationError("Aucun code de confirmation actif. Demandez un nouveau code.")

        if not confirmation.is_valid():
            raise serializers.ValidationError("Code expiré. Demandez un nouveau code.")

        if confirmation.code != data['code']:
            raise serializers.ValidationError("Code incorrect.")

        self.user = user
        self.confirmation = confirmation
        return data

    def save(self):
        self.user.email_confirmed = True
        self.user.save(update_fields=['email_confirmed'])
        self.confirmation.use()
        return self.user


class ResendConfirmationCodeSerializer(serializers.Serializer):
    """Renvoyer un nouveau code de confirmation par email"""
    email = serializers.EmailField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable.")

        if user.email_confirmed:
            raise serializers.ValidationError("Cet email est déjà confirmé.")

        self.user = user
        return data


class ExpertActivationSerializer(serializers.Serializer):
    """Activation d'un expert via token"""
    token = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    device_id = serializers.CharField(max_length=255, required=False)
    device_type = serializers.ChoiceField(choices=['ios', 'android', 'web'], default='android')

    def validate(self, data):
        try:
            self.token_obj = ActivationToken.objects.get(token=data['token'])
        except ActivationToken.DoesNotExist:
            raise serializers.ValidationError("Token invalide.")

        if not self.token_obj.is_valid():
            raise serializers.ValidationError("Token expiré ou déjà utilisé.")

        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")

        return data

    def create(self, validated_data):
        expert = self.token_obj.expert
        user = expert.user

        user.set_password(validated_data['password'])
        user.is_active = True
        user.save()

        self.token_obj.use()

        NotificationPreference.objects.get_or_create(user=user)

        return user



class MobileLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    device_id = serializers.CharField(max_length=255)
    device_type = serializers.ChoiceField(choices=['ios', 'android', 'web'])
    device_name = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, data):
        email = data['email']
        password = data['password']

        # 1. Authentification par email (si email != username)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email ou mot de passe incorrect.")

        # 2. Vérification du mot de passe
        if not user.check_password(password):
            raise serializers.ValidationError("Email ou mot de passe incorrect.")

        # 3. Vérification du statut actif
        if not user.is_active:
            raise serializers.ValidationError("Ce compte est désactivé.")

        # 4. Génération des tokens JWT
        refresh = RefreshToken.for_user(user)
        data['tokens'] = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        data['user'] = user

        # 5. (Optionnel) Enregistrer l’appareil dans un modèle Device
        # Device.objects.create(user=user, device_id=data['device_id'], ...)

        return data


class MobileUserDetailSerializer(serializers.ModelSerializer):
    """Détails utilisateur pour mobile"""
    email = serializers.EmailField()
    full_name = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'first_name', 'last_name', 'user_type', 'is_active']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_user_type(self, obj):
        if obj.is_staff or obj.is_superuser:
            return 'admin'
        if obj.is_expert:
            return 'expert'
        return 'public'


# ============ Push Notifications ============

class PushTokenSerializer(serializers.ModelSerializer):
    """Serializer pour les tokens push"""

    class Meta:
        model = PushToken
        fields = ['id', 'token', 'device_type', 'device_name', 'is_active', 'last_used']
        read_only_fields = ['id', 'last_used']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Préférences de notification"""

    class Meta:
        model = NotificationPreference
        fields = [
            'enable_reunion_invites', 'enable_votes', 'enable_amendments',
            'enable_norm_updates', 'enable_system', 'enable_payments',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'digest_enabled', 'digest_frequency'
        ]


class NotificationBasicSerializer(serializers.ModelSerializer):
    """Notification simple"""

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'body', 'notification_type', 'priority',
            'data', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationDetailSerializer(serializers.ModelSerializer):
    """Notification détaillée avec historique d'envoi"""
    logs = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'body', 'notification_type', 'priority',
            'data', 'is_read', 'read_at', 'logs', 'created_at'
        ]

    def get_logs(self, obj):
        logs = obj.logs.all()[:5]
        return NotificationLogSerializer(logs, many=True).data


class NotificationLogSerializer(serializers.ModelSerializer):
    """Log d'envoi notification"""

    class Meta:
        model = NotificationLog
        fields = [
            'id', 'status', 'provider', 'provider_response',
            'error_message', 'sent_at'
        ]


# ============ Mobile Read-Only Content ============

class MobileNormSummarySerializer(serializers.Serializer):
    """Résumé de norme pour mobile (lecture seule)"""
    id = serializers.IntegerField()
    reference_number = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    status = serializers.CharField()
    ctm_id = serializers.IntegerField()
    wg_id = serializers.IntegerField()
    version_number = serializers.IntegerField()
    updated_at = serializers.DateTimeField()
    amendment_count = serializers.IntegerField()
    web_redirect_url = serializers.SerializerMethodField()

    def get_web_redirect_url(self, obj):
        return f"https://cnetp.app/norms/{obj['id']}/"


class MobileCalendarEventSerializer(serializers.Serializer):
    """Événement calendrier pour expert mobile"""
    id = serializers.IntegerField()
    title = serializers.CharField()
    type = serializers.CharField()
    date = serializers.DateTimeField()
    lieu = serializers.CharField()
    lien_virtuel = serializers.URLField(required=False)
    user_status = serializers.CharField()  # PRESENT, ABSENT, EXCUSED
    jeton_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class MobileExpertProfileSerializer(serializers.ModelSerializer):
    """Profil expert pour mobile"""
    full_name = serializers.SerializerMethodField()
    structure = serializers.SerializerMethodField()
    ctm = serializers.SerializerMethodField()
    wg_list = serializers.SerializerMethodField()
    upcoming_reunions_count = serializers.SerializerMethodField()
    pending_votes_count = serializers.SerializerMethodField()
    unread_notifications_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'first_name', 'last_name',
            'structure', 'ctm', 'wg_list',
            'upcoming_reunions_count', 'pending_votes_count',
            'unread_notifications_count'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_structure(self, obj):
        if hasattr(obj, 'expert') and obj.expert.structure:
            return obj.expert.structure.name
        return None

    def get_ctm(self, obj):
        if hasattr(obj, 'expert'):
            aff = obj.expert.governance_affectations.first()
            return aff.ctm.titre if aff else None
        return None

    def get_wg_list(self, obj):
        if hasattr(obj, 'expert'):
            return list(
                obj.expert.governance_affectations.values_list('wg__titre', flat=True)
            )
        return []

    def get_upcoming_reunions_count(self, obj):
        if hasattr(obj, 'expert'):
            return obj.expert.presences.filter(
                reunion__date__gte=timezone.now(),
                reunion__status='PLANNED'
            ).count()
        return 0

    def get_pending_votes_count(self, obj):
        if hasattr(obj, 'expert'):
            from apps.amendments.models import Amendement
            return Amendement.objects.filter(
                status__in=['PROPOSED', 'UNDER_REVIEW']
            ).count()
        return 0

    def get_unread_notifications_count(self, obj):
        return obj.notifications.filter(is_read=False).count()


class MobileSessionSerializer(serializers.ModelSerializer):
    """Session mobile"""

    class Meta:
        model = MobileSession
        fields = ['id', 'device_id', 'device_type', 'last_activity', 'expires_at']
        read_only_fields = ['id', 'last_activity', 'expires_at']
