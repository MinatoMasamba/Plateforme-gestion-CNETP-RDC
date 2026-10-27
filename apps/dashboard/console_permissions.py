"""Accès et permissions de la console d'administration."""
from functools import wraps

from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

DEFAULT_CONSOLE_GROUP = 'Administrateurs CNE-ITP'
AUDIT_CONTENT_TYPES = {'core.auditlog', 'core.audittextchange'}
AUDIT_MUTATION_CODENAMES = {
    'add_auditlog', 'change_auditlog', 'delete_auditlog',
    'add_audittextchange', 'change_audittextchange', 'delete_audittextchange',
}


def console_group_name():
    return getattr(settings, 'CONSOLE_ACCESS_GROUP', DEFAULT_CONSOLE_GROUP)


def local_app_labels():
    return tuple(
        app.label for app in apps.get_app_configs()
        if app.name.startswith('apps.')
    )


def has_console_access(user):
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=console_group_name()).exists()


def console_required(view_func):
    @wraps(view_func)
    @login_required(login_url='web:expert_login')
    def wrapped(request, *args, **kwargs):
        if not has_console_access(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped


def sync_console_group(sender=None, **kwargs):
    """Crée/complète le groupe sans retirer les droits ajoutés manuellement."""
    from django.contrib.auth.models import Group, Permission

    group, _created = Group.objects.get_or_create(name=console_group_name())
    labels = local_app_labels()
    permissions = Permission.objects.filter(content_type__app_label__in=labels)
    permissions = permissions.exclude(content_type__app_label='core', codename='delete_user')
    permissions = permissions.exclude(
        content_type__app_label='core',
        content_type__model__in={'auditlog', 'audittextchange'},
        codename__in=AUDIT_MUTATION_CODENAMES,
    )
    log_permission = Permission.objects.filter(
        content_type__app_label='admin',
        codename='view_logentry',
    )
    group.permissions.add(*permissions, *log_permission)
    return group
