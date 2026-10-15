"""Traçabilité CTC et supervision fondées sur les actions réellement persistées."""
import json

import pytest
from django.db import transaction
from django.test import RequestFactory
from django.utils import timezone

from apps.core.ctc_audit import CTCAuditMiddleware
from apps.core.models import AuditLog
from apps.documents.models import DocumentFile
from apps.governance.models import CTCMembership, CTCProcessus, TechnicalCell
from apps.governance.ctc_supervision import build_ctc_supervision
from apps.norms.models import NormeVersion


@pytest.fixture
def ctc_actor(expert_factory):
    expert = expert_factory()
    expert.user.is_ctc_staff = True
    expert.user.is_expert = True
    expert.user.save(update_fields=['is_ctc_staff', 'is_expert'])
    CTCMembership.objects.create(
        ctc=TechnicalCell.objects.create(), expert=expert, role='EXECUTIVE',
    )
    return expert


@pytest.mark.django_db
def test_real_reception_records_actor_time_origin_and_changed_fields(client, ctc_actor, norme_factory):
    process = CTCProcessus.objects.create(norme=norme_factory())
    client.force_login(ctc_actor.user)

    response = client.post(
        f'/ctc/dossiers/{process.pk}/reception/', {'action': 'receive'},
        REMOTE_ADDR='2001:db8::1', HTTP_X_FORWARDED_FOR='203.0.113.10',
        HTTP_USER_AGENT='Mozilla/5.0 Firefox/128.0 Linux',
    )

    assert response.status_code == 200
    log = AuditLog.objects.get(content_type='governance.CTCProcessus')
    assert log.user_id == ctc_actor.user_id
    assert log.ip_address == '2001:db8::1'
    assert log.changes['path'] == f'/ctc/dossiers/{process.pk}/reception/'
    assert log.changes['norme_id'] == process.norme_id
    assert log.changes['fields']['received_at']['before'] is None
    assert log.changes['fields']['received_at']['after']
    process.refresh_from_db()
    assert process.received_by_id == ctc_actor.pk
    supervision = build_ctc_supervision(RequestFactory().get('/pilotage/'))['ctc_supervision']
    assert supervision['event_count'] == 1  # La trace historique du même jalon est dédupliquée.
    assert supervision['page'][0]['label'] == 'Dossier réceptionné'


@pytest.mark.django_db
def test_refused_action_produces_no_success_activity(client, ctc_actor, norme_factory):
    process = CTCProcessus.objects.create(norme=norme_factory())
    client.force_login(ctc_actor.user)

    response = client.post(f'/ctc/dossiers/{process.pk}/reception/', {'action': 'validate_intake'})

    assert response.status_code == 403
    assert not AuditLog.objects.exists()


@pytest.mark.django_db
def test_api_version_creation_records_the_authenticated_user_and_redacts_content(client, ctc_actor, norme_factory):
    norme = norme_factory()
    CTCProcessus.objects.create(norme=norme)
    client.force_login(ctc_actor.user)
    confidential_text = 'Section 1 — texte de travail confidentiel'

    response = client.post(
        f'/api/v1/norms/{norme.pk}/create_version/',
        json.dumps({'title': 'Version revue', 'content': confidential_text, 'comment': 'Révision de la section 1'}),
        content_type='application/json', REMOTE_ADDR='192.0.2.8',
    )

    assert response.status_code == 201
    log = AuditLog.objects.get(content_type='norms.NormeVersion')
    assert log.user_id == ctc_actor.user_id
    assert log.changes['channel'] == 'API'
    assert confidential_text not in json.dumps(log.changes)
    assert log.changes['fields']['content']['after']['length'] == len(confidential_text)
    supervision = build_ctc_supervision(RequestFactory().get('/pilotage/'))['ctc_supervision']
    assert supervision['document_count'] == 1
    assert sum(event['document_event'] for event in supervision['page']) == 1


