"""Contrat du circuit configurable ; aucune règle proposée ne s'active d'elle-même."""
from django.core.exceptions import ValidationError

ACTIONS = {
    'organisation.consulter': 'Consulter l’organisation',
    'document.consulter': 'Consulter les dossiers',
    'document.creer': 'Créer un dossier',
    'document.editer': 'Rédiger une version',
    'document.joindre': 'Joindre une pièce',
    'document.verrouiller': 'Verrouiller ou libérer un dossier',
    'reunion.planifier': 'Planifier une réunion et suivre ses présences',
    'gt.soumettre': 'Soumettre le projet du GT',
    'sc.examiner': 'Examiner en sous-commission',
    'sc.retour': 'Retourner au GT',
    'st.controler': 'Contrôler la complétude',
    'st.retour': 'Retourner pour complément',
    'st.enquete': 'Ouvrir l’enquête publique',
    'st.transmettre': 'Transmettre au COPIL',
    'copil.valider': 'Valider au COPIL',
    'copil.retour': 'Retourner pour réexamen',
    'document.adopter': 'Adopter',
    'document.homologuer': 'Homologuer',
    'document.publier': 'Publier au Journal Officiel',
    'rapport.consulter': 'Consulter les rapports du périmètre',
    'rapport.rediger': 'Rédiger les rapports du périmètre',
    'rapport.controler': 'Contrôler les rapports du périmètre',
    'rapport.approuver': 'Approuver les rapports du périmètre',
    'rapport.transmettre': 'Consigner la transmission des rapports',
}
FINAL_ACTIONS = {'document.adopter': 'ADOPTED', 'document.homologuer': 'HOMOLOGATED', 'document.publier': 'PUBLISHED'}


def validate_circuit(config):
    if not isinstance(config, dict) or not isinstance(config.get('states'), list) or not isinstance(config.get('transitions'), list):
        raise ValidationError('Renseigner les états, les transitions et l’état initial du circuit.')
    states = config['states']
    codes = [state.get('code') if isinstance(state, dict) else None for state in states]
    if not codes or any(not isinstance(code, str) or not code or len(code) > 60 for code in codes) or len(set(codes)) != len(codes):
        raise ValidationError('Les codes d’états doivent être uniques et non vides (60 caractères maximum).')
    if config.get('initial') not in codes or any(not state.get('label') for state in states):
        raise ValidationError('L’état initial et les libellés doivent être renseignés.')
    seen = set()
    for rule in config['transitions']:
        if not isinstance(rule, dict) or not rule.get('id') or not isinstance(rule['id'], str) or len(rule['id']) > 60 or rule['id'] in seen:
            raise ValidationError('Chaque transition doit avoir un identifiant unique.')
        seen.add(rule['id'])
        if rule.get('from') not in codes or rule.get('to') not in codes or rule['from'] == rule['to']:
            raise ValidationError('Une transition relie deux états distincts du circuit.')
        if (rule.get('action') not in ACTIONS or rule['action'].startswith('rapport.') or
                rule['action'] in ('organisation.consulter', 'document.consulter', 'document.creer', 'document.editer', 'document.joindre', 'document.verrouiller', 'reunion.planifier')):
            raise ValidationError('L’action de transition est invalide.')
        if not isinstance(rule.get('label'), str) or not rule.get('label') or not isinstance(rule.get('organe_types'), list) or not rule.get('organe_types') or any(kind not in ('GT', 'SC', 'ST', 'ST_POLE', 'COPIL') for kind in rule['organe_types']):
            raise ValidationError('Préciser le libellé et les organes habilités de chaque transition.')
        quorum = rule.get('quorum')
        if isinstance(quorum, bool) or not isinstance(quorum, int) or not 1 <= quorum <= 100:
            raise ValidationError('Le quorum doit être explicitement renseigné, entre 1 et 100 personnes distinctes.')
        categories = rule.get('categories', [])
        if not isinstance(categories, list) or any(c not in ('PRESIDENCY', 'SECRETARIAT', 'MEMBER', 'INVITED', 'APPOINT', 'COORDINATION', 'POLE_HEAD', 'UNKNOWN') for c in categories):
            raise ValidationError('Catégorie de poste invalide.')
        if not isinstance(rule.get('required_evidence', []), list) or any(not isinstance(kind, str) or not kind or len(kind) > 80 for kind in rule.get('required_evidence', [])):
            raise ValidationError('Les pièces exigées doivent être une liste de types documentaires.')
        if any(not isinstance(rule.get(flag, False), bool) for flag in ('independent_review', 'requires_public_inquiry', 'allow_contributors')):
            raise ValidationError('Les contrôles d’indépendance et d’enquête doivent être des booléens.')
        if rule['action'] == 'document.publier' and not rule.get('required_evidence'):
            raise ValidationError('La publication doit exiger une pièce documentaire officielle.')
    if not seen:
        raise ValidationError('Le circuit doit contenir au moins une transition.')
    if 'editable_states' in config and (not isinstance(config['editable_states'], list) or any(state not in codes for state in config['editable_states'])):
        raise ValidationError('Les étapes de rédaction doivent appartenir au circuit.')
    reachable = {config['initial']}
    while True:
        expanded = reachable | {r['to'] for r in config['transitions'] if r['from'] in reachable}
        if expanded == reachable:
            break
        reachable = expanded
    if set(codes) != reachable:
        raise ValidationError('Tous les états doivent être accessibles depuis l’état initial.')
    return config


def proposed_circuit():
    codes = [('GT', 'Production du GT'), ('SC', 'Examen en sous-commission'), ('ST', 'Contrôle du Secrétariat technique'),
             ('COPIL', 'Examen du COPIL'), ('ADOPTION', 'Adoption'), ('HOMOLOGATION', 'Homologation'), ('PUBLICATION', 'Publication au JO')]
    rules = [('soumettre', 'GT', 'SC', 'gt.soumettre', 'GT'), ('examiner', 'SC', 'ST', 'sc.examiner', 'SC'),
             ('transmettre', 'ST', 'COPIL', 'st.transmettre', 'ST'), ('valider', 'COPIL', 'ADOPTION', 'copil.valider', 'COPIL'),
             ('adopter', 'ADOPTION', 'HOMOLOGATION', 'document.adopter', 'COPIL'),
             ('homologuer', 'HOMOLOGATION', 'PUBLICATION', 'document.homologuer', 'COPIL')]
    # Les quorums et conditions ci-dessous constituent un canevas à adapter et valider.
    return {'initial': 'GT', 'states': [{'code': code, 'label': label} for code, label in codes] + [{'code': 'PUBLIE', 'label': 'Publié au Journal Officiel'}],
            'transitions': [{'id': code, 'from': start, 'to': end, 'action': action, 'label': ACTIONS[action],
                             'organe_types': [kind], 'quorum': 1, 'required_evidence': [], 'independent_review': kind in ('SC', 'ST', 'COPIL')}
                            for code, start, end, action, kind in rules] +
                           [{'id': 'publier', 'from': 'PUBLICATION', 'to': 'PUBLIE', 'action': 'document.publier', 'label': ACTIONS['document.publier'],
                             'organe_types': ['COPIL'], 'quorum': 1, 'required_evidence': ['publication_jo']}],
            'proposal_notice': 'Canevas de préparation : quorums, pouvoirs, pièces, enquête et retours à confirmer. Aucune activation automatique.'}
