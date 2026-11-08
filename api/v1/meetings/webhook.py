"""Réception signée des webhooks LiveKit."""

import logging
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.experts.models import Expert
from apps.meetings.models import (
    Enregistrement, LiveKitWebhookEvent, Presence, PresenceSession,
    Reunion, ReunionParticipant,
)
from apps.meetings.services.livekit import is_configured
from apps.meetings.services.presence import apply_presence_at_close, close_open_sessions

logger = logging.getLogger(__name__)

LEFT_REASON_BY_DISCONNECT = {
    'CLIENT_INITIATED': 'QUIT',
    'DUPLICATE_IDENTITY': 'DISCONNECT',
    'SERVER_SHUTDOWN': 'ROOM_END',
    'PARTICIPANT_REMOVED': 'KICKED',
    'ROOM_DELETED': 'ROOM_END',
}


def _reunion_for_room(room_name):
    if not room_name:
        return None
    return Reunion.objects.filter(room_name=room_name).first()


def _event_id(event):
    if event.id:
        return event.id
    return ':'.join([
        event.event or '',
        getattr(event.room, 'sid', '') or '',
        getattr(event.participant, 'sid', '') or '',
        str(event.created_at or ''),
    ])


def _handle_room_started(reunion):
    if reunion is None:
        return
    update_fields = ['updated_at']
    if reunion.status == 'PLANNED':
        reunion.status = 'IN_PROGRESS'
        update_fields.append('status')
    if reunion.ouverture_salle is None:
        reunion.ouverture_salle = timezone.now()
        update_fields.append('ouverture_salle')
    reunion.save(update_fields=update_fields)


def _handle_room_finished(reunion):
    if reunion is None:
        return
    update_fields = ['updated_at']
    if reunion.cloture_salle is None:
        reunion.cloture_salle = timezone.now()
        update_fields.append('cloture_salle')
    if reunion.status != 'COMPLETED':
        reunion.status = 'COMPLETED'
        update_fields.append('status')
    reunion.save(update_fields=update_fields)
    apply_presence_at_close(reunion)


def _handle_participant_joined(reunion, event):
    if reunion is None:
        return
    identity = getattr(event.participant, 'identity', '')
    try:
        expert = Expert.objects.select_related('user').get(pk=int(identity))
    except (TypeError, ValueError, Expert.DoesNotExist):
        logger.warning("LiveKit: identité inconnue %s pour %s", identity, reunion.room_name)
        return

    participant = ReunionParticipant.objects.filter(reunion=reunion, expert=expert).first()
    if participant is None:
        logger.warning(
            "LiveKit: expert %s non invité à la réunion %s", expert.pk, reunion.pk,
        )
        return

    now = timezone.now()
    joined_at = now
    if getattr(event.participant, 'joined_at', 0):
        joined_at = datetime.fromtimestamp(event.participant.joined_at, tz=dt_timezone.utc)

    session = reunion.sessions.filter(expert=expert, left_at__isnull=True).first()
    if session is None:
        session = PresenceSession.objects.create(
            reunion=reunion,
            expert=expert,
            livekit_sid=getattr(event.participant, 'sid', ''),
            joined_at=joined_at,
        )
    else:
        session.livekit_sid = getattr(event.participant, 'sid', '')
        session.save(update_fields=['livekit_sid', 'updated_at'])

    presence, created = Presence.objects.get_or_create(
        reunion=reunion, expert=expert, defaults={'status': 'PRESENT', 'marked_at': now},
    )
    if not created and presence.status != 'EXCUSED':
        presence.status = 'PRESENT'
        presence.marked_at = now
        presence.save(update_fields=['status', 'marked_at', 'updated_at'])


def _handle_participant_left(reunion, event):
    if reunion is None:
        return
    identity = getattr(event.participant, 'identity', '')
    try:
        expert_id = int(identity)
    except (TypeError, ValueError):
        return

    session = reunion.sessions.filter(expert_id=expert_id, left_at__isnull=True).first()
    if session is None:
        return

    disconnect_reason = getattr(event.participant, 'disconnect_reason', '')
    session.left_at = timezone.now()
    session.left_reason = LEFT_REASON_BY_DISCONNECT.get(disconnect_reason, 'DISCONNECT')
    session.save(update_fields=['left_at', 'left_reason', 'updated_at'])


def _handle_egress(reunion, event, statut):
    if reunion is None:
        return
    egress_id = getattr(getattr(event, 'egress_info', None), 'egress_id', '')
    if not egress_id:
        return
    Enregistrement.objects.filter(reunion=reunion, egress_id=egress_id).update(statut=statut)


def _process_event(event):
    room_name = getattr(getattr(event, 'room', None), 'name', '')
    reunion = _reunion_for_room(room_name)

    if event.event == 'room_started':
        _handle_room_started(reunion)
    elif event.event == 'room_finished':
        _handle_room_finished(reunion)
    elif event.event == 'participant_joined':
        _handle_participant_joined(reunion, event)
    elif event.event == 'participant_left':
        _handle_participant_left(reunion, event)
    elif event.event == 'egress_started':
        _handle_egress(reunion, event, 'EN_COURS')
    elif event.event == 'egress_updated':
        _handle_egress(reunion, event, 'EN_COURS')
    elif event.event == 'egress_ended':
        _handle_egress(reunion, event, 'TERMINE')


@csrf_exempt
@require_POST
def livekit_webhook(request):
    """Vérifier la signature du webhook puis traiter l'événement de façon idempotente."""
    if not is_configured():
        return JsonResponse({'detail': "LiveKit n'est pas configuré."}, status=503)

    from livekit import api
    from google.protobuf.json_format import MessageToDict

    body = request.body.decode('utf-8')
    auth_header = request.headers.get('Authorization', '')
    receiver = api.WebhookReceiver(api.TokenVerifier(
        settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET,
    ))
    try:
        event = receiver.receive(body, auth_header)
    except Exception:
        logger.warning("LiveKit: webhook rejeté (signature invalide).")
        return JsonResponse({'detail': 'Signature invalide.'}, status=401)

    event_id = _event_id(event)
    payload = MessageToDict(event, preserving_proto_field_name=True)
    row, created = LiveKitWebhookEvent.objects.get_or_create(
        event_id=event_id,
        defaults={
            'event_type': event.event or '',
            'room_name': getattr(getattr(event, 'room', None), 'name', ''),
            'payload': payload,
        },
    )
    if not created and row.traite_le is not None:
        return JsonResponse({'status': 'already_processed'})

    try:
        _process_event(event)
    except Exception:
        logger.exception("LiveKit: échec du traitement de l'événement %s", event_id)
        return JsonResponse({'detail': 'Erreur de traitement.'}, status=500)

    row.traite_le = timezone.now()
    row.save(update_fields=['traite_le', 'updated_at'])
    return JsonResponse({'status': 'ok'})
