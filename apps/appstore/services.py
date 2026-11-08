"""Services métier App Store : upload, quarantaine, droits, téléchargement."""
from __future__ import annotations

import hashlib
import os
from datetime import timedelta
from pathlib import PurePosixPath

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.http import FileResponse
from django.utils import timezone
from django.utils.text import get_valid_filename

from apps.dashboard.console_permissions import has_console_access

from .models import (
    AppAnnouncement,
    AppDownloadEvent,
    AppReleaseFile,
    AppVersion,
    SoftwareApp,
)

ALLOWED_EXTENSIONS = {
    '.apk', '.aab', '.ipa',
    '.exe', '.msi', '.msix',
    '.dmg', '.pkg',
    '.deb', '.rpm', '.AppImage', '.appimage',
    '.zip', '.tar', '.gz', '.tgz', '.7z',
    '.jar', '.war',
    '.pdf',  # notices / packages web parfois documentés
}

MAX_PACKAGE_BYTES = 512 * 1024 * 1024  # 512 Mo


def can_manage_appstore(user) -> bool:
    return bool(user and user.is_authenticated and user.is_active and has_console_access(user))


def can_view_version(user, version: AppVersion) -> bool:
    if version.status == AppVersion.Status.WITHDRAWN:
        return can_manage_appstore(user)
    if version.status != AppVersion.Status.PUBLISHED:
        return can_manage_appstore(user)
    if version.channel == AppVersion.Channel.STABLE:
        return True
    if can_manage_appstore(user):
        return True
    if not user or not user.is_authenticated:
        return False
    return version.beta_testers.filter(pk=user.pk).exists()


def can_download_file(user, release_file: AppReleaseFile) -> bool:
    if not user or not user.is_authenticated or not user.is_active:
        return False
    version = release_file.version
    app = version.application
    if app.is_withdrawn or not app.is_published:
        return can_manage_appstore(user)
    if not can_view_version(user, version):
        return False
    if release_file.quarantine_status != AppReleaseFile.QuarantineStatus.APPROVED:
        return can_manage_appstore(user)
    if not release_file.has_downloadable_blob:
        return False
    if not release_file.file or not release_file.file.storage.exists(release_file.file.name):
        return False
    return True


def sanitize_upload_name(filename: str) -> str:
    if not filename:
        raise ValidationError('Nom de fichier manquant.')
    name = PurePosixPath(filename.replace('\\', '/')).name
    if not name or name in {'.', '..'} or '/' in name or '\\' in name:
        raise ValidationError('Nom de fichier invalide.')
    name = get_valid_filename(name)
    if not name:
        raise ValidationError('Nom de fichier invalide.')
    ext = os.path.splitext(name)[1]
    if ext.lower() not in {e.lower() for e in ALLOWED_EXTENSIONS}:
        raise ValidationError(f'Extension non autorisée : {ext or "(aucune)"}')
    return name


def compute_sha256(file_obj) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    pos = file_obj.tell() if hasattr(file_obj, 'tell') else None
    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)
    while True:
        chunk = file_obj.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_PACKAGE_BYTES:
            raise ValidationError('Fichier trop volumineux (limite 512 Mo).')
        digest.update(chunk)
    if hasattr(file_obj, 'seek') and pos is not None:
        file_obj.seek(pos)
    elif hasattr(file_obj, 'seek'):
        file_obj.seek(0)
    return digest.hexdigest(), total


def attach_package(release_file: AppReleaseFile, uploaded_file, *, approve: bool = False) -> AppReleaseFile:
    safe_name = sanitize_upload_name(getattr(uploaded_file, 'name', '') or 'package.bin')
    sha256, size = compute_sha256(uploaded_file)
    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(0)
    release_file.original_name = safe_name
    release_file.size_bytes = size
    release_file.sha256 = sha256
    release_file.quarantine_status = (
        AppReleaseFile.QuarantineStatus.APPROVED
        if approve
        else AppReleaseFile.QuarantineStatus.PENDING
    )
    release_file.file.save(safe_name, uploaded_file, save=False)
    release_file.save()
    version = release_file.version
    if version.status == AppVersion.Status.DRAFT:
        version.status = AppVersion.Status.QUARANTINE
        version.save(update_fields=['status', 'updated_at'])
    return release_file


def approve_release_file(release_file: AppReleaseFile) -> AppReleaseFile:
    if not release_file.has_downloadable_blob:
        raise ValidationError('Aucun fichier à approuver.')
    verify_stored_hash(release_file)
    release_file.quarantine_status = AppReleaseFile.QuarantineStatus.APPROVED
    release_file.save(update_fields=['quarantine_status', 'updated_at'])
    return release_file


def reject_release_file(release_file: AppReleaseFile) -> AppReleaseFile:
    release_file.quarantine_status = AppReleaseFile.QuarantineStatus.REJECTED
    release_file.save(update_fields=['quarantine_status', 'updated_at'])
    return release_file


