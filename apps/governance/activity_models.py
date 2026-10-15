"""Modèles additifs de suivi d'activité et de supervision des équipes.

Ils complètent les objets historiques sans réécrire leurs journaux ni déduire
des durées à partir d'anciennes actions.
"""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import BaseModel


class ActivitySession(models.Model):
    class State(models.TextChoices):
        OPEN = 'OPEN', 'Ouverte'
        CLOSED = 'CLOSED', 'Fermée'
        EXPIRED = 'EXPIRED', 'Expirée'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_sessions')
    device_id = models.CharField(max_length=96)
    tab_id = models.CharField(max_length=96, blank=True)
    channel = models.CharField(max_length=20, default='WEB')
    started_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    active_seconds = models.PositiveIntegerField(default=0)
    state = models.CharField(max_length=12, choices=State.choices, default=State.OPEN)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timezone_name = models.CharField(max_length=64, blank=True)
    current_path = models.CharField(max_length=500, blank=True)
    ctm = models.ForeignKey('governance.CTM', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_sessions')
    working_group = models.ForeignKey('governance.WG', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_sessions')
    target_group = models.ForeignKey('governance.GroupeCible', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_sessions')
    norme = models.ForeignKey('norms.Norme', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_sessions')

    class Meta:
        ordering = ['-last_seen_at']
        indexes = [
            models.Index(fields=['user', 'last_seen_at'], name='activity_user_seen_idx'),
            models.Index(fields=['state', 'last_seen_at'], name='activity_state_seen_idx'),
        ]
        permissions = [
            ('view_activity_aggregates', 'Consulter les agrégats d’activité'),
            ('view_activity_contributions', 'Consulter les contributions'),
            ('view_activity_session_details', 'Consulter les sessions détaillées'),
            ('manage_activity_targets', 'Gérer les objectifs et pondérations'),
            ('review_activity_declarations', 'Valider les déclarations et absences'),
            ('review_activity_disputes', 'Instruire les contestations'),
        ]

    def __str__(self):
        return f'{self.user} · {self.started_at:%d/%m/%Y %H:%M}'


class ActivityPulse(models.Model):
    """Battement dédupliqué ; aucune donnée saisie ou lue n'est collectée."""
    session = models.ForeignKey(ActivitySession, on_delete=models.CASCADE, related_name='pulses')
    bucket = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)
    credited_seconds = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(300)])
    visible = models.BooleanField(default=True)
    interacted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-bucket']
        constraints = [
            models.UniqueConstraint(fields=['session', 'bucket'], name='activity_unique_session_bucket'),
        ]


class WorkExpectation(BaseModel):
    expert = models.ForeignKey('experts.Expert', on_delete=models.CASCADE, related_name='work_expectations')
    mandate = models.ForeignKey('governance.MandatOrganisation', on_delete=models.PROTECT, null=True, blank=True, related_name='work_expectations')
    weekly_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-effective_from']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=models.F('effective_from')),
                name='activity_expectation_dates_order',
            ),
        ]

    def __str__(self):
        return f'{self.expert.full_name} · {self.weekly_minutes} min/semaine'


class ReviewableDeclaration(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'À instruire'
        APPROVED = 'APPROVED', 'Validée'
        REJECTED = 'REJECTED', 'Refusée'

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_reason = models.TextField(blank=True)

    class Meta:
        abstract = True


class OffPlatformWork(ReviewableDeclaration):
    expert = models.ForeignKey('experts.Expert', on_delete=models.CASCADE, related_name='off_platform_work')
    work_date = models.DateField()
    minutes = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(1440)])
    reason = models.TextField()
    evidence_reference = models.CharField(max_length=500, blank=True)
    ctm = models.ForeignKey('governance.CTM', on_delete=models.PROTECT, null=True, blank=True, related_name='off_platform_work')
    working_group = models.ForeignKey('governance.WG', on_delete=models.PROTECT, null=True, blank=True, related_name='off_platform_work')
    target_group = models.ForeignKey('governance.GroupeCible', on_delete=models.PROTECT, null=True, blank=True, related_name='off_platform_work')
    norme = models.ForeignKey('norms.Norme', on_delete=models.PROTECT, null=True, blank=True, related_name='off_platform_work')

    class Meta:
        ordering = ['-work_date', '-created_at']


class JustifiedAbsence(ReviewableDeclaration):
    expert = models.ForeignKey('experts.Expert', on_delete=models.CASCADE, related_name='justified_absences')
    starts_on = models.DateField()
    ends_on = models.DateField()
    reason = models.TextField()
    evidence_reference = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-starts_on']
        constraints = [
            models.CheckConstraint(condition=models.Q(ends_on__gte=models.F('starts_on')), name='activity_absence_dates_order'),
        ]


