"""Contrat mobile des demandes opérationnelles CTC."""

import json

import pytest

from apps.governance.models import CTCMembership, CTCOperationalRequest, PlatformFreeze, TechnicalCell, CTM, Demande


@pytest.fixture
def ctc_request_actors(expert_factory, user_factory):
    assistant = expert_factory(user=user_factory(username='ctc_assistant', email='assistant@test.cd'))
    other = expert_factory(user=user_factory(username='ctc_other', email='other@test.cd'))
    requester = expert_factory(user=user_factory(username='ctc_requester', email='requester@test.cd'))
    cell = TechnicalCell.objects.create()
    CTCMembership.objects.create(ctc=cell, expert=assistant, role='EXECUTIVE')
    CTCMembership.objects.create(ctc=cell, expert=other, role='IT_ADMIN')
    item = CTCOperationalRequest.objects.create(
        requester=requester,
        restricted_resource='Accès au dossier CTC',
        reason='Transmission urgente de la pièce.',
    )
    return assistant, other, item


@pytest.mark.django_db
def test_mobile_ctc_requests_are_visible_only_to_assistant(client, ctc_request_actors):
    assistant, other, item = ctc_request_actors
    client.force_login(other.user)
    response = client.get('/api/v1/mobile/ctc/requests/')
    assert response.status_code == 200
    assert response.json() == {'count': 0, 'results': []}

    client.force_login(assistant.user)
    response = client.get('/api/v1/mobile/ctc/requests/')
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['results'][0]['id'] == item.pk
    assert response.json()['results'][0]['reason'] == 'Transmission urgente de la pièce.'


@pytest.mark.django_db
def test_mobile_ctc_review_requires_assistant_and_rejects_stale_decision(client, ctc_request_actors):
    assistant, other, item = ctc_request_actors
    url = f'/api/v1/mobile/ctc/{item.pk}/review_request/'
    payload = json.dumps({'decision': 'APPROVED', 'comment': 'Pièce reçue.'})
    client.force_login(other.user)
    assert client.post(url, payload, content_type='application/json').status_code == 403
    item.refresh_from_db()
    assert item.status == 'PENDING'

    client.force_login(assistant.user)
    response = client.post(url, payload, content_type='application/json')
    assert response.status_code == 200
    item.refresh_from_db()
    assert item.status == 'APPROVED'
    assert item.reviewed_by_id == assistant.pk
    assert item.review_comment == 'Pièce reçue.'
    assert item.reviewed_at is not None
    assert client.post(url, payload, content_type='application/json').status_code == 409


@pytest.mark.django_db
def test_mobile_ctc_review_respects_platform_freeze(client, ctc_request_actors):
    assistant, _, item = ctc_request_actors
    freeze = PlatformFreeze.get_solo()
    freeze.is_locked = True
    freeze.save(update_fields=['is_locked'])
    client.force_login(assistant.user)
    response = client.post(
        f'/api/v1/mobile/ctc/{item.pk}/review_request/',
        json.dumps({'decision': 'REJECTED'}),
        content_type='application/json',
    )
    assert response.status_code == 423
    item.refresh_from_db()
    assert item.status == 'PENDING'


@pytest.mark.django_db
def test_mobile_ctc_read_only_directory_and_traceability(client, ctc_request_actors):
    assistant, other, _ = ctc_request_actors
    client.force_login(other.user)
    directory = client.get('/api/v1/mobile/ctc/experts/')
    assert directory.status_code == 200
    assert directory.json()['count'] >= 3
    assert 'affectation_label' in directory.json()['results'][0]
    assert 'email' not in directory.json()['results'][0]

    trace = client.get('/api/v1/mobile/ctc/tracabilite/')
    assert trace.status_code == 200
    assert isinstance(trace.json()['results'], list)

    client.force_login(assistant.user)
    assert client.get('/api/v1/mobile/ctc/experts/').status_code == 200


@pytest.mark.django_db
def test_mobile_ctc_instructions_use_registered_ctms_and_latest_specific_order(client, ctc_request_actors):
    assistant, _, _ = ctc_request_actors
    first = CTM.objects.create(number=1, name='Sols', description='')
    CTM.objects.create(number=2, name='Eau', description='')
    Demande.objects.create(type='INSTRUCTION', emetteur=assistant, objet='Directive générale', message='Préparer les dossiers.')
    Demande.objects.create(type='INSTRUCTION', emetteur=assistant, sous_commission=first,
                           objet='Directive sols', message='Vérifier les projets.')
    client.force_login(assistant.user)
    response = client.get('/api/v1/mobile/ctc/instructions/')
    assert response.status_code == 200
    payload = response.json()
    assert payload['general']['objet'] == 'Directive générale'
    assert [item['number'] for item in payload['ctms']] == [1, 2]
    assert payload['ctms'][0]['last_instruction']['objet'] == 'Directive sols'
    assert payload['ctms'][1]['last_instruction']['objet'] == 'Directive générale'


@pytest.mark.django_db
def test_mobile_ctc_norm_lists_follow_persisted_status(client, ctc_request_actors, norme_factory):
    assistant, _, _ = ctc_request_actors
    norme_factory(reference_number='H-1', status='HOMOLOGATED')
    norme_factory(reference_number='A-1', status='ARCHIVED')
    client.force_login(assistant.user)
    homologations = client.get('/api/v1/mobile/ctc/homologations/')
    archives = client.get('/api/v1/mobile/ctc/archives/')
    assert homologations.status_code == archives.status_code == 200
    assert [item['reference'] for item in homologations.json()['results']] == ['H-1']
    assert [item['reference'] for item in archives.json()['results']] == ['A-1']
