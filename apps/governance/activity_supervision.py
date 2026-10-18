"""Calculs et règles serveur pour la supervision des sous-commissions."""
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.utils import timezone

from apps.core.models import AuditLog
from apps.experts.models import Expert
from apps.norms.models import Norme
from .models import (
    ActivityAccessLog, ActivityAggregate, ActivityDispute, ActivityPulse,
    ActivitySession, BusinessCalendarDay, CTCMembership, CTM,
    JustifiedAbsence, OffPlatformWork, Organe, PilotageMembreship, Tache, WG,
    WorkExpectation,
)
from .phoenix_runtime import current_organisation_version

KINSHASA_TZ = timezone.get_fixed_timezone(60)
LEAD_ACTIVITY_ROLES = {'COORDINATOR', 'VICE_COORDINATOR', 'PLANNER'}


def expert_for(user):
    if not getattr(user, 'is_authenticated', False):
        return None
    return Expert.objects.filter(user=user).select_related('user', 'structure').first()


def activity_access_for(user):
    """Matrice d'accès explicite, indépendante du statut administratif Expert."""
    expert = expert_for(user)
    roles = set()
    if expert:
        roles = set(CTCMembership.objects.filter(expert=expert).values_list('role', flat=True))
    ctc_member = bool(roles)
    ctc_lead = bool(roles & LEAD_ACTIVITY_ROLES)
    direction = bool(expert and PilotageMembreship.objects.filter(expert=expert).exists())
    superuser = bool(getattr(user, 'is_superuser', False))
    dispute_qs = ActivityDispute.objects.filter(status='PENDING')
    if expert:
        dispute_qs = dispute_qs.filter(expert=expert)
    return {
        'expert': expert,
        'roles': roles,
        'can_view_aggregates': superuser or ctc_member or direction or user.has_perm('governance.view_activity_aggregates'),
        'can_view_contributions': superuser or ctc_lead or user.has_perm('governance.view_activity_contributions'),
        'can_view_session_details': superuser or ctc_lead or user.has_perm('governance.view_activity_session_details'),
        'can_manage_targets': superuser or ctc_lead or user.has_perm('governance.manage_activity_targets'),
        'can_review_declarations': superuser or ctc_lead or user.has_perm('governance.review_activity_declarations'),
        'can_review_disputes': superuser or ctc_lead or user.has_perm('governance.review_activity_disputes'),
        'is_direction_summary': direction and not ctc_lead,
    }


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')) or None


def log_sensitive_access(request, target_expert, purpose='Consultation de la fiche détaillée', detail_level='SUMMARY'):
    return ActivityAccessLog.objects.create(
        viewer=request.user,
        target_expert=target_expert,
        detail_level=detail_level,
        purpose=purpose[:300],
        ip_address=_client_ip(request),
    )


def _validate_scope(user, ctm_id=None, working_group_id=None, target_group_id=None, norme_id=None):
    """Ne conserve que des rattachements existants et cohérents entre eux."""
    result = {'ctm': None, 'working_group': None, 'target_group': None, 'norme': None}
    if working_group_id:
        wg = WG.objects.filter(pk=working_group_id).select_related('ctm').first()
        if wg:
            result['working_group'], result['ctm'] = wg, wg.ctm
    elif ctm_id:
        result['ctm'] = CTM.objects.filter(pk=ctm_id).first()
    if target_group_id:
        result['target_group'] = __import__('apps.governance.models', fromlist=['GroupeCible']).GroupeCible.objects.filter(pk=target_group_id).first()
    if norme_id:
        norme = Norme.all_objects.filter(pk=norme_id).first()
        if norme:
            if result['working_group'] and norme.wg_id != result['working_group'].pk:
                norme = None
            elif result['ctm'] and norme.ctm_id and norme.ctm_id != result['ctm'].pk:
                norme = None
        result['norme'] = norme
    return result


