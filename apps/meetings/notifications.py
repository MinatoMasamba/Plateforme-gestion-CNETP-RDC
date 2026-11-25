"""Notifications de réunion réservées aux invitations explicites."""
from django.db import transaction
from django.utils import timezone

from apps.mobileapp.models import Notification


def notify_participant(participant, event):
    meeting = participant.reunion
    if not participant.expert.user.is_active:
        return
    if event != 'CANCELLED' and meeting.status not in ('PLANNED', 'IN_PROGRESS'):
        return
    titles = {
        'INVITED': ('REUNION_INVITE', 'Invitation à une réunion'),
        'UPDATED': ('REUNION_UPDATE', 'Réunion modifiée'),
        'CANCELLED': ('REUNION_CANCELLED', 'Réunion annulée'),
    }
    kind, title = titles[event]
    date = timezone.localtime(meeting.date).strftime('%d/%m/%Y à %H:%M')
    body = (
        f'La réunion « {meeting.titre} » du {date} est annulée.'
        if event == 'CANCELLED' else
        f'« {meeting.titre} » : {date}. Consultez les informations et les documents de la séance.'
    )
    notification = Notification.objects.create(
        user=participant.expert.user, notification_type=kind,
        title=f'{title} : {meeting.titre}'[:255], body=body, priority='HIGH',
        data={'reunion_id': str(meeting.pk), 'event': event,
              'date': meeting.date.isoformat(), 'route': '/expert?tab=3',
              'meeting_id': str(meeting.pk), 'meeting_title': meeting.titre,
              'meeting_type': meeting.get_type_display(),
              'meeting_mode': meeting.get_mode_display(),
              'meeting_lieu': meeting.lieu or '',
              'scheduled_date': date},
    )

    def dispatch():
        from apps.mobileapp.signals import _fire_task
        from apps.mobileapp.tasks import dispatch_notification
        _fire_task(dispatch_notification, str(notification.pk))

    transaction.on_commit(dispatch)
    return notification
