"""Services GED du poste 11 et confirmation documentaire par le chef du pôle 2."""
from datetime import date, timedelta
from pathlib import Path
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from apps.core.models import AuditLog, User
from apps.norms.models import Norme, NormeVersion
from .models import CTCProcessus, MandatOrganisation, Organe
from .st_admin_models import STReception
from .st_ged_models import STGEDCode, STGEDFile, STGEDIndexation, STGEDConfirmation, STGEDAnomaly
from .st_operations import actor_mandate, writable
from .st_files import inspect_document

TOMES = {'SC-SOCLE': 0, 'SC-IT': 1, 'SC-GF': 2, 'SC-OH': 3, 'SC-ETR': 4, 'SC-VRD': 4, 'SC-ENV': 5, 'SC-BAT': 6}


def tome_label(code):
    number = TOMES.get(code)
    return f'Tome {number}' if number is not None else code


def actor(user, write=False, head=False):
    mandate = actor_mandate(user)
    code = mandate.poste.code
    allowed = {'ST-V3-10'} if head else {'ST-V3-10', 'ST-V3-11'}
    if not write:
        allowed |= {f'ST-V3-{n:02}' for n in range(1, 6)}
    if code not in allowed:
        raise PermissionDenied('Opération réservée à la GED du pôle 2 et aux lecteurs habilités.')
    return mandate


def processes(user):
    mandate = actor(user)
    qs = CTCProcessus.objects.filter(norme__circuit_version='LEGACY').select_related('norme', 'administrative_reception__sc', 'administrative_reception__group')
    if mandate.poste.code == 'ST-V3-11':
        qs = qs.filter(Q(current_stage='RECEPTION', received_at__isnull=False, indexed_at__isnull=True) | Q(ged_indexations__author=user)).distinct()
    return qs


def received_processes(user):
    """Catalogue de lecture GED des normes effectivement arrivées au CTC.

    Ce catalogue ne modifie ni le périmètre d'écriture ni l'accès aux pièces.
    """
    actor(user)
    return CTCProcessus.objects.filter(
        norme__circuit_version='LEGACY', received_at__isnull=False,
    ).select_related('norme', 'administrative_reception__sc')


def dossier_processes(user):
    """Reprendre exactement le périmètre de lecture du dossier CTC existant."""
    from .st_permissions import visible_processus
    from .st_matrix import mandate_capabilities
    from .st_spaces import space_context
    mandate=actor_mandate(user)
    context={**mandate_capabilities(mandate),**space_context(mandate.poste),
        'poste':mandate.poste,'ctc_pole':mandate.poste.organe.code}
    return visible_processus(mandate.expert,context)


def dossier_readable(user, process):
    return dossier_processes(user).filter(pk=process.pk).exists()


def document_readable(user, entry):
    mandate=actor_mandate(user)
    if entry.process.norme.circuit_version!='LEGACY':
        return False
    if mandate.poste.code=='ST-V3-10' or (mandate.poste.code=='ST-V3-11' and entry.author_id==user.pk):
        return True
    return dossier_readable(user,entry.process)


def audit(user, process, action, **values):
    AuditLog.objects.create(user=user, action='UPDATE', content_type='CTCProcessus',
        object_id=process.pk, object_repr=process.norme.reference_number[:200],
        changes={'scope': 'ctc', 'subsystem':'GED', 'action': action, 'norme_id': process.norme_id,
                 'process_id': process.pk, **values})


def notify(user_ids, title, body, process_id):
    from apps.mobileapp.signals import create_notification_for_user
    def send():
        for user in User.objects.filter(pk__in=set(user_ids), is_active=True):
            create_notification_for_user(user, title, body, 'SYSTEM', data={'ged_process_id': process_id})
    transaction.on_commit(send, robust=True)


def recipients(numbers):
    today = timezone.localdate()
    return list(MandatOrganisation.objects.filter(
        poste__code__in=[f'ST-V3-{n:02}' for n in numbers], status='ACTIVE', capacity='ORGANISATION',
        expert__status='ACTIVE', expert__user__is_active=True,
    ).filter(Q(start_date__isnull=True) | Q(start_date__lte=today)).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)).values_list('expert__user_id', flat=True))


