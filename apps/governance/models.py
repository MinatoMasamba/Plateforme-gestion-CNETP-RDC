from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel
from apps.experts.models import Expert


class CTM(BaseModel):
    """Comité Technique Miroir (8 CTM au total)"""
    name = models.CharField(max_length=200, unique=True)
    number = models.PositiveIntegerField(unique=True, validators=[MinValueValidator(1), MaxValueValidator(8)])
    description = models.TextField()
    iso_reference = models.CharField(max_length=50, blank=True, help_text="Ex: ISO/TC 58")
    arso_reference = models.CharField(max_length=50, blank=True)
    
    # Leadership
    scientific_president = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ctm_president_of'
    )
    rapporteur = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ctm_rapporteur_of'
    )
    secretary = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ctm_secretary_of'
    )
    
    class Meta:
        verbose_name = "Comité Technique Miroir"
        verbose_name_plural = "Comités Techniques Miroirs"
        ordering = ['number']
    
    def __str__(self):
        return f"CTM {self.number} - {self.name}"
    
    def get_member_count(self):
        return self.affectations.filter(affectation__is_primary=True).distinct('affectation__expert').count()


class WG(BaseModel):
    """Groupe de Travail (4-5 experts par WG)"""
    ctm = models.ForeignKey(CTM, on_delete=models.CASCADE, related_name='working_groups')
    name = models.CharField(max_length=200)
    number = models.PositiveIntegerField()  # Ex: WG 2.1, 2.2...
    description = models.TextField(blank=True)
    
    # Leadership
    president = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wg_president_of'
    )
    rapporteur = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wg_rapporteur_of'
    )
    secretary = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wg_secretary_of'
    )
    
    class Meta:
        verbose_name = "Groupe de Travail"
        verbose_name_plural = "Groupes de Travail"
        unique_together = ('ctm', 'number')
        ordering = ['ctm', 'number']
    
    def __str__(self):
        return f"WG {self.ctm.number}.{self.number} - {self.name}"


class Affectation(BaseModel):
    """Affectation expert à CTM/WG - Complète le modèle dans experts"""
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='governance_affectations')
    ctm = models.ForeignKey(CTM, on_delete=models.CASCADE, related_name='affectations')
    wg = models.ForeignKey(WG, on_delete=models.CASCADE, related_name='affectations')
    
    is_primary_ctm = models.BooleanField(default=True)
    is_primary_wg = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Affectation Gouvernance"
        verbose_name_plural = "Affectations Gouvernance"
        unique_together = ('expert', 'ctm', 'wg')
        ordering = ['ctm', 'wg', 'expert']
    
    def __str__(self):
        return f"{self.expert.full_name} → {self.ctm} / {self.wg}"


class ComitePilotage(BaseModel):
    """Comité de Pilotage Stratégique (24 membres)"""
    name = models.CharField(max_length=200, default="Comité de Pilotage Stratégique CNETP")
    
    president = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pilotage_president'
    )
    vice_president = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pilotage_vice_president'
    )
    secretary = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pilotage_secretary'
    )
    rapporteur = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pilotage_rapporteur'
    )
    
    members = models.ManyToManyField(
        Expert,
        related_name='pilotage_member_of',
        through='PilotageMembreship'
    )
    
    class Meta:
        verbose_name = "Comité de Pilotage"
        verbose_name_plural = "Comités de Pilotage"
    
    def __str__(self):
        return self.name


class PilotageMembreship(BaseModel):
    """Adhésion au Comité de Pilotage"""
    comite = models.ForeignKey(ComitePilotage, on_delete=models.CASCADE)
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=50,
        choices=[
            # Bureau Directoire
            ('PRESIDENT', 'Président (Bureau)'),
            ('VICE_PRESIDENT', 'Vice-Président (Bureau)'),
            ('SECRETARY', 'Secrétaire (Bureau)'),
            ('RAPPORTEUR', 'Rapporteur Général (Bureau)'),
            
            # Collèges
            ('CONSEILLER_POLITIQUE', 'Conseiller Institutionnel et Politique'),
            ('ADMIN_TECH_FIN', 'Administrateur Technique et Financier'),
            ('PARTENAIRE_SOC_CIV', 'Partenaire Sectoriel et Société Civile'),
            
            # Default/Generic
            ('CONSEILLER', 'Conseiller'),
        ],
        default='CONSEILLER'
    )
    
    class Meta:
        verbose_name = "Membership Pilotage"
        unique_together = ('comite', 'expert')
    
    def __str__(self):
        return f"{self.expert.full_name} - {self.role}"


