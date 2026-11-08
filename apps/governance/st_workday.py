"""Agrégateur « Mon travail du jour » et tableaux de bord des cinq espaces.

Les blocs sont calculés à partir des données réelles. Aucun écran ne fabrique
un chiffre : une absence de données est rendue comme une absence.
"""
from datetime import timedelta
from django.db.models import Prefetch, F
from django.urls import reverse
from django.utils import timezone

from .st_status import process_status
from .st_permissions import effective_mandates, visible_processus, visible_tasks, visible_meetings

STAGE_LABELS = {
    'RECEPTION': 'Réception',
    'GEOSPATIAL': 'Traitement géospatial',
    'MULTI_REVIEW': 'Examens parallèles',
    'INDUSTRIAL': 'Consultation industrielle',
    'SIGNED_OUT': 'Transmise au Pilotage',
}


def _post_number(context):
    code = context.get('st_post_code') or ''
    if code.startswith('ST-V3-'):
        try:
            return int(code.split('-')[-1])
        except ValueError:
            return None
    return None


def _item(kind, reference, title, status, url='#dossiers', action='', due=None, tone='info'):
    return {
        'kind': kind,
        'reference': reference or '—',
        'title': title or 'Sans intitulé',
        'status': status,
        'url': url or '#dossiers',
        'action': action,
        'due': due,
        'tone': tone,
    }


def _processus_url(processus):
    try:
        return reverse('web:ctc_norme_read', args=[processus.norme_id])
    except Exception:
        return '#dossiers'


def _visible_processus(expert, context):
    from .models import Tache
    return visible_processus(expert, context).prefetch_related(Prefetch(
        'norme__tasks', queryset=Tache.objects.filter(status='BLOCKED').only('titre', 'description'),
        to_attr='blocked_tasks',
    ))


def _pending_records(context, head):
    from .st_operations_models import STRecord
    from django.db.models import F
    number = _post_number(context)
    pole = context.get('ctc_pole')
    if number not in (10, 13, 14, 17):
        return STRecord.objects.none()
    if pole == 'ST-P2':
        kinds = ['PTN']
    elif pole == 'ST-P3':
        kinds = ['FINANCE']
    else:
        return STRecord.objects.none()
    return (
        STRecord.objects.filter(version_id=context['poste'].organe.version_id,
            kind__in=kinds, pole=pole, versions__number=F('revision'), versions__confirmation__isnull=True)
        .distinct()
        .select_related('created_by')
        .order_by('-updated_at')[:20]
    )


def build_workday(expert, context):
    from apps.governance.models import CTCOperationalRequest
    from apps.core.models import AuditLog

    number = _post_number(context)
    head = bool(context.get('st_is_supervisor', context.get('st_is_pole_head')))
    now = timezone.now()
    week_end = now + timedelta(days=7)
    todo, waiting, deadlines, recent = [], [], [], []

    processus_qs = _visible_processus(expert, context)
    for processus in processus_qs[:80]:
        display = process_status(processus)
        item = _item(
            'Dossier', processus.norme.reference_number,
            processus.norme.title, display['label'], _processus_url(processus),
            tone=display['tone'],
        )
        if display['code'] == 'BLOQUEE':
            item['status'] = f"Bloquée — {display['motif']}"
            todo.append(item)
        elif number in (1, 2, 3, 4, 5):
            if display['code'] in ('INDEXATION_TERMINEE', 'EXAMEN_EN_COURS', 'CONSOLIDATION_TERMINEE'):
                item['action'] = 'Valider ou renvoyer'
                todo.append(item)
            else:
                waiting.append(item)
        elif number == 6:
            if display['code'] == 'ENREGISTREE':
                item['action'] = 'Enregistrer la réception'
                todo.append(item)
            elif display['code'] in ('RAPPORT_RECU', 'REVUE_SC_ATTENTE'):
                item['action'] = 'Enregistrer le rapport de SC'
                todo.append(item)
            else:
                waiting.append(item)
        elif number in (10, 11):
            if display['code'] == 'RAPPORT_RECU':
                item['action'] = 'Indexer le dossier'
                todo.append(item)
            else:
                waiting.append(item)
        elif number in (8, 9):
            if display['code'] in ('EXAMEN_EN_COURS', 'CONSOLIDATION_TERMINEE'):
                item['action'] = 'Suivre ou confirmer'
                todo.append(item)
            else:
                waiting.append(item)
        elif number in (13, 14):
            if display['code'] in ('EXAMEN_EN_COURS',):
                item['action'] = 'Rendre l’avis juridique'
                todo.append(item)
            else:
                waiting.append(item)
        else:
            waiting.append(item)

    for record in _pending_records(context, head):
        latest = record.versions.order_by('-number').first()
        if not latest:
            continue
        item = _item(
            record.get_kind_display(), record.reference, latest.title,
            'À confirmer' if head else 'En attente du chef de pôle',
            '#ptn' if record.kind == 'PTN' else '#financial',
            action='Confirmer l’état' if head else '',
            tone='warning',
        )
        (todo if head else waiting).append(item)

    if number in (1, 2, 3, 4, 5):
        for request in CTCOperationalRequest.objects.filter(status='PENDING').select_related('requester__user')[:10]:
            todo.append(_item(
                'Demande', f'Demande #{request.pk}',
                (request.motif or request.resource or 'Demande d’accès'),
                'En attente de décision', '#ctc_requests', action='Approuver ou rejeter',
                tone='warning',
            ))

    tasks = visible_tasks(expert, context).filter(
        status__in=['PLANNED', 'IN_PROGRESS', 'BLOCKED', 'ON_HOLD'],
    ).select_related('norme').order_by('due_date', 'pk')
    for task in tasks:
        due = task.due_date
        item = _item(
            'Tâche',
            task.norme.reference_number if task.norme_id else f'Tâche #{task.pk}',
            task.titre,
            task.get_status_display(),
            _processus_url(task.norme.ctc_processus) if task.norme_id and hasattr(task.norme, 'ctc_processus') else '#assignations',
            action='Traiter',
            due=due,
            tone='danger' if task.status == 'BLOCKED' else 'info',
        )
        if due and due < timezone.localdate():
            deadlines.append(item)
        elif task.assigned_to_id == expert.pk or task.backup_assignee_id == expert.pk or head:
            todo.append(item)
        else:
            waiting.append(item)
        if due and timezone.localdate() <= due <= week_end.date():
            deadlines.append(item)

    for reunion in visible_meetings(expert, context).filter(date__gte=now, date__lte=week_end):
        item = _item(
            'Réunion', reunion.get_type_display(), reunion.titre,
            reunion.get_status_display(), '#reunions', action='Consulter',
            due=reunion.date, tone='info',
        )
        deadlines.append(item)

    for entry in AuditLog.objects.filter(user=expert.user).order_by('-timestamp')[:10]:
        recent.append(_item(
            'Action', entry.content_type or 'Journal',
            entry.object_repr or entry.action,
            entry.get_action_display() if hasattr(entry, 'get_action_display') else entry.action,
            '#tracabilite', tone='neutral',
        ))

    alerts = []
    for item in deadlines:
        if item.get('due') and getattr(item['due'], 'date', None):
            due_date = item['due'].date()
        else:
            due_date = item.get('due')
        if due_date and due_date <= timezone.localdate():
            alerts.append({**item, 'severity': 'danger'})
        elif due_date and due_date <= timezone.localdate() + timedelta(days=2):
            alerts.append({**item, 'severity': 'warning'})
    blocked = [item for item in todo if 'Bloquée' in item['status'] or item['tone'] == 'danger']
    alerts.extend({**item, 'severity': 'danger'} for item in blocked[:5])

    return {
        'blocks': {
            'todo': todo[:12],
            'waiting': waiting[:12],
            'deadlines': deadlines[:12],
            'recent': recent[:12],
        },
        'counts': {
            'todo': len(todo),
            'waiting': len(waiting),
            'deadlines': len(deadlines),
            'recent': len(recent),
        },
        'alerts': alerts[:8],
        'generated_at': now,
    }


