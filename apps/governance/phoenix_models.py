"""Référentiel Phoenix additif ; les circuits et relations historiques restent autonomes."""
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, F
from apps.core.models import BaseModel, User
from apps.experts.models import Expert, Structure


class PhoenixValidatedModel:
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class OrganisationVersion(BaseModel):
    class Status(models.TextChoices):
        PROPOSED = 'PROPOSED', 'Proposée'
        VALIDATED = 'VALIDATED', 'Validée'
        ACTIVE = 'ACTIVE', 'En vigueur'
        SUSPENDED = 'SUSPENDED', 'Suspendue'
        ARCHIVED = 'ARCHIVED', 'Archivée'
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROPOSED)
    source_document = models.CharField(max_length=500)
    source_sha256 = models.CharField(max_length=64, blank=True)
    activation_reference = models.CharField(max_length=250, blank=True)
    gt_catalogue_reference = models.CharField(max_length=250, blank=True)
    permissions_reference = models.CharField(max_length=250, blank=True)
    circuit_reference = models.CharField(max_length=250, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        permissions = [('prepare_phoenix', 'Préparer le référentiel et les correspondances Phoenix'),
                       ('manage_phoenix', 'Gérer les mandats, habilitations et règles Phoenix'),
                       ('activate_phoenix', 'Activer ou suspendre une organisation Phoenix')]
        constraints = [models.UniqueConstraint(fields=['status'], condition=Q(status='ACTIVE'), name='one_active_phoenix_organisation')]

    def clean(self):
        if self.status == self.Status.ACTIVE and not all((self.activation_reference, self.gt_catalogue_reference, self.permissions_reference, self.circuit_reference)):
            raise ValidationError('L’activation exige les références des décisions, du catalogue GT, des habilitations et du circuit approuvés.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Organe(PhoenixValidatedModel, BaseModel):
    class Type(models.TextChoices):
        COPIL = 'COPIL', 'Comité de Pilotage'
        ST = 'ST', 'Secrétariat technique'
        ST_POLE = 'ST_POLE', 'Pôle du Secrétariat technique'
        SC = 'SC', 'Sous-commission'
    version = models.ForeignKey(OrganisationVersion, on_delete=models.PROTECT, related_name='organes')
    code = models.CharField(max_length=60)
    name = models.CharField(max_length=250)
    official_name = models.CharField(max_length=250, blank=True)
    type = models.CharField(max_length=20, choices=Type.choices)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children')
    domain = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=OrganisationVersion.Status.choices, default='PROPOSED')
    source_reference = models.CharField(max_length=250)
    composition = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['version', 'code'], name='unique_phoenix_organe_code')]
        ordering = ['type', 'code']

    def clean(self):
        if self.parent_id and (self.parent_id == self.pk or self.parent.version_id != self.version_id):
            raise ValidationError('Le parent doit être un autre organe de la même organisation.')
        ancestor = self.parent if self.parent_id else None
        visited = {self.pk} if self.pk else set()
        while ancestor:
            if ancestor.pk in visited:
                raise ValidationError('Un organe ne peut pas être rattaché à l’un de ses descendants.')
            visited.add(ancestor.pk)
            ancestor = ancestor.parent if ancestor.parent_id else None
        if self.type == self.Type.ST_POLE and (not self.parent_id or self.parent.type != self.Type.ST):
            raise ValidationError('Un pôle ST doit être rattaché au Secrétariat technique.')
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            if previous.type != self.type and (
                self.postes.exists() or self.groupes.exists() or self.children.exists()
                or self.habilitationaction_set.exists() or self.correspondancestructure_set.exists()
                or self.correspondancegroupe_set.exists() or self.rattachementdocumentaire_set.exists()
            ):
                raise ValidationError('Le type d’un organe déjà utilisé est conservé ; créer un nouvel organe.')

    def __str__(self):
        return f'{self.code} — {self.name}'


