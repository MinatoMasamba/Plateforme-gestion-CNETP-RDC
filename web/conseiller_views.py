"""Supervision en lecture du conseiller général du Comité de Pilotage."""

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.experts.models import Expert
from apps.governance.activity_supervision import calculate_scope_metrics
from apps.governance.models import (
    ActivityPulse, CTCProcessus, ConsultationConseiller, DemandeAnalyse, GroupeCible, OffPlatformWork,
    Organe, OrganisationVersion, PilotageMembreship, Tache,
)
from apps.norms.models import Norme, NormeComment, NormeVersion
from apps.validation.models import EconomicReview, EcologicalReview, ISOReview, LegisticReview


MENU = [
    ('ensemble', 'Vue d’ensemble', 'layout-dashboard'),
    ('copil', 'COPIL', 'landmark'),
    ('ctc', 'Coordination du Secrétariat technique', 'network'),
    ('sc', 'Sous-commissions', 'users-round'),
    ('normes', 'Normes et rédaction', 'files'),
    ('activite', 'Activité et performances', 'chart-no-axes-combined'),
    ('analyses', 'Instructions et analyses', 'clipboard-list'),
    ('profil', 'Profil', 'id-card'),
]


def conseiller_expert(request):
    expert = Expert.objects.filter(user=request.user, user__is_active=True, status='ACTIVE').select_related('user', 'structure').first()
    if not expert or not PilotageMembreship.objects.filter(expert=expert, role='CONSEILLER').exists():
        raise PermissionDenied('Accès réservé au conseiller général nommé.')
    return expert


def _dates(request):
    today = timezone.localdate()
    try:
        start = date.fromisoformat(request.GET.get('debut', ''))
    except ValueError:
        start = today - timedelta(days=89)
    try:
        end = date.fromisoformat(request.GET.get('fin', ''))
    except ValueError:
        end = today
    if end > today:
        end = today
    if start > end:
        start = end
    if (end - start).days > 365:
        start = end - timedelta(days=365)
    return start, end


def _weeks(start, end):
    first = start - timedelta(days=start.weekday())
    result = []
    while first <= end:
        result.append(first)
        first += timedelta(days=7)
    return result


def _bucket(value, weeks):
    if isinstance(value, datetime):
        value = timezone.localtime(value).date() if timezone.is_aware(value) else value.date()
    if value is None:
        return None
    monday = value - timedelta(days=value.weekday())
    return monday if monday in weeks else None


def _chart(key, title, labels, series, method, count, *, kind='bar', unit=''):
    return {
        'key': key, 'title': title, 'labels': labels,
        'series': [{'name': name, 'values': values} for name, values in series],
        'method': method, 'sources': count, 'configured': count > 0,
        'kind': kind, 'unit': unit,
        'table_rows': [
            {'label': label, 'values': [values[index] for _, values in series]}
            for index, label in enumerate(labels)
        ],
    }


def _week_chart(key, title, weeks, series_counters, method, count, unit=''):
    labels = [week.strftime('%d/%m') for week in weeks]
    series = [(name, [counter.get(week, 0) for week in weeks]) for name, counter in series_counters]
    return _chart(key, title, labels, series, method, count, kind='line', unit=unit)


def _record(label, detail, url='', when=None):
    return {'label': label, 'detail': detail, 'url': url, 'when': when}