@transaction.atomic
def record_heartbeat(*, user, device_id, tab_id='', visible=True, interacted=False,
                     timezone_name='', current_path='', ctm_id=None,
                     working_group_id=None, target_group_id=None, norme_id=None,
                     now=None, ip_address=None, user_agent=''):
    """Enregistre un battement visible sans capturer le contenu consulté ou saisi."""
    now = now or timezone.now()
    device_id = (device_id or '')[:96].strip()
    if not device_id:
        raise ValueError("L'identifiant local de l'appareil est requis.")
    resume_after = now - timedelta(minutes=10)
    session = (
        ActivitySession.objects.select_for_update()
        .filter(user=user, device_id=device_id, state=ActivitySession.State.OPEN, last_seen_at__gte=resume_after)
        .order_by('-last_seen_at').first()
    )
    scope = _validate_scope(user, ctm_id, working_group_id, target_group_id, norme_id)
    if session is None:
        session = ActivitySession.objects.create(
            user=user, device_id=device_id, tab_id=(tab_id or '')[:96],
            last_seen_at=now, ip_address=ip_address, user_agent=(user_agent or '')[:2000],
            timezone_name=(timezone_name or '')[:64], current_path=(current_path or '')[:500],
            **scope,
        )
        credited = 0
    else:
        elapsed = max(0, int((now - session.last_seen_at).total_seconds()))
        credited = min(elapsed, 300) if visible else 0
        for key, value in scope.items():
            if value is not None:
                setattr(session, key, value)
        session.tab_id = (tab_id or session.tab_id)[:96]
        session.timezone_name = (timezone_name or session.timezone_name)[:64]
        session.current_path = (current_path or session.current_path)[:500]
        session.last_seen_at = now
        if ip_address:
            session.ip_address = ip_address
        if user_agent:
            session.user_agent = user_agent[:2000]

    bucket = now.replace(second=0, microsecond=0)
    try:
        _, created = ActivityPulse.objects.get_or_create(
            session=session,
            bucket=bucket,
            defaults={'credited_seconds': credited, 'visible': visible, 'interacted': interacted},
        )
    except IntegrityError:
        created = False
    if created:
        session.active_seconds += credited
    session.save()
    return session, credited if created else 0


def close_stale_sessions(now=None):
    now = now or timezone.now()
    cutoff = now - timedelta(minutes=10)
    return ActivitySession.objects.filter(state='OPEN', last_seen_at__lt=cutoff).update(
        state='EXPIRED', ended_at=now,
    )


def business_days(start, end):
    """Jours ouvrés configurables ; lundi-vendredi est la valeur par défaut."""
    if end < start:
        return []
    overrides = {row.date: row.is_working_day for row in BusinessCalendarDay.objects.filter(date__range=(start, end))}
    days, cursor = [], start
    while cursor <= end:
        if overrides.get(cursor, cursor.weekday() < 5):
            days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _scope_task_queryset(ctm=None, wg=None, target_group=None, norme=None, target_group_ids=None):
    qs = Tache.objects.select_related('assigned_to__user', 'backup_assignee__user', 'norme', 'working_group', 'target_group').prefetch_related('blocked_by')
    if target_group_ids is not None:
        qs = qs.filter(target_group_id__in=target_group_ids)
    if norme:
        qs = qs.filter(norme=norme)
    elif target_group:
        qs = qs.filter(target_group=target_group)
    elif wg:
        qs = qs.filter(working_group=wg)
    elif ctm:
        qs = qs.filter(working_group__ctm=ctm)
    return qs


def _scope_sessions(start_dt, end_dt, ctm=None, wg=None, target_group=None, expert=None, target_group_ids=None):
    qs = ActivitySession.objects.filter(started_at__lt=end_dt, last_seen_at__gte=start_dt)
    if ctm:
        qs = qs.filter(ctm=ctm)
    if wg:
        qs = qs.filter(working_group=wg)
    if target_group:
        qs = qs.filter(target_group=target_group)
    if target_group_ids is not None:
        qs = qs.filter(target_group_id__in=target_group_ids)
    if expert:
        qs = qs.filter(user=expert.user)
    return qs


def _expectation_minutes(expert, start, end):
    if not expert:
        return None
    expectation = expert.work_expectations.filter(
        effective_from__lte=end,
    ).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=start)).order_by('-effective_from').first()
    if not expectation:
        return None
    days = business_days(start, end)
    absent = set()
    for absence in expert.justified_absences.filter(status='APPROVED', starts_on__lte=end, ends_on__gte=start):
        absent.update(business_days(max(start, absence.starts_on), min(end, absence.ends_on)))
    credited_days = max(0, len(set(days) - absent))
    return round(expectation.weekly_minutes * credited_days / 5)


