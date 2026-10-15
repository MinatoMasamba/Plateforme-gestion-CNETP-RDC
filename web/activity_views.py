"""Interfaces web de supervision des sous-commissions et de transparence."""
import csv
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from django.utils.decorators import method_decorator
from apps.core.models import AuditLog

from apps.experts.models import Expert
from apps.governance.activity_supervision import (
    activity_access_for, build_exceptions, calculate_scope_metrics,
    expert_activity_context, historical_sc_rows, log_sensitive_access,
    record_heartbeat, task_state, transition_task, weekly_heatmap,
)
from apps.governance.models import (
    ActivityAlert, ActivityDispute, ActivitySession, CTM, GroupeCible,
    JustifiedAbsence, OffPlatformWork, Organe, SavedActivityView, Tache, WG,
)
from apps.norms.models import Norme
from apps.governance.phoenix_models import MandatOrganisation, RattachementDocumentaire


def _period(request):
    today = timezone.localdate()
    end = parse_date(request.GET.get('fin', '')) or today
    start = parse_date(request.GET.get('debut', '')) or (end - timedelta(days=27))
    if start > end:
        start, end = end, start
    if (end - start).days > 370:
        start = end - timedelta(days=370)
    return start, end


def _base_context(request, title):
    start, end = _period(request)
    access = activity_access_for(request.user)
    return {
        'page_title': title,
        'period_start': start,
        'period_end': end,
        'light_data_mode': request.GET.get('leger') == '1',
        'activity_access': access,
        'saved_views': SavedActivityView.objects.filter(owner=request.user),
        'kinshasa_now': timezone.localtime(),
    }


