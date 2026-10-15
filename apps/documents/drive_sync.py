"""Transfert traçable des seuls fichiers liés à une norme validée vers Drive."""

import hashlib
import mimetypes
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from apps.norms.models import Norme
from .models import DocumentFile, DriveSyncAttempt, DriveSyncSettings


def allowed_statuses():
    config = DriveSyncSettings.objects.filter(pk=1).first()
    return ('ADOPTED', 'HOMOLOGATED', 'PUBLISHED') if config and config.include_adopted else ('HOMOLOGATED', 'PUBLISHED')


def configured():
    return all((
        settings.GDRIVE_CLIENT_ID,
        settings.GDRIVE_CLIENT_SECRET,
        settings.GDRIVE_REFRESH_TOKEN,
        settings.GDRIVE_ROOT_FOLDER_ID,
    ))


def enabled():
    return configured() and DriveSyncSettings.objects.filter(pk=1, enabled=True).exists()


def candidate_count():
    statuses = allowed_statuses()
    normes = Norme.objects.filter(status__in=statuses)
    return (
        normes.exclude(current_version='').filter(current_version__isnull=False).count()
        + normes.exclude(jo_file='').filter(jo_file__isnull=False).count()
        + DocumentFile.objects.filter(norme__status__in=statuses).exclude(file='').count()
    )


def _source_file(kind, source_id):
    if kind == 'DOCUMENT':
        document = DocumentFile.objects.select_related('norme').filter(pk=source_id).first()
        if document is None:
            return None
        if not document.norme or document.norme.status not in allowed_statuses():
            return None
        return document.file, f'{document.norme.reference_number}__{Path(document.file.name).name}'
    norme = Norme.objects.filter(pk=source_id).first()
    if norme is None:
        return None
    if norme.status not in allowed_statuses():
        return None
    if kind == 'NORM_CURRENT':
        field = norme.current_version
    elif kind == 'NORM_JO':
        field = norme.jo_file
    else:
        raise ValueError('Source Drive inconnue.')
    return field, f'{norme.reference_number}__{Path(field.name).name}'


def _drive_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    credentials = Credentials(
        token=None,
        refresh_token=settings.GDRIVE_REFRESH_TOKEN,
        client_id=settings.GDRIVE_CLIENT_ID,
        client_secret=settings.GDRIVE_CLIENT_SECRET,
        token_uri='https://oauth2.googleapis.com/token',
        scopes=['https://www.googleapis.com/auth/drive.file'],
    )
    credentials.refresh(Request())
    return build('drive', 'v3', credentials=credentials, cache_discovery=False)


def sync_one(kind, source_id):
    """Retourne sent/skipped/ineligible/failed ; conserve chaque tentative."""
    if not enabled():
        return 'disabled'
    source = _source_file(kind, source_id)
    if not source:
        return 'ineligible'
    field, remote_name = source
    if not field:
        return 'ineligible'
    try:
        with field.open('rb') as file_obj:
            digest = hashlib.sha256()
            for chunk in iter(lambda: file_obj.read(1024 * 1024), b''):
                digest.update(chunk)
            checksum = digest.hexdigest()
            if DriveSyncAttempt.objects.filter(
                source_kind=kind, source_id=source_id, sha256=checksum, status='SENT'
            ).exists():
                return 'skipped'
            attempt = DriveSyncAttempt.objects.create(
                source_kind=kind, source_id=source_id, source_name=field.name,
                sha256=checksum,
            )
            file_obj.seek(0)
            from googleapiclient.http import MediaIoBaseUpload
            media = MediaIoBaseUpload(
                file_obj, mimetype=mimetypes.guess_type(field.name)[0] or 'application/octet-stream',
                resumable=True,
            )
            result = _drive_service().files().create(
                body={
                    'name': remote_name,
                    'parents': [settings.GDRIVE_ROOT_FOLDER_ID],
                    'appProperties': {'source_kind': kind, 'source_id': str(source_id), 'sha256': checksum},
                },
                media_body=media,
                fields='id,name,parents',
            ).execute(num_retries=2)
            if not result.get('id') or settings.GDRIVE_ROOT_FOLDER_ID not in result.get('parents', []):
                raise RuntimeError('Google Drive n’a pas confirmé la destination.')
            attempt.status = 'SENT'
            attempt.drive_file_id = result['id']
            attempt.completed_at = timezone.now()
            attempt.save(update_fields=['status', 'drive_file_id', 'completed_at', 'updated_at'])
            return 'sent'
    except Exception as exc:
        if 'attempt' in locals():
            attempt.status = 'FAILED'
            attempt.error = str(exc)[:2000]
            attempt.completed_at = timezone.now()
            attempt.save(update_fields=['status', 'error', 'completed_at', 'updated_at'])
        else:
            DriveSyncAttempt.objects.create(
                source_kind=kind, source_id=source_id,
                source_name=getattr(field, 'name', ''),
                sha256='', status='FAILED', error=str(exc)[:2000],
                completed_at=timezone.now(),
            )
        return 'failed'


def sync_norm(norme_id):
    if not enabled():
        return {'disabled': 1}
    statuses = {}
    for kind in ('NORM_CURRENT', 'NORM_JO'):
        result = sync_one(kind, norme_id)
        statuses[result] = statuses.get(result, 0) + 1
    for document_id in DocumentFile.objects.filter(norme_id=norme_id).values_list('pk', flat=True):
        result = sync_one('DOCUMENT', document_id)
        statuses[result] = statuses.get(result, 0) + 1
    return statuses


def sync_backlog():
    if not enabled():
        return {'disabled': 1}
    statuses = {}
    for norme_id in Norme.objects.filter(status__in=allowed_statuses()).values_list('pk', flat=True):
        for result, count in sync_norm(norme_id).items():
            statuses[result] = statuses.get(result, 0) + count
    return statuses
