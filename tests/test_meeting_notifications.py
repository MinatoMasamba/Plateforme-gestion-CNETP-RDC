from datetime import timedelta

import pytest
from django.db import transaction
from rest_framework.test import APIClient

from apps.experts.models import Structure
from apps.meetings.models import ReunionParticipant
from apps.mobileapp.models import Notification
from apps.mobileapp.tasks import dispatch_notification
from tests.test_reunions_salle import _expert, _manager, _reunion


@pytest.mark.django_db
def test_meeting_notifications_follow_explicit_invites_and_changes(user_factory, ctm_factory, wg_factory, django_capture_on_commit_callbacks, monkeypatch):
    structure = Structure.objects.create(name='Alertes réunions', acronym='ALR', category='ADMIN')
    manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
    invited = _expert(user_factory, 'alerts_invited', structure)
    outside = _expert(user_factory, 'alerts_outside', structure)
    sent = []
    monkeypatch.setattr('apps.mobileapp.tasks.dispatch_notification.delay', lambda pk: sent.append(pk))
    meeting = _reunion(wg, manager)
    assert not Notification.objects.filter(notification_type='REUNION_INVITE').exists()
    with django_capture_on_commit_callbacks(execute=True):
        with transaction.atomic():
            participant = ReunionParticipant.objects.create(reunion=meeting, expert=invited)
            assert not sent
    invite = Notification.objects.get(user=invited.user, notification_type='REUNION_INVITE')
    assert sent == [str(invite.pk)]
    ReunionParticipant.objects.get_or_create(reunion=meeting, expert=invited)
    meeting.save()
    assert Notification.objects.filter(user=invited.user).count() == 1
    meeting.date += timedelta(days=1)
    meeting.save()
    update = Notification.objects.get(user=invited.user, notification_type='REUNION_UPDATE')
    assert update.data['date'] == meeting.date.isoformat()
    assert dispatch_notification(str(invite.pk)) is False  # Ancien horaire non expédié.
    meeting.status = 'CANCELLED'
    meeting.save()
    meeting.save()
    assert Notification.objects.filter(notification_type='REUNION_CANCELLED').count() == 1
    assert dispatch_notification(str(update.pk)) is False
    assert not Notification.objects.filter(user=outside.user).exists()
    client = APIClient()
    client.force_authenticate(outside.user)
    assert client.get(f'/api/v1/mobile/notifications/{invite.pk}/').status_code == 404
    participant.delete()
    cancelled = Notification.objects.get(notification_type='REUNION_CANCELLED')
    assert dispatch_notification(str(cancelled.pk)) is False


@pytest.mark.django_db
def test_rolled_back_invite_does_not_notify(user_factory, ctm_factory, wg_factory, django_capture_on_commit_callbacks):
    structure = Structure.objects.create(name='Annulation transaction', acronym='ATR', category='ADMIN')
    manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
    meeting = _reunion(wg, manager)
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        with pytest.raises(ValueError), transaction.atomic():
            ReunionParticipant.objects.create(reunion=meeting, expert=manager)
            raise ValueError('Annuler la création')
    assert not callbacks
    assert not Notification.objects.filter(data__reunion_id=str(meeting.pk)).exists()