def _require(request, key):
    access = activity_access_for(request.user)
    if not access.get(key):
        raise PermissionDenied
    return access


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class ActivityDashboardView(View):
    template_name = 'pilotage/activity/dashboard.html'

    def get(self, request):
        _require(request, 'can_view_aggregates')
        context = _base_context(request, 'Supervision des sous-commissions')
        start, end = context['period_start'], context['period_end']
        rows = historical_sc_rows(start, end)
        for row in rows:
            if row['kind'] == 'current':
                row['metrics'] = _unconfigured_metrics()
                groups = GroupeCible.objects.filter(sc_id=row['id']).order_by('name')
                row['group_rows'] = [{'group': group, 'metrics': calculate_scope_metrics(start=start, end=end, target_group=group), 'historical': False} for group in groups]
            else:
                groups = WG.objects.filter(ctm_id=row['id']).order_by('name')
                row['group_rows'] = [{'group': group, 'metrics': calculate_scope_metrics(start=start, end=end, wg=group), 'historical': True} for group in groups]
        rows.sort(key=lambda row: row['name'].casefold())
        heatmap = weekly_heatmap(rows, end)
        chart_payload = {
            'heatmap': {
                'weeks': [value.strftime('%d/%m') for value in heatmap['weeks']],
                'rows': heatmap['rows'],
            },
            'load': [
                {
                    'label': row['code'],
                    'tasks': row['metrics']['production'].get('sources', 0),
                    'progress': row['metrics']['production'].get('value'),
                }
                for row in rows
            ],
        }
        context.update({
            'metrics': calculate_scope_metrics(start=start, end=end),
            'exceptions': build_exceptions(),
            'subcommissions': rows,
            'heatmap': heatmap,
            'chart_payload_json': json.dumps(chart_payload),
            'recent_sessions': ActivitySession.objects.select_related('user').order_by('-last_seen_at')[:12],
        })
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class ActivitySubcommissionView(View):
    template_name = 'pilotage/activity/subcommission.html'

    def get(self, request, number):
        _require(request, 'can_view_aggregates')
        ctm = get_object_or_404(CTM.objects.select_related('scientific_president__user'), number=number)
        context = _base_context(request, f'Activité · Sous-commission {number}')
        start, end = context['period_start'], context['period_end']
        groups = []
        for wg in ctm.working_groups.select_related('president__user').order_by('number'):
            metrics = calculate_scope_metrics(start=start, end=end, wg=wg)
            experts = [assignment.expert for assignment in wg.affectations.select_related('expert__user')]
            groups.append({
                'group': wg, 'metrics': metrics, 'historical': True,
                'expert_activity': _group_expert_activity(experts, wg.tasks.all()),
                'late': sum(1 for task in wg.tasks.all() if task_state(task) == 'LATE'),
                'blocked': sum(1 for task in wg.tasks.all() if task_state(task) == 'BLOCKED'),
            })
        context.update({
            'subcommission': ctm, 'historical': True, 'groups': groups,
            'metrics': calculate_scope_metrics(start=start, end=end, ctm=ctm),
            'exceptions': build_exceptions(ctm=ctm),
            'recent_sessions': ctm.activity_sessions.select_related('user').order_by('-last_seen_at')[:20],
        })
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class ActivityCurrentSubcommissionView(View):
    template_name = 'pilotage/activity/subcommission.html'

    def get(self, request, pk):
        _require(request, 'can_view_aggregates')
        sc = get_object_or_404(Organe, pk=pk, type='SC')
        context = _base_context(request, f'Activité · {sc.official_name or sc.name}')
        start, end = context['period_start'], context['period_end']
        groups = []
        today = timezone.localdate()
        for group in sc.groupes.order_by('code'):
            mandates = list(MandatOrganisation.objects.filter(
                groupe=group, status='ACTIVE', capacity='ORGANISATION',
            ).filter(Q(start_date__isnull=True) | Q(start_date__lte=today)).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=today)
            ).select_related('expert__user'))
            groups.append({'group': group, 'metrics': calculate_scope_metrics(start=start, end=end, target_group=group), 'historical': False, 'expert_activity': _group_expert_activity([mandate.expert for mandate in mandates], group.tasks.all())})
        posts = list(sc.postes.prefetch_related('mandates__expert__user'))
        coordination = []
        for title, key in [('Président', 'PRES'), ('Rapporteur', 'RAPP'), ('Secrétaire', 'SECR')]:
            post = next((item for item in posts if key in item.code.upper() or key in item.title.upper()), None)
            holder = next((mandate for mandate in post.mandates.all() if mandate.status == 'ACTIVE' and mandate.capacity == 'ORGANISATION' and (not mandate.start_date or mandate.start_date <= today) and (not mandate.end_date or mandate.end_date >= today)), None) if post else None
            coordination.append({'title': title, 'post': post, 'holder': holder})
        bindings = list(RattachementDocumentaire.objects.filter(sc=sc).select_related('norme', 'gt').order_by('norme__title'))
        norm_sections = {'waiting': [], 'working': [], 'produced': [], 'unconfirmed': []}
        seen = set()
        for binding in bindings:
            if binding.status != 'VALIDATED' or binding.gt_id and binding.gt.sc_id != sc.pk:
                norm_sections['unconfirmed'].append(binding)
                continue
            if binding.norme_id in seen:
                continue
            seen.add(binding.norme_id)
            status = binding.norme.status
            if status in {'ADOPTED', 'HOMOLOGATED', 'PUBLISHED', 'ARCHIVED'}:
                norm_sections['produced'].append(binding)
            elif status in {'CTM_REVIEW', 'LEGISTIC_REVIEW', 'PUBLIC_INQUIRY', 'PILOTAGE_REVIEW', 'FINAL_REVIEW'}:
                norm_sections['waiting'].append(binding)
            else:
                norm_sections['working'].append(binding)
        context.update({
            'subcommission': sc, 'historical': False, 'groups': groups,
            'metrics': _unconfigured_metrics(), 'coordination': coordination,
            'norm_sections': norm_sections,
            'exceptions': [], 'recent_sessions': ActivitySession.objects.filter(target_group__sc=sc).select_related('user').order_by('-last_seen_at')[:20],
        })
        return render(request, self.template_name, context)


