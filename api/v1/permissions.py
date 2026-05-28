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


class IsMemberOfAnySharedCTM(permissions.BasePermission):
    """Permission : Permet aux experts de communiquer s'ils partagent au moins un CTM en commun."""

    def has_permission(self, request, view):
        # Seuls les utilisateurs authentifiés et experts peuvent initier ou voir des conversations de messagerie.
        if not (request.user and request.user.is_authenticated and hasattr(request.user, 'expert_profile')):
            return False
        return True

    def has_object_permission(self, request, view, obj):
        # Pour les messages existants, vérifier si l'utilisateur actuel est l'expéditeur ou le destinataire
        # et s'ils partagent un CTM commun avec l'autre partie.
        if not (request.user and request.user.is_authenticated and hasattr(request.user, 'expert_profile')):
            return False

        current_expert_ctms = set(request.user.expert_profile.ctm_choices.values_list('id', flat=True))

        if obj.sender == request.user:
            # L'utilisateur est l'expéditeur, vérifier le destinataire
            if obj.recipient and hasattr(obj.recipient, 'expert_profile'):
                recipient_expert_ctms = set(obj.recipient.expert_profile.ctm_choices.values_list('id', flat=True))
                return bool(current_expert_ctms.intersection(recipient_expert_ctms))
            # Si pas de destinataire (ex: message de groupe ou diffusé sans destinataire explicite), pas de restriction de CTM ici
            return True 

        elif obj.recipient == request.user:
            # L'utilisateur est le destinataire, vérifier l'expéditeur
            if obj.sender and hasattr(obj.sender, 'expert_profile'):
                sender_expert_ctms = set(obj.sender.expert_profile.ctm_choices.values_list('id', flat=True))
                return bool(current_expert_ctms.intersection(sender_expert_ctms))
            return True
        
        # Si le message est lié à une réunion, l'accès est déterminé par la participation à la réunion ou le CTM de la réunion.
        # Pour l'instant, nous ne gérons pas cette complexité de CTM-Reunion car le modèle Reunion n'a pas de lien direct avec CTM.
        # La logique par défaut ci-dessus couvre les messages directs entre experts.

        return False # Par défaut, refuser l'accès si aucune des conditions n'est remplie.
