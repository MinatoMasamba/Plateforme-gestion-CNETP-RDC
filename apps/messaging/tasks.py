from celery import shared_task
from .dispatch_delivery import deliver_dispatch_emails


@shared_task(name='messaging.deliver_institutional_dispatch', acks_late=True)
def deliver_institutional_dispatch(dispatch_id):
    return deliver_dispatch_emails(dispatch_id)
