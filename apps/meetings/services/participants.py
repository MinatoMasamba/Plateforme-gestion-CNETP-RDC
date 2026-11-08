"""Synchronisation des invitations à une réunion depuis les affectations."""

from apps.meetings.models import Presence, ReunionParticipant

ROLE_BY_LABEL = {
    'Président scientifique CTM': 'PRESIDENT',
    'Président WG': 'PRESIDENT',
    'Rapporteur CTM': 'RAPPORTEUR',
    'Rapporteur WG': 'RAPPORTEUR',
    'Secrétaire CTM': 'SECRETAIRE',
    'Secrétaire WG': 'SECRETAIRE',
    'Membre CTM': 'MEMBRE',
    'Membre WG': 'MEMBRE',
}


def role_from_affectation(affectation, reunion):
    """Déduire le rôle de salle depuis le rôle de gouvernance de l'affectation."""
    label = affectation.wg_role if reunion.wg_id else affectation.ctm_role
    return ROLE_BY_LABEL.get(label, 'MEMBRE')


def iter_affectations(reunion):
    """Retourner les affectations concernées par une réunion WG/CTM."""
    if reunion.wg_id:
        return reunion.wg.affectations.select_related('expert__user', 'ctm', 'wg')
    if reunion.ctm_id:
        return reunion.ctm.affectations.select_related('expert__user', 'ctm', 'wg')
    return []


def sync_participants_from_affectations(reunion):
    """Créer les invitations et les présences attendues pour WG/CTM.

    Les autres types de réunion (PILOTAGE, ASSEMBLEE, CTC) restent à saisie
    manuelle via l'endpoint ``participants/``.
    """
    created = []
    for affectation in iter_affectations(reunion):
        participant, was_created = ReunionParticipant.objects.get_or_create(
            reunion=reunion,
            expert=affectation.expert,
            defaults={'role': role_from_affectation(affectation, reunion)},
        )
        if was_created:
            created.append(participant)
        Presence.objects.get_or_create(
            reunion=reunion,
            expert=affectation.expert,
            defaults={'status': 'ABSENT'},
        )
    return created


def add_participant(
    reunion, expert, role='MEMBRE', peut_parler=True, peut_video=False,
    exclu_jusqua=None,
):
    """Ajouter ou mettre à jour un invité et sa présence attendue."""
    participant, _ = ReunionParticipant.objects.update_or_create(
        reunion=reunion,
        expert=expert,
        defaults={
            'role': role,
            'peut_parler': peut_parler,
            'peut_video': peut_video,
            'exclu_jusqua': exclu_jusqua,
        },
    )
    Presence.objects.get_or_create(
        reunion=reunion,
        expert=expert,
        defaults={'status': 'ABSENT'},
    )
    return participant
