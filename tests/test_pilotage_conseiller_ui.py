import pytest

from apps.governance.models import ComitePilotage, PilotageMembreship, PosteNominatif


@pytest.mark.django_db
def test_generic_conseiller_sees_supervision_without_specialized_access(client, expert_factory):
    expert = expert_factory()
    comite = ComitePilotage.objects.create(name='Comité test conseiller')
    PilotageMembreship.objects.create(comite=comite, expert=expert, role='CONSEILLER')
    client.force_login(expert.user)

    response = client.get('/pilotage/')

    assert response.status_code == 200
    assert b'Espace du conseiller' in response.content
    assert len(response.context['sections']) == 8
    assert b'Coordination du Secr' in response.content
    assert b'Voir les chiffres et la m' in response.content
    assert b'href="/pilotage/conseillers/"' not in response.content


@pytest.mark.django_db
def test_institutional_conseiller_without_poste_has_no_fictitious_mission(client, expert_factory):
    expert = expert_factory()
    comite = ComitePilotage.objects.create(name='Comité test conseiller')
    PilotageMembreship.objects.create(comite=comite, expert=expert, role='CONSEILLER_POLITIQUE')
    client.force_login(expert.user)

    dashboard = client.get('/pilotage/')
    workspace = client.get('/pilotage/conseillers/')

    assert dashboard.status_code == 200
    assert b'href="/pilotage/conseillers/"' in dashboard.content
    assert workspace.status_code == 200
    assert workspace.context['my_poste'] is None
    assert b'Fonction nominative \xc3\xa0 confirmer' in workspace.content
    assert b'Conseiller \xe2\x80\x94 Cabinet du Ministre des ITP (1/2)' not in workspace.content


@pytest.mark.django_db
def test_nominated_conseiller_sees_only_his_poste(client, expert_factory):
    expert = expert_factory()
    comite = ComitePilotage.objects.create(name='Comité test conseiller')
    PilotageMembreship.objects.create(comite=comite, expert=expert, role='CONSEILLER_POLITIQUE')
    PosteNominatif.objects.create(
        comite=comite, holder=expert, role='CONSEILLER_POLITIQUE',
        title='Conseiller Cabinet test', order=7,
    )
    client.force_login(expert.user)

    response = client.get('/pilotage/conseillers/')

    assert response.status_code == 200
    assert response.context['my_poste']['n'] == 7
    assert response.context['default_post_n'] == 7
    assert b'data-section="post-7-phase1"' in response.content
    assert b'Fonction nominative \xc3\xa0 confirmer' not in response.content
