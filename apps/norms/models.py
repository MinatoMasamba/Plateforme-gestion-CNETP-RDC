import json
import re
import unicodedata

from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel, User
from apps.governance.models import CTM, WG
from apps.experts.models import Expert


class Norme(BaseModel):
    """Un projet de norme"""
    STANDARD_FAMILY_CHOICES = [
        ('NCD', 'Norme Nationale Congolaise'),
        ('ISO', 'Référentiel ISO'),
        ('ARSO', 'Référentiel ARSO'),
        ('OTHER', 'Autre référentiel'),
    ]

    title = models.CharField(max_length=500)
    reference_number = models.CharField(max_length=50, unique=True, help_text="Ex: CNETP-001-2024")
    
    description = models.TextField()
    ctm = models.ForeignKey(CTM, on_delete=models.PROTECT, related_name='normes')
    wg = models.ForeignKey(WG, on_delete=models.PROTECT, related_name='normes')

    # Squelette normatif explicite
    standard_family = models.CharField(max_length=10, choices=STANDARD_FAMILY_CHOICES, default='NCD')
    category = models.CharField(max_length=100, blank=True, help_text="Catégorie d'activité (ex: Qualité, Sécurité, Éthique)")
    
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

    def infer_standard_family(self):
        """Déduire la famille de norme à partir des métadonnées disponibles."""
        if self.standard_family:
            return self.standard_family
        if self.iso_reference:
            return 'ISO'
        if self.arso_reference:
            return 'ARSO'
        if self.reference_number.startswith('NCD') or self.norm_type == 'NCD':
            return 'NCD'
        return 'OTHER'
    
    def get_latest_version(self):
        return self.versions.order_by('-version_number').first()

    def refresh_current_version(self, version=None, save=True):
        """Aligner current_version sur la dernière version disponible."""
        version = version or self.get_latest_version()
        if not version:
            self.current_version = None
            if save:
                self.save(update_fields=['current_version', 'updated_at'])
            return None

        if version.document:
            self.current_version = version.document
        else:
            self.current_version = None

        if save:
            self.save(update_fields=['current_version', 'updated_at'])
        return self.current_version

    def current_version_matches_latest(self):
        """Vérifier que current_version correspond bien à la dernière NormeVersion."""
        latest = self.get_latest_version()
        if not latest:
            return self.current_version is None
        if not self.current_version:
            return latest.document is None
        if not latest.document:
            return False
        return self.current_version.name == latest.document.name

    @classmethod
    def workflow_transitions(cls):
        return {
            'DRAFT': ['INTERNAL_REVIEW', 'CTM_REVIEW'],
            'INTERNAL_REVIEW': ['CTM_REVIEW', 'DRAFT'],
            'CTM_REVIEW': ['LEGISTIC_REVIEW', 'INTERNAL_REVIEW'],
            'LEGISTIC_REVIEW': ['PUBLIC_INQUIRY', 'CTM_REVIEW'],
            'PUBLIC_INQUIRY': ['PILOTAGE_REVIEW', 'CTM_REVIEW'],
            'PILOTAGE_REVIEW': ['FINAL_REVIEW', 'PUBLIC_INQUIRY'],
            'FINAL_REVIEW': ['ADOPTED', 'PUBLIC_INQUIRY'],
            'ADOPTED': ['HOMOLOGATED'],
            'HOMOLOGATED': ['PUBLISHED'],
            'PUBLISHED': ['ARCHIVED'],
            'ARCHIVED': [],
        }

    def can_transition_to(self, new_status):
        return new_status in self.workflow_transitions().get(self.status, [])

    def transition_to(self, new_status, save=True):
        if not self.can_transition_to(new_status):
            allowed = ', '.join(self.workflow_transitions().get(self.status, []))
            raise ValueError(f'Transition invalide de {self.status} à {new_status}. Transitions valides: {allowed}')
        self.status = new_status
        if save:
            self.save(update_fields=['status', 'updated_at'])
        return self.status


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

    def get_structured_content(self):
        """Retourner une représentation structurée compatible avec le texte brut."""
        return parse_norme_structure(self.content)


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


class NormeContentBlock(BaseModel):
    """Bloc éditorial structuré d'une version de norme."""

    BLOCK_KIND_CHOICES = [
        ('SECTION', 'Section'),
        ('ARTICLE', 'Article'),
        ('ANNEXE', 'Annexe'),
        ('PARAGRAPH', 'Paragraphe'),
    ]

    version = models.ForeignKey(NormeVersion, on_delete=models.CASCADE, related_name='content_blocks')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    kind = models.CharField(max_length=20, choices=BLOCK_KIND_CHOICES)
    code = models.CharField(max_length=50, blank=True, help_text="Ex: 1, 1.1, A")
    title = models.CharField(max_length=500, blank=True)
    body = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Bloc de contenu de norme"
        verbose_name_plural = "Blocs de contenu de norme"
        ordering = ['version', 'position', 'id']
        unique_together = ('version', 'position')

    def __str__(self):
        label = self.title or self.code or self.kind
        return f"{self.version} - {label}"


