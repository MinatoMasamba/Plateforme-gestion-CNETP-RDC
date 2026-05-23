from django.db import models
from django.core.validators import MinValueValidator
from apps.norms.models import Norme
from django.utils.timezone import now


class PublicAmendement(models.Model):
    """
    Amendements soumis par le public lors de la phase d'enquête publique.
    Contrairement aux Amendement internes, ceux-ci ne nécessitent pas d'authentification.
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente de révision'),
        ('UNDER_REVIEW', 'En cours d\'examen'),
        ('ACCEPTED', 'Accepté'),
        ('REJECTED', 'Rejeté'),
        ('ARCHIVED', 'Archivé'),
    ]

    # Norme cible
    norme = models.ForeignKey(
        Norme,
        on_delete=models.CASCADE,
        related_name='public_amendments'
    )

    # Informations du proposant
    proposed_by_name = models.CharField(
        max_length=255,
        help_text="Nom complet du proposant"
    )
    proposed_by_email = models.EmailField(
        help_text="Email du proposant (pour notification)"
    )
    proposed_by_organization = models.CharField(
        max_length=255,
        blank=True,
        help_text="Organisation/entreprise du proposant (optionnel)"
    )

    # Contenu de l'amendement
    title = models.CharField(
        max_length=255,
        help_text="Titre court de l'amendement"
    )
    description = models.TextField(
        help_text="Description détaillée de l'amendement proposé"
    )
    justification = models.TextField(
        blank=True,
        help_text="Justification/rationale de l'amendement"
    )

    # Statut & Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    review_notes = models.TextField(
        blank=True,
        help_text="Notes de révision par le CTC"
    )
    reviewed_by = models.CharField(
        max_length=255,
        blank=True,
        help_text="Nom du réviseur CTC"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Amendement Public"
        verbose_name_plural = "Amendements Publics"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['norme', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Amendement #{self.id} - {self.title} ({self.status})"

    def mark_as_reviewed(self, reviewer_name, notes, status):
        """Marquer comme révisé"""
        self.reviewed_by = reviewer_name
        self.review_notes = notes
        self.status = status
        self.reviewed_at = now()
        self.save()

    def get_status_display_fr(self):
        """French status display"""
        display = dict(self.STATUS_CHOICES)
        return display.get(self.status, self.status)
