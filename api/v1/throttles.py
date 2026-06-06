from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class MobileAuthThrottle(AnonRateThrottle):
    """5 tentatives par minute sur les endpoints d'authentification mobile."""
    scope = 'mobile_auth'


class MobileAuthUserThrottle(UserRateThrottle):
    """10 tentatives par minute pour les utilisateurs connectés sur les endpoints auth."""
    scope = 'mobile_auth'
    rate = '10/minute'