def report_for(process):
    receipt = getattr(process, 'administrative_reception', None)
    if not receipt or receipt.state != 'ENREGISTREE' or not process.sc_report_received_at:
        return None
    return receipt.pieces.filter(kind='REPORT').order_by('-pk').first()


def blockers(process):
    result = []
    receipt = getattr(process, 'administrative_reception', None)
    report = report_for(process)
    if not process.received_at:
        result.append('Réception administrative attendue')
    if not report:
        result.append('Rapport de revue : pièce réelle attendue ; une référence seule ne suffit pas')
    elif not report.file.storage.exists(report.file.name):
        result.append('Pièce du rapport introuvable dans le stockage privé')
    if not receipt or not receipt.sc_id or not receipt.group_id or receipt.group.sc_id != receipt.sc_id:
        result.append('Origine SC / GT à compléter dans la réception')
    elif receipt.sc.status not in ('VALIDATED', 'ACTIVE'):
        result.append('Sous-commission de rattachement à confirmer')
    if receipt and not STGEDCode.objects.filter(norme_id=process.norme_id, sc_id=receipt.sc_id).exists():
        result.append('Code documentaire autorisé attendu du chef du pôle 2')
    if process.ged_anomalies.filter(resolved_at__isnull=True).exists():
        result.append('Anomalie documentaire à résoudre')
    return result


def editable(user, pk):
    actor(user, write=True)
    process = processes(user).select_for_update().get(pk=pk)
    if process.current_stage != 'RECEPTION' or process.intake_validated_at:
        raise ValidationError('Le dossier a quitté la préparation documentaire. Sa validation officielle est conservée.')
    return process


@transaction.atomic
def approve_code(user, process_id, code, source_reference, sc_id):
    writable(); actor(user, write=True, head=True)
    process = processes(user).select_for_update().get(pk=process_id)
    sc = Organe.objects.get(pk=sc_id, type='SC', status__in=['VALIDATED', 'ACTIVE'])
    receipt = getattr(process, 'administrative_reception', None)
    if receipt and receipt.sc_id and sc.pk != receipt.sc_id:
        raise ValidationError('Le code doit viser la SC enregistrée à la réception.')
    code, source_reference = code.strip(), source_reference.strip()
    if not code or len(code) > 80 or not source_reference or len(source_reference) > 500:
        raise ValidationError('Code documentaire et référence officielle de son autorisation obligatoires.')
    if any(ord(c) < 32 for c in code):
        raise ValidationError('Code documentaire invalide.')
    result = STGEDCode.objects.create(code=code, norme=process.norme, sc=sc,
        source_reference=source_reference, approved_by=user)
    audit(user, process, 'ged_code_authorized', code=code, source_reference=source_reference)
    return result


@transaction.atomic
def upload(user, process_id, file):
    writable(); process = editable(user, process_id)
    if not process.received_at:
        raise ValidationError('Réception préalable obligatoire.')
    info = inspect_document(file)
    source = STGEDFile.objects.create(process=process, file=file, name=Path(file.name).name[:255],
        sha256=info['sha256'], size=info['size'], author=user)
    audit(user, process, 'ged_file_uploaded', file_id=source.pk, sha256=source.sha256, name=source.name)
    return source


def inspect_stored(file, expected_hash):
    try:
        with file.open('rb') as stream:
            info = inspect_document(stream)
        if info['sha256'] != expected_hash:
            raise ValidationError('L’empreinte du fichier a changé : signaler une anomalie.')
        return info
    except (OSError, FileNotFoundError) as exc:
        raise ValidationError('Pièce privée introuvable ou inaccessible.') from exc


