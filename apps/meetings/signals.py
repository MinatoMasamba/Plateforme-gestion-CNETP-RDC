from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Reunion, ReunionParticipant
from .notifications import notify_participant


@receiver(post_save, sender=ReunionParticipant, dispatch_uid='meeting_invitation_notification')
def notify_invitation(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        notify_participant(instance, 'INVITED')


_DETAIL_FIELDS = ('date', 'titre', 'lieu', 'lien_reunion_virtuelle', 'ordre_jour',
                  'document_links', 'question_vote')


@receiver(pre_save, sender=Reunion, dispatch_uid='meeting_previous_notification_state')
def track_meeting(sender, instance, raw=False, **kwargs):
    instance._notification_before = (
        sender.objects.filter(pk=instance.pk).values('status', *_DETAIL_FIELDS).first()
        if instance.pk and not raw else None
    )


@receiver(post_save, sender=Reunion, dispatch_uid='meeting_change_notification')
def notify_meeting_change(sender, instance, created, raw=False, **kwargs):
    before = getattr(instance, '_notification_before', None)
    if raw or created or not before:
        return
    if instance.status == 'CANCELLED' and before['status'] != 'CANCELLED':
        event = 'CANCELLED'
    elif instance.status in ('PLANNED', 'IN_PROGRESS') and (
        before['status'] == 'CANCELLED'
        or any(before[field] != getattr(instance, field) for field in _DETAIL_FIELDS)
    ):
        event = 'UPDATED'
    else:
        return
    for participant in instance.participants.select_related('reunion', 'expert__user'):
        notify_participant(participant, event)