def build_space_dashboard(expert, context):

    pole = context.get('ctc_pole')
    head = bool(context.get('st_is_supervisor', context.get('st_is_pole_head')))
    qs = _visible_processus(expert, context)
    distribution = {}
    for processus in qs:
        display = process_status(processus)
        distribution[display['label']] = distribution.get(display['label'], 0) + 1

    from .st_operations import visible_records
    pole_records = visible_records(expert.user).filter(pole=pole)
    if pole == 'ST-P2':
        pole_records = pole_records.filter(kind='PTN')
    tasks = visible_tasks(expert, context).filter(
        status__in=['PLANNED', 'IN_PROGRESS', 'BLOCKED', 'ON_HOLD'],
    )
    members = []
    if pole and head:
        mandates = effective_mandates(context).filter(poste__organe__code=pole).select_related(
            'expert__user', 'poste').order_by('poste__code')
        for mandate in mandates:
            members.append({
                'name': mandate.expert.user.get_full_name() or mandate.expert.user.username,
                'post': mandate.poste.code, 'title': mandate.poste.title,
                'head': mandate.poste.category == 'POLE_HEAD',
                'tasks': tasks.filter(assigned_to=mandate.expert).count(),
            })
    upcoming_qs = visible_meetings(expert, context).filter(date__gte=timezone.now())
    upcoming = upcoming_qs[:5]
    overdue_tasks = tasks.filter(due_date__lt=timezone.localdate()).count()
    blocked_tasks = tasks.filter(status='BLOCKED').count()

    return {
        'space': context.get('st_space'),
        'space_label': context.get('st_space_label'),
        'kpis': {
            'dossiers': qs.count(),
            'todo': len([1 for p in qs if process_status(p)['code'] in ('EXAMEN_EN_COURS', 'INDEXATION_TERMINEE', 'CONSOLIDATION_TERMINEE')]),
            'records': pole_records.count(),
            'confirmed': pole_records.filter(versions__number=F('revision'), versions__confirmation__decision='CONFIRMED').distinct().count(),
            'tasks': tasks.count(),
            'overdue': overdue_tasks,
            'blocked': blocked_tasks,
            'meetings': upcoming_qs.count(),
            'members': len(members),
        },
        'distribution': [dict(label=label, count=count, percent=round(100 * count / max(qs.count(), 1)))
                         for label, count in sorted(distribution.items())],
        'members': members,
        'upcoming_meetings': upcoming,
        'head': head,
        'role_label': context.get('poste').title if context.get('poste') else '',
    }
