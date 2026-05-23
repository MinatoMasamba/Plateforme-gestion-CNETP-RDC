from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Utilisateur personnalisé pour CNETP"""
    phone = models.CharField(max_length=20, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_expert = models.BooleanField(default=False)
    is_ctc_staff = models.BooleanField(default=False)
    is_minister = models.BooleanField(default=False)
    bio = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"


class BaseModel(models.Model):
    """Classe de base pour tous les modèles avec audit"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="%(class)s_created_by"
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="%(class)s_updated_by"
    )
    
    class Meta:
        abstract = True


class AuditLog(models.Model):
    """Enregistrement d'audit pour traçabilité complète"""
    ACTION_CHOICES = [
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('PUBLISH', 'Publication'),
        ('VOTE', 'Vote'),
        ('APPROVE', 'Approbation'),
        ('REJECT', 'Rejet'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    content_type = models.CharField(max_length=100)  # Ex: 'Norme', 'Amendement'
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=200)  # Représentation humaine
    changes = models.JSONField(default=dict, blank=True)  # Diff des changements
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journaux d'audit"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} {self.object_repr} par {self.user} le {self.timestamp}"