def verify_stored_hash(release_file: AppReleaseFile) -> str:
    if not release_file.file or not release_file.file.storage.exists(release_file.file.name):
        raise ValidationError('Fichier introuvable sur le stockage.')
    with release_file.file.open('rb') as handle:
        digest, size = compute_sha256(handle)
    if release_file.sha256 and digest != release_file.sha256:
        raise ValidationError('Empreinte SHA-256 incohérente.')
    if release_file.size_bytes and size != release_file.size_bytes:
        raise ValidationError('Taille de fichier incohérente.')
    return digest


def publish_version(version: AppVersion, *, set_recommended: bool = False) -> AppVersion:
    approved = version.files.filter(
        quarantine_status=AppReleaseFile.QuarantineStatus.APPROVED,
    ).exclude(file='')
    if not approved.exists():
        raise ValidationError('Publier au moins un fichier approuvé avant publication.')
    for release_file in approved:
        verify_stored_hash(release_file)
    version.mark_published()
    app = version.application
    if not app.is_published:
        app.is_published = True
        app.save(update_fields=['is_published', 'updated_at'])
    if set_recommended or not app.recommended_version_id:
        app.recommended_version = version
        app.save(update_fields=['recommended_version', 'updated_at'])
    return version


def withdraw_version(version: AppVersion) -> AppVersion:
    version.mark_withdrawn()
    app = version.application
    if app.recommended_version_id == version.pk:
        replacement = (
            app.versions.filter(status=AppVersion.Status.PUBLISHED, channel=AppVersion.Channel.STABLE)
            .exclude(pk=version.pk)
            .order_by('-published_at')
            .first()
        )
        app.recommended_version = replacement
        app.save(update_fields=['recommended_version', 'updated_at'])
    return version


def published_apps_queryset(search: str = '', category: str = '', platform: str = ''):
    qs = (
        SoftwareApp.objects.filter(is_published=True, withdrawn_at__isnull=True)
        .select_related('category', 'recommended_version')
        .prefetch_related('versions__files')
    )
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(short_description__icontains=search)
            | Q(full_description__icontains=search)
            | Q(publisher__icontains=search)
        )
    if category:
        qs = qs.filter(category__slug=category)
    if platform:
        qs = qs.filter(
            versions__status=AppVersion.Status.PUBLISHED,
            versions__files__platform=platform,
            versions__files__quarantine_status=AppReleaseFile.QuarantineStatus.APPROVED,
        ).distinct()
    return qs


def visible_versions_for(user, application: SoftwareApp):
    versions = application.versions.all().prefetch_related('files', 'beta_testers')
    return [v for v in versions if can_view_version(user, v)]


def downloadable_files_for(user, version: AppVersion):
    files = []
    for release_file in version.files.all():
        if can_download_file(user, release_file):
            files.append(release_file)
    return files


def client_ip(request) -> str | None:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip() or None
    return request.META.get('REMOTE_ADDR')


def serve_download(request, release_file: AppReleaseFile) -> FileResponse:
    if not can_download_file(request.user, release_file):
        raise PermissionDenied('Téléchargement non autorisé.')
    verify_stored_hash(release_file)
    handle = release_file.file.open('rb')
    filename = release_file.original_name or os.path.basename(release_file.file.name)
    response = FileResponse(handle, as_attachment=True, filename=filename)
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    response['X-AppStore-SHA256'] = release_file.sha256
    AppDownloadEvent.objects.create(
        user=request.user if request.user.is_authenticated else None,
        application=release_file.version.application,
        version=release_file.version,
        release_file=release_file,
        ip_address=client_ip(request),
        user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:2000],
    )
    return response


def download_stats(days: int | None = None):
    qs = AppDownloadEvent.objects.all()
    if days:
        since = timezone.now() - timedelta(days=days)
        qs = qs.filter(completed_at__gte=since)
    by_app = (
        qs.values('application_id', 'application__name')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    by_version = (
        qs.values('version_id', 'version__version_number', 'application__name')
        .annotate(total=Count('id'))
        .order_by('-total')[:50]
    )
    return {
        'total': qs.count(),
        'by_app': list(by_app),
        'by_version': list(by_version),
    }


def publish_announcement(announcement: AppAnnouncement) -> AppAnnouncement:
    announcement.status = AppAnnouncement.Status.PUBLISHED
    announcement.published_at = announcement.published_at or timezone.now()
    announcement.save(update_fields=['status', 'published_at', 'updated_at'])
    return announcement


def archive_announcement(announcement: AppAnnouncement) -> AppAnnouncement:
    announcement.status = AppAnnouncement.Status.ARCHIVED
    announcement.save(update_fields=['status', 'updated_at'])
    return announcement