class BusinessCalendarDay(BaseModel):
    date = models.DateField(unique=True)
    is_working_day = models.BooleanField(default=True)
    label = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f'{self.date:%d/%m/%Y} · {self.label or ("ouvré" if self.is_working_day else "non ouvré")}'


class ActivitySilencePeriod(BaseModel):
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    reason = models.CharField(max_length=300)
    ctm = models.ForeignKey('governance.CTM', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_silences')
    working_group = models.ForeignKey('governance.WG', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_silences')
    target_group = models.ForeignKey('governance.GroupeCible', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_silences')

    class Meta:
        ordering = ['-starts_at']
        constraints = [
            models.CheckConstraint(condition=models.Q(ends_at__gt=models.F('starts_at')), name='activity_silence_dates_order'),
        ]


class ActivityDispute(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Contesté'
        UPHELD = 'UPHELD', 'Contestation acceptée'
        DISMISSED = 'DISMISSED', 'Contestation rejetée'

    expert = models.ForeignKey('experts.Expert', on_delete=models.PROTECT, related_name='activity_disputes')
    source_type = models.CharField(max_length=40)
    source_identifier = models.CharField(max_length=100)
    reason = models.TextField()
    expert_evidence = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='reviewed_activity_disputes')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_position = models.TextField(blank=True)
    decision_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['expert', 'source_type', 'source_identifier'], condition=models.Q(status='PENDING'), name='activity_one_open_dispute'),
        ]


class ActivityAccessLog(models.Model):
    class DetailLevel(models.TextChoices):
        SUMMARY = 'SUMMARY', 'Fiche d’activité'
        SESSION_TECHNICAL = 'SESSION_TECHNICAL', 'Détails techniques des sessions'
        SELF_TRANSPARENCY = 'SELF_TRANSPARENCY', 'Données personnelles propres'

    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='activity_detail_accesses')
    target_expert = models.ForeignKey('experts.Expert', on_delete=models.PROTECT, related_name='activity_data_accesses')
    detail_level = models.CharField(max_length=30, choices=DetailLevel.choices, default=DetailLevel.SUMMARY)
    purpose = models.CharField(max_length=300, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['target_expert', 'created_at'], name='activity_access_target_idx')]


class ActivityAlert(BaseModel):
    class Severity(models.TextChoices):
        WATCH = 'WATCH', 'À surveiller'
        ACTION = 'ACTION', 'Action requise'
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Ouverte'
        HANDLED = 'HANDLED', 'Je gère'
        BLOCKED = 'BLOCKED', 'Bloqué'
        POSTPONEMENT = 'POSTPONEMENT', 'Report demandé'
        RESOLVED = 'RESOLVED', 'Résolue'

    severity = models.CharField(max_length=10, choices=Severity.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    kind = models.CharField(max_length=50)
    message = models.TextField()
    expert = models.ForeignKey('experts.Expert', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_alerts')
    task = models.ForeignKey('governance.Tache', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_alerts')
    norme = models.ForeignKey('norms.Norme', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_alerts')
    response = models.TextField(blank=True)
    responded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    responded_at = models.DateTimeField(null=True, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-severity', '-created_at']


class ActivityAggregate(models.Model):
    class Period(models.TextChoices):
        DAY = 'DAY', 'Jour'
        MONTH = 'MONTH', 'Mois'

    period_type = models.CharField(max_length=8, choices=Period.choices)
    period_start = models.DateField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_aggregates')
    ctm = models.ForeignKey('governance.CTM', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_aggregates')
    working_group = models.ForeignKey('governance.WG', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_aggregates')
    target_group = models.ForeignKey('governance.GroupeCible', on_delete=models.PROTECT, null=True, blank=True, related_name='activity_aggregates')
    active_seconds = models.PositiveIntegerField(default=0)
    declared_seconds = models.PositiveIntegerField(default=0)
    task_weight = models.PositiveIntegerField(default=0)
    weighted_progress = models.PositiveIntegerField(default=0)
    accepted_deliverables = models.PositiveIntegerField(default=0)
    returned_deliverables = models.PositiveIntegerField(default=0)
    source_count = models.PositiveIntegerField(default=0)
    disputed = models.BooleanField(default=False)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-period_start']
        constraints = [
            models.UniqueConstraint(fields=['period_type', 'period_start', 'user', 'ctm', 'working_group', 'target_group'], name='activity_unique_aggregate_scope'),
        ]


class SavedActivityView(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_activity_views')
    name = models.CharField(max_length=120)
    filters = models.JSONField(default=dict)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(fields=['owner', 'name'], name='activity_unique_saved_view')]

