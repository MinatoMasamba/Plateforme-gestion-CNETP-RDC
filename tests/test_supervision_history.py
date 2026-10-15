import pytest
from django.test import RequestFactory

from apps.core.ctc_audit import CTCAuditMiddleware
from apps.core.models import AuditLog
from apps.governance.models import ComitePilotage, PilotageMembreship
from apps.norms.models import NormeVersion


@pytest.fixture
def supervisor(expert_factory):
    expert = expert_factory()
    membership = PilotageMembreship.objects.create(
        expert=expert, comite=ComitePilotage.objects.create(name='Historique'), role='PRESIDENT')
    return expert, membership


@pytest.mark.django_db
def test_version_history_shows_real_colored_text_and_escapes_html(client, supervisor, norme_factory):
    expert, _ = supervisor
    norme = norme_factory()
    NormeVersion.objects.create(norme=norme, version_number=1, content='Texte ancien', version_author=expert.user)
    latest = NormeVersion.objects.create(norme=norme, version_number=2, content='Texte nouveau <script>alert(1)</script>', version_author=expert.user)
    client.force_login(expert.user)
    response = client.get(f'/pilotage/norme/{norme.pk}/historique/', {'version_id': latest.pk})
    assert response.status_code == 200
    segments = response.context['diff_sections'][0]['segments']
    assert ''.join(s['text'] for s in segments if s['type'] != 'insert') == 'Texte ancien'
    assert ''.join(s['text'] for s in segments if s['type'] != 'delete') == latest.content
    html = response.content.decode()
    assert 'class="diff-delete">ancien' in html
    assert 'class="diff-insert">nouveau' in html
    assert '<script>alert(1)</script>' not in html
    assert 'name="v1"' in html and 'name="v2"' in html


@pytest.mark.django_db
def test_audit_history_preserves_the_text_at_the_time_of_edit(client, supervisor, norme_factory):
    expert, _ = supervisor
    norme = norme_factory(description='Texte précédent')
    request = RequestFactory().post(f'/api/v1/norms/{norme.pk}/')
    request.user = expert.user

    def update(_):
        norme.description = 'Texte modifié'
        norme.save(update_fields=['description'])

    CTCAuditMiddleware(update)(request)
    log = AuditLog.objects.get(content_type='norms.Norme')
    assert log.changes['scope'] == 'ctm'
    assert log.text_changes.get(field_name='description').old_text == 'Texte précédent'
    norme.description = 'Édition ultérieure'
    norme.save(update_fields=['description'])
    client.force_login(expert.user)
    response = client.get(f'/pilotage/activite/{log.pk}/historique/')
    assert response.status_code == 200
    segments = response.context['diff_sections'][0]['segments']
    assert ''.join(s['text'] for s in segments if s['type'] != 'delete') == 'Texte modifié'
    assert 'Édition ultérieure' not in response.content.decode()


@pytest.mark.django_db
def test_history_rejects_another_norm_version_and_partner(client, supervisor, norme_factory):
    expert, membership = supervisor
    norme = norme_factory()
    other = NormeVersion.objects.create(norme=norme_factory(), version_number=1, content='Autre dossier')
    client.force_login(expert.user)
    assert client.get(f'/pilotage/norme/{norme.pk}/historique/', {'version_id': other.pk}).status_code == 404
    membership.role = 'PARTENAIRE_SOC_CIV'
    membership.save(update_fields=['role'])
    assert client.get(f'/pilotage/norme/{norme.pk}/historique/').status_code == 403


@pytest.mark.django_db
def test_ctm_graphs_and_journal_are_scoped(client, supervisor, norme_factory, ctm_factory):
    expert, _ = supervisor
    norme = norme_factory(reference_number='CTM-LOCAL')
    NormeVersion.objects.create(norme=norme, version_number=1, content='Dossier local', version_author=expert.user)
    other = norme_factory(reference_number='CTM-OTHER')
    NormeVersion.objects.create(norme=other, version_number=1, content='Dossier autre', version_author=expert.user)
    empty = ctm_factory()
    client.force_login(expert.user)
    response = client.get(f'/pilotage/ctm/{norme.ctm.number}/')
    assert response.status_code == 200
    assert response.context['ctc_supervision']['is_ctm']
    assert response.context['ctc_supervision']['event_count'] == 1
    assert sum(item['count'] for item in response.context['ctc_chart_data']['stages']) == 1
    assert 'CTM-OTHER' not in response.content.decode()
    assert response.context['ctm_dossier_page'].paginator.count == 1
    response = client.get(f'/pilotage/ctm/{empty.number}/')
    assert response.context['ctc_supervision']['event_count'] == 0
    assert sum(item['count'] for item in response.context['ctc_chart_data']['stages']) == 0


@pytest.mark.django_db
def test_old_audit_with_deleted_actor_still_renders(client, supervisor):
    expert, _ = supervisor
    log = AuditLog.objects.create(user=None, action='UPDATE', content_type='norms.Norme', object_id=999,
                                 changes={'scope': 'ctm', 'fields': {}}, object_repr='Archive')
    client.force_login(expert.user)
    response = client.get(f'/pilotage/activite/{log.pk}/historique/')
    assert response.status_code == 200
    assert 'Auteur non enregistré' in response.content.decode()
