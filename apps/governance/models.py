from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel
from apps.experts.models import Expert
from django.utils import timezone


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
    wg = models.ForeignKey(WG, on_delete=models.CASCADE, related_name='affectations', null=True, blank=True)
    
    is_primary_ctm = models.BooleanField(default=True)
    is_primary_wg = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Affectation Gouvernance"
        verbose_name_plural = "Affectations Gouvernance"
        unique_together = ('expert', 'ctm', 'wg')
        ordering = ['ctm', 'wg', 'expert']
    
    def __str__(self):
        return f"{self.expert.full_name} → {self.ctm} / {self.wg}"

    @property
    def ctm_role(self):
        """Role de l'expert dans le CTM affecte."""
        roles = (
            ('scientific_president_id', 'Président scientifique CTM'),
            ('rapporteur_id', 'Rapporteur CTM'),
            ('secretary_id', 'Secrétaire CTM'),
        )
        for field_name, label in roles:
            if getattr(self.ctm, field_name, None) == self.expert_id:
                return label
        return 'Membre CTM' if self.is_primary_ctm else ''

    @property
    def wg_role(self):
        """Role de l'expert dans le WG affecte."""
        roles = (
            ('president_id', 'Président WG'),
            ('rapporteur_id', 'Rapporteur WG'),
            ('secretary_id', 'Secrétaire WG'),
        )
        for field_name, label in roles:
            if getattr(self.wg, field_name, None) == self.expert_id:
                return label
        return 'Membre WG' if self.is_primary_wg else ''

    @property
    def role(self):
        roles = [role for role in (self.ctm_role, self.wg_role) if role]
        return ' / '.join(roles) if roles else 'Membre'


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


class PosteNominatif(BaseModel):
    """
    Poste nominatif d'un organe de direction tel que défini NOMMÉMENT dans le
    Manuel Organisationnel CNETP 2026 (validé le 22/05/2026) : chaque poste y
    est rattaché à une structure d'origine précise — référence "Quota Ligne X"
    du Tableau 1 (ex: "Vice-Président — ONIC, Ligne 15").

    Sert de grille de lecture / référentiel de nomination, distincte de
    l'affectation réelle (`holder`) : un poste reste vacant (`holder=None`)
    tant que l'expert visé n'a pas encore été inscrit puis nommé.
    """
    ROLE_CHOICES = [
        ('PRESIDENT', 'Président (Bureau)'),
        ('VICE_PRESIDENT', 'Vice-Président (Bureau)'),
        ('SECRETARY', 'Secrétaire (Bureau)'),
        ('RAPPORTEUR', 'Rapporteur Général (Bureau)'),
        ('CONSEILLER_POLITIQUE', 'Conseiller Institutionnel et Politique'),
        ('ADMIN_TECH_FIN', 'Administrateur Technique et Financier'),
        ('PARTENAIRE_SOC_CIV', 'Partenaire Sectoriel et Société Civile'),
    ]

    comite = models.ForeignKey(
        ComitePilotage,
        on_delete=models.CASCADE,
        related_name='postes_nominatifs'
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    title = models.CharField(
        max_length=300,
        help_text="Intitulé nominatif exact du poste, tel que rédigé dans le manuel organisationnel"
    )
    required_structure = models.ForeignKey(
        'experts.Structure',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='postes_nominatifs',
        help_text="Structure d'origine exigée pour ce poste (ex: Cabinet du Ministre = Quota Ligne 2)"
    )
    quota_line = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Référence « Ligne X » du Tableau 1 du manuel organisationnel"
    )
    order = models.PositiveSmallIntegerField(default=0)
    holder = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='postes_nominatifs_occupes',
        help_text="Expert nommé à ce poste — laisser vide tant que le poste est vacant"
    )

    class Meta:
        verbose_name = "Poste Nominatif (Pilotage)"
        verbose_name_plural = "Postes Nominatifs (Pilotage)"
        ordering = ['comite', 'order']
        unique_together = ('comite', 'title')

    def __str__(self):
        occupant = self.holder.full_name if self.holder else "vacant"
        return f"{self.title} ({occupant})"

    @property
    def is_vacant(self):
        return self.holder_id is None


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


