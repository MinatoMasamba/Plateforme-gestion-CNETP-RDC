"""Tests d'isolation par SC/CTM et du compteur d'activité (espace expert)."""
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.experts.models import Expert, Structure
from apps.governance.models import Affectation, Tache
from apps.governance.activity_models import ActivitySession
from apps.norms.models import NormeVersion


def _make_expert(user_factory, ctm, wg, username):
    user = user_factory(username=username, email=f'{username}@cnetp.cd')
    user.is_expert = True
    user.save(update_fields=['is_expert'])
    structure, _ = Structure.objects.get_or_create(
        name=f'Structure {username}', defaults={'acronym': 'ST', 'category': 'ADMIN'}
    )
    expert = Expert.objects.create(user=user, structure=structure, ctm=ctm, status='ACTIVE')
    Affectation.objects.create(expert=expert, ctm=ctm, wg=wg, is_primary_ctm=True, is_primary_wg=True)
    return user, expert


def _ids(payload):
    rows = payload['results'] if isinstance(payload, dict) and 'results' in payload else payload
    return {row['id'] for row in rows}


@pytest.mark.django_db
class TestNormScoping:
    def test_expert_sees_only_own_sc(self, user_factory, ctm_factory, wg_factory, norme_factory):
        ctm1 = ctm_factory()
        wg1 = wg_factory(ctm=ctm1)
        ctm2 = ctm_factory()
        wg2 = wg_factory(ctm=ctm2)
        mine = norme_factory(ctm=ctm1, wg=wg1)
        other = norme_factory(ctm=ctm2, wg=wg2)

        user, _ = _make_expert(user_factory, ctm1, wg1, 'scope1')
        client = APIClient()
        client.force_authenticate(user=user)

        resp = client.get('/api/v1/norms/')
        assert resp.status_code == 200
        listed = _ids(resp.data)
        assert mine.id in listed
        assert other.id not in listed

        assert client.get(f'/api/v1/norms/{mine.id}/').status_code == 200
        assert client.get(f'/api/v1/norms/{other.id}/').status_code == 404

    def test_expert_cannot_edit_other_sc_norm(self, user_factory, ctm_factory, wg_factory, norme_factory):
        ctm1 = ctm_factory()
        wg1 = wg_factory(ctm=ctm1)
        ctm2 = ctm_factory()
        wg2 = wg_factory(ctm=ctm2)
        other = norme_factory(ctm=ctm2, wg=wg2)

        user, _ = _make_expert(user_factory, ctm1, wg1, 'scope2')
        client = APIClient()
        client.force_authenticate(user=user)

        resp = client.patch(f'/api/v1/norms/{other.id}/', {'title': 'pirate'}, format='json')
        assert resp.status_code in (403, 404)


@pytest.mark.django_db
class TestExpertPII:
    def test_list_hides_banking_fields(self, user_factory, ctm_factory, wg_factory):
        ctm1 = ctm_factory()
        wg1 = wg_factory(ctm=ctm1)
        ctm2 = ctm_factory()
        wg2 = wg_factory(ctm=ctm2)
        _, _ = _make_expert(user_factory, ctm1, wg1, 'viewer')
        _, target = _make_expert(user_factory, ctm2, wg2, 'target')
        target.bank_account = 'SECRET-IBAN'
        target.save(update_fields=['bank_account'])

        viewer = Expert.objects.get(user__username='viewer').user
        client = APIClient()
        client.force_authenticate(user=viewer)

        resp = client.get('/api/v1/experts/')
        assert resp.status_code == 200
        rows = resp.data['results'] if isinstance(resp.data, dict) else resp.data
        for row in rows:
            assert 'bank_account' not in row
            assert 'bank_name' not in row
            assert 'mobile_money_number' not in row

    def test_peer_retrieve_hides_banking_fields(self, user_factory, ctm_factory, wg_factory):
        ctm1 = ctm_factory()
        wg1 = wg_factory(ctm=ctm1)
        ctm2 = ctm_factory()
        wg2 = wg_factory(ctm=ctm2)
        _, _ = _make_expert(user_factory, ctm1, wg1, 'viewer2')
        _, target = _make_expert(user_factory, ctm2, wg2, 'target2')
        target.bank_account = 'SECRET-IBAN'
        target.save(update_fields=['bank_account'])

        viewer = Expert.objects.get(user__username='viewer2').user
        client = APIClient()
        client.force_authenticate(user=viewer)

        resp = client.get(f'/api/v1/experts/{target.id}/')
        assert resp.status_code == 200
        assert 'bank_account' not in resp.data


@pytest.mark.django_db
class TestTaskScoping:
    def test_cross_sc_task_update_forbidden(self, user_factory, ctm_factory, wg_factory):
        ctm1 = ctm_factory()
        wg1 = wg_factory(ctm=ctm1)
        ctm2 = ctm_factory()
        wg2 = wg_factory(ctm=ctm2)
        task = Tache.objects.create(working_group=wg2, titre='Tâche autre SC')

        user, _ = _make_expert(user_factory, ctm1, wg1, 'tasker')
        client = APIClient()
        client.force_authenticate(user=user)

        resp = client.patch(f'/api/v1/tasks/tasks/{task.id}/', {'status': 'COMPLETED'}, format='json')
        assert resp.status_code == 403


@pytest.mark.django_db
class TestActivityCounter:
    def test_counter_reports_time_and_editions(self, user_factory, ctm_factory, wg_factory, norme_factory):
        ctm1 = ctm_factory()
        wg1 = wg_factory(ctm=ctm1)
        norme = norme_factory(ctm=ctm1, wg=wg1)
        user, _ = _make_expert(user_factory, ctm1, wg1, 'counter')
        NormeVersion.objects.create(
            norme=norme, version_number=1, title='v1', content='contenu', version_author=user,
        )
        ActivitySession.objects.create(
            user=user, device_id='dev-1', last_seen_at=timezone.now(), active_seconds=1800,
        )

        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get('/api/v1/activity/my-counter/')
        assert resp.status_code == 200
        assert resp.data['active_seconds_total'] == 1800
        assert resp.data['editions_total'] >= 1
        assert 'last_activity' in resp.data

    def test_counter_unknown_user(self, user_factory):
        user = user_factory(username='nocounter', email='nocounter@cnetp.cd')
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get('/api/v1/activity/my-counter/')
        assert resp.status_code == 200
        assert resp.data['active_seconds_total'] == 0
        assert resp.data['editions_total'] == 0
