import pytest
from rest_framework.test import APIClient

from apps.governance.models import Affectation


URL = '/api/v1/experts/my-affiliation/'
pytestmark = pytest.mark.django_db


def test_selection_replaces_affiliation_and_updates_norm_scope(
    expert_factory, ctm_factory, wg_factory, user_factory,
):
    from api.v1.permissions import user_ctm_scope

    old = ctm_factory(number=1)
    target = ctm_factory(number=2)
    wg = wg_factory(ctm=target)
    expert = expert_factory(ctm=old, user=user_factory(is_expert=True))
    Affectation.objects.create(expert=expert, ctm=old)
    other = expert_factory(ctm=old, user=user_factory(username='other', email='other@example.test'))
    client = APIClient()
    client.force_authenticate(expert.user)

    options = client.get(URL)
    assert options.status_code == 200
    assert target.pk in [item['id'] for item in options.data['ctms']]
    response = client.patch(URL, {'ctm': target.pk, 'wgs': [wg.pk]}, format='json')
    assert response.status_code == 200
    expert.refresh_from_db()
    other.refresh_from_db()
    assert expert.ctm_id == target.pk
    assert other.ctm_id == old.pk
    assert list(expert.governance_affectations.values_list('ctm_id', 'wg_id')) == [(target.pk, wg.pk)]
    assert user_ctm_scope(expert.user) == {target.pk}
    assert client.get(URL).data['wgs'] == [wg.pk]


@pytest.mark.parametrize('selection', ['foreign', 'missing', 'multiple'])
def test_invalid_selection_preserves_existing_affiliation(
    selection, expert_factory, ctm_factory, wg_factory,
):
    old = ctm_factory(number=1)
    target = ctm_factory(number=2)
    wg = wg_factory(ctm=target, number=1)
    second = wg_factory(ctm=target, number=2)
    foreign = wg_factory(ctm=old)
    expert = expert_factory(ctm=old)
    Affectation.objects.create(expert=expert, ctm=old, wg=foreign)
    client = APIClient()
    client.force_authenticate(expert.user)
    wgs = {'foreign': [foreign.pk], 'missing': [], 'multiple': [wg.pk, second.pk]}[selection]
    response = client.patch(URL, {'ctm': target.pk, 'wgs': wgs}, format='json')
    assert response.status_code == 400
    expert.refresh_from_db()
    assert expert.ctm_id == old.pk
    assert list(expert.governance_affectations.values_list('wg_id', flat=True)) == [foreign.pk]


def test_bureau_member_can_select_multiple_workgroups(expert_factory, ctm_factory, wg_factory):
    expert = expert_factory()
    ctm = ctm_factory(scientific_president=expert)
    first = wg_factory(ctm=ctm, number=1)
    second = wg_factory(ctm=ctm, number=2)
    client = APIClient()
    client.force_authenticate(expert.user)
    response = client.patch(URL, {'ctm': ctm.pk, 'wgs': [first.pk, second.pk]}, format='json')
    assert response.status_code == 200
    assert set(response.data['wgs']) == {first.pk, second.pk}


def test_anonymous_cannot_change_affiliation():
    assert APIClient().patch(URL, {'ctm': 1, 'wgs': []}, format='json').status_code in (401, 403)
