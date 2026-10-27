import pytest
from rest_framework.test import APIClient

from apps.governance.models import ComitePilotage, PermissionRequest, PilotageMembreship

pytestmark = pytest.mark.django_db
BASE = '/api/v1/mobile/pilotage/'


def member_client(expert_factory, role):
    expert = expert_factory()
    committee = ComitePilotage.objects.create(name='COPIL mobile')
    PilotageMembreship.objects.create(comite=committee, expert=expert, role=role)
    client = APIClient()
    client.force_authenticate(expert.user)
    return expert, client


def test_mobile_dashboard_exposes_real_pending_items(expert_factory, user_factory):
    _, client = member_client(expert_factory, 'SECRETARY')
    requester = expert_factory(user=user_factory(username='requester'))
    permission = PermissionRequest.objects.create(
        requester=requester, restricted_resource='Dossier réel', reason='Consultation',
    )
    response = client.get(BASE + 'dashboard/')
    assert response.status_code == 200
    assert response.data['permissions']['can_approve_requests'] is True
    assert permission.pk in [row['id'] for row in response.data['panels']['derogations']]
    assert response.data['pending']['derogations'] == len(response.data['panels']['derogations'])


def test_mobile_reply_uses_web_validation_and_persists(expert_factory, user_factory):
    _, client = member_client(expert_factory, 'SECRETARY')
    requester = expert_factory(user=user_factory(username='requester'))
    permission = PermissionRequest.objects.create(
        requester=requester, restricted_resource='Dossier', reason='Consultation',
    )
    payload = {'kind': 'derogation', 'id': permission.pk, 'decision': 'APPROVED', 'comment': ''}
    assert client.post(BASE + 'command/', payload, format='json').status_code == 400
    payload['comment'] = 'Accès approuvé pour consultation.'
    assert client.post(BASE + 'command/', payload, format='json').status_code == 200
    permission.refresh_from_db()
    assert permission.status == 'APPROVED'
    assert permission.review_comment == payload['comment']
    assert client.post(BASE + 'command/', payload, format='json').status_code == 409


def test_observer_cannot_execute_directoire_commands(expert_factory):
    _, client = member_client(expert_factory, 'CONSEILLER_POLITIQUE')
    assert client.post(BASE + 'command/', {'kind': 'adhesion', 'id': 1, 'action': 'activate'}, format='json').status_code == 403
    assert client.get(BASE + 'directoire/').status_code == 403


def test_non_member_and_anonymous_cannot_access_console(expert_factory):
    client = APIClient()
    assert client.get(BASE + 'dashboard/').status_code in (401, 403)
    client.force_authenticate(expert_factory().user)
    assert client.get(BASE + 'dashboard/').status_code == 403


def test_mobile_configuration_uses_web_form_and_audit(user_factory):
    from apps.governance.models import OrganisationVersion, JournalMigration
    admin = user_factory(is_staff=True, is_superuser=True)
    version = OrganisationVersion.objects.create(code='mobile-test', name='Organisation test', source_document='Acte de test')
    client = APIClient()
    client.force_authenticate(admin)
    url = BASE + f'configuration/version/?id={version.pk}'
    schema = client.get(url)
    assert schema.status_code == 200
    assert 'name' in [field['name'] for field in schema.data['fields']]
    invalid = client.post(url, {'name': '', 'source_document': ''}, format='json')
    assert invalid.status_code == 400
    assert 'name' in invalid.data['errors']
    response = client.post(url, {'name': 'Organisation corrigée', 'source_document': 'Acte officiel'}, format='json')
    assert response.status_code == 200
    version.refresh_from_db()
    assert version.name == 'Organisation corrigée'
    assert JournalMigration.objects.filter(version=version, actor=admin).exists()


def test_mobile_configuration_rejects_observer(expert_factory):
    _, client = member_client(expert_factory, 'CONSEILLER_POLITIQUE')
    assert client.get(BASE + 'configuration/poste/').status_code == 403
