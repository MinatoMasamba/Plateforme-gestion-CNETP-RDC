"""Programmer la copie Drive après validation et commit des fichiers locaux."""

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.utils import OperationalError, ProgrammingError

from apps.norms.models import Norme
from .models import DocumentFile
from .tasks import sync_drive_document, sync_drive_norm

logger = logging.getLogger(__name__)


def _schedule(task, source_id, fallback):
    try:
        task.delay(source_id)
    except Exception:
        logger.exception('File Celery Drive indisponible ; transfert direct après commit.')
        fallback(source_id)


def _enabled():
    from .drive_sync import enabled
    try:
        return enabled()
    except (OperationalError, ProgrammingError):
        # La table peut ne pas encore exister pendant l'installation initiale.
        return False


@receiver(post_save, sender=Norme, dispatch_uid='ctc_drive_norm_validated')
def queue_validated_norm(sender, instance, **kwargs):
    from .drive_sync import allowed_statuses
    if not _enabled() or instance.status not in allowed_statuses():
        return
    from .drive_sync import sync_norm
    transaction.on_commit(lambda: _schedule(sync_drive_norm, instance.pk, sync_norm))


@receiver(post_save, sender=DocumentFile, dispatch_uid='ctc_drive_document_validated')
def queue_validated_document(sender, instance, **kwargs):
    if not instance.norme_id or not _enabled():
        return
    from .drive_sync import allowed_statuses
    if instance.norme.status in allowed_statuses():
        from .drive_sync import sync_one
        transaction.on_commit(lambda: _schedule(
            sync_drive_document, instance.pk, lambda pk: sync_one('DOCUMENT', pk)
        ))
