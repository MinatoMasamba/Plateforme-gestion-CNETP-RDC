"""Supervision CTC : journal de requêtes et traces historiques conservées."""
from collections import Counter
from datetime import datetime, time, timedelta
from pathlib import PurePosixPath
from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.core.models import AuditLog, User
from apps.documents.models import DocumentFile
from apps.experts.models import Expert
from apps.governance.models import CTCMembership, CTCProcessus
from apps.norms.models import Norme, NormeVersion

KINDS = {
    'edition': 'Édition de documents', 'validation': 'Examens et validations',
    'transmission': 'Transmissions', 'reception': 'Réception et indexation',
    'creation': 'Créations et dépôts', 'commentaire': 'Commentaires',
    'suppression': 'Suppressions', 'traitement': 'Autres traitements',
}
STAGE_LABELS = {
    'RECEPTION': 'Réception', 'GEOSPATIAL': 'Traitement SIG',
    'MULTI_REVIEW': 'Examens parallèles', 'INDUSTRIAL': 'Consultation industrielle',
    'SIGNED_OUT': 'Transmis au Pilotage',
}

FIELD_LABELS = {
    'title': 'Titre', 'content': 'Texte du document', 'body': 'Commentaire',
    'summary': 'Résumé des changements', 'description': 'Description',
    'document': 'Fichier de la version', 'file': 'Fichier', 'filename': 'Nom du fichier',
    'current_stage': 'Étape', 'status': 'Statut', 'planner_status': 'Validation du chronogramme',
    'scientist_status': 'Validation scientifique', 'planner_notes': 'Observations sur le chronogramme',
    'scientist_notes': 'Observations scientifiques', 'harmonization_notes': 'Notes d’harmonisation',
    'comments': 'Observations', 'fec_feedback': 'Avis industriel',
    'received_at': 'Réception', 'indexed_at': 'Indexation',
    'intake_validated_at': 'Introduction dans le circuit', 'sig_completed_at': 'Traitement SIG',
    'signed_out_at': 'Signature de sortie', 'transmitted_to_pilotage_at': 'Transmission au Pilotage',
    'version_number': 'Numéro de version', 'reference_number': 'Référence',
    'is_draft': 'Brouillon', 'review_start_date': 'Début de l’examen',
    'review_end_date': 'Fin de l’examen', 'all_reviews_completed': 'Examens terminés',
    'industrial_completed_at': 'Consultation industrielle terminée',
}


def _filter_date(value, fallback):
    try:
        parsed = parse_date(value[:10])
        return parsed if parsed and parsed.year < 9999 else fallback
    except ValueError:
        return fallback


def _browser(agent):
    browser = next((name for token, name in (
        ('Edg/', 'Edge'), ('Firefox/', 'Firefox'), ('Chrome/', 'Chrome'),
        ('Safari/', 'Safari'),
    ) if token in agent), 'Navigateur non renseigné')
    device = next((name for token, name in (
        ('Android', 'Android'), ('iPhone', 'iPhone'), ('iPad', 'iPad'),
        ('Windows', 'Windows'), ('Macintosh', 'macOS'), ('Linux', 'Linux'),
    ) if token in agent), '')
    return ' · '.join(filter(None, (browser, device)))


def _audit_description(log):
    fields = log.changes.get('fields', {})
    model = log.content_type.rsplit('.', 1)[-1]
    if log.action == 'DELETE':
        document_event = model in ('NormeVersion', 'DocumentFile', 'NormeDocumentImport')
        return 'suppression', 'Document supprimé' if document_event else 'Suppression', document_event
    if model in ('NormeVersion', 'DocumentFile', 'NormeDocumentImport'):
        label = 'Nouvelle version' if model == 'NormeVersion' and log.action == 'CREATE' else (
            'Dépôt de document' if log.action == 'CREATE' else 'Document modifié'
        )
        return ('creation' if model == 'DocumentFile' and log.action == 'CREATE' else 'edition'), label, True
    if model == 'NormeComment':
        return 'commentaire', 'Commentaire ajouté' if log.action == 'CREATE' else 'Commentaire modifié', False
    if model == 'CTCProcessus':
        if log.action == 'CREATE':
            return 'creation', 'Dossier créé dans le circuit CTC', False
        steps = (
            ('received_at', 'Dossier réceptionné', 'reception'),
            ('indexed_at', 'Mise en page et indexation finalisées', 'reception'),
            ('intake_validated_at', 'Introduction dans le circuit validée', 'validation'),
            ('sig_completed_at', 'Traitement SIG terminé', 'traitement'),
            ('signed_out_at', 'Dossier signé et transmis au Pilotage', 'transmission'),
        )
        for field, label, kind in reversed(steps):
            if fields.get(field, {}).get('after'):
                return kind, label, False
        stage = fields.get('current_stage', {}).get('after')
        if stage:
            return 'traitement', 'Étape : ' + STAGE_LABELS.get(stage, stage), False
    if log.action in ('APPROVE', 'REJECT'):
        return 'validation', 'Examen approuvé' if log.action == 'APPROVE' else 'Examen refusé', False
    if log.action == 'CREATE':
        return 'creation', 'Création', False
    return 'traitement', 'Mise à jour', False


