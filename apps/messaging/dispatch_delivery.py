"""Boîte de sortie e-mail : résultat et tentatives distincts de la réception interne."""
from email.utils import parseaddr
import logging
import smtplib
from django.conf import settings
from django.core.mail import EmailMultiAlternatives as EmailMessage, get_connection
from django.db import transaction
from django.utils import timezone
from .dispatch_models import DispatchRecipient, DispatchEmailAttempt

logger = logging.getLogger(__name__)


def enqueue_dispatch_emails(dispatch_id):
    try:
        from .tasks import deliver_institutional_dispatch
        deliver_institutional_dispatch.delay(dispatch_id)
    except Exception as exc:
        logger.error('Planification des e-mails indisponible pour l’envoi %s (%s)', dispatch_id, type(exc).__name__)
        DispatchRecipient.objects.filter(dispatch_id=dispatch_id, email_status='PENDING').update(
            email_status='FAILED', email_error='Planification indisponible ; relance requise.')


def deliver_dispatch_emails(dispatch_id, limit=None):
    ids = list(DispatchRecipient.objects.filter(dispatch_id=dispatch_id, email_status='PENDING').order_by('pk').values_list('pk', flat=True)[:limit])
    fatal_error = False
    for recipient_id in ids:
        with transaction.atomic():
            recipient = DispatchRecipient.objects.select_for_update().select_related('dispatch', 'user').get(pk=recipient_id)
            if recipient.email_status != 'PENDING':
                continue
            if not recipient.email or not recipient.user.is_active:
                recipient.email_status = 'SKIPPED'
                recipient.email_error = 'Adresse absente ou compte désactivé avant traitement.'
                recipient.save(update_fields=['email_status', 'email_error'])
                continue
            recipient.email_status = 'SENDING'
            recipient.email_attempts += 1
            recipient.save(update_fields=['email_status', 'email_attempts'])
            attempt = DispatchEmailAttempt.objects.create(recipient=recipient, number=recipient.email_attempts)
        error, outcome = '', 'SENT'
        try:
            dispatch = recipient.dispatch
            domain = parseaddr(settings.DEFAULT_FROM_EMAIL)[1].split('@')[-1] or 'cne-itp.local'
            message = EmailMessage(subject=dispatch.subject,
                body=dispatch.body,
                from_email=settings.DEFAULT_FROM_EMAIL, to=[recipient.email], connection=get_connection(timeout=90),
                headers={'Message-ID': f'<st-dispatch-{dispatch.request_key.hex}-{recipient.pk}@{domain}>'})
            if dispatch.html_body:
                message.attach_alternative(dispatch.html_body, 'text/html')
            if dispatch.attachment:
                with dispatch.attachment.open('rb') as stream:
                    message.attach(dispatch.original_filename, stream.read(), dispatch.attachment_mime)
            if message.send(fail_silently=False) != 1:
                raise RuntimeError('Aucun e-mail accepté par le transport.')
        except Exception as exc:
            outcome = 'FAILED'
            fatal_error = isinstance(exc, (OSError, smtplib.SMTPAuthenticationError, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, smtplib.SMTPSenderRefused, smtplib.SMTPDataError))
            error = f'Échec de l’envoi ({type(exc).__name__}).'
            logger.warning('Échec e-mail pour le destinataire d’envoi %s (%s)', recipient_id, type(exc).__name__)
        with transaction.atomic():
            DispatchEmailAttempt.objects.filter(pk=attempt.pk).update(outcome=outcome, error=error, finished_at=timezone.now())
            DispatchRecipient.objects.filter(pk=recipient_id, email_status='SENDING', email_attempts=recipient.email_attempts).update(
                email_status=outcome, email_error=error, email_sent_at=timezone.now() if outcome == 'SENT' else None)
        if fatal_error:
            DispatchRecipient.objects.filter(dispatch_id=dispatch_id, email_status='PENDING').update(email_status='FAILED', email_error='Transport SMTP indisponible ; envoi non tenté, relance requise.')
            break
    return {'dispatch_id': dispatch_id, 'processed': len(ids)}
