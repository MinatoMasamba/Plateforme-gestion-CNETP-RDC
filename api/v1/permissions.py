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
        # Les coordinateurs CTC peuvent tout modifier
        if request.user.is_ctc_staff:
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


class IsExpertOfCTM(permissions.BasePermission):
    """Permission : Expert doit être du CTM"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.is_expert):
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'expert fait partie du CTM
        if hasattr(request.user, 'expert_profile'):
            expert = request.user.expert_profile
            # Vérifier si l'expert a une affectation au CTM
            if hasattr(obj, 'ctm'):
                return expert.governance_affectations.filter(ctm=obj.ctm).exists()
        return False


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
