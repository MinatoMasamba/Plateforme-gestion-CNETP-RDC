from django.db import models
from apps.core.models import BaseModel, User
from apps.norms.models import Norme, NormeVersion
from apps.experts.models import Expert


class Amendement(BaseModel):
    """Proposition d'amendement à une norme"""
    norme = models.ForeignKey(Norme, on_delete=models.CASCADE, related_name='amendements')
    version = models.ForeignKey(
        NormeVersion,
        on_delete=models.CASCADE,
        related_name='amendements'
    )
    
    proposed_by = models.ForeignKey(
        Expert,
        on_delete=models.PROTECT,
        related_name='amendements_proposed'
    )
    
    title = models.CharField(max_length=300)
    description = models.TextField()
    
    # Localisation du changement
    section = models.CharField(max_length=100, help_text="Ex: '2.1.3'")
    old_text = models.TextField()
    proposed_text = models.TextField()
    
    justification = models.TextField(help_text="Raison de l'amendement")
    
    # Statut
    STATUS_CHOICES = [
        ('PROPOSED', 'Proposé'),
        ('UNDER_REVIEW', 'En révision'),
        ('ACCEPTED', 'Accepté'),
        ('REJECTED', 'Rejeté'),
        ('WITHDRAWN', 'Retiré'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROPOSED')
    
    # Metadata
    proposal_date = models.DateTimeField(auto_now_add=True)
    review_deadline = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Amendement"
        verbose_name_plural = "Amendements"
        ordering = ['-proposal_date']
        indexes = [
            models.Index(fields=['norme', 'status']),
            models.Index(fields=['status', 'proposal_date']),
        ]
    
    def __str__(self):
        return f"{self.norme.reference_number} - {self.title}"


class Vote(BaseModel):
    """Vote d'un expert sur un amendement"""
    amendement = models.ForeignKey(
        Amendement,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    
    voter = models.ForeignKey(
        Expert,
        on_delete=models.PROTECT,
        related_name='amendement_votes'
    )
    
    VOTE_CHOICES = [
        ('FOR', 'Pour'),
        ('AGAINST', 'Contre'),
        ('ABSTAIN', 'Abstention'),
    ]
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    
    justification = models.TextField(blank=True, help_text="Justification optionnelle")
    vote_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Vote Amendement"
        verbose_name_plural = "Votes Amendements"
        unique_together = ('amendement', 'voter')
        ordering = ['vote_date']
    
    def __str__(self):
        return f"{self.voter.user.get_full_name()} - {self.amendement.title} ({self.vote})"


class ResultatVote(BaseModel):
    """Résumé des résultats de vote pour un amendement"""
    amendement = models.OneToOneField(
        Amendement,
        on_delete=models.CASCADE,
        related_name='resultat_vote'
    )
    
    total_votes = models.PositiveIntegerField(default=0)
    votes_for = models.PositiveIntegerField(default=0)
    votes_against = models.PositiveIntegerField(default=0)
    votes_abstain = models.PositiveIntegerField(default=0)
    
    quorum_reached = models.BooleanField(default=False)
    approval_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Pourcentage d'approbation (Pour / Total)"
    )
    
    vote_closed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Résultat Vote"
        verbose_name_plural = "Résultats Votes"
    
    def __str__(self):
        return f"Résultat - {self.amendement.title}"
    
    def calculate_results(self):
        """Recalculer les résultats"""
        votes = self.amendement.votes.all()
        self.total_votes = votes.count()
        self.votes_for = votes.filter(vote='FOR').count()
        self.votes_against = votes.filter(vote='AGAINST').count()
        self.votes_abstain = votes.filter(vote='ABSTAIN').count()
        
        if self.total_votes > 0:
            self.approval_percentage = (self.votes_for / self.total_votes) * 100
        
        self.save()

