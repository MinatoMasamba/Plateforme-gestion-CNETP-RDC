from apps.experts.models import Expert
from apps.governance.models import CTCMembership, PilotageMembreship


def get_expert_for_user(user):
    return (
        Expert.objects.filter(user=user, status='ACTIVE')
        .select_related('user', 'structure', 'ctm')
        .first()
    )


def available_scopes(user):
    """Liste des scopes ('expert'/'ctc'/'pilotage') accessibles à cet utilisateur."""
    expert = get_expert_for_user(user)
    if not expert:
        return []

    scopes = ['expert']

    if CTCMembership.objects.filter(expert=expert).exists():
        scopes.append('ctc')

    if PilotageMembreship.objects.filter(expert=expert).exists():
        scopes.append('pilotage')

    return scopes


def user_can_access_scope(user, scope):
    return scope in available_scopes(user)
