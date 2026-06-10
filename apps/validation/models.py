from django.db import models
from apps.core.models import BaseModel, User
from apps.norms.models import Norme
from apps.experts.models import Expert


_REVIEW_STATUS = [
    ('PENDING', 'En attente'),
    ('ASSIGNED', 'Attribué'),
    ('IN_REVIEW', 'En cours'),
    ('COMPLETED', 'Terminé'),
    ('APPROVED', 'Approuvé'),
    ('REJECTED', 'Rejeté'),
]


class LegisticReview(BaseModel):
    """Toilettage légistique — Conseiller Juridique CTC"""
    norme = models.OneToOneField(Norme, on_delete=models.CASCADE, related_name='legistic_review')
    legist = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_as_legist')

    STATUS_CHOICES = [
        ('PENDING', 'En attente de légiste'),
        ('ASSIGNED', 'Attribué au légiste'),
        ('IN_REVIEW', 'En cours de toilettage'),
        ('REVIEW_COMPLETED', 'Toilettage terminé'),
        ('APPROVED', 'Approuvé'),
        ('REJECTED', 'Rejeté'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    comments = models.TextField(blank=True, null=True, help_text="Commentaires du légiste")
    review_start_date = models.DateField(null=True, blank=True)
    review_end_date = models.DateField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Toilettage Légistique"
        verbose_name_plural = "Toilettages Légistiques"
        ordering = ['status', '-created_at']

    def __str__(self):
        return f"Toilettage {self.norme.reference_number} - {self.status}"


class ISOReview(BaseModel):
    """Vérification harmonisation ISO/SADC — Experts Veille Normative"""
    norme = models.OneToOneField(Norme, on_delete=models.CASCADE, related_name='iso_review')
    expert = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_as_iso_expert')

    STATUS_CHOICES = _REVIEW_STATUS
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    harmonization_notes = models.TextField(blank=True, help_text="Notes d'alignement ISO/SADC/RDC")
    iso_references = models.CharField(max_length=500, blank=True, help_text="Références ISO applicables, ex: ISO 9001, ISO/TC 58")
    review_start_date = models.DateField(null=True, blank=True)
    review_end_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Examen Veille ISO"
        verbose_name_plural = "Examens Veille ISO"
        ordering = ['status', '-created_at']

    def __str__(self):
        return f"ISO {self.norme.reference_number} - {self.status}"


class EcologicalReview(BaseModel):
    """Sauvegardes environnementales et sociales — Expert CI"""
    norme = models.OneToOneField(Norme, on_delete=models.CASCADE, related_name='ecological_review')
    expert = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_as_environmental_expert')

    STATUS_CHOICES = _REVIEW_STATUS
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    impact_matrix = models.JSONField(
        default=dict,
        blank=True,
        help_text="Matrice JSON: {displacement, subsistence, heritage, environmental, sensitive_zones} → niveau"
    )
    comments = models.TextField(blank=True)
    review_start_date = models.DateField(null=True, blank=True)
    review_end_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Examen Sauvegardes Écologiques"
        verbose_name_plural = "Examens Sauvegardes Écologiques"
        ordering = ['status', '-created_at']

    def __str__(self):
        return f"Écologie {self.norme.reference_number} - {self.status}"


class EconomicReview(BaseModel):
    """Évaluation financière du cycle de vie — Économiste FONER"""
    norme = models.OneToOneField(Norme, on_delete=models.CASCADE, related_name='economic_review')
    expert = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_as_economist')

    STATUS_CHOICES = _REVIEW_STATUS
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    construction_cost_usd_per_km = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    annual_maintenance_cost_usd = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    lifecycle_years = models.PositiveIntegerField(null=True, blank=True)
    discount_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    lifecycle_cost_usd = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, help_text="Coût total cycle de vie calculé")
    comments = models.TextField(blank=True)
    review_start_date = models.DateField(null=True, blank=True)
    review_end_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Évaluation Économique"
        verbose_name_plural = "Évaluations Économiques"
        ordering = ['status', '-created_at']

    def __str__(self):
        return f"Économie {self.norme.reference_number} - {self.status}"


class ScheduleReview(BaseModel):
    """Validation chronogramme + état de l'art scientifique — Planificateur & Conseiller Scientifique"""
    norme = models.OneToOneField(Norme, on_delete=models.CASCADE, related_name='schedule_review')
    planner = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_as_planner')
    scientist = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_as_scientist')

    PLANNER_STATUS_CHOICES = _REVIEW_STATUS
    SCIENTIST_STATUS_CHOICES = _REVIEW_STATUS
    planner_status = models.CharField(max_length=20, choices=PLANNER_STATUS_CHOICES, default='PENDING')
    scientist_status = models.CharField(max_length=20, choices=SCIENTIST_STATUS_CHOICES, default='PENDING')

    planner_notes = models.TextField(blank=True, help_text="Observations chronogramme et délais (J0→J+90)")
    scientist_notes = models.TextField(blank=True, help_text="Validation état de l'art scientifique et mathématique")
    review_start_date = models.DateField(null=True, blank=True)
    review_end_date = models.DateField(null=True, blank=True)

    @property
    def is_completed(self):
        return self.planner_status == 'APPROVED' and self.scientist_status == 'APPROVED'

    class Meta:
        verbose_name = "Validation Chronogramme & Scientifique"
        verbose_name_plural = "Validations Chronogramme & Scientifique"
        ordering = ['-created_at']

    def __str__(self):
        return f"Chronogramme {self.norme.reference_number} — Plan:{self.planner_status} / Sci:{self.scientist_status}"


class IndustrialConsultation(BaseModel):
    """Faisabilité marché — Expert Liaison Industrielle FEC"""
    norme = models.OneToOneField(Norme, on_delete=models.CASCADE, related_name='industrial_consultation')
    expert = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='industrial_consultations')

    STATUS_CHOICES = _REVIEW_STATUS
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    fec_feedback = models.TextField(blank=True, help_text="Retours agrégés des entreprises BTP membres FEC")
    companies_consulted = models.JSONField(default=list, blank=True, help_text="Liste des entreprises consultées")
    market_feasible = models.BooleanField(null=True, blank=True, help_text="Norme applicable par le patronat privé")
    review_start_date = models.DateField(null=True, blank=True)
    review_end_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Consultation Industrielle FEC"
        verbose_name_plural = "Consultations Industrielles FEC"
        ordering = ['status', '-created_at']

    def __str__(self):
        return f"FEC {self.norme.reference_number} - {self.status}"