class PosteOrganisation(PhoenixValidatedModel, BaseModel):
    class Category(models.TextChoices):
        PRESIDENCY = 'PRESIDENCY', 'Présidence'
        SECRETARIAT = 'SECRETARIAT', 'Secrétariat'
        MEMBER = 'MEMBER', 'Membres'
        INVITED = 'INVITED', 'Invités'
        APPOINT = 'APPOINT', 'Appoints'
        COORDINATION = 'COORDINATION', 'Coordination'
        POLE_HEAD = 'POLE_HEAD', 'Chef de pôle'
        UNKNOWN = 'UNKNOWN', 'Fonction à confirmer'
    organe = models.ForeignKey(Organe, on_delete=models.PROTECT, related_name='postes')
    code = models.CharField(max_length=60)
    category = models.CharField(max_length=20, choices=Category.choices)
    title = models.CharField(max_length=300, blank=True)
    origin_label = models.CharField(max_length=250, blank=True)
    required_structure = models.ForeignKey(Structure, on_delete=models.PROTECT, null=True, blank=True)
    source_reference = models.CharField(max_length=250)
    status = models.CharField(max_length=20, choices=OrganisationVersion.Status.choices, default='PROPOSED')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['organe', 'code'], name='unique_phoenix_poste_code')]
        ordering = ['code']

    def __str__(self):
        return f'{self.code} — {self.title or "Fonction à confirmer"}'


class GroupeCible(PhoenixValidatedModel, BaseModel):
    sc = models.ForeignKey(Organe, on_delete=models.PROTECT, related_name='groupes')
    code = models.CharField(max_length=60)
    name = models.CharField(max_length=250)
    mission = models.TextField(blank=True)
    activity = models.CharField(max_length=20, choices=[('PRODUCTION', 'Production'), ('WATCH', 'Veille')])
    source_reference = models.CharField(max_length=250)
    status = models.CharField(max_length=20, choices=OrganisationVersion.Status.choices, default='PROPOSED')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['sc', 'code'], name='unique_phoenix_gt_code')]

    def clean(self):
        if not self.sc_id:
            return
        if self.sc.type != Organe.Type.SC:
            raise ValidationError('Un GT doit être rattaché à une SC.')
        if not self.source_reference.strip():
            raise ValidationError('La source officielle du groupe doit être renseignée.')
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if (old.sc_id != self.sc_id or old.code != self.code) and self.dossiers.exists():
                raise ValidationError('L’identité d’un GT utilisé par un dossier est conservée.')

    def __str__(self):
        return f'{self.code} — {self.name}'


class ChoixOrganisationExpert(PhoenixValidatedModel, BaseModel):
    """Souhait déclaré par l'expert, sans effet sur ses affectations ou droits."""

    expert = models.ForeignKey(Expert, on_delete=models.PROTECT, related_name='organisation_choices')
    version = models.ForeignKey(OrganisationVersion, on_delete=models.PROTECT)
    sc = models.ForeignKey(Organe, on_delete=models.PROTECT)
    source_wg = models.ForeignKey('governance.WG', on_delete=models.PROTECT, null=True, blank=True)
    groupe = models.ForeignKey(GroupeCible, on_delete=models.PROTECT, null=True, blank=True)
    groupe_souhaite = models.CharField(max_length=250, blank=True)
    status = models.CharField(max_length=20, default='REVIEW', choices=[('REVIEW', 'À examiner')])

    def clean(self):
        if self.sc_id and (self.sc.type != Organe.Type.SC or self.sc.version_id != self.version_id):
            raise ValidationError('La sous-commission doit appartenir à cette organisation.')
        if self.groupe_id and self.groupe.sc_id != self.sc_id:
            raise ValidationError('Le groupe doit appartenir à la sous-commission choisie.')
        if not self.source_wg_id and not self.groupe_id and not self.groupe_souhaite.strip():
            raise ValidationError('Choisissez un groupe de travail existant.')

    class Meta:
        ordering = ['-created_at', '-id']


