"""Droits, chiffres et circuit d'analyse du conseiller général."""

from datetime import timedelta

import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.governance.models import (
    CTCMembership, ComitePilotage, DemandeAnalyse, PilotageMembreship,
    Tache, TechnicalCell,
)


pytestmark = pytest.mark.django_db


def _pilotage(expert, role):
    committee, _ = ComitePilotage.objects.get_or_create(name='Comité test supervision')
    PilotageMembreship.objects.create(comite=committee, expert=expert, role=role)


def test_eight_real_chart_sections_and_role_boundary(client, expert_factory, user_factory):
    adviser = expert_factory()
    _pilotage(adviser, 'CONSEILLER')
    Tache.objects.create(titre='Analyse norme A', assigned_to=adviser, status='COMPLETED',
                         completed_at=timezone.now(), due_date=timezone.localdate())
    client.force_login(adviser.user)
    response = client.get(reverse('web:pilotage_dashboard'))
    assert response.status_code == 200
    assert len(response.context['sections']) == 8
    assert all(section['charts'] for section in response.context['sections'])
    overview = response.context['sections'][0]['charts'][0]
    assert overview['sources'] == 1
    assert sum(overview['series'][0]['values']) == 1
    for name in ('conseiller_ctc_observation', 'conseiller_sc_observation'):
        assert client.get(reverse(f'web:{name}')).status_code == 200

    specialist = expert_factory(user=user_factory(username='specialist', email='specialist@example.test'))
    _pilotage(specialist, 'CONSEILLER_POLITIQUE')
    client.force_login(specialist.user)
    assert client.get(reverse('web:conseiller_dashboard')).status_code == 403
    assert client.get(reverse('web:conseiller_ctc_observation')).status_code == 403
    assert client.get(reverse('web:conseiller_sc_observation_data')).status_code == 403


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
def test_analysis_flow_notifications_and_private_attachment(client, expert_factory, user_factory,
                                                            django_capture_on_commit_callbacks):
    director = expert_factory()
    adviser = expert_factory(user=user_factory(username='adviser', email='adviser@example.test'))
    coordinator = expert_factory(user=user_factory(username='coordinator', email='coordinator@example.test'))
    outsider = expert_factory(user=user_factory(username='outsider', email='outsider@example.test'))
    _pilotage(director, 'PRESIDENT')
    _pilotage(adviser, 'CONSEILLER')
    CTCMembership.objects.create(ctc=TechnicalCell.objects.create(), expert=coordinator, role='COORDINATOR')

    client.force_login(director.user)
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(reverse('web:conseiller_analysis_create'), {
            'circuit': 'DIRECTOIRE', 'destinataire': adviser.pk,
            'objet': 'Analyse juridique', 'contexte': 'Étudier la conformité',
        })
    assert response.status_code == 302
    first = DemandeAnalyse.objects.get(objet='Analyse juridique')
    assert first.destinataire_id == adviser.pk
    assert len(mail.outbox) == 1
    assert adviser.user.notifications.filter(data__demande_analyse_id=first.pk).exists()

    client.force_login(adviser.user)
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(reverse('web:conseiller_analysis_create'), {
            'circuit': 'CTC', 'destinataire': coordinator.pk, 'demande_source': first.pk,
            'objet': 'Examen technique', 'contexte': 'Étudier les clauses',
        })
    assert response.status_code == 302
    second = DemandeAnalyse.objects.get(objet='Examen technique')
    assert second.demande_source_id == first.pk
    assert len(mail.outbox) == 2

    client.force_login(coordinator.user)
    uploaded = SimpleUploadedFile('reponse.pdf', b'%PDF-1.4\nTest', content_type='application/pdf')
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(reverse('web:conseiller_analysis_transition', args=[second.pk]), {
            'action': 'REPONDUE', 'texte': 'Avis transmis', 'pieces': uploaded,
        })
    assert response.status_code == 302
    second.refresh_from_db()
    assert second.statut == 'REPONDUE'
    assert len(mail.outbox) == 3
    piece = second.journal.get(action='REPONSE').pieces.get()
    assert client.get(reverse('web:conseiller_analysis_piece', args=[piece.pk])).status_code == 200

    client.force_login(outsider.user)
    assert client.get(reverse('web:conseiller_analysis_detail', args=[second.pk])).status_code == 404
    assert client.get(reverse('web:conseiller_analysis_piece', args=[piece.pk])).status_code == 403
    assert client.post(reverse('web:conseiller_analysis_transition', args=[second.pk]), {'action': 'CLOTUREE'}).status_code == 403

    client.force_login(adviser.user)
    assert client.post(reverse('web:conseiller_analysis_transition', args=[second.pk]), {'action': 'CLOTUREE'}).status_code == 302
    second.refresh_from_db()
    assert second.statut == 'CLOTUREE'
    assert second.cloturee_le >= second.repondue_le - timedelta(seconds=1)
