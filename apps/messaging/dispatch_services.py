"""Envoi interne vers une seule SC ou un seul GT ; destinataires figés à l’envoi."""
from html import escape
import hashlib
import json
from pathlib import Path
import uuid
import zipfile
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from apps.core.models import User
from apps.experts.models import Expert
from apps.governance.models import AffectationSousCommission, MandatOrganisation, Organe, GroupeCible, JournalMigration
from apps.governance.phoenix_runtime import current_organisation_version
from apps.governance.st_operations import actor_mandate, writable
from apps.mobileapp.models import Notification
from .dispatch_models import InstitutionalDispatch, DispatchRecipient

MAX_FILE_SIZE = 10 * 1024 * 1024
MIMES = {
    '.pdf': 'application/pdf', '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel', '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.ppt': 'application/vnd.ms-powerpoint', '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.odt': 'application/vnd.oasis.opendocument.text', '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
    '.txt': 'text/plain', '.csv': 'text/csv', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
}


def sender_mandate(user):
    mandate = actor_mandate(user)
    if not mandate.poste.st_sub_role:
        raise PermissionDenied('Envoi réservé aux titulaires confirmés du ST.')
    return mandate


def validated_target(sc_id=None, gt_id=None):
    if bool(sc_id) == bool(gt_id):
        raise ValidationError('Choisir une SC ou un seul GT, exclusivement.')
    version = current_organisation_version()
    valid = ('VALIDATED', 'ACTIVE')
    if gt_id:
        target = GroupeCible.objects.select_related('sc__version').filter(pk=gt_id, sc__version=version, sc__status__in=valid).first()
        if not target:
            raise ValidationError('GT introuvable, hors de la version courante ou rattaché à une SC non validée.')
        return target, target.sc
    target = Organe.objects.filter(pk=sc_id, version=version, type='SC', status__in=valid).first()
    if not target:
        raise ValidationError('SC introuvable, non validée ou hors de la version courante.')
    return target, target


def target_recipients(sc, gt=None):
    today = timezone.localdate()
    mandates = MandatOrganisation.objects.filter(expert_id=OuterRef('pk'), status='ACTIVE', capacity='ORGANISATION', start_date__lte=today).exclude(appointment_reference='').filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
    if gt:
        mandates = mandates.filter(groupe=gt)
        experts = Expert.objects.annotate(has_target_mandate=Exists(mandates)).filter(has_target_mandate=True)
    else:
        mandates = mandates.filter(Q(poste__organe=sc) | Q(groupe__sc=sc))
        assignments = AffectationSousCommission.objects.filter(expert_id=OuterRef('pk'), sc=sc, version=sc.version, status='MIGRATED', effective_from__lte=today).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=today))
        experts = Expert.objects.annotate(has_target_mandate=Exists(mandates), has_assignment=Exists(assignments)).filter(Q(has_target_mandate=True) | Q(has_assignment=True))
    return User.objects.filter(expert_profile__in=experts.filter(status='ACTIVE'), is_active=True).distinct().order_by('pk')


