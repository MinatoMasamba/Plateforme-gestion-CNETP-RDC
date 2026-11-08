"""Calcul du temps de présence à partir des sessions de salle."""

from datetime import timedelta


def merge_sessions(sessions, tolerance_seconds=60):
    """Fusionner les micro-coupures et retourner des intervalles (début, fin)."""
    ordered = sorted(
        (session for session in sessions if session.joined_at),
        key=lambda session: session.joined_at,
    )
    intervals = []
    tolerance = timedelta(seconds=tolerance_seconds)

    for session in ordered:
        start = session.joined_at
        end = session.left_at or session.reunion.cloture_salle
        if end is None:
            continue
        if end < start:
            continue

        if intervals and start - intervals[-1][1] <= tolerance:
            previous_start, previous_end = intervals[-1]
            intervals[-1] = (previous_start, max(previous_end, end))
        else:
            intervals.append((start, end))

    return intervals


def presence_seconds(sessions, tolerance_seconds=60):
    """Somme des durées de présence après fusion des coupures."""
    return int(sum((end - start).total_seconds() for start, end in merge_sessions(sessions, tolerance_seconds)))


def presence_seconds_for_expert(reunion, expert, tolerance_seconds=60):
    """Temps de présence cumulé d'un expert pour une réunion."""
    sessions = reunion.sessions.filter(expert=expert)
    return presence_seconds(sessions, tolerance_seconds)


def real_duration_seconds(reunion):
    """Durée réelle de la salle, ou durée planifiée à défaut."""
    if reunion.ouverture_salle and reunion.cloture_salle:
        return int((reunion.cloture_salle - reunion.ouverture_salle).total_seconds())
    return 0


def presence_rate(reunion, expert, tolerance_seconds=60):
    """Taux de présence (0-100) d'un expert sur la durée réelle de la réunion."""
    duration = real_duration_seconds(reunion)
    if duration <= 0:
        return 0.0
    return presence_seconds_for_expert(reunion, expert, tolerance_seconds) / duration * 100


def close_open_sessions(reunion, at=None):
    """Fermer les sessions encore ouvertes lors de la clôture de la salle."""
    from django.utils import timezone

    closed_at = at or timezone.now()
    reunion.sessions.filter(left_at__isnull=True).update(
        left_at=closed_at, left_reason='ROOM_END'
    )


def apply_presence_at_close(reunion):
    """Calculer la présence réelle et générer les jetons selon la règle métier.

    Sans ``ReglePresence`` pour le type de réunion, aucun seuil ni montant n'est
    inventé : seules les sessions sont conservées.
    """
    from apps.meetings.models import Presence, ReglePresence
    from apps.payments.models import JetonPresence

    close_open_sessions(reunion)
    rule = ReglePresence.objects.filter(type_reunion=reunion.type).first()
    if rule is None:
        return None

    duration = real_duration_seconds(reunion)
    tolerance = rule.tolerance_coupure_s

    for participant in reunion.participants.select_related('expert__user'):
        presence, _ = Presence.objects.get_or_create(
            reunion=reunion, expert=participant.expert, defaults={'status': 'ABSENT'}
        )
        if presence.status == 'EXCUSED':
            continue

        seconds = presence_seconds_for_expert(reunion, participant.expert, tolerance)
        rate = (seconds / duration * 100) if duration > 0 else 0.0
        new_status = 'PRESENT' if rate >= rule.seuil_presence_pct else 'ABSENT'
        if presence.status != new_status:
            presence.status = new_status
            presence.save(update_fields=['status', 'updated_at'])

        if new_status != 'PRESENT':
            continue

        jeton, created = JetonPresence.objects.get_or_create(
            expert=participant.expert,
            reunion=reunion,
            defaults={
                'montant': rule.montant_jeton,
                'presence_secondes': seconds,
                'calcul_automatique': True,
            },
        )
        if not created and jeton.status != 'PAID' and jeton.contestation_status == 'NONE':
            jeton.montant = rule.montant_jeton
            jeton.presence_secondes = seconds
            jeton.calcul_automatique = True
            jeton.save(update_fields=[
                'montant', 'presence_secondes', 'calcul_automatique', 'updated_at',
            ])

    return rule