@pytest.mark.django_db
def test_document_update_is_logged_once_and_noop_is_ignored(ctc_actor, norme_factory):
    norme = norme_factory()
    CTCProcessus.objects.create(norme=norme)
    document = DocumentFile.objects.create(uploaded_by=ctc_actor.user, norme=norme, title='Annexe', file='documents/annexe.pdf')
    request = RequestFactory().patch('/api/v1/documents/1/', REMOTE_ADDR='192.0.2.9')
    request.user = ctc_actor.user

    def update(_request):
        document.title = 'Annexe corrigée'
        document.save(update_fields=['title'])
        document.save(update_fields=['title'])

    CTCAuditMiddleware(update)(request)

    log = AuditLog.objects.get()
    assert log.action == 'UPDATE'
    assert log.changes['document'] == 'annexe.pdf'
    assert log.changes['fields']['title'] == {'before': 'Annexe', 'after': 'Annexe corrigée', 'label': 'title'}
    assert log.changes['fields'].keys() == {'title'}


@pytest.mark.django_db
def test_deleted_document_remains_identifiable_in_supervision(client, ctc_actor, norme_factory):
    norme = norme_factory()
    CTCProcessus.objects.create(norme=norme)
    document = DocumentFile.objects.create(uploaded_by=ctc_actor.user, norme=norme, title='Annexe supprimée', file='documents/annexe.pdf')
    document_id = document.pk
    client.force_login(ctc_actor.user)

    response = client.delete(f'/api/v1/documents/{document_id}/')

    assert response.status_code == 204
    log = AuditLog.objects.get()
    assert log.action == 'DELETE'
    assert log.object_id == document_id
    assert log.changes['document'] == 'annexe.pdf'
    supervision = build_ctc_supervision(RequestFactory().get('/pilotage/'))['ctc_supervision']
    assert supervision['document_count'] == 1
    assert supervision['document_page'][0]['last_action'] == 'Document supprimé'


@pytest.mark.django_db
def test_rollback_discards_both_edit_and_audit(ctc_actor, norme_factory):
    norme = norme_factory()
    CTCProcessus.objects.create(norme=norme)
    request = RequestFactory().post('/ctc/test/')
    request.user = ctc_actor.user

    def rolled_back(_request):
        with transaction.atomic():
            norme.title = 'Modification annulée'
            norme.save(update_fields=['title'])
            assert AuditLog.objects.exists()
            transaction.set_rollback(True)

    CTCAuditMiddleware(rolled_back)(request)
    norme.refresh_from_db()
    assert norme.title != 'Modification annulée'
    assert not AuditLog.objects.exists()
    # Le contexte de requête est nettoyé, même après l'annulation.
    norme.title = 'Hors requête'
    norme.save(update_fields=['title'])
    assert not AuditLog.objects.exists()


@pytest.mark.django_db
def test_history_does_not_invent_the_indexing_actor_or_origin(ctc_actor, norme_factory):
    CTCProcessus.objects.create(
        norme=norme_factory(), indexed_at=timezone.now(), received_by=ctc_actor,
    )
    supervision = build_ctc_supervision(RequestFactory().get('/pilotage/'))['ctc_supervision']

    event = supervision['page'][0]
    assert event['user_id'] is None
    assert event['user_name'] == 'Auteur non enregistré'
    assert event['ip'] == ''
    assert supervision['captured_count'] == 0


@pytest.mark.django_db
def test_period_actor_document_filters_and_chart_totals(ctc_actor, norme_factory):
    norme = norme_factory(reference_number='NCD-SUPERVISION')
    CTCProcessus.objects.create(norme=norme)
    NormeVersion.objects.create(norme=norme, version_number=1, title='Annexe test', content='Texte', version_author=ctc_actor.user)
    NormeVersion.objects.create(norme=norme, version_number=2, title='Autre document', content='Texte', version_author=ctc_actor.user)
    request = RequestFactory().get('/pilotage/', {
        'ctc_user': str(ctc_actor.user_id), 'ctc_document': 'Annexe', 'ctc_action': 'edition',
    })

    context = build_ctc_supervision(request)

    assert context['ctc_supervision']['event_count'] == 1
    assert context['ctc_supervision']['document_count'] == 1
    assert sum(item['count'] for item in context['ctc_chart_data']['actions']) == 1
    assert sum(item['count'] for item in context['ctc_chart_data']['users']) == 1
    assert sum(item['count'] for item in context['ctc_chart_data']['timeline']) == 1


@pytest.mark.django_db
def test_invalid_period_is_handled_without_server_error():
    context = build_ctc_supervision(RequestFactory().get('/pilotage/', {
        'from': '2026-02-31', 'to': 'invalid', 'ctc_log_page': 'invalid',
    }))
    assert context['ctc_supervision']['event_count'] == 0
    assert len(context['ctc_chart_data']['timeline']) == 30
