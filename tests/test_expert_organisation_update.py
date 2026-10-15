import pytest
from django.urls import reverse

from apps.governance.models import (
    ChoixOrganisationExpert, GroupeCible, Organe, OrganisationVersion,
)


@pytest.fixture
def organisation():
    version = OrganisationVersion.objects.create(
        code='phoenix-test', name='Organisation test', status='VALIDATED',
        source_document='Décision test',
    )
    sc1 = Organe.objects.create(
        version=version, code='SC-1', name='Sous-commission 1', type='SC',
        status='VALIDATED', source_reference='Décision test',
    )
    sc2 = Organe.objects.create(
        version=version, code='SC-2', name='Sous-commission 2', type='SC',
        status='VALIDATED', source_reference='Décision test',
    )
    group = GroupeCible.objects.create(
        sc=sc2, code='GT-2', name='Groupe 2', activity='PRODUCTION',
        status='VALIDATED', source_reference='Catalogue test',
    )
    return sc1, sc2, group


@pytest.mark.django_db
def test_expert_can_classify_existing_group(client, expert_factory, wg_factory, organisation):
    expert = expert_factory()
    wg = wg_factory()
    client.force_login(expert.user)
    sc1, _, _ = organisation
    url = reverse('web:expert_organisation_update')
    response = client.post(url, {
        'first_name': 'Amina', 'last_name': 'Expert',
        'specialties': 'Géotechnique', 'sc': sc1.pk,
        'source_wg': wg.pk,
    })
    assert response.status_code == 302
    choice = ChoixOrganisationExpert.objects.get(expert=expert)
    assert choice.sc == sc1
    assert choice.source_wg == wg
    assert choice.status == 'REVIEW'
    expert.user.refresh_from_db()
    expert.refresh_from_db()
    assert expert.user.first_name == 'Amina'
    assert expert.specialties == 'Géotechnique'


@pytest.mark.django_db
def test_group_is_required_before_saving_profile(client, expert_factory, organisation):
    expert = expert_factory()
    client.force_login(expert.user)
    sc1, _, _ = organisation
    response = client.post(reverse('web:expert_organisation_update'), {
        'first_name': 'Amina', 'sc': sc1.pk,
    })
    assert response.status_code == 400
    assert not ChoixOrganisationExpert.objects.filter(expert=expert).exists()
    expert.user.refresh_from_db()
    assert expert.user.first_name != 'Amina'