class OriginStructure(BaseModel):
    """Structure d'origine - Giron (16 structures, 200 experts)"""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    expected_expert_count = models.PositiveIntegerField(default=0, help_text="Nombre attendu d'experts")
    
    GIRON_CHOICES = [
        ('ADMIN', 'Administration publique'),
        ('OFFICES', 'Établissements publics & Offices'),
        ('ORDERS', 'Ordres professionnels'),
        ('ACADEMIA', 'Académiques & Recherche'),
        ('METROLOGY', 'Métrologie & Société civile'),
        ('PRIVATE', 'Secteur privé'),
    ]
    giron = models.CharField(max_length=50, choices=GIRON_CHOICES)
    
    class Meta:
        verbose_name = "Structure d'Origine"
        verbose_name_plural = "Structures d'Origine"
        ordering = ['giron', 'name']
    
    def __str__(self):
        return self.name
    
    def get_expert_count(self):
        return self.experts.count()


class TechnicalCell(BaseModel):
    """Cellule Technique de Coordination (CTC) - 20 experts"""
    name = models.CharField(max_length=200, default="Cellule Technique de Coordination")
    
    coordinator = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ctc_coordinator'
    )
    vice_coordinator = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ctc_vice_coordinator'
    )
    
    members = models.ManyToManyField(
        Expert,
        related_name='ctc_member_of',
        through='CTCMembership'
    )
    
    class Meta:
        verbose_name = "Cellule Technique"
        verbose_name_plural = "Cellules Techniques"
    
    def __str__(self):
        return self.name


class CTCMembership(BaseModel):
    """Adhésion à la CTC"""
    ctc = models.ForeignKey(TechnicalCell, on_delete=models.CASCADE)
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=50,
        choices=[
            ('COORDINATOR', 'Coordonnateur'),
            ('VICE_COORDINATOR', 'Vice-Coordonnateur'),
            ('ISO_EXPERT', 'Expert Veille ISO'),
            ('LEGAL', 'Légiste'),
            ('ENVIRONMENTAL', 'Environnementaliste'),
            ('PLANNER', 'Planificateur'),
            ('ECONOMIST', 'Économiste'),
            ('SCIENTIFIC', 'Conseiller Scientifique'),
            ('ACCOUNTANT', 'Comptable'),
            ('ENQUIRY_MANAGER', 'Responsable Enquêtes'),
            ('INDUSTRIAL', 'Liaison Industrielle'),
            ('COMMUNICATOR', 'Communicateur'),
            ('EXECUTIVE', 'Assistant Exécutif'),
            ('CARTOGRAPHER', 'Cartographe SIG'),
            ('DATA_ENTRY', 'Opérateur de Saisie'),
            ('IT_ADMIN', 'Administrateur IT'),
        ],
        default='COORDINATOR'
    )
    
    class Meta:
        verbose_name = "Membership CTC"
        unique_together = ('ctc', 'expert')
    
    def __str__(self):
        return f"{self.expert.full_name} - {self.role}"


class ExecutiveLevel(BaseModel):
    """Niveau Exécutif - Haute tutelle (3 postes)"""
    position = models.CharField(
        max_length=100,
        choices=[
            ('MINISTER', 'Ministre des ITP'),
            ('SG_ITP', 'Secrétaire Général aux ITP'),
            ('CABINET', 'Directeur de Cabinet'),
        ],
        unique=True
    )
    expert = models.OneToOneField(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executive_position'
    )
    
    class Meta:
        verbose_name = "Niveau Exécutif"
        verbose_name_plural = "Niveaux Exécutifs"
    
    def __str__(self):
        name = self.expert.full_name if self.expert else "Vacant"
        return f"{self.get_position_display()} - {name}"
