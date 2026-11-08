"""Indicateurs tableau de bord GED poste 11 — contrôles ciblés."""
from datetime import timedelta
from django.utils import timezone
import pytest
from apps.governance import st_ged as service
from apps.governance.st_spaces import allowed_views_for_post


@pytest.mark.django_db
def test_sc_activity_idle_not_failure(monkeypatch):
    class FakeOrgane:
        def __init__(self, pk, code, name):
            self.pk = pk
            self.code = code
            self.name = name
            self.official_name = name

    class QS:
        def filter(self, **kwargs):
            return self

        def order_by(self, *args):
            return [FakeOrgane(1, 'SC-IT', 'Sous-commission IT')]

    monkeypatch.setattr(service, 'actor', lambda user, **kw: None)
    monkeypatch.setattr(service.Organe.objects, 'filter', lambda **kw: QS())

    class EmptyReceipts:
        def filter(self, **kwargs):
            return self

        def select_related(self, *args):
            return []

    from apps.governance import st_admin_models
    monkeypatch.setattr(st_admin_models.STReception.objects, 'filter', lambda **kw: EmptyReceipts())

    result = service.sc_activity(user=None, days=30)
    assert len(result['results']) == 1
    assert result['buckets'], 'La période doit produire au moins un intervalle.'
    assert len(result['buckets']) == 5
    row = result['results'][0]
    assert row['idle'] is True
    assert row['status'] == 'aucune'
    assert row['name'] == 'Sous-commission IT'
    assert row['overdue'] == 0
    assert row['series'] == [0] * len(result['buckets'])


@pytest.mark.django_db
def test_sc_activity_retard_from_vote_deadline(monkeypatch):
    class FakeOrgane:
        def __init__(self, pk, code, name):
            self.pk = pk
            self.code = code
            self.name = name
            self.official_name = name

    class FakeProcess:
        received_at = timezone.now() - timedelta(days=20)
        sc_report_received_at = None
        norme = type('N', (), {'reference_number': 'NCD 010', 'title': 'T'})()

    class FakeReceipt:
        sc_id = 1
        process_id = 5
        vote_date = timezone.localdate() - timedelta(days=20)
        process = FakeProcess()

    class QS:
        def filter(self, **kwargs):
            return self

        def order_by(self, *args):
            return [FakeOrgane(1, 'SC-IT', 'Sous-commission IT')]

    class ReceiptQS:
        def filter(self, **kwargs):
            return self

        def select_related(self, *args):
            return [FakeReceipt()]

    monkeypatch.setattr(service, 'actor', lambda user, **kw: None)
    monkeypatch.setattr(service.Organe.objects, 'filter', lambda **kw: QS())
    from apps.governance import st_admin_models
    monkeypatch.setattr(st_admin_models.STReception.objects, 'filter', lambda **kw: ReceiptQS())

    result = service.sc_activity(user=None, days=30)
    row = result['results'][0]
    assert row['idle'] is False
    assert row['overdue'] == 1
    assert row['status'] == 'retard'
    assert sum(row['series']) == 2
    assert len(row['series']) == len(result['buckets'])


def test_allowed_views_include_rapports_for_post_11(monkeypatch):
    class Poste:
        code = 'ST-V3-11'
        title = 'GED'
        organe = type('O', (), {'code': 'ST-P2'})()

    monkeypatch.setattr('apps.governance.st_spaces._post_number', lambda post: 11)
    monkeypatch.setattr('apps.governance.st_spaces.menu_for_post', lambda post: [
        {'view': 'espace_p2', 'label': 'TB', 'icon': 'x'},
        {'view': 'indexation', 'label': 'Idx', 'icon': 'x'},
    ])
    views = allowed_views_for_post(Poste())
    assert 'rapports' in views
    assert 'indexation' in views
    assert 'ged_activity' in views


def test_period_bounds_custom():
    start, end = service._period_bounds(days=30, date_from=timezone.localdate() - timedelta(days=10), date_to=timezone.localdate())
    assert (end - start).days == 10