def _change_details(fields):
    details = []
    for name, change in fields.items():
        before, after = change.get('before'), change.get('after')
        label = FIELD_LABELS.get(name, 'Champ ' + change.get('label', name).replace('_', ' ')).capitalize()
        if isinstance(before, dict) or isinstance(after, dict):
            old_size = before.get('length', 0) if isinstance(before, dict) else 0
            new_size = after.get('length', 0) if isinstance(after, dict) else 0
            details.append(f'{label} : contenu modifié ({old_size} → {new_size} caractères)')
        else:
            details.append(f'{label} : {before or "—"} → {after or "—"}')
    return details


def _historical_events(processes, covered):
    events = []
    milestones = (
        ('received_at', 'received_by', 'Dossier réceptionné', 'reception'),
        ('indexed_at', None, 'Mise en page et indexation finalisées', 'reception'),
        ('intake_validated_at', 'intake_validated_by', 'Introduction dans le circuit validée', 'validation'),
        ('sig_completed_at', 'sig_completed_by', 'Traitement SIG terminé', 'traitement'),
        ('signed_out_at', 'signed_out_by', 'Dossier signé et transmis au Pilotage', 'transmission'),
    )
    for process in processes:
        for field, actor_field, label, kind in milestones:
            stamp = getattr(process, field)
            if not stamp or ('governance.CTCProcessus', process.pk, field) in covered:
                continue
            actor = getattr(process, actor_field) if actor_field else None
            events.append({
                'time': stamp, 'user_id': actor.user_id if actor else None,
                'kind': kind, 'label': label, 'object': process.norme.reference_number,
                'reference': process.norme.reference_number, 'title': process.norme.title,
                'norme_id': process.norme_id, 'ctm_number': process.norme.ctm.number,
                'document': '', 'document_event': False, 'source': 'historique',
                'channel': 'Circuit CTC', 'path': '', 'ip': '', 'device': '',
                'details': ['Trace conservée dans le dossier. L’origine de connexion n’était pas enregistrée.'],
            })
    return events


