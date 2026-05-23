from django.contrib.auth import get_user_model
from django.db import models
from apps.core.models import BaseModel
from apps.experts.models import Expert

User = get_user_model()

class DocumentFile(BaseModel):
    """Modèle générique pour le dépôt de fichiers par les experts"""
    
    # Uploader (expert ou utilisateur)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_documents'
    )
    expert = models.ForeignKey(
        Expert, 
        on_delete=models.CASCADE, 
        related_name='expert_documents',
        null=True,
        blank=True
    )
    
    # Fichier
    file = models.FileField(upload_to='documents/%Y/%m/')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Type et catégorie
    FILE_TYPE_CHOICES = [
        ('PDF', 'PDF'),
        ('IMAGE', 'Image'),
        ('DOC', 'Document Word'),
        ('SHEET', 'Feuille de calcul'),
        ('VIDEO', 'Vidéo'),
        ('ARCHIVE', 'Archive (ZIP)'),
        ('OTHER', 'Autre'),
    ]
    file_type = models.CharField(
        max_length=50, 
        choices=FILE_TYPE_CHOICES,
        default='OTHER'
    )
    
    category = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="Ex: Justificatif, Rapport, Annexe, Evidence"
    )
    
    # Relations optionnelles (pour contexte)
    norme = models.ForeignKey(
        'norms.Norme',
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True
    )
    
    reunion = models.ForeignKey(
        'meetings.Reunion',
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True
    )
    
    # Métadonnées
    is_public = models.BooleanField(
        default=False,
        help_text="Document visible publiquement"
    )
    file_size = models.BigIntegerField(default=0, help_text="Taille en bytes")
    mime_type = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uploaded_by', '-created_at']),
            models.Index(fields=['norme', '-created_at']),
            models.Index(fields=['reunion', '-created_at']),
            models.Index(fields=['is_public']),
        ]

    def __str__(self):
        context = "Général"
        if self.norme:
            context = f"Norme {self.norme.reference_number}"
        elif self.reunion:
            context = f"Réunion {self.reunion.id}"
        
        return f"{self.title} ({context})"
    
    def get_file_size_display(self):
        """Retourner la taille du fichier en format lisible"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
