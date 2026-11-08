from apps.experts.models import Expert
from apps.governance.models import CTCMembership, PilotageMembreship


def get_expert_for_user(user):
    return (
        Expert.objects.filter(user=user, status='ACTIVE')
        .select_related('user', 'structure', 'ctm')
        .first()
    )


def available_scopes(user):
    """Liste des scopes accessibles à cet utilisateur."""
    from .neuronne_admin import is_neuronne_admin

    admin = is_neuronne_admin(user)
    expert = get_expert_for_user(user)
    if not expert:
        scopes = ['expert'] if user.is_active and user.is_staff and user.has_perm('governance.add_nominationctc') else []
        return scopes + (['admin'] if admin else [])

    scopes = ['expert']
    if admin:
        scopes.append('admin')

    from apps.governance.phoenix_runtime import active_st_mandate
    if active_st_mandate(expert) or CTCMembership.objects.filter(expert=expert).exists():
        scopes.append('ctc')

    if PilotageMembreship.objects.filter(expert=expert).exists():
        scopes.append('pilotage')

    return scopes


def user_can_access_scope(user, scope):
    return scope in available_scopes(user)
