from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.experts.models import Structure
from apps.meetings.models import Presence, ReunionParticipant
from apps.meetings.tasks import send_meeting_reminders
from apps.mobileapp.models import Notification
from tests.test_reunions_salle import _expert, _manager, _reunion


@pytest.mark.django_db
def test_private_week_agenda_and_participation(user_factory, ctm_factory, wg_factory):
    structure = Structure.objects.create(name='Beta test', acronym='BETA', category='ADMIN')
    manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
    invited = _expert(user_factory, 'beta_invited', structure)
    outside = _expert(user_factory, 'beta_outside', structure)
    meeting = _reunion(wg, manager, mode='EXTERNE', lien_reunion_virtuelle='https://meet.google.com/abc-defg-hij')
    ReunionParticipant.objects.create(reunion=meeting, expert=invited)
    client = APIClient()
    client.force_authenticate(outside.user)
    for suffix in ('details/', 'calendrier/'):
        assert client.get(f'/api/v1/reunions/{meeting.pk}/{suffix}').status_code == 404
    for suffix in ('checkin_presence/', 'vote/', 'excuser/'):
        assert client.post(f'/api/v1/reunions/{meeting.pk}/{suffix}', {'choix': 'POUR'}).status_code == 404
    for path in ('presences', 'reunion-votes', 'pv'):
        response = client.get(f'/api/v1/{path}/')
        assert response.status_code == 200
        rows = response.data.get('results', []) if isinstance(response.data, dict) else response.data
        assert not rows
    client.force_authenticate(invited.user)
    agenda = client.get(f'/api/v1/reunions/{meeting.pk}/calendrier/')
    assert agenda.status_code == 200
    assert b'BEGIN:VCALENDAR' in agenda.content
    assert b'meet.google.com' in agenda.content
    assert agenda['Cache-Control'] == 'private, no-store'
    assert client.post('/api/v1/presences/', {'reunion': meeting.pk, 'expert': invited.pk, 'status': 'PRESENT'}).status_code == 403
    assert client.post(f'/api/v1/reunions/{meeting.pk}/excuser/').status_code == 200
    assert Presence.objects.get(reunion=meeting, expert=invited).status == 'EXCUSED'
    meeting.date = timezone.now() + timedelta(days=1)
    meeting.save()
    assert client.post(f'/api/v1/reunions/{meeting.pk}/checkin_presence/').status_code == 400
    meeting.date = timezone.now()
    meeting.save()
    assert client.post(f'/api/v1/reunions/{meeting.pk}/checkin_presence/').status_code == 200
    assert Presence.objects.filter(reunion=meeting, expert=invited, status='PRESENT').exists()
    assert client.post(f'/api/v1/reunions/{meeting.pk}/vote/', {'choix': 'POUR'}).status_code == 201
    meeting.status = 'CANCELLED'
    meeting.save()
    assert client.post(f'/api/v1/reunions/{meeting.pk}/vote/', {'choix': 'CONTRE'}).status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('hours', [1, 24])
def test_reminders_deduplicate_and_follow_current_schedule(user_factory, ctm_factory, wg_factory, hours):
    structure = Structure.objects.create(name='Rappels', acronym='RAP', category='ADMIN')
    manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
    meeting = _reunion(wg, manager, date=timezone.now() + timedelta(hours=hours, seconds=-10))
    ReunionParticipant.objects.create(reunion=meeting, expert=manager)
    assert send_meeting_reminders() == 1
    assert send_meeting_reminders() == 0
    meeting.date = timezone.now() + timedelta(days=3)
    meeting.save()
    assert send_meeting_reminders() == 0
    meeting.date = timezone.now() + timedelta(hours=24, seconds=-10)
    meeting.status = 'CANCELLED'
    meeting.save()
    assert send_meeting_reminders() == 0
    assert Notification.objects.filter(notification_type='MEETING_REMINDER').count() == 1


@pytest.mark.django_db
def test_resources_personal_scope_and_conflict(user_factory, ctm_factory, wg_factory):
    from apps.norms.models import Norme
    from apps.governance.models import Affectation
    structure = Structure.objects.create(name='Ressources', acronym='RES', category='ADMIN')
    manager, ctm, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
    other = _expert(user_factory, 'resource_other', structure)
    Affectation.objects.create(expert=other, ctm=ctm, wg=wg)
    norm = Norme.objects.create(title='Ressource de recette', reference_number='RES-001', description='Recette', ctm=ctm, wg=wg)
    client = APIClient()
    client.force_authenticate(manager.user)
    path = f'/api/v1/mobile/expert/norms/{norm.pk}/resources/'
    payload = {'revision': 0, 'data': {'drive': 'https://drive.google.com/test', 'references': []}}
    assert client.put(path, payload, format='json').status_code == 200
    assert client.put(path, payload, format='json').status_code == 409
    assert client.get(path).data['revision'] == 1
    client.force_authenticate(other.user)
    assert client.get(path).data['data'] == {}


@pytest.mark.django_db
def test_finance_scope_is_enforced_by_server(user_factory):
    from apps.payments.models import Cotisation
    own = Structure.objects.create(name='Propre structure', acronym='OWN', category='ADMIN')
    other = Structure.objects.create(name='Autre structure', acronym='OTH', category='ADMIN')
    expert = _expert(user_factory, 'finance_beta', own)
    cot = Cotisation.objects.create(structure=own, annee=2026, montant='100', due_date=timezone.now().date())
    hidden = Cotisation.objects.create(structure=other, annee=2026, montant='900', due_date=timezone.now().date())
    client = APIClient()
    client.force_authenticate(expert.user)
    assert client.get(f'/api/v1/cotisations/{hidden.pk}/').status_code == 404
    assert client.get(f'/api/v1/cotisations/{cot.pk}/').status_code == 200
    assert client.get('/api/v1/cotisations/dashboard/').data['total_cotisations'] == '100.00'
