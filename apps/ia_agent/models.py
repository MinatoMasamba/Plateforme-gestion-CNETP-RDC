from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.models import BaseModel


class AgentSession(BaseModel):
    """Une session de discussion avec l'agent IA, scopée par contexte d'usage."""

    SCOPE_CHOICES = [
        ('expert', 'Expert'),
        ('ctc', 'Cellule Technique de Coordination'),
        ('pilotage', 'Comité de Pilotage'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ia_agent_sessions',
    )
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    title = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Session Agent IA"
        verbose_name_plural = "Sessions Agent IA"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'scope']),
        ]

    def __str__(self):
        return f"Session {self.get_scope_display()} — {self.user} (#{self.pk})"


class AgentMessage(models.Model):
    """Un message échangé dans une session (utilisateur, assistant ou trace d'outil)."""

    ROLE_CHOICES = [
        ('user', 'Utilisateur'),
        ('assistant', 'Assistant'),
        ('tool', 'Outil'),
    ]

    session = models.ForeignKey(AgentSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField(blank=True)
    tool_name = models.CharField(max_length=100, blank=True)
    tool_input = models.JSONField(null=True, blank=True)
    tool_output = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Message Agent IA"
        verbose_name_plural = "Messages Agent IA"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_role_display()} — session #{self.session_id}"


class AgentArtifact(BaseModel):
    """Un élément produit par l'agent (demande, signalement, brouillon d'email, graphique...)."""

    ARTIFACT_TYPE_CHOICES = [
        ('WG_REQUEST', "Demande d'attribution WG"),
        ('NORM_OVERLAP', 'Chevauchement de normes'),
        ('EXTERNAL_PROPOSAL', 'Proposition référentiel externe'),
        ('EMAIL_DRAFT', "Brouillon d'email"),
        ('CHART', 'Graphique'),
    ]
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('APPROVED', 'Approuvé'),
        ('SENT', 'Envoyé'),
    ]

    session = models.ForeignKey(AgentSession, on_delete=models.CASCADE, related_name='artifacts')
    message = models.ForeignKey(
        AgentMessage, on_delete=models.SET_NULL, null=True, blank=True, related_name='artifacts',
    )
    artifact_type = models.CharField(max_length=20, choices=ARTIFACT_TYPE_CHOICES)
    title = models.CharField(max_length=300, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')

    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = "Artefact Agent IA"
        verbose_name_plural = "Artefacts Agent IA"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', 'artifact_type']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.get_artifact_type_display()} — {self.title or self.pk} ({self.status})"
