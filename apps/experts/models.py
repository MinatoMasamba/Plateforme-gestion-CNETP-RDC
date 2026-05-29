from django.db import models
from apps.core.models import BaseModel, User


class Structure(BaseModel):
    """Les 16 structures d'origine des experts"""
    name = models.CharField(max_length=200, unique=True)
    acronym = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('ADMIN', 'Administration publique'),
            ('PUBLIC', 'Établissements publics'),
            ('PROF', 'Ordres professionnels'),
            ('ACAD', 'Académiques & Recherche'),
            ('METRO', 'Métrologie & Société civile'),
            ('PRIVATE', 'Secteur privé'),
        ]
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    contact_person = models.CharField(max_length=200, blank=True)
    
    class Meta:
        verbose_name = "Structure"
        verbose_name_plural = "Structures"
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.acronym})"
    
    def get_expert_count(self):
        return self.experts.count()


class Expert(BaseModel):
    """Un expert CNETP"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='expert_profile')
    structure = models.ForeignKey(Structure, on_delete=models.PROTECT, related_name='experts')
    
    # Informations de nomination
    appointment_decree_number = models.CharField(max_length=100, blank=True, help_text="N° Arrêté ministériel")
    appointment_date = models.DateField(null=True, blank=True)
    
    # Compétences
    specialties = models.CharField(
        max_length=500,
        blank=True,
        help_text="Domaines de compétence (géotechnique, structures, etc.)"
    )
    cv = models.FileField(upload_to='experts/cv/', blank=True, null=True)
    
    # Sélection des CTM (Sous-Commissions Techniques)
    ctm_choices = models.ManyToManyField(
        'governance.CTM',
        related_name='member_experts',
        blank=True,
        help_text="Sous-commissions sélectionnées par l'expert"
    )
    
    # Statuts
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('ACTIVE', 'Actif'),
        ('INACTIVE', 'Inactif'),
        ('SUSPENDED', 'Suspendu'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Informations bancaires (pour jetons)
    bank_account = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=200, blank=True)
    mobile_money_number = models.CharField(max_length=20, blank=True, help_text="Pour paiements via Mobile Money")

    # Champs financiers et d'activité
    daily_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Taux journalier pour les jetons de présence (en USD)"
    )
    monthly_research_allowance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Indemnité mensuelle de recherche (en USD)"
    )
    presence_count = models.PositiveIntegerField(
        default=0,
        help_text="Nombre de présences cumulées aux sessions"
    )
    
    # Tracking
    inscription_date = models.DateTimeField(auto_now_add=True)
    activation_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Expert"
        verbose_name_plural = "Experts"
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} ({self.structure.acronym})"
    
    @property
    def full_name(self):
        return self.user.get_full_name()
