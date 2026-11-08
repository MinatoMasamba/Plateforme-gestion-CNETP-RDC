"""Régressions de la recette : postes distincts, objets et compteurs bornés."""
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.governance.models import CTCProcessus, MandatOrganisation, PosteOrganisation, Tache
from apps.governance.st_matrix import prepare_matrix, mandate_capabilities
from apps.governance.st_spaces import space_context, menu_for_post
from apps.governance.st_permissions import visible_tasks, visible_processus, visible_meetings
from apps.governance.st_workday import build_space_dashboard, build_workday
from apps.meetings.models import Reunion, ReunionParticipant


@pytest.fixture
def actors(user_factory, expert_factory):
    version = prepare_matrix()
    version.status = 'VALIDATED'
    version.save()

    def make(number):
        expert = expert_factory(user=user_factory(username=f'isolation-{number}', email=f'{number}@example.invalid'))
        post = PosteOrganisation.objects.select_related('organe').get(code=f'ST-V3-{number:02}')
        mandate = MandatOrganisation.objects.create(expert=expert, poste=post, function=post.title,
            status='ACTIVE', start_date=timezone.localdate(), appointment_reference='Recette interne')
        ctx = {**mandate_capabilities(mandate), **space_context(post), 'poste': post,
               'ctc_pole': post.organe.code}
        return expert, ctx
    return make


@pytest.mark.django_db
@pytest.mark.parametrize('number,required,forbidden', [
    (6, 'assistant_executif', 'delays'), (7, 'reunions', 'ctc_requests'),
    (9, 'alerts', 'exams'), (11, 'ged', 'ptn'), (12, 'ptn', 'indexation'),
    (15, 'financial', 'legal'), (16, 'financial', 'legal'),
    (18, 'accounts', 'communication'), (19, 'communication', 'accounts'),
])
def test_specialised_post_has_only_its_tools(actors, number, required, forbidden):
    _, ctx = actors(number)
    views = {item['view'] for item in menu_for_post(ctx['poste'])}
    assert required in views
    assert forbidden not in views
    assert forbidden not in ctx['st_allowed_views']
    assert 5 <= len(views) <= 7


@pytest.mark.django_db
def test_head_tasks_exclude_other_poles_and_future_mandates(actors):
    head, hc = actors(10)
    member, mc = actors(11)
    other, _ = actors(19)
    future, _ = actors(12)
    MandatOrganisation.objects.filter(expert=future).update(start_date=timezone.localdate()+timedelta(days=1))
    own = Tache.objects.create(titre='Tâche GED', assigned_to=member)
    Tache.objects.create(titre='Autre pôle', assigned_to=other)
    Tache.objects.create(titre='Mandat futur', assigned_to=future)
    assert list(visible_tasks(head, hc)) == [own]
    assert list(visible_tasks(member, mc)) == [own]
    assert build_space_dashboard(head, hc)['kpis']['tasks'] == 1
    workday = build_workday(member, mc)
    assert [item['title'] for item in workday['blocks']['todo']] == ['Tâche GED']


@pytest.mark.django_db
def test_meeting_counts_include_only_visible_meetings_and_all_rows(actors):
    member, ctx = actors(12)
    other, _ = actors(19)
    for i in range(7):
        meeting = Reunion.objects.create(titre=f'Invitation {i}', type='CTC',
            date=timezone.now()+timedelta(days=1), organisateur=other)
        ReunionParticipant.objects.create(reunion=meeting, expert=member)
    Reunion.objects.create(titre='Privée', type='CTC', date=timezone.now()+timedelta(days=1), organisateur=other)
    assert visible_meetings(member, ctx).count() == 7
    dashboard = build_space_dashboard(member, ctx)
    assert dashboard['kpis']['meetings'] == 7  # La liste est limitée à cinq, pas le total.
    assert len(dashboard['upcoming_meetings']) == 5


