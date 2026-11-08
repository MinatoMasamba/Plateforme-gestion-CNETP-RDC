from django.db import models
from django.contrib.postgres.fields import ArrayField
from apps.core.models import BaseModel
from apps.experts.models import Expert
from apps.governance.models import CTM, WG


class Reunion(BaseModel):
    """Modèle pour les réunions"""
    
    TYPE_CHOICES = [
        ('CTM', 'Comité Technique Miroir'),
        ('WG', 'Groupe de Travail'),
        ('PILOTAGE', 'Comité de Pilotage'),
        ('ASSEMBLEE', 'Assemblée Plénière'),
        ('CTC', 'Coordination du Secrétariat technique'),
    ]

    MODE_CHOICES = [
        ('PRESENTIEL', 'Présentiel'),
        ('EXTERNE', 'Lien externe'),
        ('SALLE', 'Salle de la plateforme'),
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
    ctm = models.ForeignKey(CTM, on_delete=models.SET_NULL, null=True, blank=True, related_name='reunions')
    wg = models.ForeignKey(WG, on_delete=models.SET_NULL, null=True, blank=True, related_name='reunions')
    document_reglementaire = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField()
    lieu = models.CharField(max_length=255, blank=True, null=True)
    lien_reunion_virtuelle = models.URLField(blank=True, null=True)
    mode = models.CharField(max_length=12, choices=MODE_CHOICES, default='PRESENTIEL')
    room_name = models.CharField(max_length=100, blank=True, unique=True, null=True)
    ouverture_salle = models.DateTimeField(null=True, blank=True)
    cloture_salle = models.DateTimeField(null=True, blank=True)
    enregistrement_actif = models.BooleanField(default=True)
    consentement_enregistrement = models.BooleanField(default=False)
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


class ReunionVote(BaseModel):
    """Vote électronique lié à une réunion."""

    CHOIX_CHOICES = [
        ('POUR', 'Pour'),
        ('CONTRE', 'Contre'),
        ('ABSTENTION', 'Abstention'),
    ]

    reunion = models.ForeignKey(Reunion, on_delete=models.CASCADE, related_name='votes')
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='reunion_votes')
    choix = models.CharField(max_length=20, choices=CHOIX_CHOICES)
    justification = models.TextField(blank=True)
    voted_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meetings_reunionvote'
        unique_together = ('reunion', 'expert')
        indexes = [
            models.Index(fields=['reunion', 'choix'], name='meetings_re_reunion_581dc1_idx'),
        ]

    def __str__(self):
        return f"{self.expert.user.get_full_name()} - {self.reunion.titre} - {self.choix}"


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

    REDACTION_CHOICES = [
        ('MANUEL', 'Rédaction manuelle'),
        ('BROUILLON_IA', 'Brouillon généré par IA'),
        ('VALIDE', 'Validé'),
    ]
    
    reunion = models.OneToOneField(Reunion, on_delete=models.CASCADE, related_name='pv')
    titre = models.CharField(max_length=255)
    contenu = models.TextField()
    nombre_presents = models.IntegerField(default=0)
    nombre_absents = models.IntegerField(default=0)
    quorum_atteint = models.BooleanField(default=False)
    redaction = models.CharField(max_length=14, choices=REDACTION_CHOICES, default='MANUEL')
    points_discutes = models.TextField(blank=True)
    decisions = models.TextField(blank=True)
    actions = models.JSONField(default=list, blank=True)
    valide_par = models.ForeignKey(
        Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='pv_valides'
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    signed_by = models.ForeignKey(Expert, on_delete=models.SET_NULL, null=True, blank=True, related_name='pv_signed')
    signature_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'meetings_processusvverbaux'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"PV - {self.reunion.titre}"


class ReunionParticipant(BaseModel):
    """Invitation à une réunion : source de vérité de l'accès à la salle."""

    ROLE_CHOICES = [
        ('PRESIDENT', 'Président'),
        ('RAPPORTEUR', 'Rapporteur'),
        ('SECRETAIRE', 'Secrétaire'),
        ('MEMBRE', 'Membre'),
        ('OBSERVATEUR', 'Observateur'),
    ]

    reunion = models.ForeignKey(Reunion, on_delete=models.CASCADE, related_name='participants')
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='reunion_invitations')
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default='MEMBRE')
    peut_parler = models.BooleanField(default=True)
    peut_video = models.BooleanField(default=False)
    invite_le = models.DateTimeField(auto_now_add=True)
    exclu_jusqua = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'meetings_reunionparticipant'
        unique_together = ('reunion', 'expert')
        ordering = ['role', 'expert__user__last_name']
        indexes = [
            models.Index(fields=['reunion', 'role'], name='meet_part_reu_role_idx'),
        ]

    def __str__(self):
        return f"{self.expert.user.get_full_name()} - {self.reunion.titre} ({self.get_role_display()})"