def _percent(numerator, denominator):
    if not denominator:
        return None
    return round(float(numerator) * 100 / float(denominator), 1)


def calculate_scope_metrics(*, start, end, ctm=None, wg=None, target_group=None, norme=None, expert=None, target_group_ids=None):
    """Calcule chaque indicateur séparément et conserve l'état non configuré."""
    tasks = list(_scope_task_queryset(ctm, wg, target_group, norme, target_group_ids).filter(
        Q(created_at__date__lte=end), Q(due_date__isnull=True) | Q(due_date__gte=start)
    ))
    if expert:
        tasks = [task for task in tasks if task.assigned_to_id == expert.pk or task.backup_assignee_id == expert.pk]
    today = timezone.localdate()
    configured_norms = defaultdict(list)
    for task in tasks:
        if task.norme_id and task.due_date:
            configured_norms[task.norme_id].append(task)
    advancement_counts = {'on_track': 0, 'watch': 0, 'blocked': 0, 'late': 0}
    for norm_tasks in configured_norms.values():
        if any(t.status == 'BLOCKED' or any(dep.status != 'COMPLETED' for dep in t.blocked_by.all()) for t in norm_tasks):
            advancement_counts['blocked'] += 1
        elif any(t.status != 'COMPLETED' and t.due_date and t.due_date < today for t in norm_tasks):
            advancement_counts['late'] += 1
        elif any(t.status != 'COMPLETED' and t.due_date and t.due_date <= today + timedelta(days=7) for t in norm_tasks):
            advancement_counts['watch'] += 1
        else:
            advancement_counts['on_track'] += 1
    advancement_total = sum(advancement_counts.values())
    advancement = _percent(advancement_counts['on_track'], advancement_total)

    weighted_total = sum(task.weight for task in tasks)
    weighted_done = sum(task.weight * task.progress for task in tasks)
    production = _percent(weighted_done, weighted_total * 100)

    accepted = sum(1 for task in tasks if task.review_status == 'ACCEPTED')
    returned = sum(1 for task in tasks if task.review_status == 'RETURNED')
    not_reviewed = sum(1 for task in tasks if task.review_status == 'NOT_REVIEWED')
    quality = _percent(accepted, accepted + returned)

    complete = sum(1 for task in tasks if task.assigned_to_id and task.due_date and task.weight and task.norme_id and (task.working_group_id or task.target_group_id))
    completeness = _percent(complete, len(tasks))

    start_dt = timezone.make_aware(datetime.combine(start, time.min))
    end_dt = timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min))
    sessions = _scope_sessions(start_dt, end_dt, ctm, wg, target_group, expert, target_group_ids)
    observed_seconds = sessions.aggregate(total=Sum('active_seconds'))['total'] or 0
    declared_qs = OffPlatformWork.objects.filter(status='APPROVED', work_date__range=(start, end))
    if ctm:
        declared_qs = declared_qs.filter(ctm=ctm)
    if wg:
        declared_qs = declared_qs.filter(working_group=wg)
    if target_group:
        declared_qs = declared_qs.filter(target_group=target_group)
    if target_group_ids is not None:
        declared_qs = declared_qs.filter(target_group_id__in=target_group_ids)
    if norme:
        declared_qs = declared_qs.filter(norme=norme)
    if expert:
        declared_qs = declared_qs.filter(expert=expert)
    declared_minutes = declared_qs.aggregate(total=Sum('minutes'))['total'] or 0
    expectation = _expectation_minutes(expert, start, end) if expert else None
    engagement = _percent(observed_seconds // 60 + declared_minutes, expectation) if expert else None
    dispute_qs = ActivityDispute.objects.filter(status='PENDING')
    if expert:
        dispute_qs = dispute_qs.filter(expert=expert)

    return {
        'advancement': {'value': advancement, 'configured': advancement is not None, 'counts': advancement_counts, 'sources': advancement_total},
        'production': {'value': production, 'configured': production is not None, 'planned_weight': weighted_total, 'sources': len(tasks)},
        'quality': {'value': quality, 'configured': quality is not None, 'accepted': accepted, 'returned': returned, 'not_reviewed': not_reviewed, 'sources': accepted + returned},
        'engagement': {'value': engagement, 'configured': engagement is not None, 'observed_minutes': observed_seconds // 60, 'declared_minutes': declared_minutes, 'objective_minutes': expectation, 'sources': sessions.count() + declared_qs.count()},
        'completeness': {'value': completeness, 'configured': completeness is not None, 'complete': complete, 'total': len(tasks), 'sources': len(tasks)},
        'updated_at': timezone.now(),
        'contested_sources': dispute_qs.count(),
    }


def task_state(task, today=None):
    today = today or timezone.localdate()
    if task.status == 'BLOCKED' or any(dep.status != 'COMPLETED' for dep in task.blocked_by.all()):
        return 'BLOCKED'
    if task.status != 'COMPLETED' and task.due_date and task.due_date < today:
        return 'LATE'
    return task.status


def build_exceptions(*, ctm=None, wg=None, target_group=None, target_group_ids=None, start=None, end=None, limit=30):
    rows = []
    tasks = _scope_task_queryset(ctm=ctm, wg=wg, target_group=target_group, target_group_ids=target_group_ids)
    if start is not None and end is not None:
        tasks = tasks.filter(Q(created_at__date__lte=end), Q(due_date__isnull=True) | Q(due_date__gte=start))
    for task in tasks:
        state = task_state(task)
        if state in {'BLOCKED', 'LATE'}:
            rows.append({'severity': 'ACTION', 'kind': state, 'label': task.titre, 'detail': task.norme.reference_number if task.norme else 'Rattachement documentaire à confirmer', 'task': task})
        elif not task.assigned_to_id:
            rows.append({'severity': 'WATCH', 'kind': 'UNASSIGNED', 'label': task.titre, 'detail': 'Aucun responsable actif', 'task': task})
        elif any(dep.status != 'COMPLETED' for dep in task.blocked_by.all()):
            rows.append({'severity': 'WATCH', 'kind': 'DEPENDENCY', 'label': task.titre, 'detail': 'Dépendance bloquante', 'task': task})
    rank = {'ACTION': 0, 'WATCH': 1}
    return sorted(rows, key=lambda row: (rank[row['severity']], row['label'].lower()))[:limit]


def historical_sc_rows(start, end):
    """Retourne uniquement les SC de la version courante.

    Les anciennes versions sont archivées dans les Communiqués et ne sont plus
    lues par l'interface.
    """
    version = current_organisation_version()
    if not version:
        return []
    rows = []
    for sc in Organe.objects.filter(
        version=version, type='SC',
    ).exclude(status='ARCHIVED').prefetch_related('groupes').order_by('code'):
        rows.append({
            'kind': 'current',
            'id': sc.pk,
            'number': sc.composition.get('tome'),
            'name': sc.official_name or sc.name,
            'code': sc.code,
            'badge': '',
            'legacy_ctm_id': None,
            'metrics': {
                key: {'value': None, 'configured': False, 'sources': 0}
                for key in ('advancement', 'production', 'quality', 'engagement', 'completeness')
            },
            'group_count': sc.groupes.count(),
        })
    return rows


def weekly_heatmap(sc_rows, start, end, weeks=8):
    """Comptage hebdomadaire des tâches clôturées, sans reconstruire leur progression passée."""
    first_week = start - timedelta(days=start.weekday())
    last_week = end - timedelta(days=end.weekday())
    starts = []
    cursor = max(first_week, last_week - timedelta(weeks=weeks - 1))
    while cursor <= last_week:
        starts.append(cursor)
        cursor += timedelta(weeks=1)
    result = []
    has_data = False
    for row in sc_rows:
        if row['kind'] == 'historical':
            tasks = Tache.objects.filter(working_group__ctm_id=row['id'])
        else:
            tasks = Tache.objects.filter(target_group__sc_id=row['id'])
        configured = tasks.exists()
        has_data = has_data or configured
        completed = list(tasks.filter(
            completed_at__date__gte=max(start, starts[0]), completed_at__date__lte=end,
        ).values_list('completed_at', flat=True))
        counts = {week: 0 for week in starts}
        for completed_at in completed:
            day = timezone.localtime(completed_at).date()
            week = day - timedelta(days=day.weekday())
            if week in counts:
                counts[week] += 1
        values = [counts[week] if configured else None for week in starts]
        result.append({'label': row['code'], 'values': values})
    return {'weeks': starts, 'rows': result, 'has_data': has_data}


def expert_activity_context(expert, start, end, include_technical=False):
    metrics = calculate_scope_metrics(start=start, end=end, expert=expert)
    tasks = _scope_task_queryset().filter(Q(assigned_to=expert) | Q(backup_assignee=expert)).order_by('status', 'due_date', 'titre')
    sessions = _scope_sessions(
        timezone.make_aware(datetime.combine(start, time.min)),
        timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min)),
        expert=expert,
    ).order_by('-last_seen_at')
    session_rows = []
    for session in sessions:
        row = {
            'id': session.pk, 'date': timezone.localtime(session.started_at, KINSHASA_TZ).date(),
            'start': timezone.localtime(session.started_at, KINSHASA_TZ),
            'end': timezone.localtime(session.last_seen_at, KINSHASA_TZ),
            'minutes': session.active_seconds // 60, 'channel': session.channel,
            'timezone_name': session.timezone_name,
        }
        if include_technical:
            row.update({'ip_address': session.ip_address, 'user_agent': session.user_agent, 'device_id': session.device_id})
        session_rows.append(row)
    return {
        'profile_expert': expert, 'metrics': metrics, 'tasks': tasks,
        'contributions': tasks.exclude(deliverable_reference=''),
        'expectations': expert.work_expectations.order_by('-effective_from'),
        'absences': expert.justified_absences.order_by('-starts_on'),
        'declarations': expert.off_platform_work.order_by('-work_date'),
        'disputes': expert.activity_disputes.order_by('-created_at'),
        'sessions': session_rows,
        'access_history': expert.activity_data_accesses.select_related('viewer').order_by('-created_at')[:50],
    }


