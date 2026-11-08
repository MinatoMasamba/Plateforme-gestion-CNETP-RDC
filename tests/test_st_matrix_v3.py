import pytest
from django.utils import timezone
from apps.governance.st_matrix import prepare_matrix, POSTS, mandate_capabilities
from apps.governance.models import MandatOrganisation, OrganisationVersion, PosteOrganisation
from apps.governance.phoenix_runtime import current_organisation_version
from web.ctc_views import get_ctc_context


@pytest.mark.django_db
def test_preparation_preserves_current_version_and_is_idempotent():
    previous = OrganisationVersion.objects.create(code='previous', name='Previous', source_document='Source')
    version = prepare_matrix()
    assert current_organisation_version() == previous
    assert prepare_matrix().pk == version.pk
    assert PosteOrganisation.objects.filter(organe__version=version).count() == 19
    assert version.organes.count() == 5
    assert not MandatOrganisation.objects.filter(poste__organe__version=version).exists()
    assert version.journal.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize('number', range(1, 20))
def test_confirmed_post_controls_capabilities_independently_of_structure(expert_factory, number):
    version = prepare_matrix()
    # A validated version may be used in isolation for testing the runtime.
    version.status = 'VALIDATED'
    version.save()
    post = PosteOrganisation.objects.get(code=f'ST-V3-{number:02}')
    expert = expert_factory()
    mandate = MandatOrganisation.objects.create(expert=expert, poste=post,
        function=post.title, appointment_reference='Communiqué 003',
        start_date=timezone.localdate(), status='ACTIVE')
    context = get_ctc_context(expert)
    assert context['ctc_sub_role'] == POSTS[number - 1][3]
    assert context['ctc_pole'] == post.organe.code
    assert context['st_is_pole_head'] == POSTS[number - 1][-1]
    assert context['can_admin_system'] == (number in (17, 18))
    assert context['can_route_documents'] == (number <= 5)
    assert mandate_capabilities(mandate)['st_can_audit_st'] == (number in (13, 14))


@pytest.mark.django_db
def test_audit_separates_own_history_and_hides_other_perimeters(expert_factory, user_factory):
    from apps.core.models import AuditLog
    from web.ctc_experts import build_traceability
    version = prepare_matrix()
    version.status = 'VALIDATED'
    version.save()
    first, second = expert_factory(), expert_factory(user=user_factory(username='second', first_name='Second'))
    for number, expert in ((13, first), (14, second)):
        post = PosteOrganisation.objects.get(code=f'ST-V3-{number:02}')
        MandatOrganisation.objects.create(expert=expert, poste=post, function=post.title,
            appointment_reference='Communiqué 003', start_date=timezone.localdate(), status='ACTIVE')
    for expert, scope in ((first, 'st'), (second, 'st_pole'), (second, 'system')):
        AuditLog.objects.create(user=expert.user, action='UPDATE', content_type='Compte',
            object_id=1, object_repr='Objet', changes={'scope': scope})
    rows = build_traceability(first)
    cross = [row for row in rows if row['channel'] == 'Audit croisé']
    own = [row for row in rows if row['channel'] == 'Historique personnel']
    assert [row['actor'] for row in cross] == [second.user.get_full_name()]
    assert [row['actor'] for row in own] == [first.user.get_full_name()]
    assert all(row['actor'] != second.user.get_full_name() for row in own)
    assert len(rows) == 2


@pytest.mark.django_db
def test_report_is_required_before_v3_indexing(client, expert_factory, norme_factory, user_factory):
    from apps.governance.models import CTCProcessus
    version = prepare_matrix()
    version.status = 'VALIDATED'
    version.save()
    assistant = expert_factory()
    operator = expert_factory(user=user_factory(username='operator'))
    for number, expert in ((6, assistant), (11, operator)):
        post = PosteOrganisation.objects.get(code=f'ST-V3-{number:02}')
        MandatOrganisation.objects.create(expert=expert, poste=post, function=post.title,
            appointment_reference='Communiqué 003', start_date=timezone.localdate(), status='ACTIVE')
    process = CTCProcessus.objects.create(norme=norme_factory())
    process.mark_received(assistant)
    url = f'/ctc/dossiers/{process.pk}/reception/'
    client.force_login(operator.user)
    assert client.post(url, {'action': 'index'}).status_code == 400
    assert client.post(url, {'action': 'record_sc_report', 'reference': 'Rapport SC 1'}).status_code == 403
    client.force_login(assistant.user)
    assert client.post(url, {'action': 'record_sc_report', 'reference': 'Rapport SC 1'}).status_code == 200
    assert client.post(url, {'action': 'record_sc_report', 'reference': 'Rapport SC 2'}).status_code == 409
    client.force_login(operator.user)
    # Une référence seule ne remplace pas le rapport réel et la fiche GED.
    response=client.post(url, {'action': 'index'})
    assert response.status_code == 400
    assert 'espace GED' in response.json()['error']
    process.refresh_from_db()
    assert process.sc_report_received_by == assistant
    assert not process.indexed_at


@pytest.mark.django_db
def test_dashboard_contains_official_matrix(client, expert_factory):
    from apps.governance.models import CTCMembership, TechnicalCell
    expert = expert_factory()
    CTCMembership.objects.create(ctc=TechnicalCell.objects.create(name='ST'), expert=expert, role='EXECUTIVE')
    client.force_login(expert.user)
    response = client.get('/ctc/')
    assert response.status_code == 200
    assert len(response.context['st_matrix_rows']) == 19
    assert b'view-matrice_st' in response.content
    assert 'Emany LUWENGA MUANA' in response.content.decode()


@pytest.mark.django_db
def test_active_legacy_membership_is_fallback_without_v3_mandate(expert_factory):
    from apps.governance.models import CTCMembership, TechnicalCell
    version = prepare_matrix()
    version.status = 'VALIDATED'
    version.save()
    expert = expert_factory()
    CTCMembership.objects.create(ctc=TechnicalCell.objects.create(name='ST'), expert=expert, role='COORDINATOR')
    context = get_ctc_context(expert)
    assert context is not None
    assert context['ctc_sub_role'] == 'coordonnateur_principal'
    assert context['ctc_pole'] == 'direction'
    assert not context.get('st_matrix_v3')
