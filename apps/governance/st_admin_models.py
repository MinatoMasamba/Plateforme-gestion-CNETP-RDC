"""Réception administrative et versions de PV ; aucun statut de Norme remplacé."""
import uuid
from django.db import models
from .phoenix_models import phoenix_private_storage
from .st_operations_models import ImmutableSTEntry


def reception_reference():
    return 'REC-' + uuid.uuid4().hex[:12].upper()


class STReception(models.Model):
    process = models.OneToOneField('governance.CTCProcessus', on_delete=models.PROTECT, related_name='administrative_reception')
    reference = models.CharField(max_length=30, unique=True, default=reception_reference, editable=False)
    state = models.CharField(max_length=16, default='BROUILLON', choices=[('BROUILLON','Brouillon'),('ANOMALIE','Anomalie'),('ENREGISTREE','Enregistrée')])
    revision = models.PositiveIntegerField(default=0)
    sc = models.ForeignKey('governance.Organe', on_delete=models.PROTECT, null=True, blank=True)
    group = models.ForeignKey('governance.GroupeCible', on_delete=models.PROTECT, null=True, blank=True)
    sender = models.ForeignKey('experts.Expert', on_delete=models.PROTECT, null=True, blank=True, related_name='st_transmissions')
    vote_date = models.DateField(null=True, blank=True)
    vote_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    observations = models.TextField(blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    verified = models.BooleanField(default=False)
    received_at = models.DateTimeField(null=True, blank=True)
    received_by = models.ForeignKey('core.User', on_delete=models.PROTECT, null=True, blank=True, related_name='st_receptions')
    created_by = models.ForeignKey('core.User', on_delete=models.PROTECT, related_name='st_reception_drafts')
    updated_at = models.DateTimeField(auto_now=True)


class STReceptionPiece(ImmutableSTEntry):
    reception = models.ForeignKey(STReception, on_delete=models.PROTECT, related_name='pieces')
    kind = models.CharField(max_length=12, choices=[('PROJECT','Projet de norme'),('VOTE','Preuve du vote'),('REPORT','Rapport de revue')])
    file = models.FileField(storage=phoenix_private_storage, upload_to='receptions/%Y/%m/')
    original_name = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64)
    author = models.ForeignKey('core.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class STPVVersion(ImmutableSTEntry):
    pv = models.ForeignKey('meetings.ProcessusVerbaux', on_delete=models.PROTECT, related_name='administrative_versions')
    number = models.PositiveIntegerField()
    state = models.CharField(max_length=16, choices=[('BROUILLON','Brouillon'),('A_VALIDER','À valider')])
    title = models.CharField(max_length=255)
    content = models.TextField()
    decisions = models.JSONField(default=list)
    meeting_snapshot = models.JSONField(default=dict, blank=True)
    author = models.ForeignKey('core.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-number']
        constraints = [models.UniqueConstraint(fields=['pv','number'], name='st_pv_version_unique')]