@transaction.atomic
def index(user, process_id, code_id, source_id, base_version_id, verified, observation='', restore_id=None, metadata=None):
    writable(); process = editable(user, process_id)
    # Verrou partagé avec les autres écritures de ce dossier ; révision optimiste en complément.
    norm = Norme.all_objects.select_for_update().get(pk=process.norme_id)
    latest = NormeVersion.all_objects.filter(norme=norm).order_by('-version_number').first()
    if (latest.pk if latest else 0) != base_version_id:
        raise ValidationError('Une nouvelle version existe. Actualisez avant de recommencer.', code='conflict')
    reasons = blockers(process)
    if reasons:
        raise ValidationError(reasons)
    if verified is not True:
        raise ValidationError('Vérifiez le rapport de revue et la lisibilité des pièces avant de confirmer.')
    receipt = process.administrative_reception
    defaults = {
        'reference': norm.reference_number, 'title': norm.title,
        'tome': tome_label(receipt.sc.code), 'sc': receipt.sc.code, 'group': receipt.group.code,
        'vote_date': receipt.vote_date.isoformat() if receipt.vote_date else '',
        'received_at': process.received_at.isoformat() if process.received_at else '',
        'sender': receipt.sender.full_name if receipt.sender_id else '',
        'version': f'v{latest.version_number}' if latest else '',
    }
    if metadata is not None:
        limits = {'reference': 80, 'title': 500, 'tome': 80, 'sc': 120, 'group': 120,
                  'vote_date': 10, 'received_at': 80, 'sender': 255, 'version': 80}
        if not isinstance(metadata, dict) or set(metadata) - set(limits):
            raise ValidationError('Métadonnées documentaires invalides.')
        for key, value in metadata.items():
            if not isinstance(value, str) or len(value) > limits[key]:
                raise ValidationError(f'Métadonnée invalide : {key}.')
        defaults.update({key: value.strip() for key, value in metadata.items()})
        if not defaults['reference'] or not defaults['title']:
            raise ValidationError('La référence et le titre documentaires sont obligatoires.')
        if defaults['vote_date']:
            try:
                date.fromisoformat(defaults['vote_date'])
            except ValueError as exc:
                raise ValidationError('Date du vote invalide.') from exc
    report = report_for(process)
    inspect_stored(report.file, report.sha256)
    code = STGEDCode.objects.get(pk=code_id, norme=norm, sc=receipt.sc)
    source = STGEDFile.objects.get(pk=source_id, process=process)
    if actor(user, write=True).poste.code == 'ST-V3-11' and source.author_id != user.pk:
        raise PermissionDenied('Utilisez un fichier de votre préparation documentaire.')
    info = inspect_stored(source.file, source.sha256)
    restored = None
    content = info['text']
    if restore_id:
        if not observation.strip():
            raise ValidationError('Motif de restauration obligatoire.')
        restored = STGEDIndexation.objects.get(pk=restore_id, process=process)
        if restored.source_id != source.pk or restored.code_id != code.pk:
            raise ValidationError('Restaurer le fichier et le code de la version sélectionnée.')
        content = restored.version.content
        if metadata is None and restored.metadata:
            defaults = dict(restored.metadata)
    number = (latest.version_number if latest else 0) + 1
    version = NormeVersion.all_objects.create(norme=norm, version_number=number, title=defaults['title'],
        content=content, summary=observation, version_author=user, is_draft=True)
    entry = STGEDIndexation.objects.create(process=process, version=version, code=code,
        sc=receipt.sc, group=receipt.group, source=source, report=report,
        observation=observation, metadata=defaults, author=user, restored_from=restored)
    if not process.indexed_at:
        process.mark_indexed()
    audit(user, process, 'ged_restored' if restored else 'ged_indexed', indexation_id=entry.pk,
        code=code.code, version=number, report_piece_id=report.pk, source_id=source.pk,
        report_verified_by=user.pk, sha256=source.sha256, restored_from=restore_id,
        comment=observation, metadata=defaults)
    notify(recipients([10]), 'Indexation à confirmer', f'{norm.reference_number} · v{number}', process.pk)
    return entry


