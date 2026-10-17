"""Read-only CTC supervision, scoped to explicit group assignments."""

from collections import Counter, defaultdict

from django.utils import timezone

from apps.governance.models import CTM, Organe, Tache
from apps.norms.models import Norme


_DONUT_PALETTE = ['#74b9ff', '#c5e736', '#7bcddd', '#9aaec1', '#ffd166', '#8b9cf4', '#f78fb3', '#4dd4ac']


def _performance(tasks):
    """Weighted planned progress; an empty scope has no percentage."""
    planned = sum(task.weight for task in tasks)
    if not planned:
        return None
    return round(sum(task.weight * task.progress for task in tasks) / planned, 1)


def _performance_color(value):
    """Couleur du donut selon l'état de performance (lime / bleu / gris)."""
    if value is None:
        return '#9aaec1'
    if value >= 70:
        return '#c5e736'
    if value >= 40:
        return '#74b9ff'
    return '#9aaec1'


def _donut_segments(items):
    """items: iterable of (label, count). Returns dict {gradient, legend, total} or None."""
    items = [(label, count) for label, count in items if count]
    total = sum(count for _, count in items)
    if total <= 0:
        return None
    legend = []
    stops = []
    acc = 0.0
    for index, (label, count) in enumerate(items):
        color = _DONUT_PALETTE[index % len(_DONUT_PALETTE)]
        start = acc
        acc += count * 100.0 / total
        stops.append(f'{color} {start:.2f}% {min(acc, 100):.2f}%')
        legend.append({'label': label, 'count': count, 'percent': round(count * 100.0 / total), 'color': color})
    return {
        'gradient': f'conic-gradient(from -90deg, {", ".join(stops)})',
        'legend': legend,
        'total': total,
    }


def _coordination(sc):
    today = timezone.localdate()
    posts = list(sc.postes.prefetch_related('mandates__expert__user').order_by('code'))
    result = []
    for post in posts:
        mandate = next((item for item in post.mandates.all()
                        if item.status == 'ACTIVE' and item.capacity == 'ORGANISATION'
                        and (not item.start_date or item.start_date <= today)
                        and (not item.end_date or item.end_date >= today)), None)
        result.append({
            'title': post.title or post.code,
            'holder': mandate.expert.full_name if mandate else 'Titulaire à confirmer',
        })
    return result


def _legacy_coordination(ctm):
    return [
        {'title': 'Président', 'holder': ctm.scientific_president.full_name if ctm.scientific_president else 'Poste vacant'},
        {'title': 'Rapporteur', 'holder': ctm.rapporteur.full_name if ctm.rapporteur else 'Poste vacant'},
        {'title': 'Secrétaire', 'holder': ctm.secretary.full_name if ctm.secretary else 'Poste vacant'},
    ]


def build_ctc_statistics():
    """Build the unified CTM list (CTM == SC) → WG → norms.

    Since CTM and SC are one entity, rows are built from the CTM records only.
    The coordination structure is taken from the matching Phoenix SC (by name)
    when available, falling back to the CTM leadership otherwise.
    """
    today = timezone.localdate()
    rows = []
    source_tasks = {}
    source_norm_ids = set()
    stages = Counter()
    overdue_ids = set()

    # SC (Phoenix) lookup by name, used only to recover the coordination posts.
    sc_by_name = {}
    for sc in Organe.objects.filter(type='SC').prefetch_related('postes', 'postes__mandates__expert__user'):
        sc_by_name[sc.name.casefold()] = sc
        if sc.official_name:
            sc_by_name[sc.official_name.casefold()] = sc

    ctms = list(CTM.objects.select_related(
        'scientific_president__user', 'rapporteur__user', 'secretary__user'
    ).prefetch_related('working_groups').order_by('number'))
    group_ids = [wg.pk for ctm in ctms for wg in ctm.working_groups.all()]
    tasks_by_wg = defaultdict(list)
    for task in Tache.objects.filter(working_group_id__in=group_ids).select_related('norme').order_by('due_date', 'titre'):
        tasks_by_wg[task.working_group_id].append(task)
    norms_by_wg = defaultdict(list)
    for norm in Norme.all_objects.filter(wg_id__in=group_ids).order_by('title'):
        norms_by_wg[norm.wg_id].append(norm)

    for ctm in ctms:
        sc = sc_by_name.get(ctm.name.casefold())
        groups = []
        scoped_tasks = []
        for wg in sorted(ctm.working_groups.all(), key=lambda value: value.name.casefold()):
            tasks = tasks_by_wg[wg.pk]
            norms = norms_by_wg[wg.pk]
            scoped_tasks.extend(tasks)
            group_performance = _performance(tasks)
            groups.append({'id': f'ctm-{wg.pk}', 'code': f'GT {ctm.number}.{wg.number}', 'name': wg.name,
                           'performance': group_performance, 'color': _performance_color(group_performance),
                           'tasks': tasks, 'norms': norms,
                           'status': 'Actif'})
            for norm in norms:
                if norm.pk not in source_norm_ids:
                    stages[norm.get_status_display()] += 1
                    source_norm_ids.add(norm.pk)
        for task in scoped_tasks:
            source_tasks[task.pk] = task
            if task.due_date and task.due_date < today and task.status != 'COMPLETED':
                overdue_ids.add(task.pk)
        rows.append({'id': f'ctm-{ctm.pk}', 'code': f'CTM {ctm.number}', 'name': ctm.name,
                     'status': 'Actif', 'historical': False,
                     'coordination': _coordination(sc) if sc else _legacy_coordination(ctm),
                     'groups': groups,
                     'performance': _performance(scoped_tasks),
                     'color': _performance_color(_performance(scoped_tasks))})

    rows.sort(key=lambda item: (item['name'].casefold(), item['code']))
    largest_stage = max(stages.values(), default=0)
    stage_rows = [
        {'label': label, 'count': count, 'width': round(count * 100 / largest_stage)}
        for label, count in sorted(stages.items())
    ]
    group_norm_rows = [
        {'label': group['name'], 'parent': row['code'], 'count': len(group['norms']),
         'target': group['id']}
        for row in rows for group in row['groups'] if group['norms']
    ]
    largest_group = max((item['count'] for item in group_norm_rows), default=0)
    for item in group_norm_rows:
        item['width'] = round(item['count'] * 100 / largest_group)
    return {'rows': rows, 'sc_count': len(rows), 'group_count': sum(len(row['groups']) for row in rows),
            'norm_count': len(source_norm_ids), 'task_count': len(source_tasks),
            'global_performance': _performance(source_tasks.values()),
            'global_color': _performance_color(_performance(source_tasks.values())),
            'overdue_count': len(overdue_ids), 'stages': sorted(stages.items()),
            'stage_rows': stage_rows, 'stage_donut': _donut_segments(sorted(stages.items())),
            'group_norm_rows': group_norm_rows}
