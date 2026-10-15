"""Le contexte Phoenix est filtré avant toute transmission à l'assistant."""
from django.shortcuts import get_object_or_404
from django.urls import reverse
from apps.governance.phoenix_workflow import accessible_dossiers, selected_mandate, permitted_transitions
from apps.norms.models import NormeVersion
from . import register


@register('search_phoenix_dossiers', 'Recherche dans les seuls dossiers Phoenix que ce compte peut consulter. Les passages retournés portent une référence et une version.',
          {'type': 'object', 'properties': {'query': {'type': 'string'}}, 'required': ['query']}, scopes=['expert', 'ctc', 'pilotage'])
def search_phoenix_dossiers(session, query):
    from django.db.models import Q
    dossiers = accessible_dossiers(session.user).filter(Q(norme__title__icontains=query[:200]) | Q(norme__reference_number__icontains=query[:200]) | Q(document_version__content__icontains=query[:200]))[:20]
    return [{'reference': dossier.norme.reference_number, 'title': dossier.norme.title, 'version_id': dossier.document_version_id,
             'state': dossier.state, 'source_url': reverse('web:phoenix_dossier', args=[dossier.pk]),
             'passage': dossier.document_version.content[:1600] if dossier.document_version else ''} for dossier in dossiers]


@register('prepare_phoenix_decision', 'Prépare une décision Phoenix autorisée pour un mandat explicite. Retourne le lien de revue humaine ; le formulaire serveur enregistre la décision après examen.',
          {'type': 'object', 'properties': {'dossier_id': {'type': 'integer'}, 'mandate_id': {'type': 'integer'}, 'transition_id': {'type': 'string'}},
           'required': ['dossier_id', 'mandate_id', 'transition_id']}, scopes=['expert', 'ctc', 'pilotage'])
def prepare_phoenix_decision(session, dossier_id, mandate_id, transition_id):
    dossier = get_object_or_404(accessible_dossiers(session.user), pk=dossier_id)
    mandate = selected_mandate(session.user, mandate_id)
    rule = next((rule for rule in permitted_transitions(session.user, mandate, dossier) if rule['id'] == transition_id), None)
    if not rule:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied('Cette décision n’est pas autorisée dans le mandat sélectionné.')
    return {'reference': dossier.norme.reference_number, 'version_id': dossier.document_version_id, 'label': rule['label'],
            'required_evidence': rule.get('required_evidence', []), 'quorum': rule['quorum'],
            'review_url': reverse('web:phoenix_dossier', args=[dossier.pk]), 'decision_recorded': False}
