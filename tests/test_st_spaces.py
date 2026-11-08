import pytest
from types import SimpleNamespace
from django.utils import timezone

from apps.governance.models import CTCProcessus, MandatOrganisation, OrganisationVersion, PosteOrganisation
from apps.governance.st_matrix import POSTS, prepare_matrix
from apps.governance.st_spaces import SPACES, audit_scope_for, menu_for_post, space_context, space_for_post
from apps.governance.st_status import process_status
from apps.governance.st_workday import build_workday


@pytest.mark.django_db
def test_every_post_has_one_space_and_a_short_menu():
    version = prepare_matrix()
    posts = PosteOrganisation.objects.filter(organe__version=version).select_related('organe')
    assert posts.count() == 19
    for post in posts:
        space = space_for_post(post)
        assert space in SPACES
        menu = menu_for_post(post)
        assert 5 <= len(menu) <= 7, (post.code, len(menu))
        assert len({item['view'] for item in menu}) == len(menu)
        info = space_context(post, {'st_is_pole_head': post.category == 'POLE_HEAD'})
        assert info['st_space'] == space
        assert info['st_space_home'] == 'assistant_executif' if post.code == 'ST-V3-06' else info['st_space_home'] in {'coordination', 'espace_p1', 'espace_p2', 'espace_p3', 'espace_p4'}


@pytest.mark.django_db
def test_audit_matrix_has_no_uncontrolled_role():
    version = prepare_matrix()
    by_number = {post.code: post for post in PosteOrganisation.objects.filter(organe__version=version)}
    assert 'st' in audit_scope_for(by_number['ST-V3-01'])
    assert 'st' in audit_scope_for(by_number['ST-V3-13'])
    assert 'system' in audit_scope_for(by_number['ST-V3-18'])
    assert 'st' in audit_scope_for(by_number['ST-V3-17'])
    assert audit_scope_for(by_number['ST-V3-11']) == {'st_pole'}


@pytest.mark.django_db
def test_display_status_follows_existing_processus_without_rewriting_norm_status(norme_factory):
    norme = norme_factory()
    process = CTCProcessus.objects.create(norme=norme)
    assert process_status(process)['code'] == 'ENREGISTREE'
    process.received_at = timezone.now()
    process.save(update_fields=['received_at'])
    assert process_status(process)['code'] == 'REVUE_SC_ATTENTE'
    process.sc_report_received_at = timezone.now()
    process.save(update_fields=['sc_report_received_at'])
    assert process_status(process)['code'] == 'RAPPORT_RECU'
    process.indexed_at = timezone.now()
    process.save(update_fields=['indexed_at'])
    assert process_status(process)['code'] == 'INDEXATION_TERMINEE'
    process.intake_validated_at = timezone.now()
    process.current_stage = 'MULTI_REVIEW'
    process.save(update_fields=['intake_validated_at', 'current_stage'])
    assert process_status(process)['code'] == 'EXAMEN_EN_COURS'
    process.current_stage = 'SIGNED_OUT'
    process.save(update_fields=['current_stage'])
    assert process_status(process)['code'] == 'VALIDEE'
    # La norme n'a pas été renommée par la lecture du statut d'affichage.
    norme.refresh_from_db()
    assert norme.status == 'DRAFT'


@pytest.mark.django_db
def test_workday_is_built_from_real_data(expert_factory, user_factory, norme_factory):
    version = prepare_matrix()
    version.status = 'VALIDATED'
    version.save()
    post = PosteOrganisation.objects.get(code='ST-V3-01')
    expert = expert_factory(user=user_factory(username='coord-workday'))
    MandatOrganisation.objects.create(expert=expert, poste=post, function=post.title,
        appointment_reference='Communiqué 003', start_date=timezone.localdate(), status='ACTIVE')
    process = CTCProcessus.objects.create(norme=norme_factory())
    process.received_at = timezone.now()
    process.sc_report_received_at = timezone.now()
    process.indexed_at = timezone.now()
    process.save()
    from web.ctc_views import get_ctc_context
    context = get_ctc_context(expert)
    workday = build_workday(expert, context)
    assert set(workday['blocks']) == {'todo', 'waiting', 'deadlines', 'recent'}
    assert workday['counts']['todo'] >= 1
    assert context['st_space'] == 'ST'
    assert 5 <= len(context['st_space_menu']) <= 7


@pytest.mark.django_db
def test_pole_2_shell_renders_space_home_and_ptn(client, expert_factory, user_factory):
    version = prepare_matrix()
    version.status = 'VALIDATED'
    version.save()
    post = PosteOrganisation.objects.get(code='ST-V3-10')
    expert = expert_factory(user=user_factory(username='chef-p2'))
    MandatOrganisation.objects.create(expert=expert, poste=post, function=post.title,
        appointment_reference='Communiqué 003', start_date=timezone.localdate(), status='ACTIVE')
    client.force_login(expert.user)
    response = client.get('/ctc/')
    assert response.status_code == 200
    content = response.content.decode()
    assert response.context['st_space_home'] == 'espace_p2'
    assert 'id="view-coordination"' in content
    assert 'Mon travail du jour' in content
    assert 'Registre des paramètres techniques nationaux' in content
    assert 'Vue générale du pôle' in content
