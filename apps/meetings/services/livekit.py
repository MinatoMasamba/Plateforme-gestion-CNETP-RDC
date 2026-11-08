"""Jetons et opérations LiveKit pour la salle de réunion."""

import uuid
from datetime import timedelta

from django.conf import settings


class LiveKitNotConfigured(RuntimeError):
    """LiveKit n'est pas configuré dans l'environnement."""


def is_configured():
    return bool(
        getattr(settings, 'LIVEKIT_URL', '')
        and getattr(settings, 'LIVEKIT_API_KEY', '')
        and getattr(settings, 'LIVEKIT_API_SECRET', '')
    )


def ensure_room_name(reunion):
    """Attribuer un nom de salle stable à une réunion de mode SALLE."""
    if not reunion.room_name:
        reunion.room_name = f"reunion-{uuid.uuid4().hex}"
        reunion.save(update_fields=['room_name'])
    return reunion.room_name


def generate_join_token(reunion, participant):
    """Générer un jeton LiveKit lié à l'identité de l'expert invité."""
    if not is_configured():
        raise LiveKitNotConfigured("LiveKit n'est pas configuré.")

    from livekit import api

    room_name = ensure_room_name(reunion)
    expert = participant.expert
    ttl = int(getattr(settings, 'LIVEKIT_TOKEN_TTL_SECONDS', 300))

    token = api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
    token.with_identity(str(expert.pk))
    token.with_name(expert.user.get_full_name() or expert.user.username)
    token.with_ttl(timedelta(seconds=ttl))
    sources = None
    if participant.peut_parler and not participant.peut_video:
        sources = ['microphone']
    token.with_grants(
        api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=participant.peut_parler,
            can_subscribe=True,
            can_publish_data=True,
            can_publish_sources=sources,
        )
    )

    return {
        'url': settings.LIVEKIT_URL,
        'token': token.to_jwt(),
        'role': participant.role,
        'peut_parler': participant.peut_parler,
        'room_name': room_name,
        'expires_in': ttl,
    }
