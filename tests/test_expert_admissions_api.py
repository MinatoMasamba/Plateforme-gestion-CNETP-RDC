"""Adhésions CTM : visibilité du bureau SC et mutations limitées à sa portée."""
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.governance.models import Affectation, Organe
from apps.governance.phoenix_models import MandatOrganisation, OrganisationVersion, PosteOrganisation

pytestmark = pytest.mark.django_db
BASE = '/api/v1/experts/'


def _pending(expert_factory, user_factory, ctm):
    expert = expert_factory(ctm=ctm, user=user_factory(username='candidate', email='candidate@example.test'))
    expert.status = 'PENDING'
    expert.save(update_fields=['status'])
    return expert


def _client(expert):
    client = APIClient()
    client.force_authenticate(expert.user)
    return client


@pytest.mark.parametrize('title', ['Président', '1e Vice-Président', 'Rapporteur', 'Secrétaire'])
def test_confirmed_sc_bureau_sees_pending_requests(title, expert_factory, user_factory, ctm_factory):
    leader = expert_factory()
    version = OrganisationVersion.objects.create(
        code='admissions-sc', name='Organisation', status='ACTIVE', source_document='Acte de test',
        activation_reference='ACT-1', gt_catalogue_reference='GT-1', permissions_reference='HAB-1', circuit_reference='CIR-1',
    )
    sc = Organe.objects.create(version=version, type='SC', code='SC-1', name='SC Qualité', status='ACTIVE', source_reference='Acte de test')
    post = PosteOrganisation.objects.create(organe=sc, code='SC-1-BUREAU', title=title, category='MEMBER', status='ACTIVE', source_reference='Nomination')
    mandate = MandatOrganisation.objects.create(expert=leader, poste=post, function=title, status='ACTIVE', capacity='ORGANISATION', start_date=timezone.localdate(), appointment_reference='NOM-1')
    ctm = ctm_factory(name='SC Qualité')
    pending = _pending(expert_factory, user_factory, ctm)
    client = _client(leader)
    assert client.get(BASE + 'pending-count-for-my-ctm/').data == {'count': 1, 'is_ctm_leader': True}
    assert [e['id'] for e in client.get(BASE + 'pending-for-my-ctm/').data] == [pending.pk]
    mandate.status = 'ENDED'
    mandate.save(update_fields=['status'])
    assert client.get(BASE + 'pending-count-for-my-ctm/').data == {'count': 0, 'is_ctm_leader': False}


def test_admission_requires_correct_wg_and_activates_once(expert_factory, user_factory, ctm_factory, wg_factory, monkeypatch):
    from apps.mobileapp.models import ActivationToken

    leader = expert_factory()
    ctm = ctm_factory(scientific_president=leader)
    wg = wg_factory(ctm=ctm)
    foreign = wg_factory(ctm=ctm_factory())
    candidate = _pending(expert_factory, user_factory, ctm)
    client = _client(leader)
    url = f'{BASE}{candidate.pk}/admit-to-ctm/'
    for group in (None, 'invalid', foreign.pk):
        assert client.post(url, {'ctm_id': ctm.pk, 'wg_id': group}, format='json').status_code == 400
        candidate.refresh_from_db()
        assert candidate.status == 'PENDING'
        assert not Affectation.objects.filter(expert=candidate).exists()
    tokens = []
    monkeypatch.setattr(ActivationToken, 'create_for_expert', lambda expert: tokens.append(expert.pk))
    assert client.post(url, {'ctm_id': ctm.pk, 'wg_id': wg.pk}, format='json').status_code == 200
    candidate.refresh_from_db()
    assert candidate.status == 'ACTIVE'
    assert candidate.accepted_by_id == leader.pk
    assert Affectation.objects.filter(expert=candidate, ctm=ctm, wg=wg).exists()
    assert tokens == [candidate.pk]
    assert client.post(url, {'ctm_id': ctm.pk, 'wg_id': wg.pk}, format='json').status_code == 400
    assert tokens == [candidate.pk]


def test_other_ctm_cannot_admit_or_reject(expert_factory, user_factory, ctm_factory, wg_factory):
    leader = expert_factory()
    ctm_factory(scientific_president=leader)
    other = ctm_factory()
    candidate = _pending(expert_factory, user_factory, other)
    wg = wg_factory(ctm=other)
    client = _client(leader)
    assert client.get(BASE + 'pending-for-my-ctm/').data == []
    assert client.post(f'{BASE}{candidate.pk}/admit-to-ctm/', {'ctm_id': other.pk, 'wg_id': wg.pk}, format='json').status_code == 403
    assert client.post(f'{BASE}{candidate.pk}/reject/', {'reason': 'Refus'}, format='json').status_code == 403
    candidate.refresh_from_db()
    assert candidate.status == 'PENDING'


def test_leader_rejection_records_reason(expert_factory, user_factory, ctm_factory):
    leader = expert_factory()
    ctm = ctm_factory(rapporteur=leader)
    candidate = _pending(expert_factory, user_factory, ctm)
    response = _client(leader).post(f'{BASE}{candidate.pk}/reject/', {'reason': 'Dossier incomplet'}, format='json')
    assert response.status_code == 200
    candidate.refresh_from_db()
    assert candidate.status == 'REJECTED'
    assert candidate.rejection_reason == 'Dossier incomplet'
    assert candidate.rejected_by_id == leader.pk
