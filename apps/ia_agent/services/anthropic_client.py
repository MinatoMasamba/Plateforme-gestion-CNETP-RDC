from django.conf import settings

_client = None


def get_client():
    """Retourne un client Anthropic partagé, ou None si aucune clé n'est configurée."""
    global _client

    if not settings.ANTHROPIC_API_KEY:
        return None

    if _client is None:
        import anthropic

        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    return _client
