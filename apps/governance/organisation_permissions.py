"""Droits de gestion du référentiel institutionnel CNE-ITP."""


def is_organisation_president(user):
    if not user.is_authenticated or not user.is_active:
        return False
    from .models import PilotageMembreship
    return PilotageMembreship.objects.filter(
        expert__user=user, expert__status='ACTIVE', role='PRESIDENT',
    ).exists()


def can_manage_organisation(user):
    return user.is_authenticated and user.is_active and (
        user.has_perm('governance.manage_phoenix') or is_organisation_president(user)
    )


def can_activate_organisation(user):
    return user.is_authenticated and user.is_active and (
        user.has_perm('governance.activate_phoenix') or is_organisation_president(user)
    )


def can_prepare_organisation(user):
    return can_manage_organisation(user) or (
        user.is_authenticated and user.is_active and user.has_perm('governance.prepare_phoenix')
    )