class PosteNominatifCTC(BaseModel):
    """
    Poste nominatif de la Cellule Technique de Coordination tel que défini
    NOMMÉMENT dans le Manuel Organisationnel CNETP 2026 (section 3.2) :
    chaque poste y est rattaché à une structure d'origine précise — référence
    "Quota Ligne X" du Tableau 1 (ex: "Coordonnateur Adjoint — Cabinet, Ligne 2").

    Pendant exact, pour la Cellule Technique, de PosteNominatif (Comité de
    Pilotage) : grille de lecture / référentiel de nomination, distincte de
    l'affectation réelle (`holder`), qui reste vide tant que le poste est vacant.
    """
    ROLE_CHOICES = [
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
    ]

    ctc = models.ForeignKey(
        TechnicalCell,
        on_delete=models.CASCADE,
        related_name='postes_nominatifs'
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    title = models.CharField(
        max_length=300,
        help_text="Intitulé nominatif exact du poste, tel que rédigé dans le manuel organisationnel"
    )
    required_structure = models.ForeignKey(
        'experts.Structure',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='postes_nominatifs_ctc',
        help_text="Structure d'origine exigée pour ce poste (ex: Cabinet du Ministre = Quota Ligne 2)"
    )
    quota_line = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Référence « Ligne X » du Tableau 1 du manuel organisationnel"
    )
    order = models.PositiveSmallIntegerField(default=0)
    holder = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='postes_nominatifs_ctc_occupes',
        help_text="Expert nommé à ce poste — laisser vide tant que le poste est vacant"
    )

    class Meta:
        verbose_name = "Poste Nominatif (Cellule Technique)"
        verbose_name_plural = "Postes Nominatifs (Cellule Technique)"
        ordering = ['ctc', 'order']
        unique_together = ('ctc', 'title')

    def __str__(self):
        occupant = self.holder.full_name if self.holder else "vacant"
        return f"{self.title} ({occupant})"

    @property
    def is_vacant(self):
        return self.holder_id is None


class CTCOperationalRequest(BaseModel):
    """
    Demande d'ouverture de droits temporaires ou de transmission urgente
    émise par un membre de la CTC lorsqu'il tente d'accéder à une ressource
    hors de son pôle. Routée vers l'Assistant Exécutif de la Direction des Opérations.
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvée'),
        ('REJECTED', 'Refusée'),
    ]

    requester = models.ForeignKey(
        Expert, on_delete=models.CASCADE, related_name='ctc_requests',
        verbose_name="Demandeur"
    )
    restricted_resource = models.CharField(
        max_length=300,
        help_text="Module ou ressource CTC dont l'accès temporaire est demandé"
    )
    reason = models.TextField(
        verbose_name="Demande d'ouverture de droits temporaires ou de transmission urgente de données"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    reviewed_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ctc_reviews', verbose_name="Examiné par (Assistant Exécutif)"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True)

    class Meta:
        verbose_name = "Demande Opérationnelle CTC"
        verbose_name_plural = "Demandes Opérationnelles CTC"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requester.full_name} → {self.restricted_resource} ({self.status})"

    @property
    def is_pending(self):
        return self.status == 'PENDING'


class PermissionRequest(BaseModel):
    """
    Demande de dérogation d'accès émise par un membre du Comité de Pilotage
    lorsqu'il tente d'accéder à une ressource hors de ses privilèges habituels.
    Routée automatiquement vers le Bureau Directoire (Secrétaire + Président).
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvée'),
        ('REJECTED', 'Refusée'),
    ]

    requester = models.ForeignKey(
        Expert, on_delete=models.CASCADE, related_name='permission_requests',
        verbose_name="Demandeur"
    )
    restricted_resource = models.CharField(
        max_length=300,
        help_text="Ressource ou module dont l'accès est demandé (ex: CTM 1 – Géotechnique)"
    )
    reason = models.TextField(verbose_name="Motif de la demande de consultation ou de dérogation")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    reviewed_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='permission_reviews', verbose_name="Examiné par"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True, verbose_name="Commentaire du Bureau Directoire")

    class Meta:
        verbose_name = "Demande de Permission"
        verbose_name_plural = "Demandes de Permission"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requester.full_name} → {self.restricted_resource} ({self.status})"

    @property
    def is_pending(self):
        return self.status == 'PENDING'


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


