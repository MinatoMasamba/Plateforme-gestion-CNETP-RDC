"""Avis juridiques du pôle 3 : demandes reçues, avis rédigés et double contrôle des co-chefs."""
from django.conf import settings
from django.db import models
from apps.core.models import BaseModel


class STLegalRequest(BaseModel):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Ouverte'
        IN_PROGRESS = 'IN_PROGRESS', 'En cours'
        ANSWERED = 'ANSWERED', 'Répondue'
        CLOSED = 'CLOSED', 'Clôturée'

    class Priority(models.TextChoices):
        NORMAL = 'NORMAL', 'Normale'
        HIGH = 'HIGH', 'Prioritaire'

    reference = models.CharField(max_length=40, unique=True)
    process = models.ForeignKey('governance.CTCProcessus', on_delete=models.PROTECT, related_name='legal_requests')
    subject = models.CharField(max_length=250)
    question = models.TextField()
    requester_name = models.CharField(max_length=200)
    source_reference = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='legal_requests_opened')
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='legal_requests_closed')

    class Meta:
        ordering = ['-created_at', '-pk']
        indexes = [models.Index(fields=['status', 'due_date'], name='legal_request_state_due_idx')]

    def __str__(self):
        return f'{self.reference} · {self.subject}'


class STLegalOpinion(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Brouillon'
        SUBMITTED = 'SUBMITTED', 'Transmis au co-chef'
        CONFIRMED = 'CONFIRMED', 'Confirmé'
        RETURNED = 'RETURNED', 'À retravailler'

    class Recommendation(models.TextChoices):
        FAVORABLE = 'FAVORABLE', 'Favorable'
        RESERVE = 'RESERVE', 'Favorable avec réserves'
        COMPLEMENT = 'COMPLEMENT', 'Complément demandé'
        DEFAVORABLE = 'DEFAVORABLE', 'Défavorable'

    request = models.ForeignKey(STLegalRequest, on_delete=models.CASCADE, related_name='opinions')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='legal_opinions')
    analysis = models.TextField()
    recommendation = models.CharField(max_length=20, choices=Recommendation.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='legal_opinions_decided')
    decision_comment = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        indexes = [models.Index(fields=['status', 'author'], name='legal_opinion_state_author_idx')]

    def __str__(self):
        return f'Avis {self.request.reference} · {self.get_status_display()}'
