from celery import shared_task

from .drive_sync import sync_backlog, sync_norm, sync_one


@shared_task
def sync_drive_norm(norme_id):
    return sync_norm(norme_id)


@shared_task
def sync_drive_document(document_id):
    return sync_one('DOCUMENT', document_id)


@shared_task
def sync_drive_backlog():
    return sync_backlog()