def _unconfigured_metrics():
    return {key: {'value': None, 'configured': False, 'sources': 0} for key in ('advancement', 'production', 'quality', 'engagement', 'completeness')} | {'updated_at': timezone.now()}


def _group_expert_activity(experts, tasks):
    task_rows = list(tasks)
    rows = []
    for expert in experts:
        owned = [task for task in task_rows if task.assigned_to_id == expert.pk or task.backup_assignee_id == expert.pk]
        latest = max(owned, key=lambda task: task.updated_at) if owned else None
        rows.append({'expert': expert, 'current_count': sum(task.status != 'COMPLETED' for task in owned), 'deliverable_count': sum(bool(task.deliverable_reference) for task in owned), 'latest': latest})
    return rows


def _combine_group_metrics(metrics_list):
    if not metrics_list:
        return calculate_scope_metrics(start=timezone.localdate(), end=timezone.localdate(), target_group_id=-1) if False else {
            key: {'value': None, 'configured': False, 'sources': 0} for key in ('advancement', 'production', 'quality', 'engagement', 'completeness')
        } | {'updated_at': timezone.now()}
    result = {'updated_at': timezone.now()}
    for key in ('advancement', 'production', 'quality', 'engagement', 'completeness'):
        weighted = [(item[key]['value'], item[key].get('sources', 0)) for item in metrics_list if item[key]['value'] is not None]
        total = sum(weight for _, weight in weighted)
        value = round(sum(value * weight for value, weight in weighted) / total, 1) if total else None
        result[key] = {'value': value, 'configured': value is not None, 'sources': total}
    return result


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class ActivityGroupView(View):
    template_name = 'pilotage/activity/group.html'

    def get(self, request, pk):
        _require(request, 'can_view_contributions')
        group = get_object_or_404(WG.objects.select_related('ctm', 'president__user'), pk=pk)
        context = _base_context(request, f'Groupe de travail · {group.name}')
        start, end = context['period_start'], context['period_end']
        tasks = group.tasks.select_related('norme', 'assigned_to__user', 'backup_assignee__user').prefetch_related('blocked_by').order_by('due_date', 'titre')
        normes = group.normes.prefetch_related('tasks').order_by('status', 'reference_number')
        context.update({
            'group': group, 'historical': True, 'tasks': tasks, 'normes': normes,
            'group_experts': _group_expert_activity([assignment.expert for assignment in group.affectations.select_related('expert__user')], tasks),
            'metrics': calculate_scope_metrics(start=start, end=end, wg=group),
            'status_columns': ['PLANNED', 'IN_PROGRESS', 'BLOCKED', 'ON_HOLD', 'COMPLETED'],
            'experts_alphabetical': Expert.objects.select_related('user').order_by('user__last_name', 'user__first_name'),
        })
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class ActivityCurrentGroupView(View):
    template_name = 'pilotage/activity/group.html'

    def get(self, request, pk):
        _require(request, 'can_view_contributions')
        group = get_object_or_404(GroupeCible.objects.select_related('sc'), pk=pk)
        context = _base_context(request, f'Groupe de travail · {group.name}')
        start, end = context['period_start'], context['period_end']
        tasks = group.tasks.select_related('norme', 'assigned_to__user', 'backup_assignee__user').prefetch_related('blocked_by').order_by('due_date', 'titre')
        normes = Norme.all_objects.filter(
            Q(tasks__target_group=group) | Q(organisation_bindings__gt=group, organisation_bindings__status='VALIDATED')
        ).distinct().order_by('reference_number')
        context.update({
            'group': group, 'historical': False, 'tasks': tasks, 'normes': normes,
            'group_experts': _group_expert_activity([mandate.expert for mandate in MandatOrganisation.objects.filter(groupe=group, status='ACTIVE', capacity='ORGANISATION').filter(Q(start_date__isnull=True) | Q(start_date__lte=timezone.localdate())).filter(Q(end_date__isnull=True) | Q(end_date__gte=timezone.localdate())).select_related('expert__user')], tasks),
            'metrics': calculate_scope_metrics(start=start, end=end, target_group=group),
            'status_columns': ['PLANNED', 'IN_PROGRESS', 'BLOCKED', 'ON_HOLD', 'COMPLETED'],
            'experts_alphabetical': Expert.objects.select_related('user').order_by('user__last_name', 'user__first_name'),
        })
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class ActivityNormView(View):
    template_name = 'pilotage/activity/norm.html'

    def get(self, request, pk):
        _require(request, 'can_view_contributions')
        norme = get_object_or_404(Norme.all_objects.select_related('ctm', 'wg'), pk=pk)
        context = _base_context(request, f'Norme · {norme.reference_number}')
        start, end = context['period_start'], context['period_end']
        workflow = list(Norme.STATUS_CHOICES)
        codes = [code for code, _ in workflow]
        current_index = codes.index(norme.status) if norme.status in codes else 0
        context.update({
            'norme': norme, 'tasks': norme.tasks.select_related('assigned_to__user', 'backup_assignee__user').prefetch_related('blocked_by'),
            'versions': norme.versions.select_related('version_author').order_by('-version_number'),
            'comments': norme.comments.select_related('author__user').order_by('-created_at'),
            'metrics': calculate_scope_metrics(start=start, end=end, norme=norme),
            'workflow_steps': [{'code': code, 'label': label, 'done': index < current_index, 'current': index == current_index} for index, (code, label) in enumerate(workflow)],
            'history_events': AuditLog.objects.filter(content_type__in=['Norme', 'Tache']).filter(Q(object_id=norme.pk) | Q(object_repr__icontains=norme.reference_number)).select_related('user').order_by('-timestamp')[:80],
            'activity_sessions': norme.activity_sessions.select_related('user').order_by('-last_seen_at')[:30],
        })
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class ActivityExpertView(View):
    template_name = 'pilotage/activity/expert.html'

    def get(self, request, pk):
        access = _require(request, 'can_view_contributions')
        target = get_object_or_404(Expert.objects.select_related('user', 'structure'), pk=pk)
        technical = request.GET.get('details') == 'techniques'
        if technical and not access['can_view_session_details']:
            raise PermissionDenied
        log_sensitive_access(
            request, target,
            purpose='Consultation des détails techniques' if technical else 'Consultation de la fiche d’activité',
            detail_level='SESSION_TECHNICAL' if technical else 'SUMMARY',
        )
        context = _base_context(request, f'Activité · {target.full_name}')
        context.update(expert_activity_context(target, context['period_start'], context['period_end'], include_technical=technical))
        context.update({'technical_details': technical, 'is_self_view': target.user_id == request.user.pk})
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class MyActivityDataView(View):
    template_name = 'pilotage/activity/expert.html'

    def get(self, request):
        expert = get_object_or_404(Expert.objects.select_related('user', 'structure'), user=request.user)
        log_sensitive_access(request, expert, purpose='Consultation de ses propres données', detail_level='SELF_TRANSPARENCY')
        context = _base_context(request, 'Ce qui est enregistré sur moi')
        context.update(expert_activity_context(expert, context['period_start'], context['period_end'], include_technical=True))
        context.update({'technical_details': True, 'is_self_view': True, 'transparency_view': True})
        return render(request, self.template_name, context)