ALLOWED_TASK_TRANSITIONS = {
    'PLANNED': {'IN_PROGRESS', 'ON_HOLD'},
    'IN_PROGRESS': {'COMPLETED', 'BLOCKED', 'ON_HOLD'},
    'BLOCKED': {'IN_PROGRESS', 'ON_HOLD'},
    'ON_HOLD': {'PLANNED', 'IN_PROGRESS'},
    'COMPLETED': {'IN_PROGRESS'},
}


@transaction.atomic
def transition_task(*, task, new_status, actor, request=None):
    task = Tache.objects.select_for_update().get(pk=task.pk)
    if new_status not in ALLOWED_TASK_TRANSITIONS.get(task.status, set()):
        raise ValueError('Cette transition est interdite par le circuit de travail.')
    old_status = task.status
    task.status = new_status
    now = timezone.now()
    if new_status == 'IN_PROGRESS' and not task.started_at:
        task.started_at = now
    if new_status == 'COMPLETED':
        task.completed_at, task.progress = now, 100
    elif old_status == 'COMPLETED':
        task.completed_at = None
    task.updated_by = actor
    task.save()
    AuditLog.objects.create(
        user=actor, action='UPDATE', content_type='Tache', object_id=task.pk,
        object_repr=str(task)[:200], changes={'status': {'old': old_status, 'new': new_status}},
        ip_address=_client_ip(request) if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:2000] if request else '',
    )
    return task


def aggregate_activity_day(day):
    """Recalcule les agrégats journaliers à partir des seules sources observées."""
    start_dt = timezone.make_aware(datetime.combine(day, time.min))
    end_dt = start_dt + timedelta(days=1)
    users = ActivitySession.objects.filter(started_at__lt=end_dt, last_seen_at__gte=start_dt).values_list('user_id', flat=True).distinct()
    count = 0
    for user_id in users:
        sessions = ActivitySession.objects.filter(user_id=user_id, started_at__lt=end_dt, last_seen_at__gte=start_dt)
        active = sessions.aggregate(total=Sum('active_seconds'))['total'] or 0
        expert = Expert.objects.filter(user_id=user_id).first()
        declared = 0
        if expert:
            declared = (OffPlatformWork.objects.filter(expert=expert, status='APPROVED', work_date=day).aggregate(total=Sum('minutes'))['total'] or 0) * 60
        ActivityAggregate.objects.update_or_create(
            period_type='DAY', period_start=day, user_id=user_id,
            ctm=None, working_group=None, target_group=None,
            defaults={'active_seconds': active, 'declared_seconds': declared, 'source_count': sessions.count()},
        )
        count += 1
    return count

