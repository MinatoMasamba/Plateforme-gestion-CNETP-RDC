import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_artifact_email(self, artifact_id, user_id):
    try:
        from apps.core.models import AuditLog

        from .models import AgentArtifact

        artifact = AgentArtifact.objects.select_related('session').get(id=artifact_id)
        payload = artifact.payload
        to_email = payload.get('to')
        subject = payload.get('subject')
        body = payload.get('body')

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )

        related_id = payload.get('related_artifact_id')
        if related_id:
            related = AgentArtifact.objects.filter(id=related_id, session=artifact.session).first()
            if related and related.artifact_type == 'WG_REQUEST':
                from .services.pdf_artifacts import generate_wg_request_pdf_from_artifact

                pdf_bytes = generate_wg_request_pdf_from_artifact(related)
                email.attach(f"demande_wg_{related.id}.pdf", pdf_bytes, 'application/pdf')

        email.send(fail_silently=False)

        artifact.status = 'SENT'
        artifact.save(update_fields=['status', 'updated_at'])

        AuditLog.objects.create(
            user_id=user_id,
            action='APPROVE',
            content_type='AgentArtifact',
            object_id=artifact.id,
            object_repr=f"Email envoyé : {subject}",
            changes={"to": to_email, "status": "SENT"},
        )
        return True
    except Exception as exc:
        logger.exception("Erreur lors de l'envoi de l'email pour l'artefact %s : %s", artifact_id, exc)
        try:
            raise self.retry(exc=exc)
        except Exception:
            return False