@transaction.atomic
def confirm(user, indexation_id, decision, comment):
    writable(); actor(user, write=True, head=True)
    entry = STGEDIndexation.objects.select_related('process__norme', 'version').get(pk=indexation_id)
    process = processes(user).select_for_update().get(pk=entry.process_id)
    if process.intake_validated_at or process.current_stage != 'RECEPTION':
        raise ValidationError('La préparation documentaire est close pour ce dossier.')
    if process.ged_indexations.order_by('-version__version_number').first().pk != entry.pk:
        raise ValidationError('Seule la dernière version peut recevoir la décision courante.', code='conflict')
    if decision not in ('CONFIRMED', 'RETURNED') or not comment.strip():
        raise ValidationError('Décision et commentaire obligatoires.')
    if decision == 'CONFIRMED':
        reasons=blockers(process)
        if reasons:
            raise ValidationError(reasons)
        inspect_stored(entry.report.file, entry.report.sha256)
        inspect_stored(entry.source.file, entry.source.sha256)
    if STGEDConfirmation.objects.filter(indexation=entry).exists():
        raise ValidationError('Cette version possède déjà une décision.', code='conflict')
    result = STGEDConfirmation.objects.create(indexation=entry, decision=decision, comment=comment, author=user)
    audit(user, process, 'ged_confirmed' if decision == 'CONFIRMED' else 'ged_returned', indexation_id=entry.pk, comment=comment)
    notify([entry.author_id] + (recipients([1,2,3,4,5,8]) if decision == 'CONFIRMED' else []),
        'Contrôle documentaire : '+result.get_decision_display(), process.norme.reference_number, process.pk)
    return result


@transaction.atomic
def anomaly(user, process_id, comment, resolve_id=None, kind='INCONSISTENT', recipient_id=None):
    writable(); process = editable(user, process_id)
    if not comment.strip():
        raise ValidationError('Motif documentaire obligatoire.')
    valid_kinds = {choice[0] for choice in STGEDAnomaly.KIND_CHOICES}
    if kind not in valid_kinds:
        raise ValidationError('Type d’anomalie documentaire invalide.')
    if resolve_id:
        issue = STGEDAnomaly.objects.select_for_update().get(pk=resolve_id, process=process)
        if issue.resolved_at:
            raise ValidationError('Anomalie déjà résolue.', code='conflict')
        if issue.author_id != user.pk and actor(user, write=True).poste.code != 'ST-V3-10':
            raise PermissionDenied('Seul le déclarant ou le chef du pôle 2 peut résoudre cette anomalie.')
        issue.resolved_at=timezone.now(); issue.resolved_by=user; issue.resolution=comment
        issue.save(update_fields=['resolved_at', 'resolved_by', 'resolution'])
        action = 'ged_anomaly_resolved'
    else:
        recipient = None
        if recipient_id:
            recipient = User.objects.get(pk=recipient_id, is_active=True)
        issue = STGEDAnomaly.objects.create(process=process, comment=comment, author=user,
            kind=kind, recipient=recipient)
        action = 'ged_anomaly_reported'
    audit(user, process, action, anomaly_id=issue.pk, comment=comment, kind=issue.kind,
        recipient_id=issue.recipient_id)
    receipt = getattr(process, 'administrative_reception', None)
    users = recipients([10,6])
    if issue.recipient_id:
        users.append(issue.recipient_id)
    if receipt and receipt.sender_id:
        users.append(receipt.sender.user_id)
    notify(users, 'Suivi d’une anomalie documentaire', comment, process.pk)
    return issue


def confirmed_for_intake(process):
    entry = process.ged_indexations.order_by('-version__version_number').first()
    if not entry:
        return True  # Les indexations historiques restent identifiables comme telles.
    latest=NormeVersion.all_objects.filter(norme_id=process.norme_id).order_by('-version_number').first()
    return bool(latest and latest.pk==entry.version_id and not blockers(process)
        and STGEDConfirmation.objects.filter(indexation=entry, decision='CONFIRMED').exists())


OBJECTIVE_DAYS = 3
REVIEW_DAYS = 14