class Tache(BaseModel):
    """Tâche de production suivie par la coordination technique."""
    working_group = models.ForeignKey(
        WG,
        on_delete=models.PROTECT,
        related_name='tasks',
        null=True,
        blank=True,
        verbose_name="Groupe historique",
    )
    target_group = models.ForeignKey(
        'governance.GroupeCible',
        on_delete=models.PROTECT,
        related_name='tasks',
        null=True,
        blank=True,
        verbose_name="Groupe de travail",
    )
    norme = models.ForeignKey(
        'norms.Norme',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    titre = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('PLANNED', 'Planifiée'),
            ('IN_PROGRESS', 'En cours'),
            ('COMPLETED', 'Complétée'),
            ('BLOCKED', 'Bloquée'),
            ('ON_HOLD', 'En attente'),
        ],
        default='PLANNED'
    )
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    assigned_to = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    backup_assignee = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='backup_tasks',
        verbose_name="Remplaçant",
    )
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(
        max_length=12,
        choices=[
            ('LOW', 'Basse'),
            ('NORMAL', 'Normale'),
            ('HIGH', 'Haute'),
            ('CRITICAL', 'Critique'),
        ],
        default='NORMAL',
    )
    weight = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Poids",
    )
    weight_source = models.CharField(
        max_length=12,
        choices=[('DEFAULT', 'Valeur par défaut'), ('MANUAL', 'Valeur configurée')],
        default='DEFAULT',
    )
    expected_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="Effort attendu (minutes)")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deliverable_reference = models.CharField(max_length=500, blank=True, verbose_name="Preuve documentaire")
    review_status = models.CharField(
        max_length=20,
        choices=[
            ('NOT_REVIEWED', 'Non évalué'),
            ('ACCEPTED', 'Accepté'),
            ('RETURNED', 'Retourné'),
        ],
        default='NOT_REVIEWED',
    )
    reviewed_by = models.ForeignKey(
        Expert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_tasks',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    blocked_by = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='unblocks',
        verbose_name="Bloquée par",
    )
    
    class Meta:
        verbose_name = "Tâche de groupe"
        verbose_name_plural = "Tâches de groupe"
        ordering = ['-created_at']
        permissions = [
            ('manage_task_planning', 'Gérer les objectifs et pondérations'),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.working_group_id and not self.target_group_id:
            raise ValidationError('La tâche doit être rattachée à un groupe de travail.')
        if self.working_group_id and self.target_group_id:
            raise ValidationError('Choisir le groupe historique ou le groupe courant, pas les deux.')
        if self.backup_assignee_id and self.backup_assignee_id == self.assigned_to_id:
            raise ValidationError('Le remplaçant doit être distinct du responsable.')
    
    def __str__(self):
        group = self.target_group or self.working_group
        return f"{self.titre} ({group.name if group else 'Rattachement à confirmer'})"


class CTCProcessus(BaseModel):
    """
    Hub de suivi du parcours d'une norme dans la CTC.
    Ajoute la granularité interne à Norme.status == 'INTERNAL_REVIEW'
    sans modifier les STATUS_CHOICES existants du modèle Norme.
    """
    norme = models.OneToOneField(
        'norms.Norme',
        on_delete=models.CASCADE,
        related_name='ctc_processus'
    )

    STAGE_CHOICES = [
        ('RECEPTION',    'Étape 1 — Réception, Numérisation & Cadrage'),
        ('GEOSPATIAL',   'Étape 2 — Traitement Géospatial SIG (si applicable)'),
        ('MULTI_REVIEW', 'Étape 3 — Toilettage Multi-Critères (examens parallèles)'),
        ('INDUSTRIAL',   'Étape 4 — Consultation Industrielle FEC'),
        ('SIGNED_OUT',   'Étape 5 — Signé & Transmis au Comité de Pilotage'),
    ]
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='RECEPTION')

    # ── Étape 1 : Réception & Numérisation ──────────────────────────────────
    received_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='received_norms',
        help_text="Assistant Exécutif qui a enregistré le dossier"
    )
    received_at = models.DateTimeField(null=True, blank=True)
    indexed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Date de fin de mise en page et indexation par les Opérateurs de Saisie"
    )
    intake_validated_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='intake_validated_norms',
        help_text="Coordonnateur qui a validé l'introduction dans le circuit"
    )
    intake_validated_at = models.DateTimeField(null=True, blank=True)

    # ── Étape 2 : Traitement SIG ─────────────────────────────────────────────
    requires_sig = models.BooleanField(
        default=False,
        help_text="Cocher si la norme traite d'infrastructures linéaires nécessitant géolocalisation"
    )
    sig_completed_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sig_completed_norms',
        help_text="Ingénieur Cartographe SIG"
    )
    sig_completed_at = models.DateTimeField(null=True, blank=True)
    it_stored_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Date de dépôt en base sécurisée par les Techniciens IT"
    )

    # ── Étape 3 : Multi-Review ───────────────────────────────────────────────
    # Le suivi détaillé est dans les modèles OneToOne de validation :
    # norme.iso_review, norme.legistic_review, norme.ecological_review,
    # norme.economic_review, norme.schedule_review
    multi_review_started_at = models.DateTimeField(null=True, blank=True)
    all_reviews_completed = models.BooleanField(default=False)
    all_reviews_completed_at = models.DateTimeField(null=True, blank=True)

    # ── Étape 4 : Consultation FEC ───────────────────────────────────────────
    # Suivi détaillé dans norme.industrial_consultation
    industrial_completed_at = models.DateTimeField(null=True, blank=True)

    # ── Étape 5 : Signature de sortie & Transmission Pilotage ────────────────
    signed_out_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='signed_out_norms',
        help_text="Coordonnateur Technique Principal qui certifie la fin du toilettage"
    )
    signed_out_at = models.DateTimeField(null=True, blank=True)
    transmitted_to_pilotage_at = models.DateTimeField(null=True, blank=True)

    # ── Réception officielle par le Comité de Pilotage Élargi ────────────────
    # Section 5.4.3 : le Président (Poste 16) et le Rapporteur Général (Poste 1)
    # réceptionnent officiellement la norme nettoyée par la CTC.
    received_by_president = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='president_received_norms',
        help_text="Président du Comité de Pilotage Élargi"
    )
    received_by_president_at = models.DateTimeField(null=True, blank=True)
    received_by_rapporteur = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapporteur_received_norms',
        help_text="Rapporteur Général du Comité de Pilotage Élargi"
    )
    received_by_rapporteur_at = models.DateTimeField(null=True, blank=True)

    # ── Helpers ──────────────────────────────────────────────────────────────
    def advance_to(self, stage):
        self.current_stage = stage
        self.save(update_fields=['current_stage', 'updated_at'])

    def mark_received(self, expert):
        self.received_by = expert
        self.received_at = timezone.now()
        self.save(update_fields=['received_by', 'received_at', 'updated_at'])

    def mark_indexed(self):
        self.indexed_at = timezone.now()
        self.save(update_fields=['indexed_at', 'updated_at'])

    def mark_intake_validated(self, expert):
        self.intake_validated_by = expert
        self.intake_validated_at = timezone.now()
        if not self.requires_sig:
            self.current_stage = 'MULTI_REVIEW'
            self.multi_review_started_at = timezone.now()
        else:
            self.current_stage = 'GEOSPATIAL'
        self.save()

    def mark_sig_completed(self, expert):
        self.sig_completed_by = expert
        self.sig_completed_at = timezone.now()
        self.current_stage = 'MULTI_REVIEW'
        self.multi_review_started_at = timezone.now()
        self.save()

    def check_all_reviews(self):
        """Vérifie si tous les examens parallèles sont APPROVED → passe à INDUSTRIAL."""
        norme = self.norme
        # Le toilettage légistique possède un état métier intermédiaire
        # REVIEW_COMPLETED ; il vaut acceptation pour le passage CTC suivant.
        legistic = getattr(norme, 'legistic_review', None)
        reviews_done = all([
            legistic and legistic.status in ('APPROVED', 'REVIEW_COMPLETED'),
            getattr(norme, 'iso_review', None) and norme.iso_review.status == 'APPROVED',
            getattr(norme, 'ecological_review', None) and norme.ecological_review.status == 'APPROVED',
            getattr(norme, 'economic_review', None) and norme.economic_review.status == 'APPROVED',
            getattr(norme, 'schedule_review', None) and norme.schedule_review.is_completed,
        ])
        if reviews_done and not self.all_reviews_completed:
            self.all_reviews_completed = True
            self.all_reviews_completed_at = timezone.now()
            self.current_stage = 'INDUSTRIAL'
            self.save()
        return reviews_done

    def mark_signed_out(self, expert):
        self.signed_out_by = expert
        self.signed_out_at = timezone.now()
        self.transmitted_to_pilotage_at = timezone.now()
        self.current_stage = 'SIGNED_OUT'
        self.save()
        # Le statut macro suit la transmission réelle, pas un simple clic d'interface.
        if self.norme.status != 'PILOTAGE_REVIEW':
            self.norme.transition_to('PILOTAGE_REVIEW')
            self.norme.save(update_fields=['status', 'updated_at'])

    @property
    def pilotage_reception_complete(self):
        return bool(self.received_by_president_at and self.received_by_rapporteur_at)

    def mark_received_by_president(self, expert):
        self.received_by_president = expert
        self.received_by_president_at = timezone.now()
        self.save(update_fields=['received_by_president', 'received_by_president_at', 'updated_at'])

    def mark_received_by_rapporteur(self, expert):
        self.received_by_rapporteur = expert
        self.received_by_rapporteur_at = timezone.now()
        self.save(update_fields=['received_by_rapporteur', 'received_by_rapporteur_at', 'updated_at'])
        # Passer la norme au statut macro Pilotage
        self.norme.status = 'PILOTAGE_REVIEW'
        self.norme.save(update_fields=['status'])

    class Meta:
        verbose_name = "Processus CTC"
        verbose_name_plural = "Processus CTC"
        ordering = ['-created_at']

    def __str__(self):
        return f"CTC Processus — {self.norme.reference_number} [{self.current_stage}]"


