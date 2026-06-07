from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import NormeVote
from .tasks import trigger_ctm_meeting_if_majority


@receiver(post_save, sender=NormeVote)
def check_wg_vote_majority(sender, instance, created, **kwargs):
    """Déclenche la convocation CTM dès qu'un vote WG fait basculer la majorité."""
    if not created:
        return
    norme = instance.norme
    if norme.status not in ('DRAFT', 'INTERNAL_REVIEW'):
        return
    trigger_ctm_meeting_if_majority.delay(norme.id)
