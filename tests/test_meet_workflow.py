from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import AuditLog
from apps.experts.models import Structure
from apps.meetings.models import Presence, ProcessusVerbaux, ReunionParticipant
from tests.test_reunions_salle import _expert, _manager, _reunion


@pytest.mark.django_db
def test_meet_preparation_participation_and_pv_validation(user_factory, ctm_factory, wg_factory, monkeypatch):
    structure = Structure.objects.create(name='Meet recette', acronym='MET', category='ADMIN')
    manager, ctm, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
    invited = _expert(user_factory, 'meet_member', structure)
    validator = _expert(user_factory, 'meet_validator', structure)
    validator.user.is_ctc_staff = True
    validator.user.save()
    meeting = _reunion(wg, manager, mode='EXTERNE', date=timezone.now() + timedelta(minutes=5))
    for expert in (manager, invited):
        ReunionParticipant.objects.create(reunion=meeting, expert=expert)
    client = APIClient()
    base = f'/api/v1/mobile/expert/meetings/{meeting.pk}/'
    client.force_authenticate(manager.user)
    assert client.get('/api/v1/mobile/expert/meetings/capabilities/').data['can_plan'] is True
    payload = {'revision': 0, 'meet_link': 'https://meet.google.com/abc-defg-hij', 'ordre_jour': 'Examiner le projet', 'question_vote': 'Approuver le projet ?', 'documents': [{'title': 'Projet', 'url': 'https://example.org/projet.pdf'}]}
    assert client.put(base + 'preparation/', payload, format='json').status_code == 200
    assert client.put(base + 'preparation/', payload, format='json').status_code == 409
    client.force_authenticate(invited.user)
    rights = client.get(base + 'details/').data['capabilities']
    assert rights['can_manage'] is False and rights['can_validate_pv'] is False
    assert client.get('/api/v1/mobile/expert/meetings/capabilities/').data['can_plan'] is False
    assert client.put(base + 'preparation/', {**payload, 'revision': 1}, format='json').status_code == 403
    assert client.post(base + 'close/').status_code == 403
    assert client.put(base + 'pv_draft/', {}, format='json').status_code == 403
    assert client.post(base + 'checkin_presence/').status_code == 201
    assert client.post(base + 'vote/', {'choix': 'POUR'}).status_code == 201
    client.force_authenticate(manager.user)
    assert client.put(base + 'preparation/', {**payload, 'revision': 1, 'question_vote': 'Autre question ?'}, format='json').status_code == 409
    monkeypatch.setattr('api.v1.meetings.views.apply_presence_at_close', lambda _: pytest.fail('Une présence Meet ne peut pas être calculée à partir de LiveKit.'))
    closed = client.post(base + 'close/')
    assert closed.status_code == 201
    pv = ProcessusVerbaux.objects.get(reunion=meeting)
    assert pv.signature_date is None and pv.redaction != 'VALIDE'
    assert Presence.objects.get(reunion=meeting, expert=invited).status == 'PRESENT'
    client.force_authenticate(invited.user)
    assert client.post(f'/api/v1/pv/{pv.pk}/sign/', {'revision': 0}).status_code == 403
    client.force_authenticate(manager.user)
    draft = {'revision': 0, 'contenu': 'Compte rendu relu', 'points_discutes': 'Article 1', 'decisions': 'Révision de l’article 1', 'actions': [{'text': 'Mettre à jour le projet', 'responsible': 'Rapporteur', 'due_date': '2026-12-01'}]}
    assert client.put(base + 'pv_draft/', draft, format='json').status_code == 200
    assert client.put(base + 'pv_draft/', draft, format='json').status_code == 409
    assert client.post(base + 'generate_pv/').data['contenu'] == 'Compte rendu relu'
    assert client.post(f'/api/v1/pv/{pv.pk}/sign/', {'revision': 1}).status_code == 403
    client.force_authenticate(validator.user)
    assert client.post(f'/api/v1/pv/{pv.pk}/sign/', {'revision': 0}).status_code == 409
    signed = client.post(f'/api/v1/pv/{pv.pk}/sign/', {'revision': 1})
    assert signed.status_code == 200 and signed.data['redaction'] == 'VALIDE'
    client.force_authenticate(manager.user)
    assert client.put(base + 'pv_draft/', {**draft, 'revision': 2}, format='json').status_code == 409
    assert AuditLog.objects.filter(content_type='MeetingPV', object_id=pv.pk).count() == 2


@pytest.mark.django_db
def test_preparation_rejects_fake_meet_links(user_factory, ctm_factory, wg_factory):
    structure = Structure.objects.create(name='Liens Meet', acronym='LMT', category='ADMIN')
    manager, _, wg = _manager(user_factory, ctm_factory, wg_factory, structure)
    meeting = _reunion(wg, manager)
    client = APIClient()
    client.force_authenticate(manager.user)
    for link in ('https://meet.google.com.evil.test/abc', 'http://meet.google.com/abc', 'https://example.org/abc'):
        response = client.put(f'/api/v1/mobile/expert/meetings/{meeting.pk}/preparation/', {'revision': 0, 'meet_link': link, 'ordre_jour': '', 'question_vote': '', 'documents': []}, format='json')
        assert response.status_code == 400
