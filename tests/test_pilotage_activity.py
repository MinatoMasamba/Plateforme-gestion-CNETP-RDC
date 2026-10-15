"""Suivi CTC du Pilotage : dossiers réels, pagination et droits de supervision."""
import pytest

from apps.governance.models import ComitePilotage, CTCProcessus, PilotageMembreship


@pytest.fixture
def pilotage_member(expert_factory):
    expert = expert_factory()
    committee = ComitePilotage.objects.create(name='Pilotage activité')
    membership = PilotageMembreship.objects.create(
        comite=committee, expert=expert, role='PRESIDENT',
    )
    return expert, membership


@pytest.mark.django_db
@pytest.mark.parametrize('role', ['PRESIDENT', 'CONSEILLER_POLITIQUE', 'ADMIN_TECH_FIN'])
def test_supervision_shows_real_ctc_stages(client, pilotage_member, norme_factory, role):
    expert, membership = pilotage_member
    membership.role = role
    membership.save(update_fields=['role'])
    reception = CTCProcessus.objects.create(norme=norme_factory())
    transmitted = CTCProcessus.objects.create(
        norme=norme_factory(), current_stage='SIGNED_OUT',
    )
    client.force_login(expert.user)

    response = client.get('/pilotage/')

    assert response.status_code == 200
    assert [stage['count'] for stage in response.context['ctc_activity_stages']] == [1, 0, 0, 0, 1]
    assert {p.pk for p in response.context['ctc_activity_page']} == {reception.pk, transmitted.pk}
    assert reception.norme.reference_number in response.content.decode()
    reception.refresh_from_db()
    assert reception.current_stage == 'RECEPTION'


@pytest.mark.django_db
def test_ctc_activity_is_not_exposed_without_supervision(client, pilotage_member, norme_factory):
    expert, membership = pilotage_member
    membership.role = 'PARTENAIRE_SOC_CIV'
    membership.save(update_fields=['role'])
    norme = norme_factory(reference_number='CTC-RESTRICTED-ACTIVITY')
    CTCProcessus.objects.create(norme=norme)
    client.force_login(expert.user)

    response = client.get('/pilotage/')

    assert response.status_code == 200
    assert response.context['ctc_activity_page'] is None
    assert response.context['ctc_activity_stages'] == []
    assert norme.reference_number not in response.content.decode()
    assert 'href="/pilotage/#panel-ctc"' not in response.content.decode()


@pytest.mark.django_db
def test_ctc_activity_pagination_keeps_stage_totals(client, pilotage_member, norme_factory, wg_factory):
    expert, _ = pilotage_member
    wg = wg_factory()
    for index in range(26):
        CTCProcessus.objects.create(
            norme=norme_factory(ctm=wg.ctm, wg=wg, reference_number=f'CTC-PAGE-{index}'),
        )
    client.force_login(expert.user)

    response = client.get('/pilotage/', {'ctc_page': '2'})

    assert response.status_code == 200
    page = response.context['ctc_activity_page']
    assert page.number == 2
    assert len(page.object_list) == 1
    assert page.paginator.count == 26
    assert response.context['ctc_activity_stages'][0]['count'] == 26
    assert 'ctc_page=1#panel-ctc' in response.content.decode()
