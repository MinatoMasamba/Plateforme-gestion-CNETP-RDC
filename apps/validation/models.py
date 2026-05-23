from django.db import models
from apps.core.models import BaseModel, User
from apps.norms.models import Norme
from apps.experts.models import Expert # Assuming Expert model is in experts app


class LegisticReview(BaseModel):
    """Suivi du toilettage légistique d'une norme"""
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