class MappingStatus(models.TextChoices):
    PROPOSED = 'PROPOSED', 'Proposée'
    VALIDATED = 'VALIDATED', 'Validée'
    REJECTED = 'REJECTED', 'Écartée'


class CorrespondanceStructure(PhoenixValidatedModel, BaseModel):
    version = models.ForeignKey(OrganisationVersion, on_delete=models.PROTECT, related_name='ctm_mappings')
    ctm = models.ForeignKey('governance.CTM', on_delete=models.PROTECT, related_name='phoenix_mappings')
    sc = models.ForeignKey(Organe, on_delete=models.PROTECT, null=True, blank=True)
    nature = models.CharField(max_length=20, choices=[('PRIMARY', 'Principale candidate'), ('CONTRIBUTION', 'Contribution'), ('NONE', 'Sans équivalent confirmé')], default='PRIMARY')
    domain = models.CharField(max_length=500)
    justification = models.TextField(blank=True)
    source_reference = models.CharField(max_length=250)
    status = models.CharField(max_length=20, choices=MappingStatus.choices, default='PROPOSED')
    decision_reference = models.CharField(max_length=250, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['version', 'ctm', 'domain'], name='unique_phoenix_ctm_domain')]

    def clean(self):
        if self.sc_id and (self.sc.version_id != self.version_id or self.sc.type != Organe.Type.SC):
            raise ValidationError('La cible doit être une SC de la même organisation.')
        if self.status == MappingStatus.VALIDATED and not self.decision_reference.strip():
            raise ValidationError('La validation exige une référence de décision.')


class CorrespondanceGroupe(PhoenixValidatedModel, BaseModel):
    version = models.ForeignKey(OrganisationVersion, on_delete=models.PROTECT, related_name='wg_mappings')
    wg = models.ForeignKey('governance.WG', on_delete=models.PROTECT, related_name='phoenix_mappings')
    sc = models.ForeignKey(Organe, on_delete=models.PROTECT, null=True, blank=True)
    gt = models.ForeignKey(GroupeCible, on_delete=models.PROTECT, null=True, blank=True)
    domain = models.CharField(max_length=500)
    justification = models.TextField(blank=True)
    source_reference = models.CharField(max_length=250)
    status = models.CharField(max_length=20, choices=MappingStatus.choices, default='PROPOSED')
    decision_reference = models.CharField(max_length=250, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['version', 'wg', 'domain'], name='unique_phoenix_wg_domain')]

    def clean(self):
        if self.sc_id and (self.sc.version_id != self.version_id or self.sc.type != Organe.Type.SC):
            raise ValidationError('La SC doit appartenir à cette organisation.')
        if self.gt_id and (not self.sc_id or self.gt.sc_id != self.sc_id):
            raise ValidationError('Le GT doit être rattaché à la SC choisie.')
        if self.status == MappingStatus.VALIDATED and not self.decision_reference.strip():
            raise ValidationError('La validation exige une référence de décision.')