class NormeCadrage(BaseModel):
    """
    Hub de suivi du Bureau Directoire (Postes 1 à 5) pour une norme donnée,
    couvrant les deux phases du Manuel Organisationnel 2026 :

      Phase 1 — AVANT la création de la norme (cadrage stratégique) :
        Poste 1 (Président)          : ouverture politique du chantier normatif
        Poste 2 (1er VP — ONIC)       : validation des experts WG du giron Ingénierie
        Poste 3 (2nd VP — AIBTP/CNIRS-BTP) : validation du mandat opérationnel des experts BTP
        Poste 4 (Secrétaire)          : formalisation du mandat opérationnel + méthodologie
        Poste 5 (Rapporteur Général)  : chronogramme général + ordre de service à la CTC

      Phase 2 — APRÈS la finalisation technique (validation finale) :
        Poste 4 (Secrétaire)          : vérification du PV de l'Assemblée Plénière
        Postes 2 & 3 (1er & 2nd VP)    : quitus de conformité technique
        Poste 1 (Président)           : validation finale, signature de la résolution,
                                          transmission au Ministre (Arrêté d'Homologation)

    Ajoute la granularité « amont/aval » du Bureau Directoire sans modifier
    Norme.STATUS_CHOICES, sur le modèle de CTCProcessus.
    """
    norme = models.OneToOneField(
        'norms.Norme',
        on_delete=models.CASCADE,
        related_name='cadrage'
    )

    STAGE_CHOICES = [
        # Phase 1 — avant création de la norme
        ('PROPOSED',              "Phase 1.1 — Orientation stratégique (Président)"),
        ('EXPERTS_REVIEW',         "Phase 1.2 — Validation des experts WG (1er & 2nd Vice-Présidents)"),
        ('MANDATE_FORMALIZATION', "Phase 1.3 — Mandat opérationnel formalisé (Secrétaire)"),
        ('SCHEDULED',             "Phase 1.4 — Chronogramme & ordre de service (Rapporteur Général)"),
        # Phase 2 — après finalisation technique
        ('PV_VERIFICATION',       "Phase 2.1 — Vérification du PV de l'Assemblée Plénière (Secrétaire)"),
        ('CONFORMITY_QUITUS',     "Phase 2.2 — Quitus de conformité technique (1er & 2nd Vice-Présidents)"),
        ('FINAL_VALIDATION',      "Phase 2.3 — Validation finale & signature (Président)"),
        ('COMPLETED',             "Terminé — Transmis au Ministre (Arrêté d'Homologation)"),
    ]
    current_stage = models.CharField(max_length=24, choices=STAGE_CHOICES, default='PROPOSED')

    # ── Phase 1.1 — Poste 1 : Président — ouverture du chantier normatif ────
    opened_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cadrages_ouverts',
        help_text="Président du Comité de Pilotage Élargi"
    )
    opened_at = models.DateTimeField(null=True, blank=True)
    strategic_orientation = models.TextField(
        blank=True, help_text="Orientations stratégiques formulées pour la mise en chantier de cette norme"
    )

    # ── Phase 1.2 — Poste 2 : 1er Vice-Président (ONIC) ──────────────────────
    onic_validated_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cadrages_valides_onic',
        help_text="1er Vice-Président — ONIC (giron Ingénierie)"
    )
    onic_validated_at = models.DateTimeField(null=True, blank=True)
    onic_notes = models.TextField(
        blank=True, help_text="Avis sur la légitimité technique des experts WG du giron Ingénierie"
    )

    # ── Phase 1.2 — Poste 3 : 2nd Vice-Président (AIBTP/CNIRS-BTP) ───────────
    btp_validated_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cadrages_valides_btp',
        help_text="2nd Vice-Président — AIBTP/CNIRS-BTP (giron Construction)"
    )
    btp_validated_at = models.DateTimeField(null=True, blank=True)
    btp_notes = models.TextField(
        blank=True, help_text="Avis sur le mandat opérationnel des experts WG du secteur BTP"
    )

    # ── Phase 1.3 — Poste 4 : Secrétaire — mandat opérationnel ───────────────
    mandate_formalized_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cadrages_mandats_formalises',
        help_text="Secrétaire du Comité de Pilotage Élargi"
    )
    mandate_formalized_at = models.DateTimeField(null=True, blank=True)
    operational_mandate = models.TextField(
        blank=True, help_text="Mandat opérationnel initial et méthodologie scientifique transmis aux CTM"
    )

    # ── Phase 1.4 — Poste 5 : Rapporteur Général — chronogramme & ordre de service
    scheduled_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cadrages_planifies',
        help_text="Rapporteur Général — SG-ITP"
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    deadline_ctm_review = models.DateField(
        null=True, blank=True, help_text="Date butoir — Remise des travaux du CTM/WG"
    )
    deadline_ctc_handoff = models.DateField(
        null=True, blank=True, help_text="Date butoir — Transmission du dossier à la CTC"
    )
    deadline_pilotage_review = models.DateField(
        null=True, blank=True, help_text="Date butoir — Retour devant le Comité de Pilotage"
    )
    transmitted_to_ctc_at = models.DateTimeField(
        null=True, blank=True, help_text="Date de transmission de l'ordre de service à la CTC"
    )

    # ── Phase 2.1 — Poste 4 : Secrétaire — vérification du PV de l'AP ────────
    pv_verified_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cadrages_pv_verifies',
        help_text="Secrétaire du Comité de Pilotage Élargi"
    )
    pv_verified_at = models.DateTimeField(null=True, blank=True)
    pv_reference = models.CharField(
        max_length=100, blank=True, help_text="Référence du PV de l'Assemblée Plénière"
    )

    # ── Phase 2.2 — Postes 2 & 3 : Quitus de conformité technique ────────────
    onic_quitus_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cadrages_quitus_onic',
        help_text="1er Vice-Président — ONIC"
    )
    onic_quitus_at = models.DateTimeField(null=True, blank=True)
    btp_quitus_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cadrages_quitus_btp',
        help_text="2nd Vice-Président — AIBTP/CNIRS-BTP"
    )
    btp_quitus_at = models.DateTimeField(null=True, blank=True)

    # ── Phase 2.3 — Poste 1 : Président — validation finale & signature ─────
    final_validated_by = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cadrages_valides_finaux',
        help_text="Président du Comité de Pilotage Élargi"
    )
    final_validated_at = models.DateTimeField(null=True, blank=True)
    resolution_reference = models.CharField(
        max_length=100, blank=True, help_text="Référence de la résolution signée par le Président"
    )
    transmitted_to_ministry_at = models.DateTimeField(
        null=True, blank=True, help_text="Date de transmission au Ministre pour l'Arrêté d'Homologation"
    )

    # ── Helpers — Phase 1 ─────────────────────────────────────────────────────
    @property
    def experts_review_complete(self):
        return bool(self.onic_validated_at and self.btp_validated_at)

    def mark_opened(self, expert, orientation=''):
        self.opened_by = expert
        self.opened_at = timezone.now()
        if orientation:
            self.strategic_orientation = orientation
        self.current_stage = 'EXPERTS_REVIEW'
        self.save()

    def mark_onic_validated(self, expert, notes=''):
        self.onic_validated_by = expert
        self.onic_validated_at = timezone.now()
        if notes:
            self.onic_notes = notes
        if self.experts_review_complete:
            self.current_stage = 'MANDATE_FORMALIZATION'
        self.save()

    def mark_btp_validated(self, expert, notes=''):
        self.btp_validated_by = expert
        self.btp_validated_at = timezone.now()
        if notes:
            self.btp_notes = notes
        if self.experts_review_complete:
            self.current_stage = 'MANDATE_FORMALIZATION'
        self.save()

    def mark_mandate_formalized(self, expert, mandate_text=''):
        self.mandate_formalized_by = expert
        self.mandate_formalized_at = timezone.now()
        if mandate_text:
            self.operational_mandate = mandate_text
        self.current_stage = 'SCHEDULED'
        self.save()

    def mark_scheduled(self, expert, deadline_ctm_review=None, deadline_ctc_handoff=None,
                        deadline_pilotage_review=None):
        self.scheduled_by = expert
        self.scheduled_at = timezone.now()
        self.deadline_ctm_review = deadline_ctm_review
        self.deadline_ctc_handoff = deadline_ctc_handoff
        self.deadline_pilotage_review = deadline_pilotage_review
        self.transmitted_to_ctc_at = timezone.now()
        self.current_stage = 'PV_VERIFICATION'
        self.save()

    # ── Helpers — Phase 2 ─────────────────────────────────────────────────────
    @property
    def conformity_quitus_complete(self):
        return bool(self.onic_quitus_at and self.btp_quitus_at)

    @property
    def ctc_handoff_complete(self):
        """
        True si la CTC a terminé son traitement (Article 12 — toilettage,
        enquête publique, certification — Étape 5/SIGNED_OUT) ET que le
        Président ET le Rapporteur Général ont accusé réception du dossier
        nettoyé (Section 5.4.3). Condition préalable à 'verify_pv'
        (Phase 2.1) : le Secrétaire ne peut auditer un PV dont le dossier
        n'est pas encore revenu de la CTC.
        """
        processus = getattr(self.norme, 'ctc_processus', None)
        return bool(processus and processus.pilotage_reception_complete)

    def mark_pv_verified(self, expert, pv_reference=''):
        self.pv_verified_by = expert
        self.pv_verified_at = timezone.now()
        if pv_reference:
            self.pv_reference = pv_reference
        self.current_stage = 'CONFORMITY_QUITUS'
        self.save()

    def mark_onic_quitus(self, expert):
        self.onic_quitus_by = expert
        self.onic_quitus_at = timezone.now()
        if self.conformity_quitus_complete:
            self.current_stage = 'FINAL_VALIDATION'
        self.save()

    def mark_btp_quitus(self, expert):
        self.btp_quitus_by = expert
        self.btp_quitus_at = timezone.now()
        if self.conformity_quitus_complete:
            self.current_stage = 'FINAL_VALIDATION'
        self.save()

    def mark_final_validated(self, expert, resolution_reference=''):
        self.final_validated_by = expert
        self.final_validated_at = timezone.now()
        if resolution_reference:
            self.resolution_reference = resolution_reference
        self.transmitted_to_ministry_at = timezone.now()
        self.current_stage = 'COMPLETED'
        self.save()

    class Meta:
        verbose_name = "Cadrage Bureau Directoire"
        verbose_name_plural = "Cadrages Bureau Directoire"
        ordering = ['-created_at']

    def __str__(self):
        return f"Cadrage Bureau Directoire — {self.norme.reference_number} [{self.current_stage}]"


