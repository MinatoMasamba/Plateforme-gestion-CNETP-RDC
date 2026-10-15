from datetime import datetime, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.governance.activity_supervision import calculate_scope_metrics, record_heartbeat
from apps.governance.models import (
    ActivityAccessLog, ActivitySession, CTCMembership, JustifiedAbsence,
    OffPlatformWork, Tache, TechnicalCell, WorkExpectation,
)


pytestmark = pytest.mark.django_db


def coordinator(expert):
    cell = TechnicalCell.objects.create(name='Coordination test')
    CTCMembership.objects.create(ctc=cell, expert=expert, role='COORDINATOR')
    return cell


def test_task_defaults_are_explicit(wg_factory):
    task = Tache.objects.create(working_group=wg_factory(), titre='Préparer le projet')
    assert task.weight == 3
    assert task.priority == 'NORMAL'
    assert task.weight_source == 'DEFAULT'
    assert task.get_weight_source_display() == 'Valeur par défaut'


def test_indicators_keep_missing_values_distinct_from_zero(expert_factory, norme_factory):
    expert = expert_factory()
    norme = norme_factory()
    empty = calculate_scope_metrics(start=timezone.localdate() - timedelta(days=7), end=timezone.localdate(), wg=norme.wg)
    assert empty['production']['value'] is None
    assert empty['quality']['value'] is None
    assert empty['completeness']['value'] is None

    due = timezone.localdate() + timedelta(days=30)
    Tache.objects.create(working_group=norme.wg, norme=norme, titre='Tâche A', assigned_to=expert, due_date=due, weight=1, weight_source='MANUAL', progress=100, status='COMPLETED', review_status='ACCEPTED')
    Tache.objects.create(working_group=norme.wg, norme=norme, titre='Tâche B', assigned_to=expert, due_date=due, weight=3, weight_source='MANUAL', progress=0, review_status='NOT_REVIEWED')
    metrics = calculate_scope_metrics(start=timezone.localdate() - timedelta(days=7), end=timezone.localdate(), wg=norme.wg)
    assert metrics['production']['value'] == 25.0
    assert metrics['quality']['value'] == 100.0
    assert metrics['quality']['not_reviewed'] == 1
    assert metrics['completeness']['value'] == 100.0


def test_heartbeat_deduplicates_tabs_and_caps_network_gap(user_factory):
    user = user_factory()
    start = timezone.make_aware(datetime(2026, 10, 13, 10, 0, 0))
    first, credit = record_heartbeat(user=user, device_id='device-a', tab_id='tab-1', now=start)
    assert credit == 0
    second, credit = record_heartbeat(user=user, device_id='device-a', tab_id='tab-1', now=start + timedelta(seconds=60))
    assert second.pk == first.pk
    assert credit == 60
    same_bucket, credit = record_heartbeat(user=user, device_id='device-a', tab_id='tab-2', now=start + timedelta(seconds=60))
    assert same_bucket.pk == first.pk
    assert credit == 0
    resumed, credit = record_heartbeat(user=user, device_id='device-a', tab_id='tab-2', now=start + timedelta(minutes=8))
    assert resumed.pk == first.pk
    assert credit == 300
    resumed.refresh_from_db()
    assert resumed.active_seconds == 360


def test_engagement_counts_only_validated_work_and_prorates_absence(expert_factory):
    expert = expert_factory()
    monday = timezone.localdate()
    monday -= timedelta(days=monday.weekday())
    friday = monday + timedelta(days=4)
    WorkExpectation.objects.create(expert=expert, weekly_minutes=500, effective_from=monday)
    JustifiedAbsence.objects.create(expert=expert, starts_on=monday, ends_on=monday, reason='Mission', status='APPROVED')
    OffPlatformWork.objects.create(expert=expert, work_date=monday, minutes=100, reason='Réunion', status='APPROVED')
    OffPlatformWork.objects.create(expert=expert, work_date=monday, minutes=999, reason='En attente', status='PENDING')
    now = timezone.now()
    ActivitySession.objects.create(user=expert.user, device_id='d', started_at=now, last_seen_at=now, active_seconds=6000)
    metrics = calculate_scope_metrics(start=monday, end=friday, expert=expert)
    assert metrics['engagement']['objective_minutes'] == 400
    assert metrics['engagement']['declared_minutes'] == 100
    assert metrics['engagement']['observed_minutes'] == 100
    assert metrics['engagement']['value'] == 50.0


def test_access_matrix_and_detailed_access_log(client, expert_factory, user_factory):
    target = expert_factory(user=user_factory(username='target', email='target@example.cd'))
    lead = expert_factory(user=user_factory(username='lead', email='lead@example.cd'))
    coordinator(lead)
    client.force_login(lead.user)
    response = client.get(reverse('web:activity_expert', args=[target.pk]))
    assert response.status_code == 200
    assert ActivityAccessLog.objects.filter(viewer=lead.user, target_expert=target, detail_level='SUMMARY').exists()
    response = client.get(reverse('web:activity_expert', args=[target.pk]), {'details': 'techniques'})
    assert response.status_code == 200
    assert ActivityAccessLog.objects.filter(viewer=lead.user, target_expert=target, detail_level='SESSION_TECHNICAL').exists()

    outsider = expert_factory(user=user_factory(username='outsider', email='outsider@example.cd'))
    client.force_login(outsider.user)
    assert client.get(reverse('web:activity_dashboard')).status_code == 403


def test_kanban_rejects_forbidden_transition_without_change(client, expert_factory, wg_factory):
    lead = expert_factory()
    coordinator(lead)
    task = Tache.objects.create(working_group=wg_factory(), titre='Tâche verrouillée', status='PLANNED')
    client.force_login(lead.user)
    response = client.post(reverse('web:activity_task_transition', args=[task.pk]), {'status': 'COMPLETED'})
    assert response.status_code == 409
    task.refresh_from_db()
    assert task.status == 'PLANNED'


def test_global_interface_and_legacy_public_route(client, expert_factory):
    lead = expert_factory()
    coordinator(lead)
    client.force_login(lead.user)
    response = client.get(reverse('web:activity_dashboard'))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'Avancement' in body
    assert 'Production' in body
    assert 'Complétude' in body
    assert 'Sous-commissions' in body
    assert 'Phoenix' not in body
    assert reverse('web:phoenix_workspace') == '/pilotage/organisation/dossiers/'
    legacy = client.get('/phoenix/')
    assert legacy.status_code == 200