class AffectationSousCommission(PhoenixValidatedModel, BaseModel):
    """Rattachement migré d'un expert à une SC, sans mandat ni droit implicite."""

    class Status(models.TextChoices):
        MIGRATED = 'MIGRATED', 'Affecté par migration'
        REVIEW = 'REVIEW', 'À examiner'
        ENDED = 'ENDED', 'Terminé'
        CANCELLED = 'CANCELLED', 'Annulé'

    version = models.ForeignKey(OrganisationVersion, on_delete=models.PROTECT, related_name='expert_assignments')
    expert = models.ForeignKey(Expert, on_delete=models.PROTECT, related_name='subcommission_assignments')
    sc = models.ForeignKey(Organe, on_delete=models.PROTECT, null=True, blank=True, related_name='expert_assignments')
    source_affectation = models.ForeignKey(
        'governance.Affectation', on_delete=models.PROTECT, null=True, blank=True,
        related_name='phoenix_assignments',
    )
    source_ctm = models.ForeignKey(
        'governance.CTM', on_delete=models.PROTECT, null=True, blank=True,
        related_name='phoenix_expert_assignments',
    )
    source_wg = models.ForeignKey(
        'governance.WG', on_delete=models.PROTECT, null=True, blank=True,
        related_name='phoenix_expert_assignments',
    )
    structure_mapping = models.ForeignKey(
        CorrespondanceStructure, on_delete=models.PROTECT, null=True, blank=True,
        related_name='expert_assignments',
    )
    group_mapping = models.ForeignKey(
        CorrespondanceGroupe, on_delete=models.PROTECT, null=True, blank=True,
        related_name='expert_assignments',
    )
    source_key = models.CharField(max_length=100)
    batch_reference = models.CharField(max_length=80, db_index=True)
    source_kind = models.CharField(
        max_length=30,
        choices=[
            ('AFFECTATION_WG', 'Affectation WG'),
            ('AFFECTATION_CTM', 'Affectation CTM'),
            ('PROFILE_CTM', 'CTM du profil'),
            ('NO_SOURCE', 'Aucune affectation source'),
            ('REPORT_PROPOSAL', 'Proposition du rapport adopté'),
        ],
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REVIEW)
    is_primary = models.BooleanField(default=False)
    migration_reference = models.CharField(max_length=250)
    source_database_sha256 = models.CharField(max_length=64)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    rationale = models.TextField(blank=True)
    source_snapshot = models.JSONField(default=dict)

    class Meta:
        ordering = ['sc__code', 'expert__user__last_name', 'expert_id']
        constraints = [
            models.UniqueConstraint(fields=['version', 'source_key'], name='phoenix_unique_expert_source'),
            models.UniqueConstraint(
                fields=['version', 'expert'], condition=Q(status='MIGRATED', is_primary=True),
                name='phoenix_one_primary_sc_per_expert',
            ),
            models.CheckConstraint(
                condition=Q(status__in=['REVIEW', 'CANCELLED']) | Q(sc__isnull=False, effective_from__isnull=False),
                name='phoenix_migrated_expert_has_target',
            ),
            models.CheckConstraint(
                condition=Q(effective_to__isnull=True) | Q(effective_from__isnull=False, effective_to__gte=F('effective_from')),
                name='phoenix_expert_assignment_dates',
            ),
        ]

    def clean(self):
        if self.sc_id and (self.sc.version_id != self.version_id or self.sc.type != Organe.Type.SC):
            raise ValidationError('La cible doit être une sous-commission de cette organisation.')
        if self.status == self.Status.MIGRATED:
            if not self.sc_id or not self.effective_from or not self.migration_reference.strip():
                raise ValidationError('Une affectation migrée exige une SC, une date et une référence de migration.')
            if not self.source_ctm_id:
                raise ValidationError('Une affectation migrée exige une provenance CTM vérifiable.')
        if self.source_wg_id and self.source_ctm_id != self.source_wg.ctm_id:
            raise ValidationError('Le WG source doit appartenir au CTM source.')
        if self.source_affectation_id:
            if self.source_affectation.expert_id != self.expert_id:
                raise ValidationError('L’affectation source doit appartenir au même expert.')
            if self.source_ctm_id != self.source_affectation.ctm_id or self.source_wg_id != self.source_affectation.wg_id:
                raise ValidationError('La provenance CTM/WG doit correspondre à l’affectation historique.')
        if self.structure_mapping_id:
            mapping = self.structure_mapping
            if mapping.version_id != self.version_id or mapping.ctm_id != self.source_ctm_id or mapping.sc_id != self.sc_id:
                raise ValidationError('La correspondance CTM ne justifie pas cette affectation.')
        if self.group_mapping_id:
            mapping = self.group_mapping
            if mapping.version_id != self.version_id or mapping.wg_id != self.source_wg_id or mapping.sc_id != self.sc_id:
                raise ValidationError('La correspondance WG ne justifie pas cette affectation.')
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            immutable = ('version_id', 'expert_id', 'source_key', 'batch_reference', 'source_kind', 'source_affectation_id',
                         'source_ctm_id', 'source_wg_id', 'source_database_sha256')
            if old.status in (self.Status.MIGRATED, self.Status.ENDED) and any(
                getattr(old, field) != getattr(self, field) for field in immutable
            ):
                raise ValidationError('La provenance d’une affectation migrée est conservée.')

    def __str__(self):
        target = self.sc.code if self.sc_id else 'À examiner'
        return f'{self.expert.user.get_full_name() or self.expert.user.username} → {target}'


