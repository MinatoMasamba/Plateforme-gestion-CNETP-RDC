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
