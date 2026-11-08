"""Statuts d'affichage du circuit ST v3.

Les statuts du prompt ne remplacent pas `Norme.status` ni les cinq étapes de
`CTCProcessus` : ils en sont la lecture métier. Chaque transition reste
enregistrée par les services existants avec auteur, date et commentaire.
"""
from django.utils import timezone

STATUS_DEFINITIONS = {
    'ENREGISTREE': {'label': 'Enregistrée', 'tone': 'neutral', 'order': 1},
    'REVUE_SC_ATTENTE': {'label': 'Revue SC en attente', 'tone': 'info', 'order': 2},
    'RAPPORT_RECU': {'label': 'Rapport de revue reçu', 'tone': 'info', 'order': 3},
    'INDEXATION_TERMINEE': {'label': 'Indexation terminée', 'tone': 'info', 'order': 4},
    'EXAMEN_EN_COURS': {'label': 'Examen en cours', 'tone': 'warning', 'order': 5},
    'CONSOLIDATION_TERMINEE': {'label': 'Consolidation terminée', 'tone': 'warning', 'order': 6},
    'VALIDEE': {'label': 'Validée', 'tone': 'success', 'order': 7},
    'RENVOYEE': {'label': 'Renvoyée à la SC', 'tone': 'danger', 'order': 8},
    'BLOQUEE': {'label': 'Bloquée', 'tone': 'danger', 'order': 9},
}

STATUS_CHOICES = tuple(
    (code, meta['label'])
    for code, meta in sorted(STATUS_DEFINITIONS.items(), key=lambda item: item[1]['order'])
)


def status_meta(code, motif=''):
    meta = STATUS_DEFINITIONS.get(code, STATUS_DEFINITIONS['ENREGISTREE'])
    return {
        'code': code if code in STATUS_DEFINITIONS else 'ENREGISTREE',
        'label': meta['label'],
        'tone': meta['tone'],
        'motif': motif or '',
    }


def _blocked_task(norme):
    if not norme or not getattr(norme, 'pk', None):
        return None
    return (
        norme.tasks.filter(status='BLOCKED')
        .order_by('-updated_at', '-pk')
        .only('titre', 'description')
        .first()
    )


def process_status(processus):
    """Traduit un CTCProcessus en statut d'affichage ST v3."""
    if processus is None:
        return status_meta('ENREGISTREE')
    norme = getattr(processus, 'norme', None)
    task = _blocked_task(norme)
    if task is not None:
        return status_meta('BLOQUEE', task.titre or task.description or 'Motif à préciser')
    returned_at = getattr(processus, 'returned_to_sc_at', None)
    validated_at = getattr(processus, 'validated_at', None)
    if returned_at and (not validated_at or returned_at > validated_at):
        return status_meta('RENVOYEE')
    if validated_at:
        return status_meta('VALIDEE')
    if getattr(processus, 'consolidation_completed_at', None):
        return status_meta('CONSOLIDATION_TERMINEE')
    if norme is not None and norme.status in ('ADOPTED', 'HOMOLOGATED', 'PUBLISHED'):
        return status_meta('VALIDEE')
    if processus.current_stage == 'SIGNED_OUT':
        return status_meta('VALIDEE')
    if not processus.received_at:
        return status_meta('ENREGISTREE')
    if not getattr(processus, 'sc_report_received_at', None):
        return status_meta('REVUE_SC_ATTENTE')
    if not processus.indexed_at:
        return status_meta('RAPPORT_RECU')
    if not processus.intake_validated_at:
        return status_meta('INDEXATION_TERMINEE')
    if processus.current_stage in ('GEOSPATIAL', 'MULTI_REVIEW', 'INDUSTRIAL'):
        return status_meta('EXAMEN_EN_COURS')
    return status_meta('ENREGISTREE')


def with_display_status(processus):
    processus.display_status = process_status(processus)
    return processus


def age_days(processus):
    if processus is None or not processus.received_at:
        return 0
    return max(0, (timezone.now() - processus.received_at).days)
