from rest_framework import permissions


class IsExpert(permissions.BasePermission):
    """Permission : Utilisateur est un expert inscrit"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_expert
        )
    
    def has_object_permission(self, request, view, obj):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_expert
        )


class IsCTCCoordinator(permissions.BasePermission):
    """Permission : Utilisateur est coordinateur CTC"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_ctc_staff
        )


class IsMinister(permissions.BasePermission):
    """Permission : Utilisateur est ministre"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_minister
        )


class IsExpertOrCTC(permissions.BasePermission):
    """Permission : Expert OU Coordinateur CTC"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_expert or request.user.is_ctc_staff)
        )


class IsOwnerOrCTC(permissions.BasePermission):
    """Permission : Propriétaire de l'objet OU Coordinateur CTC"""
    
    def has_object_permission(self, request, view, obj):
        # Les coordinateurs CTC / staff peuvent tout modifier
        if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_ctc_staff', False):
            return True

        # L'utilisateur ne peut modifier ses propres données
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        return False


class IsMeetingOrganizerOrCTC(permissions.BasePermission):
    """Permission : Organisateur de la réunion (gestion de l'émargement) OU Coordinateur CTC/Admin."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_ctc_staff or request.user.is_superuser:
            return True
        expert = getattr(request.user, 'expert_profile', None)
        if not expert:
            return False
        return obj.reunion.organisateur_id == expert.id


def user_ctm_scope(user):
    """Périmètre CTM/SC (sous-commissions) visible par l'utilisateur.

    Retourne ``None`` lorsque l'accès n'est pas restreint (superuser, staff,
    coordinateur CTC, ou membre de la direction/pilotage), sinon un ``set``
    d'IDs de CTM auxquels l'expert est rattaché.
    """
    if not (user and user.is_authenticated):
        return set()
    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False) or getattr(user, 'is_ctc_staff', False):
        return None
    if not getattr(user, 'is_expert', False):
        return None
    expert = getattr(user, 'expert_profile', None)
    if expert is None:
        return None
    # La direction / le pilotage garde une vue transverse.
    try:
        from apps.governance.models import PilotageMembreship
        if PilotageMembreship.objects.filter(expert=expert).exists():
            return None
    except Exception:
        pass
    scope = set()
    if expert.ctm_id:
        scope.add(expert.ctm_id)
    scope.update(expert.governance_affectations.values_list('ctm_id', flat=True))
    scope.discard(None)
    return scope


class IsExpertOfCTM(permissions.BasePermission):
    """Permission : l'objet doit appartenir au CTM/SC de l'expert.

    Les coordinateurs CTC, le staff et les superusers ne sont pas restreints.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_ctc_staff', False) or getattr(request.user, 'is_staff', False):
            return True
        scope = user_ctm_scope(request.user)
        if scope is None:
            return True
        target_ctm_id = getattr(obj, 'ctm_id', None)
        if target_ctm_id is None and hasattr(obj, 'ctm'):
            target_ctm_id = getattr(obj.ctm, 'id', None)
        if target_ctm_id is None:
            return True
        return target_ctm_id in scope


class ReadOnly(permissions.BasePermission):
    """Permission : Lecture seule"""
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsPublicOrAuthenticated(permissions.BasePermission):
    """Permission : Lecture publique (GET) OU utilisateur authentifié"""
    
    def has_permission(self, request, view):
        # GET, HEAD, OPTIONS sont autorisés sans auth
        if request.method in permissions.SAFE_METHODS:
            return True
        # Autres méthodes nécessitent l'authentification
        return request.user and request.user.is_authenticated


class IsLegist(permissions.BasePermission):
    """Permission : Utilisateur est un légiste enregistré"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        # Vérifier que l'utilisateur est un expert avec statut actif
        if hasattr(request.user, 'expert_profile'):
            expert = request.user.expert_profile
            return expert.status == 'ACTIVE'
        return False


class IsMemberOfAnySharedCTM(permissions.BasePermission):
    """Permission : Permet aux experts de communiquer s'ils appartiennent au même CTM."""

    def has_permission(self, request, view):
        # Seuls les utilisateurs authentifiés et experts peuvent initier ou voir des conversations de messagerie.
        if not (request.user and request.user.is_authenticated and hasattr(request.user, 'expert_profile')):
            return False
        return True

    def has_object_permission(self, request, view, obj):
        # Pour les messages existants, vérifier si l'utilisateur actuel est l'expéditeur ou le destinataire
        # et s'ils appartiennent au même CTM.
        if not (request.user and request.user.is_authenticated and hasattr(request.user, 'expert_profile')):
            return False

        current_ctm = request.user.expert_profile.ctm

        if obj.sender == request.user:
            # L'utilisateur est l'expéditeur, vérifier le destinataire
            if obj.recipient and hasattr(obj.recipient, 'expert_profile'):
                recipient_ctm = obj.recipient.expert_profile.ctm
                return current_ctm is not None and current_ctm == recipient_ctm
            # Si pas de destinataire, pas de restriction de CTM ici
            return True 

        elif obj.recipient == request.user:
            # L'utilisateur est le destinataire, vérifier l'expéditeur
            if obj.sender and hasattr(obj.sender, 'expert_profile'):
                sender_ctm = obj.sender.expert_profile.ctm
                return current_ctm is not None and current_ctm == sender_ctm
            return True
        
        return False # Par défaut, refuser l'accès si aucune des conditions n'est remplie.
