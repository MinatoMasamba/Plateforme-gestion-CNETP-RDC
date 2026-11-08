"""Centre ST : notifications existantes et cas documentaires, sans envoi externe."""
import hashlib
import json
from datetime import datetime, timedelta

from django.utils import timezone
from django.core.exceptions import PermissionDenied
from apps.mobileapp.models import Notification
from .st_notification_models import STNotificationRead
from .st_operations import actor_mandate
from . import st_ged


def cases(user):
    try:
        mandate = actor_mandate(user)
    except PermissionDenied:
        return []
    rows = []
    if mandate.poste.code not in ('ST-V3-10', 'ST-V3-11'):
        return rows

    def add(kind, process, title, body, signature, target):
        digest = hashlib.sha256(json.dumps([kind, process.pk, signature], sort_keys=True, default=str).encode()).hexdigest()
        rows.append({'key': 'case:' + digest, 'title': title, 'body': body,
                     'category': 'Documentation', 'target': target, 'process_id': process.pk,
                     'date': process.received_at.isoformat(), 'is_read': False})

    for process in st_ged.processes(user).filter(received_at__isnull=False).prefetch_related('ged_anomalies'):
        blockers = st_ged.blockers(process)
        reference = process.norme.reference_number
        if blockers:
            add('blocked', process, reference + ' · Dossier à compléter', '\n'.join(blockers),
                blockers, 'indexation')
        receipt = getattr(process, 'administrative_reception', None)
        if (not process.sc_report_received_at and receipt and receipt.vote_date
                and receipt.vote_date < timezone.localdate() - timedelta(days=14)):
            add('report', process, reference + ' · Rapport SC attendu',
                'Le rapport de revue est attendu depuis plus de 14 jours après le vote.',
                receipt.vote_date.isoformat(), 'indexation')
        for anomaly in process.ged_anomalies.all():
            if not anomaly.resolved_at:
                add('anomaly', process, reference + ' · Anomalie documentaire', anomaly.comment,
                    [anomaly.pk, anomaly.comment], 'ged_anomalies')
    read = set(STNotificationRead.objects.filter(user=user, key__in=[r['key'] for r in rows]).values_list('key', flat=True))
    for row in rows:
        row['is_read'] = row['key'] in read
    return rows


def notifications(user):
    rows = cases(user)
    for item in Notification.objects.filter(user=user).order_by('-created_at'):
        rows.append({'key': 'notification:' + str(item.pk), 'title': item.title, 'body': item.body,
                     'category': item.get_notification_type_display(), 'date': item.created_at.isoformat(),
                     'is_read': item.is_read, 'target': '', 'process_id': None})
    rows.sort(key=lambda row: (row['is_read'], -datetime.fromisoformat(row['date']).timestamp()))
    return {'results': rows, 'unread_count': sum(not row['is_read'] for row in rows)}
