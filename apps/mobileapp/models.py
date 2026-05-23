from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import secrets
import uuid

from apps.core.models import BaseModel
from apps.experts.models import Expert

User = get_user_model()


class ActivationToken(BaseModel):
    """Token d'activation pour les experts"""
    
    expert = models.OneToOneField(Expert, on_delete=models.CASCADE, related_name='activation_token')
    token = models.CharField(max_length=255, unique=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'mobileapp_activationtoken'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'is_used']),
            models.Index(fields=['expert', 'is_used']),
        ]
    
    def __str__(self):
        return f"Token {self.expert.user.email}"
    
    @staticmethod
    def generate_token():
        """Générer un token unique sécurisé"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_for_expert(expert, expires_in_days=7):
        """Créer un nouveau token pour un expert"""
        token_str = ActivationToken.generate_token()
        expires_at = timezone.now() + timedelta(days=expires_in_days)
        
        # Supprimer ancien token s'il existe
        ActivationToken.objects.filter(expert=expert).delete()
        
        return ActivationToken.objects.create(
            expert=expert,
            token=token_str,
            expires_at=expires_at
        )
    
    def is_valid(self):
        """Vérifier si le token est valide"""
        return (
            not self.is_used and 
            timezone.now() <= self.expires_at
        )
    
    def use(self):
        """Marquer le token comme utilisé"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()


class PublicUser(BaseModel):
    """Utilisateur public (simple consultation)"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='public_profile')
    province = models.CharField(max_length=100)
    profession = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_login_mobile = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'mobileapp_publicuser'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Public {self.user.email}"


class PushToken(BaseModel):
    """Token de notification push"""
    
    DEVICE_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_tokens')
    token = models.CharField(max_length=500, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_CHOICES)
    device_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'mobileapp_pushtoken'
        unique_together = ('user', 'token')
        ordering = ['-last_used']
    
    def __str__(self):
        return f"{self.user.email} - {self.device_type}"


class Notification(BaseModel):
    """Modèle pour les notifications"""
    
    TYPE_CHOICES = [
        ('REUNION_INVITE', 'Invitation à réunion'),
        ('VOTE_OPEN', 'Vote ouvert'),
        ('AMENDMENT', 'Nouvel amendement'),
        ('NORM_UPDATE', 'Mise à jour de norme'),
        ('SYSTEM', 'Notification système'),
        ('PAYMENT', 'Paiement'),
        ('JETON', 'Jeton de présence'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Basse'),
        ('NORMAL', 'Normale'),
        ('HIGH', 'Haute'),
        ('URGENT', 'Urgente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    data = models.JSONField(default=dict)  # Données supplémentaires (lien, ID ressource, etc.)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'mobileapp_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'notification_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        """Marquer comme lue"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()


class NotificationLog(BaseModel):
    """Log d'envoi de notifications push"""
    
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('SENT', 'Envoyée'),
        ('FAILED', 'Échouée'),
        ('BOUNCED', 'Rejectée'),
    ]
    
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    push_token = models.ForeignKey(PushToken, on_delete=models.SET_NULL, null=True, related_name='logs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    provider = models.CharField(max_length=50, blank=True)  # FCM, APNs, WebPush, etc.
    provider_response = models.JSONField(default=dict)
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'mobileapp_notificationlog'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'sent_at']),
            models.Index(fields=['push_token', 'status']),
        ]
    
    def __str__(self):
        return f"Log {self.status} - {self.notification.id}"


class NotificationPreference(BaseModel):
    """Préférences de notification pour chaque utilisateur"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Préférences par type
    enable_reunion_invites = models.BooleanField(default=True)
    enable_votes = models.BooleanField(default=True)
    enable_amendments = models.BooleanField(default=True)
    enable_norm_updates = models.BooleanField(default=True)
    enable_system = models.BooleanField(default=True)
    enable_payments = models.BooleanField(default=True)
    
    # Horaires silencieux
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(blank=True, null=True)  # ex: 20:00
    quiet_hours_end = models.TimeField(blank=True, null=True)    # ex: 08:00
    
    # Fréquence
    digest_enabled = models.BooleanField(default=False)
    digest_frequency = models.CharField(
        max_length=20,
        choices=[('DAILY', 'Quotidien'), ('WEEKLY', 'Hebdomadaire')],
        default='DAILY'
    )
    
    class Meta:
        db_table = 'mobileapp_notificationpreference'
    
    def __str__(self):
        return f"Prefs {self.user.email}"


class MobileSession(BaseModel):
    """Session utilisateur mobile (JWT tracking)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mobile_sessions')
    device_id = models.CharField(max_length=255)
    device_type = models.CharField(max_length=20)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'mobileapp_mobilesession'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"Session {self.user.email}"
    
    def is_valid(self):
        """Vérifier si la session est valide"""
        return self.is_active and timezone.now() <= self.expires_at
