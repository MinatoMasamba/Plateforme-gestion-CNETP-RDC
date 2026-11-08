"""Registre backend du ST : versions conservées et décisions séparées."""
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel


class STAccessPolicy(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    version = models.ForeignKey('governance.OrganisationVersion', on_delete=models.PROTECT)
    enabled = models.BooleanField(default=True)


class STRecord(BaseModel):
    class Kind(models.TextChoices):
        PTN = 'PTN', 'Paramètre technique national'
        FINANCE = 'FINANCE', 'Écriture financière'
        WORK = 'WORK', 'Travail de pôle'
    kind = models.CharField(max_length=12, choices=Kind.choices)
    version = models.ForeignKey('governance.OrganisationVersion', on_delete=models.PROTECT)
    pole = models.CharField(max_length=12)
    reference = models.CharField(max_length=100)
    revision = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['version', 'kind', 'reference'], name='st_unique_record_reference')]


class ImmutableSTEntry(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Une version ou décision ST est immuable ; créer une nouvelle version.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Les versions et décisions ST sont conservées.')


class STRecordRevision(ImmutableSTEntry):
    record = models.ForeignKey(STRecord, on_delete=models.PROTECT, related_name='versions')
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=250)
    content = models.TextField(blank=True)
    source_reference = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    movement = models.CharField(max_length=12, choices=[('ENGAGEMENT', 'Engagement'), ('DEPENSE', 'Dépense')], blank=True)
    operation_date = models.DateField(null=True, blank=True)
    author = models.ForeignKey('core.User', on_delete=models.PROTECT)
    mandate = models.ForeignKey('governance.MandatOrganisation', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['record', 'number'], name='st_unique_record_revision')]
        ordering = ['-number']


class STConfirmation(ImmutableSTEntry):
    revision = models.OneToOneField(STRecordRevision, on_delete=models.PROTECT, related_name='confirmation')
    decision = models.CharField(max_length=10, choices=[('CONFIRMED', 'Confirmé'), ('REJECTED', 'Rejeté')])
    comment = models.TextField()
    author = models.ForeignKey('core.User', on_delete=models.PROTECT)
    mandate = models.ForeignKey('governance.MandatOrganisation', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
