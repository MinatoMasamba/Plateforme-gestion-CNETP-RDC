from django.db import models
from django.contrib.postgres.fields import ArrayField
from apps.core.models import BaseModel
from apps.experts.models import Expert


class Reunion(BaseModel):
    """Modèle pour les réunions"""
    
    TYPE_CHOICES = [
        ('CTM', 'Comité Technique Miroir'),
        ('WG', 'Groupe de Travail'),
        ('PILOTAGE', 'Comité de Pilotage'),
        ('ASSEMBLEE', 'Assemblée Plénière'),
        ('CTC', 'Cellule Technique de Coordination'),
    ]
    
    STATUS_CHOICES = [
        ('PLANNED', 'Planifiée'),
        ('IN_PROGRESS', 'En cours'),
        ('COMPLETED', 'Complétée'),
        ('CANCELLED', 'Annulée'),
    ]
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date = models.DateTimeField()
    lieu = models.CharField(max_length=255, blank=True, null=True)
    lien_reunion_virtuelle = models.URLField(blank=True, null=True)
    ordre_jour = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    organisateur = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, related_name='reunions_organisees')
    
    class Meta:
        db_table = 'meetings_reunion'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['type', 'date']),
            models.Index(fields=['status', 'date']),
        ]
    
    def __str__(self):
        return f"{self.titre} ({self.date.strftime('%Y-%m-%d')})"


class Presence(BaseModel):
    """Modèle pour les présences aux réunions"""
    
    STATUS_CHOICES = [
        ('PRESENT', 'Présent'),
        ('ABSENT', 'Absent'),
        ('EXCUSED', 'Excusé'),
    ]
    
    reunion = models.ForeignKey(Reunion, on_delete=models.CASCADE, related_name='presences')
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='presences')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    marked_at = models.DateTimeField(auto_now_add=True)
    marked_by = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='presences_marked')
    
    class Meta:
        db_table = 'meetings_presence'
        unique_together = ('reunion', 'expert')
        indexes = [
            models.Index(fields=['reunion', 'status']),
        ]
    
    def __str__(self):
        return f"{self.expert.user.get_full_name()} - {self.reunion.titre}"


class ProcessusVerbaux(BaseModel):
    """Modèle pour les procès-verbaux"""
    
    reunion = models.OneToOneField(Reunion, on_delete=models.CASCADE, related_name='pv')
    titre = models.CharField(max_length=255)
    contenu = models.TextField()
    nombre_presents = models.IntegerField(default=0)
    nombre_absents = models.IntegerField(default=0)
    quorum_atteint = models.BooleanField(default=False)
    generated_at = models.DateTimeField(auto_now_add=True)
    signed_by = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='pv_signed')
    signature_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'meetings_processusvverbaux'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"PV - {self.reunion.titre}"
