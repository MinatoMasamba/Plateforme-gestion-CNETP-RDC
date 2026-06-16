from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.models import BaseModel


class AgentSession(BaseModel):
    """Une session de discussion avec l'agent IA, scopée par contexte d'usage."""

    SCOPE_CHOICES = [
        ('expert', 'Expert'),
        ('ctc', 'Cellule Technique de Coordination'),
        ('pilotage', 'Comité de Pilotage'),
    ]
    PROVIDER_CHOICES = [
        ('anthropic', 'Claude (Anthropic)'),
        ('gemini', 'Gemini (Google)'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ia_agent_sessions',
    )
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='anthropic')
    title = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Session Agent IA"
        verbose_name_plural = "Sessions Agent IA"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'scope']),
        ]

    def __str__(self):
        return f"Session {self.get_scope_display()} — {self.user} (#{self.pk})"


class AgentMessage(models.Model):
    """Un message échangé dans une session (utilisateur, assistant ou trace d'outil)."""

    ROLE_CHOICES = [
        ('user', 'Utilisateur'),
        ('assistant', 'Assistant'),
        ('tool', 'Outil'),
    ]

    session = models.ForeignKey(AgentSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField(blank=True)
    tool_name = models.CharField(max_length=100, blank=True)
    tool_input = models.JSONField(null=True, blank=True)
    tool_output = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Message Agent IA"
        verbose_name_plural = "Messages Agent IA"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_role_display()} — session #{self.session_id}"