@login_required(login_url='/se-connecter/')
@require_GET
def conseiller_dashboard(request):
    expert = conseiller_expert(request)
    start, end = _dates(request)
    weeks = _weeks(start, end)
    active_version = OrganisationVersion.objects.filter(status='ACTIVE').first()
    scs = list(Organe.objects.filter(version=active_version, type='SC', status='ACTIVE').order_by('code')) if active_version else []
    groups = list(GroupeCible.objects.filter(sc__in=scs).select_related('sc').order_by('sc__code', 'code'))
    sc_raw, group_raw, norm_raw, person_raw = (request.GET.get(key, '') for key in ('sc', 'groupe', 'norme', 'personne'))
    sc = next((item for item in scs if str(item.pk) == sc_raw), None)
    group = next((item for item in groups if str(item.pk) == group_raw and (not sc or item.sc_id == sc.pk)), None)
    if group and not sc:
        sc = group.sc
    norm = Norme.all_objects.filter(pk=norm_raw).first() if norm_raw.isdecimal() else None
    person = Expert.objects.filter(pk=person_raw, status='ACTIVE').select_related('user').first() if person_raw.isdecimal() else None
    if person:
        ConsultationConseiller.objects.create(lecteur=request.user, rubrique='PERFORMANCE_PERSONNE', cible=str(person.pk))

    tasks_qs = Tache.objects.filter(created_at__date__lte=end).filter(Q(due_date__isnull=True) | Q(due_date__gte=start))
    if sc:
        tasks_qs = tasks_qs.filter(target_group__sc=sc)
    if group:
        tasks_qs = tasks_qs.filter(target_group=group)
    if norm:
        tasks_qs = tasks_qs.filter(norme=norm)
    if person:
        tasks_qs = tasks_qs.filter(Q(assigned_to=person) | Q(backup_assignee=person))
    tasks = list(tasks_qs.select_related('norme', 'target_group__sc', 'assigned_to__user').order_by('-updated_at'))
    task_norm_ids = {task.norme_id for task in tasks if task.norme_id}
    scope_norms = Norme.all_objects.filter(created_at__date__lte=end)
    if norm:
        scope_norms = scope_norms.filter(pk=norm.pk)
    elif sc or group or person:
        scope_norms = scope_norms.filter(pk__in=task_norm_ids)
    norms = list(scope_norms.order_by('-updated_at'))
    norm_ids = [item.pk for item in norms]
    processes = list(CTCProcessus.objects.filter(norme_id__in=norm_ids, updated_at__date__range=(start, end)).select_related('norme').order_by('-updated_at'))
    versions = list(NormeVersion.all_objects.filter(norme_id__in=norm_ids, created_at__date__range=(start, end)).select_related('norme').order_by('-created_at'))
    comments = list(NormeComment.objects.filter(norme_id__in=norm_ids, created_at__date__range=(start, end)).order_by('-created_at'))
    analyses = list(DemandeAnalyse.objects.filter(Q(emetteur=expert) | Q(destinataire=expert), created_at__date__lte=end).select_related('emetteur__user', 'destinataire__user').order_by('-created_at'))

    completed = Counter(_bucket(task.completed_at, weeks) for task in tasks if task.status == 'COMPLETED' and task.completed_at and start <= task.completed_at.date() <= end)
    task_states = Counter(task.get_status_display() for task in tasks)
    stage_counts = Counter(process.get_current_stage_display() for process in processes)
    norm_statuses = Counter(item.get_status_display() for item in norms)
    group_counts = Counter(task.target_group.code for task in tasks if task.target_group_id)
    version_weeks = Counter(_bucket(item.created_at, weeks) for item in versions)
    comment_weeks = Counter(_bucket(item.created_at, weeks) for item in comments)
    review_counts = Counter(task.get_review_status_display() for task in tasks)
    examination_weeks = Counter()
    examination_source_count = 0
    for model in (LegisticReview, ISOReview, EcologicalReview, EconomicReview):
        for finished_on in model.objects.filter(
            norme_id__in=norm_ids, review_end_date__range=(start, end),
        ).values_list('review_end_date', flat=True):
            examination_weeks[_bucket(finished_on, weeks)] += 1
            examination_source_count += 1
    return_weeks = Counter(_bucket(task.reviewed_at, weeks) for task in tasks
                           if task.review_status == 'RETURNED' and task.reviewed_at
                           and start <= task.reviewed_at.date() <= end)
    due_counts = Counter({'À venir': 0, 'Dépassée': 0})
    today = timezone.localdate()
    for task in tasks:
        if task.status != 'COMPLETED' and task.due_date:
            due_counts['Dépassée' if task.due_date < today else 'À venir'] += 1
    sc_counts = Counter(task.target_group.sc.code for task in tasks if task.target_group_id and task.target_group.sc_id)

    pulse_qs = ActivityPulse.objects.filter(bucket__date__range=(start, end))
    work_qs = OffPlatformWork.objects.filter(status='APPROVED', work_date__range=(start, end))
    if sc:
        pulse_qs = pulse_qs.filter(session__target_group__sc=sc)
        work_qs = work_qs.filter(target_group__sc=sc)
    if group:
        pulse_qs = pulse_qs.filter(session__target_group=group)
        work_qs = work_qs.filter(target_group=group)
    if norm:
        pulse_qs = pulse_qs.filter(session__norme=norm)
        work_qs = work_qs.filter(norme=norm)
    if person:
        pulse_qs = pulse_qs.filter(session__user=person.user)
        work_qs = work_qs.filter(expert=person)
    pulse_count = pulse_qs.count()
    work_count = work_qs.count()
    observed = defaultdict(int)
    declared = defaultdict(int)
    for bucket, seconds in pulse_qs.values_list('bucket', 'credited_seconds').iterator():
        observed[_bucket(bucket, weeks)] += seconds
    for work_date, minutes in work_qs.values_list('work_date', 'minutes').iterator():
        declared[_bucket(work_date, weeks)] += minutes
    observed = {key: round(value / 60) for key, value in observed.items()}

    sent_counts = Counter(item.get_statut_display() for item in analyses if item.emetteur_id == expert.pk)
    received_counts = Counter(item.get_statut_display() for item in analyses if item.destinataire_id == expert.pk)
    response_times = defaultdict(list)
    for item in analyses:
        if item.cloturee_le and item.repondue_le and start <= item.cloturee_le.date() <= end:
            response_times[_bucket(item.cloturee_le, weeks)].append(round((item.repondue_le - item.created_at).total_seconds() / 86400, 1))
    response_avg = {week: round(sum(values) / len(values), 1) for week, values in response_times.items()}
    sent_weeks = Counter(_bucket(item.created_at, weeks) for item in analyses if item.emetteur_id == expert.pk and start <= item.created_at.date() <= end)
    received_weeks = Counter(_bucket(item.created_at, weeks) for item in analyses if item.destinataire_id == expert.pk and start <= item.created_at.date() <= end)
    treated_weeks = Counter(_bucket(item.repondue_le, weeks) for item in analyses if item.destinataire_id == expert.pk and item.repondue_le and start <= item.repondue_le.date() <= end)

    activity_url = reverse('web:activity_dashboard')
    analysis_url = reverse('web:conseiller_analysis_list')
    sections = [
        {'key': 'ensemble', 'title': 'Vue d’ensemble', 'lead': 'Production suivie et dossiers du circuit.', 'charts': [
            _week_chart('ensemble-taches', 'Tâches terminées par semaine', weeks, [('Terminées', completed)], 'Tâches du périmètre terminées à la date enregistrée.', len(tasks)),
            _chart('ensemble-dossiers', 'Dossiers par étape', list(stage_counts), [('Dossiers', list(stage_counts.values()))], 'Étape actuelle des dossiers CTC mis à jour dans la période.', len(processes)),
        ], 'records': [_record(task.titre, task.get_status_display(), activity_url, task.due_date) for task in tasks[:15]], 'link': activity_url, 'link_label': 'Voir les activités'},
        {'key': 'copil', 'title': 'COPIL', 'lead': 'Lecture du circuit et des échéances.', 'charts': [
            _chart('copil-etapes', 'Dossiers par étape', list(stage_counts), [('Dossiers', list(stage_counts.values()))], 'Étape CTC actuelle des dossiers mis à jour dans la période.', len(processes)),
            _chart('copil-echeances', 'Échéances des tâches ouvertes', list(due_counts), [('Tâches', list(due_counts.values()))], 'Tâches non terminées disposant d’une échéance.', sum(due_counts.values())),
        ], 'records': [_record(p.norme.reference_number, p.get_current_stage_display(), activity_url, p.updated_at) for p in processes[:20]], 'link': activity_url, 'link_label': 'Voir les dossiers'},
        {'key': 'ctc', 'title': 'Coordination du Secrétariat technique', 'lead': 'Normes et examens du circuit technique.', 'charts': [
            _chart('ctc-statuts', 'Normes par statut', list(norm_statuses), [('Normes', list(norm_statuses.values()))], 'Statut actuel des normes du périmètre.', len(norms)),
            _chart('ctc-groupes', 'Tâches par groupe actuel', list(group_counts), [('Tâches', list(group_counts.values()))], 'Tâches rattachées explicitement à un groupe actuel.', sum(group_counts.values())),
            _week_chart('ctc-examens', 'Examens terminés et tâches retournées', weeks, [('Examens', examination_weeks), ('Retours', return_weeks)], 'Examens avec date de fin enregistrée ; retours avec date de revue enregistrée.', examination_source_count + sum(return_weeks.values())),
        ], 'records': [_record(p.norme.reference_number, p.get_current_stage_display(), reverse('web:conseiller_ctc_observation'), p.updated_at) for p in processes[:20]], 'link': reverse('web:conseiller_ctc_observation'), 'link_label': 'Ouvrir la coordination en observation'},
        {'key': 'sc', 'title': 'Sous-commissions', 'lead': 'Travaux des SC actuelles.', 'charts': [
            _chart('sc-etats', 'Tâches par état', list(task_states), [('Tâches', list(task_states.values()))], 'État actuel des tâches du périmètre.', len(tasks)),
            _week_chart('sc-progression', 'Tâches terminées par semaine', weeks, [('Terminées', completed)], 'Date de fin enregistrée des tâches.', len(tasks)),
            _chart('sc-repartition', 'Tâches par SC', list(sc_counts), [('Tâches', list(sc_counts.values()))], 'Rattachement explicite des tâches aux SC actuelles.', sum(sc_counts.values())),
        ], 'records': [_record(task.titre, task.get_status_display(), activity_url, task.due_date) for task in tasks if task.target_group_id][:20], 'link': reverse('web:conseiller_sc_observation'), 'link_label': 'Ouvrir la vue SC en observation'},
        {'key': 'normes', 'title': 'Normes et rédaction', 'lead': 'Versions et commentaires conservés.', 'charts': [
            _week_chart('normes-versions', 'Rédaction par semaine', weeks, [('Versions', version_weeks), ('Commentaires', comment_weeks)], 'Versions et commentaires créés dans la période.', len(versions) + len(comments)),
            _chart('normes-etats', 'Normes par statut', list(norm_statuses), [('Normes', list(norm_statuses.values()))], 'Statut actuel des normes du périmètre.', len(norms)),
        ], 'records': [_record(f'{v.norme.reference_number} · v{v.version_number}', v.title, reverse('web:conseiller_sc_observation'), v.created_at) for v in versions[:20]], 'link': reverse('web:conseiller_sc_observation'), 'link_label': 'Lire les versions'},
        {'key': 'activite', 'title': 'Activité et performances', 'lead': 'Indicateurs séparés et sources consultables.', 'charts': [
            _chart('activite-taches', 'Tâches par état', list(task_states), [('Tâches', list(task_states.values()))], 'État actuel des tâches affectées au périmètre.', len(tasks)),
            _chart('activite-avis', 'Avis sur les tâches', list(review_counts), [('Avis', list(review_counts.values()))], 'Statut de revue enregistré sur chaque tâche.', len(tasks)),
            _week_chart('activite-temps', 'Minutes observées et déclarées', weeks, [('Observées', observed), ('Déclarées approuvées', declared)], 'Observées : battements visibles crédités. Déclarées : travail hors plateforme approuvé. Ce total ne mesure pas tout le temps travaillé.', pulse_count + work_count, 'min'),
        ], 'records': [_record(task.titre, f'{task.get_status_display()} · {task.get_review_status_display()}', activity_url, task.due_date) for task in tasks[:20]], 'link': activity_url, 'link_label': 'Voir les sources d’activité'},
        {'key': 'analyses', 'title': 'Instructions et analyses', 'lead': 'Demandes d’analyse traçables.', 'charts': [
            _chart('analyses-etats', 'Demandes par état', sorted(set(sent_counts) | set(received_counts)), [('Émises', [sent_counts[key] for key in sorted(set(sent_counts) | set(received_counts))]), ('Reçues', [received_counts[key] for key in sorted(set(sent_counts) | set(received_counts))])], 'Demandes auxquelles le conseiller participe, par état actuel.', len(analyses)),
            _week_chart('analyses-delais', 'Délai moyen des réponses clôturées', weeks, [('Jours', response_avg)], 'Jours entre création et réponse, pour les demandes clôturées dans la période.', sum(len(values) for values in response_times.values()), 'jours'),
        ], 'records': [_record(a.objet, a.get_statut_display(), reverse('web:conseiller_analysis_detail', args=[a.pk]), a.created_at) for a in analyses[:20]], 'link': analysis_url, 'link_label': 'Ouvrir les demandes'},
        {'key': 'profil', 'title': 'Profil', 'lead': 'Mandat et activité personnelle du conseiller.', 'charts': [
            _week_chart('profil-demandes', 'Activité de conseil par semaine', weeks, [('Émises', sent_weeks), ('Reçues', received_weeks), ('Traitées', treated_weeks)], 'Demandes créées et réponses enregistrées pour ce conseiller.', len(analyses)),
        ], 'records': [_record(a.objet, a.get_statut_display(), reverse('web:conseiller_analysis_detail', args=[a.pk]), a.created_at) for a in analyses[:15]], 'link': reverse('web:expert_profile'), 'link_label': 'Ouvrir mon profil complet'},
    ]
    # Les indicateurs de performance existants restent calculés séparément.
    metrics = calculate_scope_metrics(start=start, end=end, target_group=group, norme=norm, expert=person) if (group or norm or person) else None
    people = Expert.objects.filter(status='ACTIVE', user__is_active=True).select_related('user').order_by('user__last_name')[:300]
    return render(request, 'pilotage/conseiller/dashboard.html', {
        'expert': expert, 'menu': MENU, 'sections': sections,
        'start': start, 'end': end, 'scs': scs, 'groups': groups,
        'norms': Norme.all_objects.order_by('reference_number')[:300], 'people': people,
        'selected_sc': sc, 'selected_group': group, 'selected_norm': norm, 'selected_person': person,
        'metrics': metrics,
    })


@login_required(login_url='/se-connecter/')
@require_GET
def ctc_observation(request):
    conseiller_expert(request)
    ConsultationConseiller.objects.create(lecteur=request.user, rubrique='CTC_OBSERVATION')
    start, end = _dates(request)
    processes = CTCProcessus.objects.filter(updated_at__date__range=(start, end)).select_related('norme').order_by('-updated_at')
    return render(request, 'pilotage/conseiller/ctc_observation.html', {
        'processes': processes[:100], 'start': start, 'end': end,
        'stage_counts': [(label, processes.filter(current_stage=code).count()) for code, label in CTCProcessus.STAGE_CHOICES],
    })
