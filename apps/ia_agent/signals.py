"""Réindexation asynchrone après modification des sources métier."""

import logging

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _enqueue(task, object_id):
    def dispatch():
        try:
            task.delay(object_id)
        except Exception:
            # Une panne Celery ne doit pas empêcher l'enregistrement métier.
            logger.exception('Réindexation RAG différée impossible pour %s/%s', task.name, object_id)

    transaction.on_commit(dispatch)


@receiver(post_save, sender='documents.DocumentFile', dispatch_uid='rag_index_document_file')
def index_document_after_save(sender, instance, raw=False, **kwargs):
    if not raw:
        from .tasks import reindex_document_file
        _enqueue(reindex_document_file, instance.pk)


@receiver(post_save, sender='norms.Norme', dispatch_uid='rag_index_norme')
def index_norme_after_save(sender, instance, raw=False, **kwargs):
    if not raw and instance.circuit_version == 'LEGACY':
        from .tasks import reindex_norme
        _enqueue(reindex_norme, instance.pk)


@receiver(post_save, sender='norms.NormeVersion', dispatch_uid='rag_index_norme_version')
def index_norme_version_after_save(sender, instance, raw=False, **kwargs):
    if not raw and instance.norme.circuit_version == 'LEGACY':
        from .tasks import reindex_norme_version
        _enqueue(reindex_norme_version, instance.pk)


@receiver(pre_save, sender='experts.Expert', dispatch_uid='rag_track_expert_cv')
def track_expert_cv_change(sender, instance, **kwargs):
    if not instance.pk:
        instance._rag_cv_changed = bool(instance.cv)
        return
    previous = sender.objects.filter(pk=instance.pk).values_list('cv', flat=True).first()
    instance._rag_cv_changed = previous != (instance.cv.name if instance.cv else '')


@receiver(post_save, sender='experts.Expert', dispatch_uid='rag_index_expert_cv')
def index_expert_cv_after_save(sender, instance, raw=False, **kwargs):
    if not raw and getattr(instance, '_rag_cv_changed', False):
        from .tasks import reindex_expert_cv
        _enqueue(reindex_expert_cv, instance.pk)