@login_required(login_url='/se-connecter/')
@require_POST
@csrf_protect
def activity_heartbeat(request):
    try:
        payload = json.loads(request.body or '{}')
        session, credited = record_heartbeat(
            user=request.user,
            device_id=payload.get('device_id'), tab_id=payload.get('tab_id', ''),
            visible=bool(payload.get('visible', True)), interacted=bool(payload.get('interacted', False)),
            timezone_name=payload.get('timezone', ''), current_path=payload.get('path', ''),
            ctm_id=payload.get('ctm_id'), working_group_id=payload.get('working_group_id'),
            target_group_id=payload.get('target_group_id'), norme_id=payload.get('norme_id'),
            ip_address=request.META.get('REMOTE_ADDR'), user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    return JsonResponse({'ok': True, 'session': str(session.pk), 'credited_seconds': credited, 'server_time': timezone.now().isoformat()})


@login_required(login_url='/se-connecter/')
@require_POST
@csrf_protect
def activity_task_transition(request, pk):
    access = _require(request, 'can_manage_targets')
    task = get_object_or_404(Tache, pk=pk)
    new_status = request.POST.get('status', '')
    try:
        task = transition_task(task=task, new_status=new_status, actor=request.user, request=request)
    except ValueError as exc:
        return JsonResponse({'ok': False, 'error': str(exc), 'status': task.status}, status=409)
    return JsonResponse({'ok': True, 'status': task.status, 'progress': task.progress})


@login_required(login_url='/se-connecter/')
@require_POST
@csrf_protect
@transaction.atomic
def activity_task_configure(request, pk):
    _require(request, 'can_manage_targets')
    task = get_object_or_404(Tache, pk=pk)
    try:
        if 'weight' in request.POST:
            task.weight = int(request.POST['weight'])
            task.weight_source = 'MANUAL'
        if 'priority' in request.POST:
            task.priority = request.POST['priority']
        if 'due_date' in request.POST:
            task.due_date = parse_date(request.POST['due_date'])
        if 'assigned_to' in request.POST:
            task.assigned_to_id = int(request.POST['assigned_to']) if request.POST['assigned_to'] else None
        task.updated_by = request.user
        task.full_clean()
        task.save()
    except (ValueError, ValidationError) as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    return JsonResponse({'ok': True, 'weight': task.weight, 'priority': task.priority, 'weight_source': task.weight_source})


@login_required(login_url='/se-connecter/')
@require_POST
@csrf_protect
@transaction.atomic
def activity_tasks_bulk_configure(request):
    _require(request, 'can_manage_targets')
    task_ids = request.POST.getlist('task_ids')
    tasks = Tache.objects.select_for_update().filter(pk__in=task_ids)
    if not task_ids or not tasks.exists():
        messages.error(request, 'Sélectionnez au moins une tâche.')
        return redirect(request.META.get('HTTP_REFERER', 'web:activity_dashboard'))
    try:
        weight = int(request.POST['weight']) if request.POST.get('weight') else None
        if weight is not None and not 1 <= weight <= 5:
            raise ValueError
    except ValueError:
        messages.error(request, 'Le poids doit être compris entre 1 et 5.')
        return redirect(request.META.get('HTTP_REFERER', 'web:activity_dashboard'))
    priority = request.POST.get('priority') or None
    due_date = parse_date(request.POST.get('due_date', '')) if request.POST.get('due_date') else None
    for task in tasks:
        if weight is not None:
            task.weight, task.weight_source = weight, 'MANUAL'
        if priority:
            task.priority = priority
        if due_date:
            task.due_date = due_date
        task.updated_by = request.user
        task.full_clean()
        task.save()
    messages.success(request, f'{tasks.count()} tâche(s) configurée(s).')
    return redirect(request.META.get('HTTP_REFERER', 'web:activity_dashboard'))


@login_required(login_url='/se-connecter/')
@require_POST
@csrf_protect
def declare_off_platform_work(request):
    expert = get_object_or_404(Expert, user=request.user)
    work_date = parse_date(request.POST.get('work_date', ''))
    try:
        minutes = int(request.POST.get('minutes', '0'))
        if not work_date or not 1 <= minutes <= 1440 or not request.POST.get('reason', '').strip():
            raise ValueError
    except ValueError:
        messages.error(request, 'Indiquez une date, une durée valide et le motif du travail déclaré.')
        return redirect('web:my_activity_data')
    OffPlatformWork.objects.create(
        expert=expert, work_date=work_date, minutes=minutes,
        reason=request.POST['reason'].strip(), evidence_reference=request.POST.get('evidence_reference', '').strip(),
        norme_id=request.POST.get('norme_id') or None, created_by=request.user,
    )
    messages.success(request, 'Votre déclaration a été transmise pour validation.')
    return redirect('web:my_activity_data')


@login_required(login_url='/se-connecter/')
@require_POST
@csrf_protect
def declare_absence(request):
    expert = get_object_or_404(Expert, user=request.user)
    starts_on, ends_on = parse_date(request.POST.get('starts_on', '')), parse_date(request.POST.get('ends_on', ''))
    if not starts_on or not ends_on or ends_on < starts_on or not request.POST.get('reason', '').strip():
        messages.error(request, 'La période et le motif de l’absence doivent être renseignés.')
        return redirect('web:my_activity_data')
    JustifiedAbsence.objects.create(
        expert=expert, starts_on=starts_on, ends_on=ends_on,
        reason=request.POST['reason'].strip(), evidence_reference=request.POST.get('evidence_reference', '').strip(),
        created_by=request.user,
    )
    messages.success(request, 'Votre absence a été transmise pour validation.')
    return redirect('web:my_activity_data')


@login_required(login_url='/se-connecter/')
@require_POST
@csrf_protect
def create_activity_dispute(request):
    expert = get_object_or_404(Expert, user=request.user)
    reason = request.POST.get('reason', '').strip()
    source_type, source_identifier = request.POST.get('source_type', '')[:40], request.POST.get('source_identifier', '')[:100]
    if not reason or not source_type or not source_identifier:
        messages.error(request, 'La donnée contestée et le motif sont obligatoires.')
        return redirect('web:my_activity_data')
    ActivityDispute.objects.create(
        expert=expert, source_type=source_type, source_identifier=source_identifier,
        reason=reason, expert_evidence=request.POST.get('expert_evidence', '').strip(), created_by=request.user,
    )
    messages.success(request, 'La contestation a été enregistrée sans modifier la donnée source.')
    return redirect('web:my_activity_data')


@login_required(login_url='/se-connecter/')
@require_POST
@csrf_protect
def review_activity_declaration(request, kind, pk):
    _require(request, 'can_review_declarations')
    model = OffPlatformWork if kind == 'work' else JustifiedAbsence if kind == 'absence' else None
    if model is None:
        raise Http404
    item = get_object_or_404(model, pk=pk)
    status = request.POST.get('status')
    reason = request.POST.get('review_reason', '').strip()
    if status not in {'APPROVED', 'REJECTED'} or (status == 'REJECTED' and not reason):
        messages.error(request, 'La décision est invalide ou sa justification manque.')
    else:
        item.status, item.reviewed_by, item.reviewed_at, item.review_reason = status, request.user, timezone.now(), reason
        item.updated_by = request.user
        item.save()
        messages.success(request, 'La déclaration a été instruite et la décision conservée.')
    return redirect(request.META.get('HTTP_REFERER', 'web:activity_dashboard'))


@login_required(login_url='/se-connecter/')
@require_POST
@csrf_protect
def review_activity_dispute(request, pk):
    _require(request, 'can_review_disputes')
    dispute = get_object_or_404(ActivityDispute, pk=pk)
    status = request.POST.get('status')
    position = request.POST.get('reviewer_position', '').strip()
    decision = request.POST.get('decision_reason', '').strip()
    if status not in {'UPHELD', 'DISMISSED'} or not position or not decision:
        messages.error(request, 'La position de la coordination et la justification de décision sont obligatoires.')
    else:
        dispute.status, dispute.reviewer_position, dispute.decision_reason = status, position, decision
        dispute.reviewed_by, dispute.reviewed_at, dispute.updated_by = request.user, timezone.now(), request.user
        dispute.save()
        messages.success(request, 'La contestation a été instruite sans modifier sa donnée source.')
    return redirect(request.META.get('HTTP_REFERER', 'web:activity_dashboard'))


@login_required(login_url='/se-connecter/')
@require_POST
@csrf_protect
def answer_activity_alert(request, pk):
    alert = get_object_or_404(ActivityAlert, pk=pk)
    allowed = {'HANDLED', 'BLOCKED', 'POSTPONEMENT'}
    status = request.POST.get('status')
    if status not in allowed:
        return JsonResponse({'ok': False, 'error': 'Réponse invalide.'}, status=400)
    if alert.expert_id and alert.expert.user_id != request.user.pk and not activity_access_for(request.user)['can_review_declarations']:
        raise PermissionDenied
    alert.status, alert.response = status, request.POST.get('response', '').strip()
    alert.responded_by, alert.responded_at = request.user, timezone.now()
    alert.save(update_fields=['status', 'response', 'responded_by', 'responded_at', 'updated_at'])
    return JsonResponse({'ok': True, 'status': alert.status})


@login_required(login_url='/se-connecter/')
@require_GET
def export_subcommission_activity(request, number):
    _require(request, 'can_view_aggregates')
    ctm = get_object_or_404(CTM, number=number)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="activite-sous-commission-{number}.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Sous-commission', 'Groupe', 'Norme', 'Tâche', 'Responsable', 'Échéance', 'Statut', 'Avancement', 'Poids'])
    for task in Tache.objects.filter(working_group__ctm=ctm).select_related('working_group', 'norme', 'assigned_to__user'):
        writer.writerow([
            ctm.name, task.working_group.name, task.norme.reference_number if task.norme else '', task.titre,
            task.assigned_to.full_name if task.assigned_to else '', task.due_date.strftime('%d/%m/%Y') if task.due_date else '',
            task.get_status_display(), task.progress, task.weight,
        ])
    return response


@login_required(login_url='/se-connecter/')
@require_GET
def activity_metric_sources(request):
    """Sources lisibles d'un indicateur, sans adresse réseau ni appareil."""
    _require(request, 'can_view_aggregates')
    metric = request.GET.get('metric', '')
    tasks = Tache.objects.select_related('norme', 'assigned_to__user', 'working_group', 'target_group')
    sessions = ActivitySession.objects.select_related('user')
    if request.GET.get('ctm'):
        tasks = tasks.filter(working_group__ctm_id=request.GET['ctm'])
        sessions = sessions.filter(ctm_id=request.GET['ctm'])
    if request.GET.get('wg'):
        tasks = tasks.filter(working_group_id=request.GET['wg'])
        sessions = sessions.filter(working_group_id=request.GET['wg'])
    if request.GET.get('target_group'):
        tasks = tasks.filter(target_group_id=request.GET['target_group'])
        sessions = sessions.filter(target_group_id=request.GET['target_group'])
    if request.GET.get('norme'):
        tasks = tasks.filter(norme_id=request.GET['norme'])
        sessions = sessions.filter(norme_id=request.GET['norme'])
    start, end = _period(request)
    tasks = tasks.filter(created_at__date__lte=end).prefetch_related('blocked_by')
    items = []
    if metric == 'engagement':
        for session in sessions.filter(last_seen_at__date__gte=start, started_at__date__lte=end).order_by('-last_seen_at')[:100]:
            items.append({
                'title': session.user.get_full_name() or session.user.username,
                'detail': f'{session.active_seconds // 60} min observées · {timezone.localtime(session.last_seen_at):%d/%m/%Y %H:%M}',
                'status': 'Observé',
            })
    else:
        for task in tasks.order_by('titre')[:100]:
            if metric == 'quality' and task.review_status == 'NOT_REVIEWED':
                continue
            items.append({
                'title': task.titre,
                'detail': f'{task.norme.reference_number if task.norme else "Rattachement à confirmer"} · {task.assigned_to.full_name if task.assigned_to else "Sans responsable"}',
                'status': task.get_review_status_display() if metric == 'quality' else task.get_status_display(),
                'value': f'{task.progress} % · poids {task.weight}',
            })
    return JsonResponse({'ok': True, 'metric': metric, 'items': items, 'count': len(items), 'limited': len(items) == 100})

