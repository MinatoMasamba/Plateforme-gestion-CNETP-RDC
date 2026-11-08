"""Diffusion administrative explicite du communiqué original, sans nommer un titulaire ST."""
import hashlib
import json
from pathlib import Path
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.validators import validate_email
from django.db import transaction
from apps.core.models import User
from apps.governance.models import Organe, JournalMigration
from apps.governance.phoenix_runtime import current_organisation_version
from apps.mobileapp.models import Notification
from .dispatch_models import InstitutionalDispatch, DispatchRecipient
from .dispatch_services import target_recipients


def official_asset():
    folder = Path(settings.BASE_DIR) / 'communiquer'
    manifest = json.loads((folder / 'communique_003_manifest.json').read_text())
    source = folder / manifest['filename']
    if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != manifest['sha256']:
        raise ValidationError('Le PDF original ne correspond pas à son empreinte archivée.')
    return manifest, source, (folder / manifest['plain_text_fallback']).read_text(), (folder / manifest['html_template']).read_text()


def confirmed_sc_users():
    version = current_organisation_version()
    if not version:
        raise ValidationError('Aucun référentiel de sous-commissions.')
    ids = set()
    for sc in Organe.objects.filter(version=version, type='SC', status__in=('VALIDATED', 'ACTIVE')):
        ids.update(target_recipients(sc).values_list('pk', flat=True))
    return version, User.objects.filter(pk__in=ids, is_active=True).order_by('pk')


@transaction.atomic
def archive_official_communique(all_users=False):
    manifest, source, body, html = official_asset()
    version, users = confirmed_sc_users()
    if all_users:
        users = User.objects.filter(is_active=True).order_by('pk')
    recipients = list(users)
    if not recipients:
        raise ValidationError('Aucun membre confirmé des sous-commissions.')
    key = uuid.uuid5(uuid.NAMESPACE_URL, 'cne-itp:communique:' + manifest['reference'] + ':' + manifest['date'] + (':all-users' if all_users else ':sc'))
    fingerprint = hashlib.sha256((manifest['sha256'] + body + html).encode()).hexdigest()
    existing = InstitutionalDispatch.objects.select_for_update().filter(sender__isnull=True, request_key=key).first()
    if existing:
        if existing.fingerprint != fingerprint:
            raise ValidationError('Le contenu de ce communiqué déjà archivé a changé.')
        return existing, False
    dispatch = InstitutionalDispatch(sender_name='Ecosys RDC', target_all_sc=not all_users, target_all_users=all_users,
        organisation_version=version, target_code='TOUS-UTILISATEURS' if all_users else 'TOUTES-SC', target_label='Tous les utilisateurs' if all_users else 'Toutes les sous-commissions',
        subject=manifest['subject'], body=body, html_body=html, request_key=key, fingerprint=fingerprint,
        original_filename=manifest['filename'], attachment_sha256=manifest['sha256'],
        attachment_size=source.stat().st_size, attachment_mime='application/pdf')
    stored = None
    try:
        with source.open('rb') as stream:
            dispatch.attachment.save(source.name, File(stream), save=False)
        stored = dispatch.attachment.name
        dispatch.full_clean()
        dispatch.save()
        notifications = [Notification(user=user, title=manifest['subject'], body=body[:300], notification_type='MESSAGE',
            data={'kind': 'institutional_dispatch', 'dispatch_id': dispatch.pk, 'communique_reference': manifest['reference'], 'api_url': f'/api/v1/communications/{dispatch.pk}/'}) for user in recipients]
        Notification.objects.bulk_create(notifications)
        deliveries = []
        seen_emails = set()
        for user, notification in zip(recipients, notifications):
            address = (user.email or '').strip()
            try:
                validate_email(address)
                status, error = 'PENDING', ''
                if address.casefold() in seen_emails:
                    status, error = 'SKIPPED', 'Adresse déjà prise en charge pour un autre compte du même envoi.'
                else:
                    seen_emails.add(address.casefold())
            except ValidationError:
                address, status, error = '', 'SKIPPED', 'Adresse e-mail absente ou invalide.'
            deliveries.append(DispatchRecipient(dispatch=dispatch, user=user, recipient_name=user.get_full_name() or user.username,
                notification=notification, email=address, email_status=status, email_error=error))
        DispatchRecipient.objects.bulk_create(deliveries)
        JournalMigration.objects.create(version=version, actor_name='Ecosys RDC — diffusion demandée par l’utilisateur',
            operation='OFFICIAL_COMMUNIQUE', target=f'dispatch:{dispatch.pk}', after={'reference': manifest['reference'], 'sha256': manifest['sha256'], 'recipient_count': len(recipients)},
            reason='Diffusion administrative explicitement demandée ; aucune nomination ST.')
        return dispatch, True
    except Exception:
        if stored:
            dispatch.attachment.storage.delete(stored)
        raise