def build_ctc_supervision(request, ctm=None):
    today = timezone.localdate()
    start_date = _filter_date(request.GET.get('from', ''), today - timedelta(days=29))
    end_date = _filter_date(request.GET.get('to', ''), today)
    error = ''
    if start_date > end_date:
        start_date, end_date = end_date, start_date
        error = 'Les dates ont été remises dans l’ordre chronologique.'
    if (end_date - start_date).days > 365:
        start_date = end_date - timedelta(days=365)
        error = 'La période de consultation est limitée à un an.'
    start = timezone.make_aware(datetime.combine(start_date, time.min))
    end = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), time.min))
    selected_user = request.GET.get('ctc_user', '')
    selected_user = selected_user if selected_user.isdecimal() else ''
    selected_kind = request.GET.get('ctc_action', '')
    selected_kind = selected_kind if selected_kind in KINDS else ''
    search = request.GET.get('ctc_document', '').strip()[:200]

    normes = Norme.objects.filter(ctm=ctm) if ctm else Norme.objects.filter(ctc_processus__isnull=False)
    norme_ids = normes.values_list('pk', flat=True)
    scope = (Q(changes__scope='ctc') | Q(changes__scope='ctm', changes__norme_id__in=norme_ids)) if not ctm else (
        Q(changes__scope__in=['ctc', 'ctm']) &
        (Q(changes__norme_id__in=norme_ids) | Q(changes__ctm_number=ctm.number))
    )
    logs = list(AuditLog.objects.filter(scope, timestamp__gte=start, timestamp__lt=end).order_by('-timestamp', '-pk'))
    covered = set()
    events = []
    for log in logs:
        meta = log.changes
        for field in meta.get('fields', {}):
            covered.add((log.content_type, log.object_id, field))
        if log.action == 'CREATE':
            covered.add((log.content_type, log.object_id, 'created'))
        kind, label, document_event = _audit_description(log)
        events.append({
            'time': log.timestamp, 'user_id': log.user_id, 'kind': kind,
            'label': label, 'object': log.object_repr, 'reference': meta.get('reference', ''),
            'title': meta.get('title', ''), 'norme_id': meta.get('norme_id'),
            'ctm_number': meta.get('ctm_number'), 'document': meta.get('document', ''),
            'document_event': document_event, 'source': 'journal',
            'document_key': f'{log.content_type}:{log.object_id}',
            'recorded_structure': meta.get('actor_structure', ''),
            'recorded_role': meta.get('actor_role', ''),
            'channel': meta.get('channel', 'Plateforme'), 'path': meta.get('path', ''),
            'ip': log.ip_address or '', 'device': _browser(log.user_agent),
            'details': ([meta['summary']] if meta.get('summary') else []) + _change_details(meta.get('fields', {})),
            'history_url': reverse('web:pilotage_activity_history', args=[log.pk]),
        })

    processes = list(CTCProcessus.objects.filter(norme_id__in=norme_ids).select_related(
        'norme__ctm', 'received_by', 'intake_validated_by', 'sig_completed_by', 'signed_out_by',
    ))
    events.extend(_historical_events(processes, covered))
    versions = NormeVersion.objects.filter(
        norme_id__in=norme_ids, created_at__gte=start, created_at__lt=end,
    ).select_related('norme__ctm')
    documents = DocumentFile.objects.filter(
        norme_id__in=norme_ids, created_at__gte=start, created_at__lt=end,
    ).select_related('norme__ctm')
    for model, items in (('norms.NormeVersion', versions), ('documents.DocumentFile', documents)):
        for item in items:
            if (model, item.pk, 'created') in covered:
                continue
            version = model == 'norms.NormeVersion'
            document = item.document if version else item.file
            events.append({
                'time': item.created_at, 'user_id': item.version_author_id if version else item.uploaded_by_id,
                'kind': 'edition' if version else 'creation',
                'label': f'Nouvelle version v{item.version_number}' if version else 'Dépôt de document',
                'object': f'{item.norme.reference_number} v{item.version_number}' if version else item.title,
                'reference': item.norme.reference_number, 'title': item.title,
                'norme_id': item.norme_id, 'ctm_number': item.norme.ctm.number,
                'document': PurePosixPath(str(document)).name if document else '',
                'document_event': True, 'source': 'historique', 'channel': 'Documents',
                'document_key': f'{model}:{item.pk}',
                'path': '', 'ip': '', 'device': '',
                'details': [item.summary] if version and item.summary else ['Création conservée dans l’historique du document.'],
                'history_url': reverse('web:pilotage_norme_history', args=[item.norme_id]) + (f'?version_id={item.pk}' if version else ''),
            })

    events = [event for event in events if start <= event['time'] < end]
    user_ids = {event['user_id'] for event in events if event['user_id']}
    users = User.objects.in_bulk(user_ids)
    experts = {
        expert.user_id: expert for expert in Expert.objects.filter(user_id__in=user_ids).select_related('structure')
    }
    roles = {membership.expert.user_id: membership.get_role_display()
             for membership in CTCMembership.objects.filter(expert__user_id__in=user_ids).select_related('expert')}
    user_options = sorted(
        [{'id': user.pk, 'name': user.get_full_name() or user.username} for user in users.values()],
        key=lambda item: item['name'].casefold(),
    )
    events = [event for event in events
              if (not selected_user or str(event['user_id']) == selected_user)
              and (not selected_kind or event['kind'] == selected_kind)
              and (not search or search.casefold() in ' '.join(
                  str(event.get(field) or '') for field in ('title', 'reference', 'document', 'object')
              ).casefold())]
    events.sort(key=lambda event: event['time'], reverse=True)
    collaborators = {}
    documents_summary = {}
    for event in events:
        if not event.get('history_url') and event.get('norme_id'):
            event['history_url'] = reverse('web:pilotage_norme_history', args=[event['norme_id']])
        user = users.get(event['user_id'])
        expert = experts.get(event['user_id'])
        event['user_name'] = user.get_full_name() or user.username if user else 'Auteur non enregistré'
        event['email'] = user.email if user else ''
        event['structure'] = event.get('recorded_structure') or (expert.structure.name if expert else 'Structure non renseignée')
        event['role'] = event.get('recorded_role') or roles.get(event['user_id'], 'Contributeur au dossier')
        event['kind_label'] = KINDS[event['kind']]
        if user:
            collaborator = collaborators.setdefault(user.pk, {
                'id': user.pk, 'name': event['user_name'], 'email': user.email,
                'structure': event['structure'], 'role': event['role'],
                'count': 0, 'edits': 0, 'last_activity': event['time'],
            })
            collaborator['count'] += 1
            collaborator['edits'] += int(event['document_event'])
        if event['document_event']:
            key = event['document_key']
            document = documents_summary.setdefault(key, {
                'title': event['document'] or event['object'], 'reference': event['reference'],
                'count': 0, 'last_activity': event['time'], 'last_user': event['user_name'],
                'last_action': event['label'], 'ctm_number': event['ctm_number'],
            })
            document['count'] += 1

    stage_counts = Counter(normes.values_list('status', flat=True)) if ctm else Counter(process.current_stage for process in processes)
    stage_labels = dict(Norme.STATUS_CHOICES) if ctm else STAGE_LABELS
    kind_counts = Counter(event['kind'] for event in events)
    actor_counts = Counter((event['user_id'], event['user_name']) for event in events)
    name_counts = Counter(user.get_full_name() or user.username for user in users.values())

    def actor_label(key):
        user_id, name = key
        if user_id in users and name_counts[name] > 1:
            return f'{name} · {users[user_id].username}'
        return name
    day_counts = Counter(timezone.localdate(event['time']).isoformat() for event in events)
    timeline = []
    day = start_date
    while day <= end_date:
        timeline.append({'label': day.strftime('%d/%m'), 'date': day.isoformat(), 'count': day_counts[day.isoformat()]})
        day += timedelta(days=1)
    chart_data = {
        'stages': [{'label': label, 'count': stage_counts[stage]} for stage, label in stage_labels.items()],
        'actions': [{'label': KINDS[kind], 'count': count} for kind, count in kind_counts.items()],
        'users': [{'label': actor_label(key), 'count': count} for key, count in actor_counts.most_common(7)],
        'timeline': timeline,
    }
    if len(actor_counts) > 7:
        chart_data['users'].append({'label': 'Autres contributeurs', 'count': sum(count for _, count in actor_counts.most_common()[7:])})
    parameters = {
        'from': start_date.isoformat(), 'to': end_date.isoformat(),
        'ctc_user': selected_user, 'ctc_action': selected_kind, 'ctc_document': search,
    }
    query = urlencode(parameters)
    page = Paginator(events, 25).get_page(request.GET.get('ctc_log_page'))
    document_page = Paginator(list(documents_summary.values()), 10).get_page(request.GET.get('ctc_doc_page'))
    return {
        'ctc_supervision': {
            'is_ctm': ctm is not None,
            'title': f'Supervision du CTM {ctm.number}' if ctm else 'Supervision de l’équipe CTC',
            'dossier_label': 'Dossiers du CTM' if ctm else 'Dossiers CTC',
            'stage_title': 'État des dossiers du CTM' if ctm else 'État du circuit CTC',
            'stage_caption': f'Situation actuelle des dossiers du CTM {ctm.number}' if ctm else 'Situation actuelle de l’ensemble des dossiers CTC',
            'base_url': reverse('web:pilotage_ctm_detail', args=[ctm.number]) if ctm else reverse('web:pilotage_dashboard'),
            'anchor': '#ctm-activity' if ctm else '#panel-ctc',
            'from': start_date.isoformat(), 'to': end_date.isoformat(), 'error': error,
            'timezone': timezone.get_current_timezone_name(),
            'selected_user': selected_user, 'selected_action': selected_kind, 'search': search,
            'user_options': user_options, 'action_options': KINDS.items(),
            'event_count': len(events), 'active_users': len(collaborators),
            'document_count': len(documents_summary),
            'captured_count': sum(event['source'] == 'journal' for event in events),
            'historical_count': sum(event['source'] == 'historique' for event in events),
            'unattributed_count': sum(not event['user_id'] for event in events),
            'team': sorted(collaborators.values(), key=lambda item: -item['count']),
            'document_page': document_page, 'page': page, 'query': query,
        },
        'ctc_chart_data': chart_data,
        'ctm_dossier_page': Paginator(normes.select_related('wg').order_by('-updated_at', '-pk'), 25).get_page(request.GET.get('ctc_page')) if ctm else None,
    }
