from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.meetings.models import MeetingReminder, ReunionParticipant
from apps.mobileapp.models import Notification
from apps.mobileapp.tasks import dispatch_notification


@shared_task
def send_meeting_reminders():
    """Recalculer les échéances chaque minute : aucun envoi différé périmé."""
    now = timezone.now()
    count = 0
    for hours in (24, 1):
        invitations = ReunionParticipant.objects.filter(
            reunion__status='PLANNED',
            reunion__date__lte=now + timedelta(hours=hours),
            reunion__date__gt=now + timedelta(hours=hours, minutes=-10),
            expert__user__is_active=True,
        ).select_related('reunion', 'expert__user')
        for invitation in invitations:
            with transaction.atomic():
                # Verrouillage du parent : protège aussi l'absence de journal.
                invitation = ReunionParticipant.objects.select_for_update().select_related('reunion', 'expert__user').get(pk=invitation.pk)
                meeting = invitation.reunion
                if meeting.status != 'PLANNED' or MeetingReminder.objects.filter(
                    participant=invitation, scheduled_for=meeting.date, hours=hours,
                ).exists():
                    continue
                if meeting.presences.filter(expert=invitation.expert, status='EXCUSED').exists():
                    continue
                notification = Notification.objects.create(
                    user=invitation.expert.user, notification_type='MEETING_REMINDER',
                    title=f'Réunion dans {hours} h : {meeting.titre}'[:255],
                    body='Consultez votre réunion et ses documents dans votre espace Expert.',
                    priority='HIGH', data={'reunion_id': str(meeting.pk), 'date': meeting.date.isoformat(), 'route': '/expert?tab=3'},
                )
                MeetingReminder.objects.create(participant=invitation, scheduled_for=meeting.date, hours=hours, notification=notification)
                transaction.on_commit(lambda pk=str(notification.pk): dispatch_notification.delay(pk))
                count += 1
    return count