class AgentArtifact(BaseModel):
    """Un élément produit par l'agent (demande, signalement, brouillon d'email, graphique...)."""

    ARTIFACT_TYPE_CHOICES = [
        ('WG_REQUEST', "Demande d'attribution WG"),
        ('NORM_OVERLAP', 'Chevauchement de normes'),
        ('EXTERNAL_PROPOSAL', 'Proposition référentiel externe'),
        ('EMAIL_DRAFT', "Brouillon d'email"),
        ('CHART', 'Graphique'),
    ]
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('APPROVED', 'Approuvé'),
        ('SENT', 'Envoyé'),
    ]

    session = models.ForeignKey(AgentSession, on_delete=models.CASCADE, related_name='artifacts')
    message = models.ForeignKey(
        AgentMessage, on_delete=models.SET_NULL, null=True, blank=True, related_name='artifacts',
    )
    artifact_type = models.CharField(max_length=20, choices=ARTIFACT_TYPE_CHOICES)
    title = models.CharField(max_length=300, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')

    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = "Artefact Agent IA"
        verbose_name_plural = "Artefacts Agent IA"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', 'artifact_type']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.get_artifact_type_display()} — {self.title or self.pk} ({self.status})"


class AgentScopeConfig(BaseModel):
    """Prompt et permissions IA par scope + rôle utilisateur — éditable dans l'admin."""

    SCOPE_CHOICES = AgentSession.SCOPE_CHOICES

    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    role_key = models.CharField(
        max_length=60,
        help_text="Clé unique du rôle (ex : pilotage_directoire, ctc_member, expert_active)",
    )
    label = models.CharField(max_length=200, help_text="Nom affiché dans l'admin")
    system_prompt_extra = models.TextField(
        blank=True,
        help_text="Instructions supplémentaires ajoutées au prompt de base pour ce rôle.",
    )
    allowed_tools = models.JSONField(
        null=True, blank=True,
        help_text=(
            "Liste des outils autorisés pour ce rôle (null = tous les outils du scope). "
            'Ex : ["get_chart_data", "list_ctm_norms"]'
        ),
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Configuration Agent IA — Rôle"
        verbose_name_plural = "Configurations Agent IA — Rôles"
        unique_together = [('scope', 'role_key')]
        ordering = ['scope', 'role_key']

    def __str__(self):
        return f"{self.get_scope_display()} / {self.label}"


class AgentPosteContext(BaseModel):
    """
    Contexte IA enrichi par poste/sous-rôle, stocké en base et éditable depuis l'admin.

    Chaque enregistrement correspond à un sous-rôle précis (ex: 'president',
    'rapporteur', 'coordonnateur_principal') et fournit au moteur de prompt :
    - l'intitulé officiel du poste
    - le résumé de mission
    - les outils IA disponibles
    - le niveau hiérarchique (1 = Président COPIL → 8 = Expert CTM/WG)

    Le lien optionnel vers PosteNominatif/PosteNominatifCTC permet d'enrichir
    le contexte avec les données relationnelles (titulaire, structure, quota).
    """

    ORGAN_CHOICES = [
        ('pilotage', 'Comité de Pilotage Stratégique'),
        ('ctc', 'Cellule Technique de Coordination'),
        ('expert', 'Expert CTM/WG'),
    ]

    HIERARCHY_CHOICES = [
        (1, 'Niveau 1 — Président du COPIL'),
        (2, 'Niveau 2 — Bureau Directoire (VP / Secrétaire / Rapporteur)'),
        (3, 'Niveau 3 — Conseillers Institutionnels'),
        (4, 'Niveau 4 — Administrateurs Techniques et Financiers'),
        (5, 'Niveau 5 — Partenaires Sectoriels et Société Civile'),
        (6, 'Niveau 6 — Direction de la CTC'),
        (7, 'Niveau 7 — Pôles et Bureau Numérique CTC'),
        (8, 'Niveau 8 — Expert CTM / WG'),
    ]

    organ = models.CharField(
        max_length=20, choices=ORGAN_CHOICES,
        help_text="Organe auquel appartient ce poste",
    )
    sub_role = models.CharField(
        max_length=60,
        help_text=(
            "Clé du sous-rôle issue du moteur de privilèges "
            "(ex: president, rapporteur, coordonnateur_principal, foner)"
        ),
    )
    hierarchy_level = models.PositiveSmallIntegerField(
        choices=HIERARCHY_CHOICES, default=8,
        help_text="Niveau hiérarchique du poste (1 = plus élevé)",
    )
    position_label = models.CharField(
        max_length=500,
        help_text="Intitulé officiel complet du poste, affiché dans le prompt IA",
    )
    mission_summary = models.TextField(
        blank=True,
        help_text="Résumé de la mission et des responsabilités, pour contextualiser l'IA",
    )
    tools_hint = models.TextField(
        blank=True,
        help_text="Description des outils IA disponibles et des capacités spécifiques à ce poste",
    )

    # Liens relationnels optionnels vers les postes nominatifs
    poste_pilotage = models.OneToOneField(
        'governance.PosteNominatif',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='agent_context',
        help_text="Poste nominatif Pilotage lié (pour enrichissement relationnel)",
    )
    poste_ctc = models.OneToOneField(
        'governance.PosteNominatifCTC',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='agent_context',
        help_text="Poste nominatif CTC lié (pour enrichissement relationnel)",
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Contexte IA — Poste"
        verbose_name_plural = "Contextes IA — Postes (27 Pilotage + 19 CTC)"
        unique_together = [('organ', 'sub_role')]
        ordering = ['organ', 'hierarchy_level', 'sub_role']

    def __str__(self):
        return f"[{self.get_organ_display()}] {self.position_label[:80]}"

    @property
    def holder_name(self):
        """Retourne le nom du titulaire via le lien relationnel (si disponible)."""
        if self.poste_pilotage_id and self.poste_pilotage.holder:
            return self.poste_pilotage.holder.full_name
        if self.poste_ctc_id and self.poste_ctc.holder:
            return self.poste_ctc.holder.full_name
        return None

    @property
    def holder_structure(self):
        """Retourne la structure du titulaire via le lien relationnel."""
        if self.poste_pilotage_id and self.poste_pilotage.holder:
            s = self.poste_pilotage.holder.structure
            return s.acronym if s else None
        if self.poste_ctc_id and self.poste_ctc.holder:
            s = self.poste_ctc.holder.structure
            return s.acronym if s else None
        return None
