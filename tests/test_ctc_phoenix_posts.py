import pytest
from django.utils import timezone

from apps.governance.models import (
    CTCMembership, MandatOrganisation, Organe, OrganisationVersion,
    PosteOrganisation, TechnicalCell,
)
from apps.governance.phoenix_runtime import active_st_mandate, st_posts
from web.ctc_views import get_ctc_context


def _organisation():
    version = OrganisationVersion.objects.create(
        code='ctc-matrice-2026', name='Organisation CNE-ITP', source_document='Décision',
    )
    st = Organe.objects.create(
        version=version, type='ST', code='ST', name='Secrétariat technique',
        status='VALIDATED', source_reference='Décision',
    )
    pole = Organe.objects.create(
        version=version, type='ST_POLE', code='ST-AD', name='Analyse documentaire',
        parent=st, status='VALIDATED', source_reference='Décision',
    )
    sc = Organe.objects.create(
        version=version, type='SC', code='SC-BAT', name='Bâtiment',
        status='VALIDATED', source_reference='Décision',
    )
    coord = PosteOrganisation.objects.create(
        organe=st, code='ST-COORD-01', category='COORDINATION',
        title='Coordonnateur — Directeur DRN', status='VALIDATED', source_reference='Décision',
    )
    pole_head = PosteOrganisation.objects.create(
        organe=pole, code='ST-AD-01', category='POLE_HEAD',
        title='Chef de pôle', status='VALIDATED', source_reference='Décision',
    )
    sc_post = PosteOrganisation.objects.create(
        organe=sc, code='SC-BAT-BUREAU-01', category='PRESIDENCY',
        title='Président', status='VALIDATED', source_reference='Décision',
    )
    return version, coord, pole_head, sc_post


@pytest.mark.django_db
def test_st_posts_contains_only_the_24_coordination_posts():
    _organisation()
    posts = list(st_posts())
    assert {(post.organe.type, post.code) for post in posts} == {
        ('ST', 'ST-COORD-01'), ('ST_POLE', 'ST-AD-01'),
    }


@pytest.mark.django_db
def test_ctc_context_uses_the_active_phoenix_st_mandate(expert_factory):
    _, coord, _, _ = _organisation()
    expert = expert_factory()
    TechnicalCell.objects.create(name='Coordination ST')
    CTCMembership.objects.create(
        ctc=TechnicalCell.objects.first(), expert=expert, role='COORDINATOR',
    )
    mandate = MandatOrganisation.objects.create(
        expert=expert, poste=coord, function=coord.title, capacity='ORGANISATION',
        appointment_reference='Arrêté 2026/01', start_date=timezone.localdate(), status='ACTIVE',
    )

    assert active_st_mandate(expert) == mandate
    context = get_ctc_context(expert)
    assert context['poste'] == coord
    assert context['poste'].title == 'Coordonnateur — Directeur DRN'


@pytest.mark.django_db
def test_admin_nomination_lists_only_phoenix_st_posts(client, user_factory):
    _, coord, pole_head, sc_post = _organisation()
    admin = user_factory(username='ctc-admin', is_staff=True, is_superuser=True)
    client.force_login(admin)

    response = client.get('/admin/governance/nominationctc/add/')
    content = response.content.decode()

    assert response.status_code == 200
    assert coord.code in content
    assert pole_head.code in content
    assert sc_post.code not in content