class MandatOrganisation(PhoenixValidatedModel, BaseModel):
    expert = models.ForeignKey(Expert, on_delete=models.PROTECT, related_name='organisation_mandates')
    poste = models.ForeignKey(PosteOrganisation, on_delete=models.PROTECT, null=True, blank=True, related_name='mandates')
    groupe = models.ForeignKey(GroupeCible, on_delete=models.PROTECT, null=True, blank=True)
    function = models.CharField(max_length=250, blank=True)
    capacity = models.CharField(max_length=20, choices=[('ORGANISATION', 'Fonction dans l’organe'), ('HOMOLOGATION', 'Mandat d’homologation'), ('PUBLICATION', 'Mandat de publication')], default='ORGANISATION')
    appointment_reference = models.CharField(max_length=250, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('PROPOSED', 'Proposé'), ('ACTIVE', 'En cours'), ('ENDED', 'Terminé')], default='PROPOSED')

    class Meta:
        constraints = [
            models.CheckConstraint(condition=(Q(poste__isnull=False, groupe__isnull=True) | Q(poste__isnull=True, groupe__isnull=False)), name='phoenix_mandate_one_target'),
            models.CheckConstraint(condition=Q(end_date__isnull=True) | Q(start_date__isnull=True) | Q(end_date__gte=F('start_date')), name='phoenix_mandate_dates_order'),
            models.UniqueConstraint(fields=['poste', 'capacity'], condition=Q(status='ACTIVE', poste__isnull=False), name='one_active_phoenix_post_capacity'),
        ]

    @property
    def organisation_version(self):
        return self.poste.organe.version if self.poste_id else self.groupe.sc.version

    def clean(self):
        if bool(self.poste_id) == bool(self.groupe_id):
            raise ValidationError('Un mandat doit viser un poste ou un groupe, exclusivement.')
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if old.status in ('ACTIVE', 'ENDED') and (old.expert_id != self.expert_id or old.poste_id != self.poste_id or old.groupe_id != self.groupe_id or old.capacity != self.capacity):
                raise ValidationError('Le titulaire et la cible d’un mandat nommé sont conservés ; enregistrer une nouvelle nomination.')
        if self.status == 'ACTIVE':
            if not self.appointment_reference or not self.start_date or not self.function:
                raise ValidationError('Une nomination, une date et une fonction confirmées sont nécessaires.')
            if self.poste_id and not self.poste.title:
                raise ValidationError('La fonction de ce poste n’est pas encore confirmée.')
        if self.capacity != 'ORGANISATION' and not self.poste_id:
            raise ValidationError('Un mandat de décision finale doit être rattaché à une fonction confirmée.')

    def __str__(self):
        return f'{self.expert.user.get_full_name() or self.expert.user.username} · {self.function or "Fonction à confirmer"} · {self.get_capacity_display()}'