class PlatformFreeze(BaseModel):
    """Verrou plateforme — gèle toutes les actions CTC et CTM (action souveraine du Président)."""
    is_locked = models.BooleanField(default=False, verbose_name="Plateforme verrouillée")
    locked_by = models.ForeignKey(Expert, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Verrou plateforme CTC/CTM"
        verbose_name_plural = "Verrous plateforme CTC/CTM"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Plateforme verrouillée" if self.is_locked else "Plateforme déverrouillée"


class Demande(BaseModel):
    """Demande transverse (instruction, action, signalement) qui fait circuler le travail.

    Modèle de base unique du module « Production » : un ordre du Directoire vers
    un groupe (instruction), une action confiée à un responsable, ou un
    signalement vers la CTC. Chaque création et chaque changement de statut est
    journalisé dans :model:`JournalDemande`.
    """
    TYPE_CHOICES = [
        ('INSTRUCTION', 'Instruction'),
        ('ACTION', 'Action'),
        ('SIGNALEMENT', 'Signalement'),
    ]
    STATUS_CHOICES = [
        ('ENVOYEE', 'Envoyée'),
        ('LUE', 'Lue'),
        ('EN_COURS', 'En cours'),
        ('EXECUTEE', 'Exécutée'),
    ]
    GRAVITE_CHOICES = [
        ('FAIBLE', 'Faible'),
        ('NORMALE', 'Normale'),
        ('HAUTE', 'Haute'),
        ('CRITIQUE', 'Critique'),
    ]
    # Transitions autorisées (le même flux sert instruction, action et signalement).
    TRANSITIONS = {
        'ENVOYEE': ['LUE', 'EN_COURS', 'EXECUTEE'],
        'LUE': ['EN_COURS', 'EXECUTEE'],
        'EN_COURS': ['EXECUTEE'],
        'EXECUTEE': [],
    }

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='INSTRUCTION', verbose_name="Type")
    emetteur = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, related_name='demandes_emises',
        verbose_name="Émetteur"
    )
    destinataire = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='demandes_recues',
        verbose_name="Responsable"
    )
    groupe = models.ForeignKey(
        WG, on_delete=models.PROTECT, null=True, blank=True, related_name='demandes',
        verbose_name="Groupe de travail"
    )
    sous_commission = models.ForeignKey(
        CTM, on_delete=models.PROTECT, null=True, blank=True, related_name='demandes',
        verbose_name="Sous-commission"
    )
    norme = models.ForeignKey(
        'norms.Norme', on_delete=models.SET_NULL, null=True, blank=True, related_name='demandes',
        verbose_name="Norme"
    )
    objet = models.CharField(max_length=300, verbose_name="Objet")
    message = models.TextField(blank=True, verbose_name="Message")
    echeance = models.DateField(null=True, blank=True, verbose_name="Échéance")
    gravite = models.CharField(max_length=20, choices=GRAVITE_CHOICES, blank=True, verbose_name="Gravité")
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ENVOYEE', verbose_name="Statut")

    # ── Instructions de production (Cellule Technique de Coordination) ─────
    nb_normes = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Nombre de normes à produire"
    )
    province = models.CharField(max_length=100, blank=True, verbose_name="Province")
    commune = models.CharField(max_length=100, blank=True, verbose_name="Commune")
    territoire = models.CharField(max_length=100, blank=True, verbose_name="Territoire")
    district = models.CharField(max_length=100, blank=True, verbose_name="District")
    quartier = models.CharField(max_length=100, blank=True, verbose_name="Quartier")
    avenue_rue = models.CharField(max_length=150, blank=True, verbose_name="Avenue ou rue")

    class Meta:
        verbose_name = "Demande"
        verbose_name_plural = "Demandes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['type', 'statut']),
            models.Index(fields=['groupe', 'statut']),
        ]

    def __str__(self):
        return f"{self.get_type_display()} — {self.objet} ({self.get_statut_display()})"

    @property
    def destinee_a(self):
        """Destinataire lisible : responsable, groupe ou sous-commission."""
        if self.destinataire:
            return self.destinataire.full_name
        if self.groupe:
            return str(self.groupe)
        if self.sous_commission:
            return f"Sous-commission {self.sous_commission.number} — {self.sous_commission.name}"
        return 'Direction'

    def transition(self, nouveau_statut, acteur=None, commentaire=''):
        """Change le statut en respectant le flux autorisé et journalise la transition."""
        ancien = self.statut
        if nouveau_statut not in dict(self.STATUS_CHOICES):
            raise ValueError("Statut inconnu.")
        if nouveau_statut == ancien:
            return self
        if nouveau_statut not in self.TRANSITIONS.get(ancien, []):
            raise ValueError(f"Transition refusée : {ancien} → {nouveau_statut}.")
        self.statut = nouveau_statut
        self.save(update_fields=['statut', 'updated_at'])
        JournalDemande.objects.create(
            demande=self, statut_avant=ancien, statut_apres=nouveau_statut,
            commentaire=commentaire, acteur=acteur,
        )
        return self


