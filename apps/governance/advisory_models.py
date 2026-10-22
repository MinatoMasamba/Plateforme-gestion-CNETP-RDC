"""Demandes d'analyse du conseiller général, distinctes des ordres de production."""

from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.deconstruct import deconstructible

from apps.core.models import BaseModel


@deconstructible
class AdvisoryPrivateStorage(FileSystemStorage):
    """Storage outside MEDIA_ROOT; downloads are served through an authorized view."""

    def __init__(self):
        super().__init__(location=Path(settings.BASE_DIR) / 'private_advisory')


private_advisory_storage = AdvisoryPrivateStorage()


class ConsultationConseiller(models.Model):
    """Trace a counselor's access to technical or personal supervision details."""

    lecteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    rubrique = models.CharField(max_length=40)
    cible = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class DemandeAnalyse(BaseModel):
    class Circuit(models.TextChoices):
        DIRECTOIRE = 'DIRECTOIRE', 'Directoire vers conseiller'
        CTC = 'CTC', 'Conseiller vers coordination CTC'
        SC = 'SC', 'Conseiller vers bureau SC'

    class Statut(models.TextChoices):
        ENVOYEE = 'ENVOYEE', 'Envoyée'
        EN_COURS = 'EN_COURS', 'En cours'
        REPONDUE = 'REPONDUE', 'Répondue'
        CLOTUREE = 'CLOTUREE', 'Clôturée'

    emetteur = models.ForeignKey('experts.Expert', on_delete=models.PROTECT, related_name='analyses_emises')
    destinataire = models.ForeignKey('experts.Expert', on_delete=models.PROTECT, related_name='analyses_recues')
    circuit = models.CharField(max_length=20, choices=Circuit.choices)
    objet = models.CharField(max_length=250)
    contexte = models.TextField()
    echeance = models.DateField(null=True, blank=True)
    sc = models.ForeignKey('governance.Organe', on_delete=models.PROTECT, null=True, blank=True, related_name='analyses')
    norme = models.ForeignKey('norms.Norme', on_delete=models.PROTECT, null=True, blank=True, related_name='demandes_analyse')
    demande_source = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='sous_demandes')
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.ENVOYEE)
    repondue_le = models.DateTimeField(null=True, blank=True)
    cloturee_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['destinataire', 'statut'], name='analyse_recipient_state_idx')]

    def __str__(self):
        return self.objet


class JournalAnalyse(models.Model):
    class Action(models.TextChoices):
        ENVOI = 'ENVOI', 'Envoi'
        PRISE_EN_CHARGE = 'PRISE_EN_CHARGE', 'Prise en charge'
        REPONSE = 'REPONSE', 'Réponse'
        CLOTURE = 'CLOTURE', 'Clôture'

    demande = models.ForeignKey(DemandeAnalyse, on_delete=models.CASCADE, related_name='journal')
    acteur = models.ForeignKey('experts.Expert', on_delete=models.PROTECT)
    action = models.CharField(max_length=20, choices=Action.choices)
    texte = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'pk']


class PieceAnalyse(models.Model):
    journal = models.ForeignKey(JournalAnalyse, on_delete=models.CASCADE, related_name='pieces')
    fichier = models.FileField(storage=private_advisory_storage, upload_to='pieces/%Y/%m/')
    nom_original = models.CharField(max_length=255)
    taille = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class AvisConseiller(BaseModel):
    """Avis préparatoire d'un conseiller, distinct d'une validation du COPIL.

    Le conseiller peut rédiger puis transmettre une recommandation au circuit
    de décision. Aucune transition de ce modèle ne vaut validation, signature
    ou homologation d'une norme.
    """

    class Profil(models.TextChoices):
        EXPERTISE = 'EXPERTISE', 'Expertise technique'
        COORDINATION = 'COORDINATION', 'Coordination institutionnelle'
        CONFORMITE = 'CONFORMITE', 'Conformité et réglementation'
        CONTROLE = 'CONTROLE', 'Contrôle technique et financier'
        PARTENAIRES = 'PARTENAIRES', 'Partenaires et expertise'

    class Recommandation(models.TextChoices):
        FAVORABLE = 'FAVORABLE', 'Favorable'
        RESERVE = 'RESERVE', 'Favorable avec réserves'
        COMPLEMENT = 'COMPLEMENT', 'Complément demandé'
        DEFAVORABLE = 'DEFAVORABLE', 'Défavorable'

    class Statut(models.TextChoices):
        BROUILLON = 'BROUILLON', 'Brouillon'
        SOUMIS = 'SOUMIS', 'Transmis au circuit'

    norme = models.ForeignKey(
        'norms.Norme', on_delete=models.PROTECT, related_name='avis_conseillers',
    )
    auteur = models.ForeignKey(
        'experts.Expert', on_delete=models.PROTECT, related_name='avis_conseillers',
    )
    profil = models.CharField(max_length=20, choices=Profil.choices)
    objet = models.CharField(max_length=250)
    analyse = models.TextField()
    recommandation = models.CharField(max_length=20, choices=Recommandation.choices)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.BROUILLON)
    soumis_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['auteur', 'statut'], name='avis_auteur_statut_idx'),
            models.Index(fields=['norme', 'profil'], name='avis_norme_profil_idx'),
        ]
        verbose_name = 'Avis de conseiller'
        verbose_name_plural = 'Avis de conseillers'

    def __str__(self):
        return f'{self.objet} — {self.get_profil_display()}'