class HabilitationAction(PhoenixValidatedModel, BaseModel):
    mandat = models.ForeignKey(MandatOrganisation, on_delete=models.PROTECT, related_name='habilitations')
    action = models.CharField(max_length=100)
    perimeter = models.ForeignKey(Organe, on_delete=models.PROTECT)
    decision_reference = models.CharField(max_length=250)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    enabled = models.BooleanField(default=False)
    delegated_from = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='delegations')

    def clean(self):
        if not self.mandat_id or not self.perimeter_id:
            return
        if self.perimeter.version_id != self.mandat.organisation_version.pk:
            raise ValidationError('L’habilitation et son périmètre doivent appartenir à la même organisation.')
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError('La fin doit suivre le début de l’habilitation.')
        if self.delegated_from_id:
            source = self.delegated_from
            if source.pk == self.pk or source.delegated_from_id or source.action != self.action or source.perimeter_id != self.perimeter_id:
                raise ValidationError('Une délégation doit reprendre l’action et le périmètre d’une habilitation directe.')
            if self.start_date < source.start_date or (source.end_date and (not self.end_date or self.end_date > source.end_date)):
                raise ValidationError('La délégation doit rester dans la période de l’habilitation source.')


class RattachementDocumentaire(PhoenixValidatedModel, BaseModel):
    norme = models.ForeignKey('norms.Norme', on_delete=models.PROTECT, related_name='organisation_bindings')
    version = models.ForeignKey(OrganisationVersion, on_delete=models.PROTECT)
    sc = models.ForeignKey(Organe, on_delete=models.PROTECT)
    gt = models.ForeignKey(GroupeCible, on_delete=models.PROTECT, null=True, blank=True)
    role = models.CharField(max_length=20, choices=[('OWNER', 'Propriétaire proposé'), ('CONTRIBUTOR', 'Contribution')])
    status = models.CharField(max_length=20, choices=[*MappingStatus.choices, ('ENDED', 'Terminé')], default='PROPOSED')
    decision_reference = models.CharField(max_length=250, blank=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['norme', 'version'], condition=Q(role='OWNER', status='VALIDATED'), name='one_validated_phoenix_document_owner')]

    def clean(self):
        if not self.sc_id:
            return
        if self.sc.type != Organe.Type.SC or self.sc.version_id != self.version_id:
            raise ValidationError('Le rattachement exige une SC de la même organisation.')
        if self.gt_id and self.gt.sc_id != self.sc_id:
            raise ValidationError('Le GT doit appartenir à cette SC.')
        if self.status == MappingStatus.VALIDATED and not self.decision_reference:
            raise ValidationError('Une référence de décision est requise.')
        if self.effective_to and (not self.effective_from or self.effective_to < self.effective_from):
            raise ValidationError('Période de rattachement invalide.')
        if self.status == 'ENDED' and not self.effective_to:
            raise ValidationError('La clôture du rattachement exige une date de fin.')
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if old.status in ('VALIDATED', 'ENDED') and any(getattr(old, field) != getattr(self, field) for field in ('norme_id', 'version_id', 'sc_id', 'gt_id', 'role', 'decision_reference', 'effective_from')):
                raise ValidationError('Un rattachement validé conserve sa décision ; clôturer sa période et créer une nouvelle proposition.')


class CircuitOrganisation(PhoenixValidatedModel, BaseModel):
    version = models.ForeignKey(OrganisationVersion, on_delete=models.PROTECT, related_name='circuits')
    code = models.SlugField(max_length=60)
    name = models.CharField(max_length=250)
    configuration = models.JSONField()
    decision_reference = models.CharField(max_length=250, blank=True)
    status = models.CharField(max_length=20, choices=[('PROPOSED', 'Proposé'), ('VALIDATED', 'Validé')], default='PROPOSED')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['version', 'code'], name='phoenix_unique_circuit_code')]

    def clean(self):
        from .phoenix_rules import validate_circuit
        validate_circuit(self.configuration)
        if self.status == 'VALIDATED' and not self.decision_reference.strip():
            raise ValidationError('La validation du circuit exige une référence de décision.')
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            if previous.status == 'VALIDATED' and (previous.configuration != self.configuration or previous.decision_reference != self.decision_reference or previous.version_id != self.version_id or self.status != 'VALIDATED'):
                raise ValidationError('Un circuit validé est figé ; créer une nouvelle édition.')

    def __str__(self):
        return self.name


