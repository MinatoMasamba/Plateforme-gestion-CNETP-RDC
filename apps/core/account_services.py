"""Règles métier de désactivation et réactivation des comptes."""
from django.apps import apps
from django.db import transaction

from apps.core.models import AuditLog, User

VALID_EXPERT_STATUSES = {'PENDING', 'ACTIVE', 'INACTIVE', 'SUSPENDED', 'REJECTED'}


def is_last_active_superuser(user):
    if not user.is_superuser or not user.is_active:
        return False
    return not User.objects.filter(
        is_superuser=True,
        is_active=True,
    ).exclude(pk=user.pk).exists()


def previous_expert_status(user):
    expert = getattr(user, 'expert_profile', None)
    if expert is None:
        return None
    Expert = apps.get_model('experts', 'Expert')
    logs = AuditLog.objects.filter(
        content_type=Expert._meta.label,
        object_id=expert.pk,
        action='UPDATE',
    ).order_by('-timestamp')
    for log in logs:
        change = (log.changes or {}).get('status')
        if not change or change.get('new') != 'SUSPENDED':
            continue
        old = change.get('old')
        if old in VALID_EXPERT_STATUSES:
            return old
    return None


@transaction.atomic
def deactivate_user(user):
    if is_last_active_superuser(user):
        raise ValueError('Impossible de désactiver le dernier superutilisateur actif.')
    if not user.is_active:
        return user
    user.is_active = False
    user.save(update_fields=['is_active'])
    expert = getattr(user, 'expert_profile', None)
    if expert is not None and expert.status in {'ACTIVE', 'PENDING'}:
        expert.status = 'SUSPENDED'
        expert.save(update_fields=['status'])
    return user


@transaction.atomic
def reactivate_user(user, restore_expert_status=True):
    if user.is_active:
        return user
    user.is_active = True
    user.save(update_fields=['is_active'])
    expert = getattr(user, 'expert_profile', None)
    if restore_expert_status and expert is not None and expert.status == 'SUSPENDED':
        status = previous_expert_status(user) or 'ACTIVE'
        expert.status = status
        expert.save(update_fields=['status'])
    return user