@pytest.mark.django_db
def test_ptn_member_cannot_read_unassigned_norm_from_web_or_api(actors, norme_factory, client):
    member, ctx = actors(12)
    process = CTCProcessus.objects.create(norme=norme_factory())
    assert not visible_processus(member, ctx).exists()
    client.force_login(member.user)
    assert client.get(f'/ctc/norme/{process.norme_id}/lecture/').status_code == 403
    assert client.get('/ctc/espace/indexation/').status_code == 403
    shell = client.get('/ctc/')
    assert shell.status_code == 200
    assert b'id="view-indexation"' not in shell.content
    assert b'id="view-ptn"' in shell.content
    payload = client.get('/api/v1/mobile/ctc/dossiers/').json()
    assert payload['count'] == 0


@pytest.mark.django_db
def test_upcoming_task_is_listed_in_weekly_deadlines(actors):
    member, ctx = actors(19)
    Tache.objects.create(titre='Communiqué de demain', assigned_to=member,
        due_date=timezone.localdate()+timedelta(days=1))
    workday = build_workday(member, ctx)
    assert any(item['title'] == 'Communiqué de demain' for item in workday['blocks']['deadlines'])


@pytest.mark.django_db
def test_final_decision_and_consolidation_cannot_skip_reviews(actors, norme_factory, client):
    coordinator, _ = actors(1)
    head, _ = actors(10)
    process = CTCProcessus.objects.create(norme=norme_factory(), received_at=timezone.now(),
        indexed_at=timezone.now(), sc_report_received_at=timezone.now(),
        intake_validated_at=timezone.now(), current_stage='MULTI_REVIEW')
    client.force_login(coordinator.user)
    response = client.post(f'/ctc/dossiers/{process.pk}/validation/', {'action':'validate','comment':'Trop tôt'})
    assert response.status_code == 400
    process.refresh_from_db()
    assert process.validated_at is None
    client.force_login(head.user)
    assert client.post(f'/ctc/dossiers/{process.pk}/consolidation/', {'comment':'Trop tôt'}).status_code == 400
    process.refresh_from_db()
    assert process.consolidation_completed_at is None


@pytest.mark.django_db
def test_logistics_can_create_st_meeting_without_pilotage_rights(actors, client):
    logistics, _ = actors(7)
    member, _ = actors(19)
    payload = {'type':'CTC','titre':'Réunion ST', 'mode':'PRESENTIEL',
               'date':(timezone.now()+timedelta(days=1)).isoformat(), 'lieu':'Recette'}
    client.force_login(logistics.user)
    assert client.post('/api/v1/reunions/', payload, content_type='application/json').status_code == 201
    assert client.post('/api/v1/reunions/', {**payload, 'type':'PILOTAGE'}, content_type='application/json').status_code == 403
    client.force_login(member.user)
    assert client.post('/api/v1/reunions/', payload, content_type='application/json').status_code == 403


@pytest.mark.django_db
def test_supervision_audit_includes_own_and_member_but_not_another_pole(actors):
    from apps.governance.st_operations import write_record
    from web.ctc_experts import build_traceability
    head, _ = actors(10)
    member, _ = actors(12)
    outsider, _ = actors(19)
    for actor, kind, reference in [(head, 'PTN', 'CHEF'), (member, 'PTN', 'MEMBRE'), (outsider, 'WORK', 'HORS-POLE')]:
        write_record(actor.user, dict(kind=kind, reference=reference, title=reference, source_reference='Recette'))
    references = {row['reference'] for row in build_traceability(head)}
    assert {'CHEF', 'MEMBRE'} <= references
    assert 'HORS-POLE' not in references


@pytest.mark.django_db
def test_head_cannot_independently_confirm_own_work(actors):
    from django.core.exceptions import PermissionDenied
    from apps.governance.st_operations import write_record, confirm_record
    head, _ = actors(10)
    record = write_record(head.user, dict(kind='PTN', reference='AUTO', title='Source', source_reference='Recette'))
    with pytest.raises(PermissionDenied, match='indépendant'):
        confirm_record(head.user, record.pk, 1, 'CONFIRMED', 'Ma propre saisie')
