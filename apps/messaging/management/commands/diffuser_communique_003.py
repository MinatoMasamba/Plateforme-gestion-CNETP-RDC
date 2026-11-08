"""Diffuser le PDF original et le HTML exact aux membres confirmés des SC."""
from collections import Counter
import json
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from apps.messaging.official_dispatch import official_asset, confirmed_sc_users, archive_official_communique
from apps.messaging.dispatch_delivery import deliver_dispatch_emails


class Command(BaseCommand):
    help = 'Prévisualise ou diffuse le communiqué original 003, avec historique plateforme et e-mail.'

    def add_arguments(self, parser):
        parser.add_argument('--send', action='store_true')
        parser.add_argument('--all-users', action='store_true')
        parser.add_argument('--retry-failed', action='store_true')

    def handle(self, *args, **options):
        manifest, source, body, html = official_asset()
        version, users = confirmed_sc_users()
        if options['all_users']:
            from apps.core.models import User
            users = User.objects.filter(is_active=True).order_by('pk')
        users = list(users)
        valid = 0
        unique_addresses = set()
        for user in users:
            try:
                validate_email((user.email or '').strip())
                valid += 1
                unique_addresses.add(user.email.strip().casefold())
            except ValidationError:
                pass
        self.stdout.write(json.dumps({'reference': manifest['reference'], 'version': version.code, 'recipients': len(users),
            'valid_email_addresses': valid, 'unique_email_recipients': len(unique_addresses), 'duplicate_email_addresses': valid-len(unique_addresses), 'missing_or_invalid_email': len(users)-valid, 'pdf_bytes': source.stat().st_size,
            'html_ready': bool(html), 'email_backend': settings.EMAIL_BACKEND, 'smtp_host': settings.EMAIL_HOST,
            'preview_only': not options['send']}, ensure_ascii=False))
        if not options['send']:
            return
        if settings.EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend':
            raise CommandError('Envoi réel refusé : le backend SMTP de production n’est pas configuré.')
        dispatch, created = archive_official_communique(all_users=options['all_users'])
        if options['retry_failed']:
            dispatch.recipients.filter(email_status='FAILED').update(email_status='PENDING', email_error='')
        deliver_dispatch_emails(dispatch.pk)
        statuses = Counter(dispatch.recipients.values_list('email_status', flat=True))
        self.stdout.write(json.dumps({'dispatch_id': dispatch.pk, 'created': created, 'email_results': dict(statuses),
            'internal_notifications': dispatch.recipients.count(), 'platform_archive': True}, ensure_ascii=False))
