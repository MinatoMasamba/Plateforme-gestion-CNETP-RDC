"""Indexation documentaire : fichiers privés, codes autorisés et versions conservées."""
import uuid
from django.db import models
from .phoenix_models import phoenix_private_storage
from .st_operations_models import ImmutableSTEntry


def ged_path(instance, filename):
    from pathlib import Path
    return f'ged/{instance.process_id}/{uuid.uuid4().hex}{Path(filename).suffix.lower()}'


class STGEDCode(ImmutableSTEntry):
    code = models.CharField(max_length=80, unique=True)
    norme = models.ForeignKey('norms.Norme', on_delete=models.PROTECT, related_name='ged_codes')
    sc = models.ForeignKey('governance.Organe', on_delete=models.PROTECT)
    source_reference = models.CharField(max_length=500)
    approved_by = models.ForeignKey('core.User', on_delete=models.PROTECT)
    approved_at = models.DateTimeField(auto_now_add=True)


class STGEDFile(ImmutableSTEntry):
    process = models.ForeignKey('governance.CTCProcessus', on_delete=models.PROTECT, related_name='ged_files')
    file = models.FileField(storage=phoenix_private_storage, upload_to=ged_path)
    name = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64)
    size = models.PositiveIntegerField()
    author = models.ForeignKey('core.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class STGEDIndexation(ImmutableSTEntry):
    process = models.ForeignKey('governance.CTCProcessus', on_delete=models.PROTECT, related_name='ged_indexations')
    version = models.OneToOneField('norms.NormeVersion', on_delete=models.PROTECT, related_name='ged_indexation')
    code = models.ForeignKey(STGEDCode, on_delete=models.PROTECT)
    sc = models.ForeignKey('governance.Organe', on_delete=models.PROTECT)
    group = models.ForeignKey('governance.GroupeCible', on_delete=models.PROTECT)
    source = models.ForeignKey(STGEDFile, on_delete=models.PROTECT)
    report = models.ForeignKey('governance.STReceptionPiece', on_delete=models.PROTECT)
    observation = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    author = models.ForeignKey('core.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    restored_from = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        ordering = ['-created_at', '-pk']


class STGEDConfirmation(ImmutableSTEntry):
    indexation = models.OneToOneField(STGEDIndexation, on_delete=models.PROTECT, related_name='confirmation')
    decision = models.CharField(max_length=12, choices=[('CONFIRMED', 'Confirmée'), ('RETURNED', 'À corriger')])
    comment = models.TextField()
    author = models.ForeignKey('core.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class STGEDAnomaly(models.Model):
    KIND_CHOICES = [
        ('MISSING_FILE', 'Fichier manquant'),
        ('CORRUPT', 'Fichier corrompu'),
        ('MISFILED', 'Pièce mal classée'),
        ('INCONSISTENT', 'Information incohérente'),
    ]
    process = models.ForeignKey('governance.CTCProcessus', on_delete=models.PROTECT, related_name='ged_anomalies')
    author = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='ged_anomalies')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='INCONSISTENT')
    recipient = models.ForeignKey('core.User', on_delete=models.PROTECT, null=True, blank=True, related_name='ged_anomalies_received')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('core.User', on_delete=models.PROTECT, null=True, blank=True, related_name='ged_anomalies_resolved')
    resolution = models.TextField(blank=True)

    @property
    def status(self):
        if self.resolved_at:
            return 'RESOLVED'
        return 'TRANSMITTED' if self.recipient_id else 'OPEN'

    @property
    def status_label(self):
        return {'RESOLVED': 'Résolue', 'TRANSMITTED': 'Transmise', 'OPEN': 'Ouverte'}[self.status]