class JournalDemande(models.Model):
    """Historique des transitions de statut d'une demande (traçabilité)."""
    demande = models.ForeignKey(Demande, on_delete=models.CASCADE, related_name='journal')
    statut_avant = models.CharField(max_length=20, blank=True)
    statut_apres = models.CharField(max_length=20)
    commentaire = models.TextField(blank=True)
    acteur = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
        verbose_name="Acteur"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Journal de demande"
        verbose_name_plural = "Journaux de demandes"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.demande.objet} : {self.statut_avant or '—'} → {self.statut_apres}"


class CopilRapport(BaseModel):
    """Rapport officiel émis par le Comité de Pilotage (COPIL).

    Consultable depuis l'onglet « Instruction » de la CTC. Le contenu est
    rendu au format A4 (même en-tête/pied que la lecture d'une norme) et peut
    s'étendre sur plusieurs feuilles selon sa longueur.
    """
    reference = models.CharField(max_length=100, blank=True, verbose_name="Référence")
    titre = models.CharField(max_length=300, verbose_name="Titre")
    contenu = models.TextField(blank=True, verbose_name="Contenu")
    emetteur = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='copil_rapports', verbose_name="Émetteur (COPIL)",
    )
    date_rapport = models.DateField(null=True, blank=True, verbose_name="Date du rapport")

    class Meta:
        verbose_name = "Rapport COPIL"
        verbose_name_plural = "Rapports COPIL"
        ordering = ['-date_rapport', '-created_at']

    def __str__(self):
        return f"{self.reference or 'Rapport'} — {self.titre}"


from .phoenix_models import (  # noqa: E402,F401
    OrganisationVersion, Organe, PosteOrganisation, GroupeCible, ChoixOrganisationExpert,
    CorrespondanceStructure, CorrespondanceGroupe, AffectationSousCommission, MandatOrganisation,
    HabilitationAction, RattachementDocumentaire, JournalMigration,
    CircuitOrganisation, DossierPhoenix, PiecePhoenix, DecisionPhoenix, EnquetePhoenix,
    ReunionPhoenix, ParticipationPhoenix,
)

from .activity_models import (  # noqa: E402,F401
    ActivitySession, ActivityPulse, WorkExpectation, OffPlatformWork,
    JustifiedAbsence, BusinessCalendarDay, ActivitySilencePeriod,
    ActivityDispute, ActivityAccessLog, ActivityAlert, ActivityAggregate,
    SavedActivityView,
)

from .advisory_models import (  # noqa: E402,F401
    AvisConseiller, ConsultationConseiller, DemandeAnalyse, JournalAnalyse, PieceAnalyse,
)
