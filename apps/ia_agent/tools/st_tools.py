"""Nominations ST depuis une liste ; contrôle administrateur côté serveur."""
from . import register
from apps.governance.st_operations import nominate_batch, require_admin
from apps.governance.phoenix_runtime import st_posts


@register('list_st_posts', 'Liste les 19 postes ST v3 et leur occupation. Réservé aux administrateurs habilités.',
    {'type': 'object', 'properties': {}}, scopes=['expert', 'ctc', 'pilotage'])
def list_st_posts(session):
    require_admin(session.user)
    return [{'post_code': p.code, 'title': p.title, 'nominated_name': p.nominated_name,
        'occupied': p.mandates.filter(status='ACTIVE').exists()} for p in st_posts()]


@register('assign_st_posts',
    'Attribue les postes ST à partir de la liste explicite fournie par un administrateur. Utiliser email exact ou expert_id, jamais un nom supposé. Date de début et référence de nomination requises. apply=false vérifie sans écrire ; apply=true active les mandats. Un email de nomination est envoyé après activation.',
    {'type': 'object', 'properties': {
        'assignments': {'type': 'array', 'minItems': 1, 'maxItems': 19, 'items': {'type': 'object', 'properties': {
            'post_code': {'type': 'string'}, 'expert_id': {'type': 'integer'}, 'email': {'type': 'string'},
            'start_date': {'type': 'string'}, 'appointment_reference': {'type': 'string'}},
            'required': ['post_code', 'start_date', 'appointment_reference']}},
        'apply': {'type': 'boolean'}}, 'required': ['assignments']}, scopes=['expert', 'ctc', 'pilotage'])
def assign_st_posts(session, assignments, apply=False):
    if not isinstance(apply, bool):
        from django.core.exceptions import ValidationError
        raise ValidationError('apply doit être un booléen.')
    return {'results': nominate_batch(session.user, assignments, apply=apply)}
