from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

from apps.payments.models import Cotisation

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_payment_reminder(self, cotisation_id):
    """Envoyer un email de rappel pour une cotisation (tâche Celery).
    Mode simple : utilise le champ email de la structure si disponible.
    """
    try:
        cotisation = Cotisation.objects.select_related('structure').get(id=cotisation_id)
    except Cotisation.DoesNotExist:
        logger.exception("Cotisation %s introuvable", cotisation_id)
        return False

    structure = cotisation.structure
    recipient = structure.email
    if not recipient:
        logger.warning("Structure %s n'a pas d'email — rappel non envoyé", structure.name)
        return False

    subject = f"Rappel de cotisation CNETP — {cotisation.annee}"
    message = (
        f"Bonjour,\n\n"
        f"Ce message concerne la cotisation de {structure.name} pour l'année {cotisation.annee}.\n"
        f"Montant dû : {cotisation.montant}\n"
        f"Date d'échéance : {cotisation.due_date}\n\n"
        "Merci de procéder au paiement.\n\n"
        "CNETP"
    )

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
    logger.info("Rappel de paiement envoyé pour cotisation %s à %s", cotisation_id, recipient)
    return True