class DossierPhoenix(PhoenixValidatedModel, BaseModel):
    norme = models.OneToOneField('norms.Norme', on_delete=models.PROTECT, related_name='phoenix_dossier')
    circuit = models.ForeignKey(CircuitOrganisation, on_delete=models.PROTECT, related_name='dossiers')
    gt = models.ForeignKey(GroupeCible, on_delete=models.PROTECT, related_name='dossiers')
    creator_mandate = models.ForeignKey(MandatOrganisation, on_delete=models.PROTECT)
    document_version = models.ForeignKey('norms.NormeVersion', on_delete=models.PROTECT, null=True, blank=True)
    state = models.CharField(max_length=60)
    revision = models.PositiveIntegerField(default=0)
    stage_sequence = models.PositiveIntegerField(default=0)
    suspended = models.BooleanField(default=False)

    def clean(self):
        if self.norme.circuit_version != 'PHOENIX' or self.gt.sc.version_id != self.circuit.version_id:
            raise ValidationError('Le dossier Phoenix et son GT doivent appartenir au même circuit cible.')
        if self.state not in {state['code'] for state in self.circuit.configuration['states']}:
            raise ValidationError('État absent du circuit.')
        if self.document_version_id and self.document_version.norme_id != self.norme_id:
            raise ValidationError('La version documentaire appartient à un autre dossier.')
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            if previous.circuit_id != self.circuit_id or previous.norme_id != self.norme_id or previous.gt_id != self.gt_id:
                raise ValidationError('Le circuit et l’origine d’un dossier ouvert sont conservés.')


def phoenix_private_storage():
    from django.conf import settings
    from django.core.files.storage import FileSystemStorage
    return FileSystemStorage(location=settings.BASE_DIR / '.phoenix_documents', file_permissions_mode=0o600, directory_permissions_mode=0o700)


class PiecePhoenix(PhoenixValidatedModel, BaseModel):
    dossier = models.ForeignKey(DossierPhoenix, on_delete=models.PROTECT, related_name='pieces')
    version = models.ForeignKey('norms.NormeVersion', on_delete=models.PROTECT)
    mandate = models.ForeignKey(MandatOrganisation, on_delete=models.PROTECT)
    kind = models.CharField(max_length=80)
    reference = models.CharField(max_length=250)
    content = models.TextField(blank=True)
    file = models.FileField(upload_to='pieces/%Y/%m/', storage=phoenix_private_storage, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)

    def clean(self):
        if self.version.norme_id != self.dossier.norme_id or self.mandate.organisation_version.pk != self.dossier.circuit.version_id:
            raise ValidationError('La pièce, son auteur et la version examinée doivent correspondre au dossier.')
        if not self.content.strip() and not self.file:
            raise ValidationError('Joindre un fichier ou le texte de la pièce justificative.')
        if self.pk:
            raise ValidationError('Une pièce justificative est conservée ; joindre un complément pour la remplacer.')


class DecisionPhoenix(models.Model):
    dossier = models.ForeignKey(DossierPhoenix, on_delete=models.PROTECT, related_name='decisions')
    mandate = models.ForeignKey(MandatOrganisation, on_delete=models.PROTECT)
    expert = models.ForeignKey(Expert, on_delete=models.PROTECT)
    document_version = models.ForeignKey('norms.NormeVersion', on_delete=models.PROTECT)
    stage_sequence = models.PositiveIntegerField()
    transition = models.CharField(max_length=60)
    from_state = models.CharField(max_length=60)
    to_state = models.CharField(max_length=60)
    decision_reference = models.CharField(max_length=250)
    reason = models.TextField()
    request_key = models.CharField(max_length=100)
    payload_sha256 = models.CharField(max_length=64)
    completed = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    channel = models.CharField(max_length=30, default='Web')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [models.UniqueConstraint(fields=['dossier', 'request_key'], name='phoenix_unique_decision_request'),
                       models.UniqueConstraint(fields=['dossier', 'stage_sequence', 'transition', 'expert'], name='phoenix_one_vote_per_person')]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Une décision enregistrée ne peut pas être réécrite.')
        return super().save(*args, **kwargs)