def file_metadata(upload):
    if not upload:
        return {'name': '', 'sha256': '', 'size': 0, 'mime': ''}
    name = upload.name.replace('\\', '/').rsplit('/', 1)[-1]
    if len(name) > 255 or any(c in name for c in ('\r', '\n', '\x00')):
        raise ValidationError('Nom de fichier invalide.')
    suffix = Path(name).suffix.lower()
    if suffix not in MIMES:
        raise ValidationError('Format non autorisé. Formats acceptés : PDF, Office, ODT/ODS, TXT/CSV, PNG/JPG.')
    digest, size = hashlib.sha256(), 0
    upload.seek(0)
    for chunk in upload.chunks():
        size += len(chunk)
        if size > MAX_FILE_SIZE:
            raise ValidationError('La pièce jointe dépasse 10 Mo.')
        digest.update(chunk)
    if not size:
        raise ValidationError('La pièce jointe est vide.')
    upload.seek(0)
    header = upload.read(16)
    upload.seek(0)
    signatures = {'.pdf': b'%PDF-', '.png': b'\x89PNG\r\n\x1a\n', '.jpg': b'\xff\xd8', '.jpeg': b'\xff\xd8',
        '.doc': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', '.xls': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', '.ppt': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'}
    if suffix in signatures and not header.startswith(signatures[suffix]):
        raise ValidationError('Le contenu du fichier ne correspond pas à son extension.')
    archive_members = {'.docx': 'word/document.xml', '.xlsx': 'xl/workbook.xml', '.pptx': 'ppt/presentation.xml', '.odt': 'content.xml', '.ods': 'content.xml'}
    if suffix in archive_members:
        try:
            with zipfile.ZipFile(upload) as archive:
                entries = archive.infolist()
                if len(entries) > 10000 or sum(i.file_size for i in entries) > 100 * 1024 * 1024 or archive_members[suffix] not in archive.namelist():
                    raise ValidationError('Conteneur documentaire invalide ou excessivement volumineux.')
        except (zipfile.BadZipFile, OSError, ValueError):
            raise ValidationError('Le fichier Office/ODF est invalide.')
        finally:
            upload.seek(0)
    return {'name': name, 'sha256': digest.hexdigest(), 'size': size, 'mime': MIMES[suffix]}


def visible_dispatches(user):
    if not user.is_authenticated or not user.is_active:
        return InstitutionalDispatch.objects.none()
    qs = InstitutionalDispatch.objects.select_related('sender', 'target_sc', 'target_gt').prefetch_related('recipients')
    if user.is_staff and user.has_perm('messaging.view_institutionaldispatch'):
        return qs
    return qs.filter(Q(sender=user) | Q(recipients__user=user)).distinct()


def send_dispatch(
    user, *, subject, body='', sc_id=None, gt_id=None, upload=None,
    request_key=None, allow_admin=False,
):
    """Créer un envoi SC/GT. ``allow_admin`` autorise Neuronne sans mandat ST."""
    if allow_admin:
        from apps.dashboard.console_permissions import has_console_access

        if not (user.is_authenticated and user.is_active and user.is_staff and has_console_access(user)):
            raise PermissionDenied('Envoi réservé à l’administration Neuronne.')
        mandate = None
    else:
        mandate = sender_mandate(user)
    writable()
    subject, body = str(subject).strip(), str(body).strip()
    if not subject or len(subject) > 250 or len(body) > 100000 or '\r' in subject or '\n' in subject:
        raise ValidationError('Objet requis (250 caractères maximum), texte limité à 100 000 caractères.')
    if not body and not upload:
        raise ValidationError('Un texte ou une pièce jointe est obligatoire.')
    if bool(sc_id) == bool(gt_id):
        raise ValidationError('Choisir une SC ou un seul GT, exclusivement.')
    try:
        request_key = uuid.UUID(str(request_key)) if request_key else uuid.uuid4()
    except ValueError:
        raise ValidationError('Clé de requête UUID invalide.')
    metadata = file_metadata(upload)
    fingerprint = hashlib.sha256(json.dumps({'subject': subject, 'body': body, 'sc_id': sc_id, 'gt_id': gt_id, 'file': metadata}, sort_keys=True).encode()).hexdigest()
    stored_file = None
    try:
        with transaction.atomic():
            existing = InstitutionalDispatch.objects.select_for_update().filter(sender=user, request_key=request_key).first()
            if existing:
                if existing.fingerprint != fingerprint:
                    raise ValidationError('Cette clé de requête correspond à un autre contenu.', code='conflict')
                return existing, False
            target, sc = validated_target(sc_id, gt_id)
            recipients = list(target_recipients(sc, target if gt_id else None))
            if not recipients:
                raise ValidationError('Aucun destinataire confirmé et actif pour cette cible ; aucun envoi effectué.')
            dispatch = InstitutionalDispatch(sender=user, sender_name=user.get_full_name() or user.username,
                mandate=mandate, target_sc=sc if sc_id else None, target_gt=target if gt_id else None,
                organisation_version=sc.version, target_code=target.code, target_label=target.name,
                subject=subject, body=body, html_body='<html><body><p>' + escape(body).replace('\n', '<br>') + '</p></body></html>', request_key=request_key, fingerprint=fingerprint,
                original_filename=metadata['name'], attachment_sha256=metadata['sha256'],
                attachment_size=metadata['size'], attachment_mime=metadata['mime'])
            if upload:
                dispatch.attachment.save(metadata['name'], upload, save=False)
                stored_file = (dispatch.attachment.storage, dispatch.attachment.name)
            dispatch.full_clean()
            dispatch.save()
            notifications = [Notification(user=recipient, title=subject, body=body[:300] or 'Document transmis.',
                notification_type='MESSAGE', priority='NORMAL', data={'kind': 'institutional_dispatch',
                'dispatch_id': dispatch.pk, 'api_url': f'/api/v1/communications/{dispatch.pk}/'}) for recipient in recipients]
            # Notification interne uniquement : aucun dispatch email, SMS ou FCM.
            Notification.objects.bulk_create(notifications)
            deliveries = []
            for recipient, notification in zip(recipients, notifications):
                address = (recipient.email or '').strip()
                try:
                    validate_email(address)
                    email_status, email_error = 'PENDING', ''
                except ValidationError:
                    address, email_status, email_error = '', 'SKIPPED', 'Adresse e-mail absente ou invalide.'
                deliveries.append(DispatchRecipient(dispatch=dispatch, user=recipient,
                    recipient_name=recipient.get_full_name() or recipient.username, notification=notification,
                    email=address, email_status=email_status, email_error=email_error))
            DispatchRecipient.objects.bulk_create(deliveries)
            from .dispatch_delivery import enqueue_dispatch_emails
            transaction.on_commit(lambda dispatch_id=dispatch.pk: enqueue_dispatch_emails(dispatch_id))
            journal_version = mandate.organisation_version if mandate else sc.version
            JournalMigration.objects.create(version=journal_version, actor=user,
                actor_name=dispatch.sender_name, mandate=mandate, operation='ST_DISPATCH',
                target=f'dispatch:{dispatch.pk}', after={'target_code': target.code, 'recipient_count': len(recipients), 'attachment_sha256': metadata['sha256']},
                reason=subject)
            return dispatch, True
    except Exception as exc:
        if stored_file:
            stored_file[0].delete(stored_file[1])
        if isinstance(exc, IntegrityError):
            existing = InstitutionalDispatch.objects.filter(sender=user, request_key=request_key).first()
            if existing and existing.fingerprint == fingerprint:
                return existing, False
            raise ValidationError('Un envoi concurrent existe déjà pour cette clé.', code='conflict') from exc
        raise


@transaction.atomic
def retry_dispatch_emails(user, dispatch_id):
    writable()
    dispatch = visible_dispatches(user).select_for_update().filter(pk=dispatch_id).first()
    if not dispatch:
        raise PermissionDenied('Envoi inaccessible.')
    admin = user.is_staff and user.has_perm('messaging.change_institutionaldispatch')
    mandate = None
    if not admin:
        mandate = sender_mandate(user)
        if dispatch.sender_id != user.pk:
            raise PermissionDenied('Seul l’émetteur peut relancer cet envoi.')
    ids = list(dispatch.recipients.filter(email_status='FAILED').values_list('pk', flat=True))
    if not ids:
        raise ValidationError('Aucun e-mail en échec à relancer.', code='conflict')
    DispatchRecipient.objects.filter(pk__in=ids, email_status='FAILED').update(email_status='PENDING', email_error='')
    JournalMigration.objects.create(version=dispatch.mandate.organisation_version if dispatch.mandate_id else dispatch.organisation_version, actor=user,
        actor_name=user.get_full_name() or user.username, mandate=mandate, operation='ST_DISPATCH_RETRY',
        target=f'dispatch:{dispatch.pk}', after={'recipient_count': len(ids)}, reason='Relance des seuls e-mails en échec.')
    from .dispatch_delivery import enqueue_dispatch_emails
    transaction.on_commit(lambda: enqueue_dispatch_emails(dispatch.pk))
    return len(ids)
