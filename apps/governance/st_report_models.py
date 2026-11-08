"""Rapports de travail du ST : modèles réutilisables et versions conservées."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def validate_report_sections(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 20:
        raise ValidationError('Prévoir entre une et vingt sections.')
    total = 0
    for section in value:
        if not isinstance(section, dict) or set(section) != {'title', 'content'}:
            raise ValidationError('Chaque section doit contenir title et content.')
        if not isinstance(section['title'], str) or not section['title'].strip() or len(section['title']) > 150 or not isinstance(section['content'], str):
            raise ValidationError('Titre de section requis (150 caractères maximum) et contenu textuel attendu.')
        if any(ord(c) < 32 and c not in '\n\r\t' for c in section['title'] + section['content']):
            raise ValidationError('Le texte contient des caractères de contrôle non pris en charge.')
        total += len(section['content'])
    if total > 100000:
        raise ValidationError('Le rapport dépasse 100 000 caractères.')


class STReportTemplate(models.Model):
    name = models.CharField(max_length=200)
    system_code = models.SlugField(max_length=80, unique=True, null=True, blank=True)
    sections = models.JSONField(validators=[validate_report_sections])
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name', 'pk']
        verbose_name = 'Modèle de rapport ST'
        verbose_name_plural = 'Modèles de rapports ST'

    def __str__(self):
        return self.name


class STReport(models.Model):
    reference = models.CharField(max_length=100, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    pole_code = models.CharField(max_length=12)
    template = models.ForeignKey(STReportTemplate, on_delete=models.PROTECT, null=True, blank=True)
    revision = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-pk']
        verbose_name = 'Rapport du ST'
        verbose_name_plural = 'Rapports du ST'


class STReportVersion(models.Model):
    report = models.ForeignKey(STReport, on_delete=models.PROTECT, related_name='versions')
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=250)
    sections = models.JSONField(validators=[validate_report_sections])
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    author_name = models.CharField(max_length=350)
    mandate = models.ForeignKey('governance.MandatOrganisation', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-number']
        constraints = [models.UniqueConstraint(fields=['report', 'number'], name='st_report_unique_version')]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Une version de rapport est conservée ; créer une nouvelle version.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('L’historique des rapports est conservé.')


class STReportDispatch(models.Model):
    version = models.ForeignKey(STReportVersion, on_delete=models.PROTECT, related_name='dispatches')
    dispatch = models.OneToOneField('messaging.InstitutionalDispatch', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