class EnquetePhoenix(PhoenixValidatedModel, BaseModel):
    dossier = models.ForeignKey(DossierPhoenix, on_delete=models.PROTECT, related_name='enquetes')
    version = models.ForeignKey('norms.NormeVersion', on_delete=models.PROTECT)
    reference = models.CharField(max_length=250)
    starts_at = models.DateField()
    ends_at = models.DateField()
    report = models.ForeignKey(PiecePhoenix, on_delete=models.PROTECT, null=True, blank=True)

    def clean(self):
        if self.ends_at < self.starts_at or self.version.norme_id != self.dossier.norme_id:
            raise ValidationError('La période et la version de l’enquête doivent correspondre au dossier.')
        if self.report_id and (self.report.dossier_id != self.dossier_id or self.report.version_id != self.version_id):
            raise ValidationError('Le rapport d’enquête doit correspondre à la version examinée.')


class JournalMigration(models.Model):
    version = models.ForeignKey(OrganisationVersion, on_delete=models.PROTECT, related_name='journal')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    actor_name = models.CharField(max_length=250, blank=True)
    operation = models.CharField(max_length=100)
    target = models.CharField(max_length=250)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    reason = models.TextField(blank=True)
    mandate = models.ForeignKey(MandatOrganisation, on_delete=models.PROTECT, null=True, blank=True)
    actor_role = models.CharField(max_length=250, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    channel = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Une trace de migration ne peut pas être réécrite.')
        return super().save(*args, **kwargs)


class ReunionPhoenix(PhoenixValidatedModel, BaseModel):
    dossier = models.ForeignKey(DossierPhoenix, on_delete=models.PROTECT, related_name='reunions')
    document_version = models.ForeignKey('norms.NormeVersion', on_delete=models.PROTECT)
    organizer = models.ForeignKey(MandatOrganisation, on_delete=models.PROTECT)
    title = models.CharField(max_length=250)
    agenda = models.TextField()
    starts_at = models.DateTimeField()
    location = models.CharField(max_length=250)
    minutes = models.ForeignKey(PiecePhoenix, on_delete=models.PROTECT, null=True, blank=True)

    def clean(self):
        if self.document_version.norme_id != self.dossier.norme_id:
            raise ValidationError('La version examinée doit appartenir au dossier de la réunion.')
        if self.minutes_id and (self.minutes.dossier_id != self.dossier_id or self.minutes.version_id != self.document_version_id):
            raise ValidationError('Le procès-verbal doit correspondre à la réunion et à sa version documentaire.')


class ParticipationPhoenix(PhoenixValidatedModel, BaseModel):
    reunion = models.ForeignKey(ReunionPhoenix, on_delete=models.PROTECT, related_name='participants')
    mandate = models.ForeignKey(MandatOrganisation, on_delete=models.PROTECT)
    presence = models.CharField(max_length=20, choices=[('EXPECTED', 'Attendue'), ('PRESENT', 'Présente'), ('ABSENT', 'Absente'), ('EXCUSED', 'Excusée')], default='EXPECTED')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['reunion', 'mandate'], name='phoenix_unique_meeting_participant')]

    def clean(self):
        if self.mandate.organisation_version.pk != self.reunion.dossier.circuit.version_id:
            raise ValidationError('Le participant doit avoir un mandat dans la même organisation.')

