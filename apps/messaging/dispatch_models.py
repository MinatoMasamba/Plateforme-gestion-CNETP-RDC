"""Envois institutionnels conservés, distincts du chat et du circuit des normes."""
import uuid
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import Q
from django.utils.deconstruct import deconstructible


@deconstructible
class DispatchPrivateStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(file_permissions_mode=0o600, directory_permissions_mode=0o700)

    @property
    def base_location(self):
        return str(getattr(settings, 'ST_COMMUNICATIONS_ROOT', Path(settings.BASE_DIR) / '.phoenix_documents' / 'communications'))

    @property
    def location(self):
        return str(Path(self.base_location).resolve())

    def url(self, name):
        raise ValueError('Document privé : utiliser le téléchargement authentifié.')


def dispatch_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f'{uuid.uuid4().hex}{suffix}'


class InstitutionalDispatch(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='institutional_dispatches')
    sender_name = models.CharField(max_length=250)
    mandate = models.ForeignKey('governance.MandatOrganisation', null=True, blank=True, on_delete=models.PROTECT)
    target_sc = models.ForeignKey('governance.Organe', null=True, blank=True, on_delete=models.PROTECT, related_name='institutional_dispatches')
    target_gt = models.ForeignKey('governance.GroupeCible', null=True, blank=True, on_delete=models.PROTECT, related_name='institutional_dispatches')
    organisation_version = models.ForeignKey('governance.OrganisationVersion', on_delete=models.PROTECT)
    target_code = models.CharField(max_length=60)
    target_label = models.CharField(max_length=250)
    subject = models.CharField(max_length=250)
    body = models.TextField(blank=True, default='')
    html_body = models.TextField(blank=True, default='')
    target_all_sc = models.BooleanField(default=False)
    target_all_users = models.BooleanField(default=False)
    attachment = models.FileField(storage=DispatchPrivateStorage(), upload_to=dispatch_upload_to, blank=True, default='')
    original_filename = models.CharField(max_length=255, blank=True)
    attachment_sha256 = models.CharField(max_length=64, blank=True)
    attachment_size = models.PositiveIntegerField(default=0)
    attachment_mime = models.CharField(max_length=120, blank=True)
    request_key = models.UUIDField(default=uuid.uuid4)
    fingerprint = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'Envoi institutionnel SC/GT'
        verbose_name_plural = 'Historique des envois SC/GT'
        constraints = [
            models.CheckConstraint(condition=(Q(target_sc__isnull=False, target_gt__isnull=True, target_all_sc=False, target_all_users=False) | Q(target_sc__isnull=True, target_gt__isnull=False, target_all_sc=False, target_all_users=False) | Q(target_sc__isnull=True, target_gt__isnull=True, target_all_sc=True, target_all_users=False) | Q(target_sc__isnull=True, target_gt__isnull=True, target_all_sc=False, target_all_users=True)), name='dispatch_exactly_one_target'),
            models.CheckConstraint(condition=(~Q(body='') | ~Q(attachment='')), name='dispatch_requires_content'),
            models.UniqueConstraint(fields=['sender', 'request_key'], name='dispatch_unique_sender_request'),
            models.UniqueConstraint(fields=['request_key'], condition=Q(sender__isnull=True), name='dispatch_unique_system_request'),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Un envoi effectué ne peut pas être modifié.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Les envois sont conservés dans l’historique.')


class DispatchRecipient(models.Model):
    dispatch = models.ForeignKey(InstitutionalDispatch, on_delete=models.PROTECT, related_name='recipients')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='institutional_deliveries')
    recipient_name = models.CharField(max_length=250)
    email = models.EmailField(blank=True)
    email_status = models.CharField(max_length=10, choices=[('PENDING', 'En attente'), ('SENDING', 'En cours'), ('SENT', 'Accepté par le serveur e-mail'), ('FAILED', 'Échec'), ('SKIPPED', 'Non envoyé')], default='PENDING')
    email_error = models.CharField(max_length=300, blank=True)
    email_attempts = models.PositiveIntegerField(default=0)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    notification = models.OneToOneField('mobileapp.Notification', null=True, blank=True, on_delete=models.SET_NULL)
    received_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['dispatch', 'user'], name='dispatch_unique_recipient')]
        verbose_name = 'Destinataire d’envoi institutionnel'
        verbose_name_plural = 'Destinataires des envois institutionnels'


class DispatchEmailAttempt(models.Model):
    recipient = models.ForeignKey(DispatchRecipient, on_delete=models.PROTECT, related_name='email_history')
    number = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    outcome = models.CharField(max_length=10, choices=[('SENDING', 'En cours'), ('SENT', 'Accepté par le serveur e-mail'), ('FAILED', 'Échec')], default='SENDING')
    error = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['number']
        constraints = [models.UniqueConstraint(fields=['recipient', 'number'], name='dispatch_unique_email_attempt')]
