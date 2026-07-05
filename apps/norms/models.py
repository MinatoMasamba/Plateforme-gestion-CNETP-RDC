from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel, User
from apps.governance.models import CTM, WG
from apps.experts.models import Expert


class Norme(BaseModel):
    """Un projet de norme"""
    title = models.CharField(max_length=500)
    reference_number = models.CharField(max_length=50, unique=True, help_text="Ex: CNETP-001-2024")
    
    description = models.TextField()
    ctm = models.ForeignKey(CTM, on_delete=models.PROTECT, related_name='normes')
    wg = models.ForeignKey(WG, on_delete=models.PROTECT, related_name='normes')
    
    # References
    iso_reference = models.CharField(max_length=50, blank=True, help_text="Ex: ISO 12345")
    arso_reference = models.CharField(max_length=50, blank=True)

    # Catégorisation (Plan de Production CNE-ITP/CTC/PPT-2026)
    NORM_TYPE_CHOICES = [
        ('NCD', 'Norme Nationale Congolaise'),
        ('CA', 'Code Applicatif'),
        ('DIR', 'Directive Technique'),
        ('REC', 'Recommandation Technique'),
    ]
    norm_type = models.CharField(max_length=3, choices=NORM_TYPE_CHOICES, default='NCD')
    target_count = models.PositiveIntegerField(
        default=1,
        help_text="Nombre de normes individuelles couvertes par cette ligne de planification"
    )

    # Status du cycle de vie
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('INTERNAL_REVIEW', 'En révision interne'),
        ('CTM_REVIEW', 'Soumis au CTM'),
        ('LEGISTIC_REVIEW', 'Toilettage légistique'),
        ('PUBLIC_INQUIRY', 'En enquête publique'),
        ('PILOTAGE_REVIEW', 'Validation Comité Pilotage'),
        ('FINAL_REVIEW', 'En révision finale'),
        ('ADOPTED', 'Adopté'),
        ('HOMOLOGATED', 'Homologué'),
        ('PUBLISHED', 'Publié au JO'),
        ('ARCHIVED', 'Archivé'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Workflow dates
    start_date = models.DateField(auto_now_add=True)
    ctm_submission_date = models.DateField(null=True, blank=True)
    legistic_review_date = models.DateField(null=True, blank=True)
    public_inquiry_start = models.DateField(null=True, blank=True)
    public_inquiry_end = models.DateField(null=True, blank=True)
    pilotage_validation_date = models.DateField(null=True, blank=True)
    adoption_date = models.DateField(null=True, blank=True)
    homologation_date = models.DateField(null=True, blank=True)
    
    # Publication Journal Officiel
    publication_date = models.DateField(null=True, blank=True)
    jo_reference = models.CharField(max_length=100, blank=True, help_text="Référence au Journal Officiel")
    jo_file = models.FileField(upload_to='norms/jo/', null=True, blank=True, help_text="Scan de la publication au JO")
    
    # Attachments
    current_version = models.FileField(
        upload_to='norms/versions/',
        null=True,
        blank=True,
        help_text="Dernière version du document"
    )
    
    # Metadata
    tags = models.CharField(max_length=500, blank=True, help_text="Mots-clés séparés par virgule")
    is_public = models.BooleanField(default=False, help_text="Accessible au public?")
    
    # Collaborative Editing
    locked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='locked_norms'
    )
    lock_timeout = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Norme"
        verbose_name_plural = "Normes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'ctm']),
            models.Index(fields=['publication_date']),
        ]
    
    def __str__(self):
        return f"{self.reference_number} - {self.title[:50]}"
    
    def get_latest_version(self):
        return self.versions.order_by('-version_number').first()


class NormeVersion(BaseModel):
    """Version d'une norme (historique complet)"""
    norme = models.ForeignKey(Norme, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    
    title = models.CharField(max_length=500)
    content = models.TextField()  # Stockage du texte intégral
    document = models.FileField(upload_to='norms/versions/', null=True, blank=True)
    
    # Metadata
    summary = models.TextField(blank=True, help_text="Résumé des changements")
    is_draft = models.BooleanField(default=True)
    
    # Tracking
    version_author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Version de Norme"
        verbose_name_plural = "Versions de Normes"
        unique_together = ('norme', 'version_number')
        ordering = ['norme', '-version_number']
    
    def __str__(self):
        return f"{self.norme.reference_number} v{self.version_number}"


class NormeComment(BaseModel):
    """Commentaire interne porté sur une norme en cours."""

    norme = models.ForeignKey(Norme, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='norme_comments')
    body = models.TextField(verbose_name="Commentaire")

    class Meta:
        verbose_name = "Commentaire de Norme"
        verbose_name_plural = "Commentaires de Norme"
        ordering = ['-created_at']

    def __str__(self):
        author = self.author.full_name if self.author else "Anonyme"
        return f"{author} — {self.norme.reference_number}"


class ChangementVersion(BaseModel):
    """Suivi détaillé des modifications par section/paragraphe"""
    version = models.ForeignKey(NormeVersion, on_delete=models.CASCADE, related_name='changes')
    previous_version = models.ForeignKey(
        NormeVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='changes_from'
    )
    
    section = models.CharField(max_length=100, help_text="Ex: '2.1.3' ou 'Introduction'")
    old_text = models.TextField(blank=True, help_text="Texte précédent")
    new_text = models.TextField(help_text="Nouveau texte")
    
    change_type = models.CharField(
        max_length=20,
        choices=[
            ('ADD', 'Ajout'),
            ('REMOVE', 'Suppression'),
            ('MODIFY', 'Modification'),
        ]
    )
    change_reason = models.TextField(blank=True, help_text="Justification du changement")
    
    class Meta:
        verbose_name = "Changement Version"
        verbose_name_plural = "Changements Versions"
        ordering = ['version', 'section']
    
    def __str__(self):
        return f"{self.version} - Section {self.section} ({self.change_type})"


class NormeVote(BaseModel):
    """Vote d'un expert sur la norme ouverte en édition."""

    VOTE_CHOICES = [
        ('FOR', 'Pour'),
        ('AGAINST', 'Contre'),
        ('ABSTAIN', 'Abstention'),
    ]

    norme = models.ForeignKey(Norme, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(Expert, on_delete=models.PROTECT, related_name='norme_votes')
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    justification = models.TextField(blank=True)
    vote_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vote Norme"
        verbose_name_plural = "Votes Normes"
        unique_together = ('norme', 'voter')
        ordering = ['-vote_date']
        indexes = [
            models.Index(fields=['norme', 'vote'], name='norms_norme_vote_idx'),
        ]

    def __str__(self):
        return f"{self.voter.user.get_full_name()} - {self.norme.reference_number} ({self.vote})"
