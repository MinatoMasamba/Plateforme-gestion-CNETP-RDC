from django.db import models
from django.utils import timezone
from decimal import Decimal
from apps.core.models import BaseModel
from apps.experts.models import Expert, Structure
from apps.meetings.models import Reunion


class Cotisation(BaseModel):
    """Modèle pour les cotisations des structures"""
    
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('PARTIAL', 'Partiellement payée'),
        ('PAID', 'Payée'),
        ('OVERDUE', 'En retard'),
    ]
    
    structure = models.ForeignKey(Structure, on_delete=models.CASCADE, related_name='cotisations')
    annee = models.IntegerField()
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    due_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'payments_cotisation'
        unique_together = ('structure', 'annee')
        ordering = ['-annee', 'due_date']
        indexes = [
            models.Index(fields=['structure', 'annee']),
            models.Index(fields=['status', 'due_date']),
        ]
    
    def __str__(self):
        return f"Cotisation {self.structure.name} - {self.annee}"
    
    @property
    def montant_paye(self):
        """Calculer le montant total payé"""
        return self.paiements.filter(status='CONFIRMED').aggregate(
            total=models.Sum('montant')
        )['total'] or Decimal('0')
    
    @property
    def reste_payer(self):
        """Calculer le reste à payer"""
        return max(Decimal('0'), self.montant - self.montant_paye)


class Paiement(BaseModel):
    """Modèle pour les paiements des cotisations"""
    
    METHODE_CHOICES = [
        ('VIREMENT', 'Virement bancaire'),
        ('CHEQUE', 'Chèque'),
        ('ESPECES', 'Espèces'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('AUTRE', 'Autre'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'En attente de confirmation'),
        ('CONFIRMED', 'Confirmé'),
        ('REJECTED', 'Rejeté'),
        ('CANCELLED', 'Annulé'),
    ]
    
    cotisation = models.ForeignKey(Cotisation, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    methode_paiement = models.CharField(max_length=20, choices=METHODE_CHOICES)
    numero_recu = models.CharField(max_length=50, unique=True, blank=True, null=True)
    numero_transaction = models.CharField(max_length=100, blank=True, null=True)
    proof_file = models.FileField(upload_to='payment_proofs/', blank=True, null=True)
    payment_date = models.DateField()
    confirmed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'payments_paiement'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['cotisation', 'status']),
            models.Index(fields=['payment_date', 'status']),
        ]
    
    def __str__(self):
        return f"Paiement {self.montant} - {self.cotisation.structure.name}"
    
    def save(self, *args, **kwargs):
        # Générer le numéro de reçu si absent
        if not self.numero_recu:
            last_paiement = Paiement.objects.latest('id')
            next_id = (last_paiement.id if last_paiement else 0) + 1
            self.numero_recu = f"REC-{timezone.now().strftime('%Y%m%d')}-{next_id:05d}"
        super().save(*args, **kwargs)


class JetonPresence(BaseModel):
    """Modèle pour les jetons de présence des experts"""
    
    STATUS_CHOICES = [
        ('PENDING', 'En attente de paiement'),
        ('PAID', 'Payé'),
    ]
    
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='jetons')
    reunion = models.ForeignKey(Reunion, on_delete=models.CASCADE, related_name='jetons_presence')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'payments_jetonpresence'
        unique_together = ('expert', 'reunion')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['expert', 'status']),
            models.Index(fields=['reunion', 'status']),
        ]
    
    def __str__(self):
        return f"Jeton {self.expert.user.get_full_name()} - {self.reunion.titre}"