class PresenceSession(BaseModel):
    """Une connexion effective d'un expert à la salle de réunion."""

    LEFT_REASONS = [
        ('QUIT', 'Départ volontaire'),
        ('DISCONNECT', 'Déconnexion'),
        ('KICKED', 'Exclu'),
        ('ROOM_END', 'Fin de salle'),
        ('TIMEOUT', 'Délai dépassé'),
    ]

    reunion = models.ForeignKey(Reunion, on_delete=models.CASCADE, related_name='sessions')
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='sessions_reunion')
    livekit_sid = models.CharField(max_length=64, blank=True)
    joined_at = models.DateTimeField()
    left_at = models.DateTimeField(null=True, blank=True)
    left_reason = models.CharField(max_length=30, blank=True, choices=LEFT_REASONS)

    class Meta:
        db_table = 'meetings_presencesession'
        ordering = ['joined_at']
        indexes = [
            models.Index(fields=['reunion', 'expert', 'joined_at'], name='meet_sess_reu_exp_join_idx'),
        ]

    def __str__(self):
        return f"{self.expert.user.get_full_name()} - {self.joined_at:%Y-%m-%d %H:%M}"


class Enregistrement(BaseModel):
    """Fichier audio produit par le serveur média (egress)."""

    STATUT_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('ECHEC', 'Échec'),
        ('PURGE', 'Purgé'),
    ]

    reunion = models.ForeignKey(Reunion, on_delete=models.CASCADE, related_name='enregistrements')
    expert = models.ForeignKey(
        Expert, null=True, blank=True, on_delete=models.SET_NULL, related_name='enregistrements_reunion'
    )
    egress_id = models.CharField(max_length=64, blank=True)
    fichier = models.CharField(max_length=500)
    debut = models.DateTimeField()
    duree_secondes = models.PositiveIntegerField(default=0)
    statut = models.CharField(max_length=12, choices=STATUT_CHOICES, default='EN_COURS')

    class Meta:
        db_table = 'meetings_enregistrement'
        ordering = ['debut']
        indexes = [
            models.Index(fields=['reunion', 'statut'], name='meet_enr_reu_statut_idx'),
        ]

    def __str__(self):
        return f"Enregistrement {self.egress_id or self.pk} - {self.reunion.titre}"


class Transcription(BaseModel):
    """Transcription d'une réunion, produite de façon asynchrone."""

    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
        ('ECHEC', 'Échec'),
    ]

    reunion = models.OneToOneField(Reunion, on_delete=models.CASCADE, related_name='transcription')
    statut = models.CharField(max_length=12, choices=STATUT_CHOICES, default='EN_ATTENTE')
    langue = models.CharField(max_length=8, default='fr')
    modele = models.CharField(max_length=40, blank=True)
    erreur = models.TextField(blank=True)
    termine_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'meetings_transcription'
        ordering = ['-created_at']

    def __str__(self):
        return f"Transcription - {self.reunion.titre}"


class TranscriptSegment(BaseModel):
    """Segment horodaté d'une transcription, attribué à un locuteur."""

    transcription = models.ForeignKey(Transcription, on_delete=models.CASCADE, related_name='segments')
    expert = models.ForeignKey(Expert, null=True, blank=True, on_delete=models.SET_NULL)
    debut_s = models.FloatField()
    fin_s = models.FloatField()
    texte = models.TextField()
    confiance = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'meetings_transcriptsegment'
        ordering = ['debut_s']
        indexes = [
            models.Index(fields=['transcription', 'debut_s'], name='meet_seg_tra_debut_idx'),
        ]

    def __str__(self):
        return f"{self.debut_s:.1f}s - {self.texte[:60]}"


class ReglePresence(BaseModel):
    """Paramétrage métier des seuils et montants de jetons de présence."""

    type_reunion = models.CharField(max_length=20, choices=Reunion.TYPE_CHOICES, unique=True)
    seuil_presence_pct = models.PositiveSmallIntegerField()
    tolerance_coupure_s = models.PositiveSmallIntegerField(default=60)
    montant_jeton = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'meetings_reglepresence'
        ordering = ['type_reunion']

    def __str__(self):
        return f"{self.get_type_reunion_display()} - {self.seuil_presence_pct}% - {self.montant_jeton}"


class LiveKitWebhookEvent(BaseModel):
    """Trace des webhooks LiveKit pour garantir l'idempotence."""

    event_id = models.CharField(max_length=64, unique=True)
    event_type = models.CharField(max_length=60)
    room_name = models.CharField(max_length=100, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    traite_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'meetings_livekitwebhookevent'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at'], name='meet_wh_type_created_idx'),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.event_id}"