class NormeDocumentImport(BaseModel):
    """Dépôt des documents Word importés depuis la racine norme/."""

    DOCUMENT_TYPE_CHOICES = [
        ('guide', 'Guide'),
        ('liste_normes', 'Liste des normes'),
        ('norme', 'Norme'),
        ('inconnu', 'Inconnu'),
    ]

    filename = models.CharField(max_length=255, unique=True)
    source_path = models.CharField(max_length=500)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    paragraph_count = models.PositiveIntegerField(default=0)
    extracted_json = models.JSONField(default=dict, blank=True)
    checksum = models.CharField(max_length=64, blank=True, default='')
    imported_at = models.DateTimeField(auto_now=True)
    norme = models.ForeignKey(
        Norme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='document_imports',
    )

    class Meta:
        verbose_name = "Document normatif importé"
        verbose_name_plural = "Documents normatifs importés"
        ordering = ['-imported_at', 'filename']

    def __str__(self):
        return f"{self.filename} ({self.document_type})"

    def _normalized_text(self, value):
        if not value:
            return ''
        ascii_text = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
        return re.sub(r'\s+', ' ', ascii_text).lower()

    def _collect_search_text(self):
        parts = []
        for value in [self.filename, self.source_path, self.document_type]:
            parts.append(self._normalized_text(value))

        payload = self.extracted_json or {}
        if isinstance(payload, dict):
            for part in payload.get('parts', []) or []:
                if isinstance(part, dict):
                    parts.append(self._normalized_text(part.get('title', '')))
                    content = part.get('content', [])
                    if isinstance(content, list):
                        for item in content:
                            parts.append(self._normalized_text(item))

        return ' '.join(part for part in parts if part)

    def resolve_governance_assignment(self):
        search_text = self._collect_search_text()

        if any(token in search_text for token in ['gouvernance', 'governance', 'redaction', 'drafting', 'normalisation', 'standardization', 'guide']):
            ctm = CTM.objects.filter(number=8).first()
            wg = WG.objects.filter(ctm=ctm, number=4).first() if ctm else None
            if ctm and wg:
                return ctm, wg

        if any(token in search_text for token in ['batiment', 'building', 'construction', 'urbanisme', 'genie civil', 'civil engineering', 'structure', 'ouvrages']):
            ctm = CTM.objects.filter(number=3).first()
            wg = WG.objects.filter(ctm=ctm, number=1).first() if ctm else None
            if ctm and wg:
                return ctm, wg

        ctm = CTM.objects.order_by('number').first()
        wg = WG.objects.filter(ctm=ctm).order_by('number').first() if ctm else None
        return ctm, wg

    def build_reference_number(self):
        if self.document_type == 'guide':
            return 'NORME-GUIDE-001'
        if self.document_type == 'liste_normes':
            return 'NORME-LISTE-001'
        return 'NORME-001'

    def ensure_norme(self):
        ctm, wg = self.resolve_governance_assignment()
        if not ctm or not wg:
            return None

        title = self.filename.rsplit('.', 1)[0]
        description = (
            self.extracted_json.get('summary')
            if isinstance(self.extracted_json, dict) and self.extracted_json.get('summary')
            else f"Document importé: {title}"
        )

        norme, created = Norme.objects.update_or_create(
            reference_number=self.build_reference_number(),
            defaults={
                'title': title,
                'description': description,
                'ctm': ctm,
                'wg': wg,
                'status': 'DRAFT',
                'standard_family': 'OTHER',
                'is_public': False,
            },
        )
        self.norme = norme
        self.save(update_fields=['norme', 'updated_at'])
        return norme


def parse_norme_structure(content):
    """
    Découpage léger du texte en sections, articles et annexes.
    Compatible avec le contenu brut actuel.
    """
    blocks = []
    current = None

    def flush():
        nonlocal current
        if current:
            current['content'] = '\n\n'.join(current['content']).strip()
            blocks.append(current)
            current = None

    for raw_line in (content or '').splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            if current and current['content'] and current['content'][-1] != '':
                current['content'].append('')
            continue

        lower = stripped.lower()
        if lower.startswith(('section ', 'chapitre ', 'partie ', 'annexe ')):
            flush()
            current = {
                'type': 'section' if not lower.startswith('annexe ') else 'annexe',
                'title': stripped,
                'content': [],
            }
            continue

        if current is None:
            current = {'type': 'section', 'title': 'Introduction', 'content': []}
        current['content'].append(stripped)

    flush()
    return blocks


def build_content_blocks(version):
    """
    Crée une liste de blocs structurés à partir du texte brut.
    Le parsing reste compatible avec les normes déjà rédigées en texte libre.
    """
    blocks = []
    for index, block in enumerate(parse_norme_structure(version.content), start=1):
        title = block.get('title', '')
        kind = 'ANNEXE' if block.get('type') == 'annexe' else 'SECTION'
        blocks.append(
            NormeContentBlock(
                version=version,
                kind=kind,
                title=title,
                body=block.get('content', ''),
                position=index,
                metadata={'source': 'auto-import', 'raw_type': block.get('type')},
            )
        )
    return blocks


def structured_content_summary(content):
    """Résumé lisible des blocs structurés du texte brut."""
    blocks = parse_norme_structure(content)
    return [
        {
            'type': block['type'],
            'title': block['title'],
            'characters': len(block['content']),
        }
        for block in blocks
    ]