def _median(values):
    values = sorted(values)
    if not values:
        return None
    if len(values) % 2:
        return round(values[len(values)//2], 2)
    return round((values[len(values)//2-1]+values[len(values)//2])/2, 2)


def _period_bounds(days=30, date_from=None, date_to=None):
    today = timezone.localdate()
    if date_from or date_to:
        start = date_from or (today - timedelta(days=max(1, int(days or 30)) - 1))
        end = date_to or today
        if end < start:
            start, end = end, start
        return start, end
    days = max(1, min(int(days or 30), 365))
    return today - timedelta(days=days - 1), today


def _activity_series(items, start, end):
    """Série temporelle réelle : événements datés (réception, vote, rapport) par SC."""
    span = (end - start).days + 1
    bucket_days = 1 if span <= 10 else max(7, -(-span // 13))
    buckets, cursor = [], start
    while cursor <= end:
        stop = min(cursor + timedelta(days=bucket_days - 1), end)
        buckets.append((cursor, stop))
        cursor = stop + timedelta(days=1)
    total = len(buckets)
    counts = [0] * total
    for receipt in items:
        process = receipt.process
        moments = [
            receipt.vote_date,
            process.received_at.date() if process.received_at else None,
            process.sc_report_received_at.date() if process.sc_report_received_at else None,
        ]
        for moment in moments:
            if not moment or moment < start or moment > end:
                continue
            index = min((moment - start).days // bucket_days, total - 1)
            counts[index] += 1
    labels = []
    for index, (begin, _) in enumerate(buckets):
        if bucket_days == 1:
            labels.append(begin.strftime('%d/%m'))
        else:
            labels.append('S' if index == total - 1 else f'S-{total - 1 - index}')
    return counts, [{'label': labels[i], 'start': b.isoformat(), 'end': e.isoformat()} for i, (b, e) in enumerate(buckets)]


def sc_activity(user, days=30, date_from=None, date_to=None):
    """Activité réelle des sous-commissions sur la période demandée."""
    from .st_admin_models import STReception
    actor(user)
    start, end = _period_bounds(days, date_from, date_to)
    cutoff = timezone.localdate() - timedelta(days=REVIEW_DAYS)
    scs = list(Organe.objects.filter(type='SC', status__in=['VALIDATED', 'ACTIVE']).order_by('code'))
    receipts = list(
        STReception.objects
        .filter(state='ENREGISTREE', sc_id__in=[s.pk for s in scs])
        .select_related('process__norme', 'sc')
    )
    by_sc = {s.pk: [] for s in scs}
    for receipt in receipts:
        by_sc.setdefault(receipt.sc_id, []).append(receipt)
    rows = []
    buckets = []
    for sc in scs:
        items = by_sc.get(sc.pk, [])
        series, buckets = _activity_series(items, start, end)
        dossiers = len({r.process_id for r in items if r.process.received_at and start <= r.process.received_at.date() <= end})
        votes = sum(1 for r in items if r.vote_date and start <= r.vote_date <= end)
        transmitted = sum(1 for r in items if r.process.received_at and start <= r.process.received_at.date() <= end)
        reports = sum(1 for r in items if r.process.sc_report_received_at and start <= r.process.sc_report_received_at.date() <= end)
        waiting_report = sum(1 for r in items if r.process.received_at and not r.process.sc_report_received_at)
        overdue = sum(
            1 for r in items
            if r.vote_date and r.vote_date < cutoff and r.process.received_at and not r.process.sc_report_received_at
        )
        idle = (votes + transmitted + reports) == 0
        if idle:
            status = 'aucune'
        elif overdue > 0:
            status = 'retard'
        elif transmitted > 0 and waiting_report > 0:
            status = 'partielle'
        else:
            status = 'normale'
        rows.append({
            'id': sc.pk,
            'code': sc.code,
            'name': sc.official_name or sc.name,
            'official_name': sc.official_name or sc.name,
            'tome': TOMES.get(sc.code),
            'dossiers': dossiers,
            'votes': votes,
            'transmitted': transmitted,
            'reports': reports,
            'waiting_report': waiting_report,
            'overdue': overdue,
            'idle': idle,
            'status': status,
            'series': series,
        })
    return {'period_start': start.isoformat(), 'period_end': end.isoformat(), 'buckets': buckets, 'results': rows}


def pipeline_upstream(user):
    """Suivi des réceptions du poste 6 visibles pour le poste 11."""
    from .st_admin_models import STReception
    actor(user)
    week = timezone.now() - timedelta(days=7)
    qs = STReception.objects.filter(state='ENREGISTREE').select_related(
        'process__norme', 'sc', 'group'
    ).order_by('-received_at', '-pk')
    registered = qs.count()
    recent = qs.filter(received_at__gte=week).count()
    awaiting = qs.filter(process__received_at__isnull=False, process__sc_report_received_at__isnull=True).count()
    scoped = list(qs[:250])
    eligible = sum(1 for r in scoped if not blockers(r.process) and not r.process.indexed_at)
    latest = []
    for receipt in scoped[:5]:
        process = receipt.process
        latest.append({
            'process_id': process.pk,
            'reference': process.norme.reference_number,
            'title': process.norme.title,
            'sc': receipt.sc.code if receipt.sc_id else '',
            'sc_name': (receipt.sc.official_name or receipt.sc.name) if receipt.sc_id else '',
            'received_at': receipt.received_at.isoformat() if receipt.received_at else None,
            'has_report': bool(process.sc_report_received_at and report_for(process)),
            'eligible': not blockers(process),
        })
    return {
        'registered_after_vote': registered,
        'recently_transmitted': recent,
        'awaiting_sc_report': awaiting,
        'eligible_for_indexation': eligible,
        'latest': latest,
    }


def pipeline_downstream(user):
    """Suivi après indexation : contrôle Pôle 2, pas validation normative."""
    mandate = actor(user)
    qs = STGEDIndexation.objects.select_related(
        'process__norme', 'confirmation', 'code', 'author', 'version'
    ).order_by('-created_at')
    if mandate.poste.code == 'ST-V3-11':
        qs = qs.filter(author=user)
    pending = qs.filter(confirmation__isnull=True)
    confirmed = qs.filter(confirmation__decision='CONFIRMED')
    returned = qs.filter(confirmation__decision='RETURNED')
    latest = []
    for entry in qs[:5]:
        decision = getattr(getattr(entry, 'confirmation', None), 'decision', None)
        latest.append({
            'process_id': entry.process_id,
            'reference': entry.process.norme.reference_number,
            'title': entry.process.norme.title,
            'code': entry.code.code,
            'version': entry.version.version_number if entry.version_id else None,
            'author': entry.author.get_full_name() or entry.author.username,
            'created_at': entry.created_at.isoformat(),
            'decision': decision,
            'state': 'CONFIRMED' if decision == 'CONFIRMED' else ('RETURNED' if decision == 'RETURNED' else 'PENDING'),
        })
    return {
        'sent_to_p2_control': pending.count(),
        'awaiting_post_10': pending.count(),
        'left_p2': confirmed.count(),
        'returned_after_exam': returned.count(),
        'latest': latest,
    }


def codification_analysis(user):
    """Contrôles déterministes des codes documentaires (sans nomenclature inventée)."""
    actor(user)
    codes = list(STGEDCode.objects.select_related('norme', 'sc', 'approved_by').order_by('code'))
    by_code = {}
    for code in codes:
        by_code.setdefault(code.code.strip().lower(), []).append(code)
    indexed_norme_ids = set(STGEDIndexation.objects.values_list('process__norme_id', flat=True))
    coded_norme_ids = {c.norme_id for c in codes}
    rows = []
    conflicts = duplicates = inconsistent = format_errors = 0
    for key, group in by_code.items():
        if len(group) > 1:
            normes = {c.norme_id for c in group}
            if len(normes) > 1:
                conflicts += 1
                kind = 'conflit'
            else:
                duplicates += 1
                kind = 'doublon'
            for code in group:
                rows.append({
                    'norme': code.norme.reference_number,
                    'norme_id': code.norme_id,
                    'tome': TOMES.get(code.sc.code),
                    'reference': code.code,
                    'anomaly': 'Code partagé entre plusieurs normes' if kind == 'conflit' else 'Code dupliqué pour la même norme',
                    'suggestion': 'Conserver une seule autorisation active',
                    'level': 'erreur',
                    'detected_at': None,
                    'state': 'ouverte',
                    'kind': kind,
                })
        for code in group:
            if not code.code.strip() or any(ord(c) < 32 for c in code.code):
                format_errors += 1
                rows.append({
                    'norme': code.norme.reference_number,
                    'norme_id': code.norme_id,
                    'tome': TOMES.get(code.sc.code),
                    'reference': code.code,
                    'anomaly': 'Format de code invalide',
                    'suggestion': '',
                    'level': 'erreur',
                    'detected_at': None,
                    'state': 'ouverte',
                    'kind': 'format',
                })
            expected_tome = TOMES.get(code.sc.code)
            if expected_tome is None:
                inconsistent += 1
                rows.append({
                    'norme': code.norme.reference_number,
                    'norme_id': code.norme_id,
                    'tome': None,
                    'reference': code.code,
                    'anomaly': 'SC sans tome de rattachement connu',
                    'suggestion': '',
                    'level': 'alerte',
                    'detected_at': None,
                    'state': 'ouverte',
                    'kind': 'incoherent',
                })
    missing = 0
    for norme_id in indexed_norme_ids - coded_norme_ids:
        missing += 1
        norme = Norme.objects.filter(pk=norme_id).first()
        if not norme:
            continue
        rows.append({
            'norme': norme.reference_number,
            'norme_id': norme_id,
            'tome': None,
            'reference': '',
            'anomaly': 'Document indexé sans code autorisé associé',
            'suggestion': 'Autorisation du chef du Pôle 2 requise',
            'level': 'alerte',
            'detected_at': None,
            'state': 'ouverte',
            'kind': 'manquant',
        })
    anomalous_codes = {(r['reference'], r['norme_id']) for r in rows if r['reference']}
    verified = sum(1 for c in codes if (c.code, c.norme_id) not in anomalous_codes and c.code.strip())
    return {
        'conflicts': conflicts,
        'duplicates': duplicates,
        'inconsistent': inconsistent,
        'missing': missing,
        'format_errors': format_errors,
        'verified': verified,
        'rows': rows[:200],
    }


def statistics(user, days=30):
    mandate = actor(user)
    qs = STGEDIndexation.objects.all() if mandate.poste.code != 'ST-V3-11' else STGEDIndexation.objects.filter(author=user)
    confirmed = qs.filter(confirmation__decision='CONFIRMED')
    today = timezone.localdate(); start = today-timedelta(days=today.weekday())
    weeks = []
    for i in range(5, -1, -1):
        begin = start-timedelta(weeks=i); end = begin+timedelta(days=7)
        weeks.append({'label':begin.strftime('%d/%m'),
            'count':confirmed.filter(confirmation__created_at__date__gte=begin, confirmation__created_at__date__lt=end).count()})
    grouped = {}
    for entry in qs.select_related('sc', 'process'):
        key = tome_label(entry.sc.code)
        bucket = grouped.setdefault(key, {'processes': set(), 'delays': []})
        bucket['processes'].add(entry.process_id)
        received_at = entry.process.sc_report_received_at
        if received_at and entry.created_at >= received_at:
            bucket['delays'].append((entry.created_at-received_at).total_seconds()/86400)
    tones = [{'tome':key, 'count':len(bucket['processes']),
        'delay_days':round(sum(bucket['delays'])/len(bucket['delays']),2) if bucket['delays'] else None,
        'delay_seconds':round(sum(bucket['delays'])*86400/len(bucket['delays'])) if bucket['delays'] else None,
        'delay_samples':len(bucket['delays'])} for key,bucket in sorted(grouped.items())]
    confirmed_delays = []
    for entry in confirmed.select_related('process'):
        received_at = entry.process.sc_report_received_at
        if received_at and entry.confirmation.created_at >= received_at:
            confirmed_delays.append((entry.confirmation.created_at-received_at).total_seconds()/86400)
    entries = list(qs.select_related('sc', 'group', 'code'))
    duplicate_codes = len(entries) - len({entry.code_id for entry in entries})
    classified = sum(bool(entry.sc_id and entry.group_id) for entry in entries)
    identifiable = sum(bool(entry.version_id) for entry in entries)
    return {'weeks':weeks, 'tomes':tones, 'indexations':len(entries),
        'scope':'Mes indexations' if mandate.poste.code=='ST-V3-11' else 'Indexations du pôle 2',
        'confirmed_period':confirmed.filter(confirmation__created_at__date__gte=today-timedelta(days=days-1)).count(),
        'median_delay_days':_median(confirmed_delays),
        'objective_days':OBJECTIVE_DAYS,
        'last_indexation_at':qs.order_by('-created_at').values_list('created_at', flat=True).first(),
        'conformity':{
            'total':len(entries),
            'reference_unique':duplicate_codes == 0,
            'duplicate_codes':duplicate_codes,
            'version_identifiable':identifiable == len(entries),
            'classified':classified == len(entries),
        }}
