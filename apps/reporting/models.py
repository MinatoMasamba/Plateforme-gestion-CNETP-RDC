import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.core.files.storage import FileSystemStorage
from pathlib import Path

from .catalog import TYPES


def report_private_storage():
    return FileSystemStorage(location=Path(settings.BASE_DIR) / '.report_documents', file_permissions_mode=0o600, directory_permissions_mode=0o700)


class Report(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Brouillon'
        SUBMITTED = 'SUBMITTED', 'Soumis'
        RETURNED = 'RETURNED', 'Renvoyé'
        REVIEWED = 'REVIEWED', 'Contrôlé'
        APPROVED = 'APPROVED', 'Approuvé'
        REJECTED = 'REJECTED', 'Rejeté'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=80, unique=True)
    report_type = models.CharField(max_length=50, choices=[(code, f'{code} · {title}') for code, (_, title, _) in TYPES.items()])
    title = models.CharField(max_length=300)
    version = models.ForeignKey('governance.OrganisationVersion', on_delete=models.PROTECT)
    supersedes = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='newer_versions')
    pole = models.ForeignKey('governance.Organe', on_delete=models.PROTECT, null=True, blank=True)
    norme = models.ForeignKey('norms.Norme', on_delete=models.PROTECT, null=True, blank=True)
    sc = models.ForeignKey('governance.Organe', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    gt = models.ForeignKey('governance.GroupeCible', on_delete=models.PROTECT, null=True, blank=True)
    period_start = models.DateField()
    period_end = models.DateField()
    recipient = models.CharField(max_length=250)
    prepared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reports_prepared')
    prepared_mandate = models.ForeignKey('governance.MandatOrganisation', on_delete=models.PROTECT, related_name='reports_prepared')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='reports_reviewed')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='reports_approved')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    fields = models.JSONField(default=dict, blank=True)
    source_snapshot = models.JSONField(default=dict, blank=True)
    reservations = models.TextField(blank=True)
    decision_requested = models.TextField(blank=True)
    revision = models.PositiveIntegerField(default=1)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['report_type', 'status']), models.Index(fields=['version', 'period_end'])]

    def clean(self):
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValidationError('La fin de période doit suivre le début.')
        if self.pole_id and self.pole.version_id != self.version_id:
            raise ValidationError('Le pôle et le rapport doivent appartenir au même référentiel.')
        if self.sc_id and self.sc.version_id != self.version_id:
            raise ValidationError('La sous-commission et le rapport doivent appartenir au même référentiel.')
        if self.gt_id and self.gt.sc.version_id != self.version_id:
            raise ValidationError('Le groupe et le rapport doivent appartenir au même référentiel.')


class ReportTypePermission(models.Model):
    """Précise les modèles de rapport accordés par une habilitation Phoenix."""
    habilitation = models.ForeignKey('governance.HabilitationAction', on_delete=models.PROTECT, related_name='report_types')
    report_type = models.CharField(max_length=50, choices=[(code, f'{code} · {title}') for code, (_, title, _) in TYPES.items()])
    enabled = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['habilitation', 'report_type'], name='unique_report_type_habilitation')]

    def clean(self):
        from .catalog import TYPES
        if self.report_type not in TYPES:
            raise ValidationError('Modèle de rapport inconnu.')
        if self.habilitation_id and self.habilitation.action not in ('rapport.consulter', 'rapport.rediger', 'rapport.controler', 'rapport.approuver', 'rapport.transmettre'):
            raise ValidationError('Une habilitation de reporting est nécessaire.')


class ReportEvidence(models.Model):
    report = models.ForeignKey(Report, on_delete=models.PROTECT, related_name='evidence')
    title = models.CharField(max_length=250)
    source_reference = models.CharField(max_length=500, blank=True)
    file = models.FileField(upload_to='pieces/%Y/%m/', storage=report_private_storage, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class ReportEvent(models.Model):
    report = models.ForeignKey(Report, on_delete=models.PROTECT, related_name='events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=30)
    from_status = models.CharField(max_length=12, blank=True)
    to_status = models.CharField(max_length=12)
    comment = models.TextField(blank=True)
    snapshot = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class FinancialLine(models.Model):
    report = models.ForeignKey(Report, on_delete=models.PROTECT, related_name='financial_lines')
    norme = models.ForeignKey('norms.Norme', on_delete=models.PROTECT, null=True, blank=True)
    task = models.ForeignKey('governance.Tache', on_delete=models.PROTECT, null=True, blank=True)
    activity = models.CharField(max_length=250)
    need = models.CharField(max_length=500)
    result_expected = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=80)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    confirmed_funding = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    committed = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    liquidated = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    ordered = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    evidence = models.ForeignKey(ReportEvidence, on_delete=models.PROTECT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        return self.quantity * self.unit_cost

    def clean(self):
        if self.evidence_id and self.evidence.report_id != self.report_id:
            raise ValidationError('La pièce financière doit appartenir au même rapport.')
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError('La quantité doit être positive.')
        if self.unit_cost is not None and self.unit_cost < 0:
            raise ValidationError('Le coût unitaire ne peut pas être négatif.')
