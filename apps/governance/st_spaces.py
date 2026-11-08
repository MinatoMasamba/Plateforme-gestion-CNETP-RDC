"""Espaces fonctionnels du Secrétariat technique (matrice ST v3).

Le poste décrit l'organisation, la permission décrit l'action. Ce module est la
source unique des espaces, des menus autorisés et des périmètres d'audit. Il ne
donne aucun droit par lui-même : les vues et l'API revérifient les capacités.
"""
from .st_matrix import POSTS, POLES

SPACE_ORDER = ('ST', 'ST-P1', 'ST-P2', 'ST-P3', 'ST-P4')

SPACES = {
    'ST': {
        'code': 'ST',
        'label': 'Coordination',
        'long_label': 'Coordination du Secrétariat technique',
        'icon': 'network',
        'home': 'coordination',
    },
    'ST-P1': {
        'code': 'ST-P1',
        'label': 'Pôle 1',
        'long_label': 'Planification et suivi',
        'icon': 'calendar-check',
        'home': 'espace_p1',
    },
    'ST-P2': {
        'code': 'ST-P2',
        'label': 'Pôle 2',
        'long_label': 'Documentation, codification et PTN',
        'icon': 'library',
        'home': 'espace_p2',
    },
    'ST-P3': {
        'code': 'ST-P3',
        'label': 'Pôle 3',
        'long_label': 'Juridique, administratif et financier',
        'icon': 'scale',
        'home': 'espace_p3',
    },
    'ST-P4': {
        'code': 'ST-P4',
        'label': 'Pôle 4',
        'long_label': 'Appui techniques et Formation',
        'icon': 'wrench',
        'home': 'espace_p4',
    },
}

# Rattachement des 19 postes aux cinq espaces. Le numéro reste la clé de
# lecture de la matrice officielle ; aucun nom n'est interprété.
POST_NUMBER_BY_ROLE = {row[3]: row[0] for row in POSTS}
POST_NUMBER_BY_CODE = {f'ST-V3-{row[0]:02}': row[0] for row in POSTS}
SPACE_BY_POST_NUMBER = {row[0]: row[1] for row in POSTS}
SPACE_BY_ROLE = {row[3]: row[1] for row in POSTS}


def space_for_pole(pole):
    return pole if pole in SPACES else 'ST'


def space_for_post(post):
    if post is None:
        return None
    return SPACE_BY_POST_NUMBER.get(_post_number(post))


def _post_number(post):
    code = getattr(post, 'code', '') or ''
    if code in POST_NUMBER_BY_CODE:
        return POST_NUMBER_BY_CODE[code]
    title = getattr(post, 'title', '')
    for number, _pole, post_title, _role, _name, _origin, _head in POSTS:
        if title and title == post_title:
            return number
    return None


def is_head(post):
    number = _post_number(post)
    if number is None:
        return False
    return POSTS[number - 1][-1]


# Menus : 5 à 7 entrées maximum par poste, dans l'ordre de travail réel.
# Les entrées pointent vers les vues du shell CTC ; les modules non encore
# développés sont rendus par un écran « Module à venir » explicite.
MENUS = {
    'ST': [
        {'view': 'coordination', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
        {'view': 'dossiers', 'label': 'Circuit des normes', 'icon': 'folders'},
        {'view': 'ctc_requests', 'label': 'Demandes à traiter', 'icon': 'send'},
        {'view': 'delays', 'label': 'Arbitrage des retards', 'icon': 'alarm-clock'},
        {'view': 'reunions', 'label': 'Réunions et convocations', 'icon': 'calendar-days'},
    ],
    'ST-P1': [
        {'view': 'espace_p1', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
        {'view': 'planning', 'label': 'Plan de travail', 'icon': 'calendar-check'},
        {'view': 'deliverables', 'label': 'Suivi des livrables', 'icon': 'package-check'},
        {'view': 'statistiques', 'label': 'Indicateurs', 'icon': 'chart-no-axes-combined'},
        {'view': 'exams', 'label': 'Pilotage des examens', 'icon': 'file-search'},
    ],
    'ST-P2': [
        {'view': 'espace_p2', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
        {'view': 'indexation', 'label': 'Dossiers à indexer', 'icon': 'files'},
        {'view': 'ged', 'label': 'Bibliothèque (GED)', 'icon': 'library'},
        {'view': 'ptn', 'label': 'Registre des PTN', 'icon': 'list-tree'},
        {'view': 'consolidation', 'label': 'Consolidation des avis', 'icon': 'combine'},
    ],
    'ST-P3': [
        {'view': 'espace_p3', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
        {'view': 'legal', 'label': 'Avis juridiques', 'icon': 'scale'},
        {'view': 'financial', 'label': 'Budget et comptabilité', 'icon': 'banknote'},
        {'view': 'contributions', 'label': 'Cotisations et jetons', 'icon': 'receipt'},
        {'view': 'statements', 'label': 'États à confirmer', 'icon': 'clipboard-check'},
    ],
    'ST-P4': [
        {'view': 'espace_p4', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
        {'view': 'accounts', 'label': 'Comptes et accès', 'icon': 'user-cog'},
        {'view': 'backups', 'label': 'Sauvegardes et incidents', 'icon': 'database-backup'},
        {'view': 'training', 'label': 'Formation', 'icon': 'graduation-cap'},
        {'view': 'communication', 'label': 'Communication', 'icon': 'megaphone'},
        {'view': 'usagers', 'label': 'Relations usagers', 'icon': 'messages-square'},
    ],
}

# Vues de travail accessibles à tous les postes, quel que soit l'espace.
TRANSVERSAL = [
    {'view': 'matrice_st', 'label': 'Organisation du ST', 'icon': 'network'},
]

# Matrice A.9 : qui lit les actions de qui. Les valeurs sont des portées de
# journal (scope) et non des noms de personnes.
AUDIT_SCOPES = {
    'membre_pole': {'st_pole'},
    'chef_pole_1_2_4': {'st_pole', 'st'},
    'coordination': {'st', 'st_pole'},
    'coechef_pole_3': {'st', 'system'},
    'admin_systeme': {'st', 'st_pole', 'system'},
}


def menu_for_post(post):
    """Retourne 5 à 7 entrées + les accès transversaux, sans doublon."""
    space = space_for_post(post) or 'ST'
    menu = list(MENUS.get(space, MENUS['ST']))
    number = _post_number(post)
    specialised = {
        6: [('assistant_executif', 'Réception norme', 'inbox'),
            ('assignations', 'Mes travaux', 'file-check'),
            ('ctc_requests', 'Demande et traitement', 'send'),
            ('dossiers', 'Circuit des normes', 'folders'),
            ('rapports', 'Rapport', 'file-chart-column'),
            ('reunions', 'Réunions', 'calendar-days')],
        7: [('coordination', 'Tableau de bord', 'layout-dashboard'),
            ('reunions', 'Réunions et convocations', 'calendar-days'),
            ('experts', 'Annuaire', 'users'),
            ('dossiers', 'Dossiers normatifs', 'folders')],
        9: [('espace_p1', 'Tableau de bord', 'layout-dashboard'),
            ('deliverables', 'Suivi des livrables', 'package-check'),
            ('alerts', 'Alertes et relances', 'alarm-clock'),
            ('statistiques', 'Mes indicateurs', 'chart-no-axes-combined')],
        11: [('espace_p2', 'Tableau de bord', 'layout-dashboard'),
             ('indexation', 'Dossiers à indexer', 'files'),
             ('ged', 'Documents GED', 'library'),
             ('codification', 'Codification', 'scan-line'),
             ('versions', 'Versions', 'history'),
             ('ged_anomalies', 'Anomalies', 'file-warning'),
             ('ged_activity', 'Mon activité', 'chart-no-axes-combined')],
        12: [('espace_p2', 'Tableau de bord', 'layout-dashboard'),
             ('ptn', 'Registre des PTN', 'list-tree'),
             ('ged', 'Bibliothèque (GED)', 'library'),
             ('reunions', 'Mes réunions', 'calendar-days')],
        15: [('espace_p3', 'Tableau de bord', 'layout-dashboard'),
             ('financial', 'Budget et comptabilité', 'banknote'),
             ('contributions', 'Cotisations et jetons', 'receipt'),
             ('expenses', 'Engagements et dépenses', 'receipt-text')],
        18: [('espace_p4', 'Tableau de bord', 'layout-dashboard'),
             ('accounts', 'Comptes et accès', 'user-cog'),
             ('backups', 'Sauvegardes et incidents', 'database-backup'),
             ('travaux', 'Travaux enregistrés', 'clipboard-list')],
        19: [('espace_p4', 'Tableau de bord', 'layout-dashboard'),
             ('communication', 'Communication', 'megaphone'),
             ('usagers', 'Relations usagers', 'messages-square'),
             ('reunions', 'Mes réunions', 'calendar-days')],
    }
    specialised[16] = specialised[15]
    if number in specialised:
        menu = [dict(view=v, label=l, icon=i) for v, l, i in specialised[number]]
    seen = {item['view'] for item in menu}
    for item in TRANSVERSAL:
        if len(menu) >= 7:
            break
        if item['view'] not in seen:
            menu.append(item)
            seen.add(item['view'])
    return menu[:7]


def allowed_views_for_post(post):
    """Modules rendus par Django, y compris les raccourcis hors du menu."""
    views = {item['view'] for item in menu_for_post(post)}
    views.update({'parametres', 'reunions', 'tracabilite', 'aide', 'travaux', 'dossiers', 'assignations', 'notifications'})
    number = _post_number(post)
    if number in (1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 13, 14):
        views.add('dossiers')
    if number in (1, 2, 3, 4, 5):
        views.update({'experts', 'statistiques'})
    if number == 6:
        views.add('rapports')
    if number in (10, 11):
        views.update({'espace_p2', 'indexation', 'ged', 'codification', 'versions',
                      'ged_versions_todo', 'ged_anomalies', 'ged_activity', 'rapports'})
    if number in (13, 14):
        views.add('expenses')
    return sorted(views)


def space_context(post, capabilities=None):
    """Contexte d'espace injecté dans le shell et les composants."""
    capabilities = capabilities or {}
    space = space_for_post(post) or 'ST'
    info = SPACES[space]
    number = _post_number(post)
    profiles = {
        1: ('coordination', 'Piloter le Secrétariat technique', 'Décisions, arbitrages et suivi des cinq espaces.'),
        6: ('reception', 'Réception et secrétariat de séance', 'Enregistrer les réceptions, instruire les demandes et préparer les procès-verbaux.'),
        7: ('logistique', 'Organisation des réunions', 'Préparer les convocations, les invités et le suivi logistique.'),
        8: ('planification', 'Superviser la planification et le suivi', 'Piloter les livrables et le travail du chargé du suivi.'),
        9: ('suivi', 'Suivi des livrables et relances', 'Préparer vos états d’avancement et suivre vos échéances.'),
        10: ('documentation', 'Superviser la bibliothèque normative', 'Contrôler la GED, les paramètres techniques et la consolidation des avis.'),
        11: ('ged', 'Mon atelier documentaire', 'Indexer les dossiers reçus et préparer leurs documents, codes et versions.'),
        12: ('ptn', 'Mon registre des paramètres techniques', 'Préparer les fiches et leurs révisions pour confirmation par le chef du pôle 2.'),
        13: ('juridique', 'Superviser le juridique et les finances', 'Rendre les avis, contrôler les états et consulter l’audit institutionnel.'),
        15: ('finance', 'Mon bureau comptable', 'Saisir les engagements et dépenses et préparer les états financiers.'),
        17: ('appui', 'Superviser l’appui et la formation', 'Suivre l’administration technique, les formations et la communication.'),
        18: ('technique', 'Mon atelier d’appui technique', 'Traiter vos interventions sur les comptes, les sauvegardes et les incidents.'),
        19: ('communication', 'Mon bureau de communication', 'Préparer les publications et traiter les demandes des usagers.'),
    }
    profile = profiles.get({2: 1, 3: 1, 4: 1, 5: 1, 14: 13, 16: 15}.get(number, number), profiles[1])
    return {
        'st_space': space,
        'st_space_label': info['label'],
        'st_space_long_label': info['long_label'],
        'st_space_icon': info['icon'],
        'st_space_home': 'assistant_executif' if number == 6 else info['home'],
        'st_workspace': {'kind': profile[0], 'title': profile[1], 'mission': profile[2]},
        'st_workspace_tools': [item for item in menu_for_post(post)
                               if item['view'] not in (info['home'], 'assignations', 'matrice_st')],
        'st_space_menu': menu_for_post(post),
        'st_allowed_views': allowed_views_for_post(post),
        'st_is_supervisor': _post_number(post) in (1, 2, 3, 4, 5, 8, 10, 13, 14, 17),
        'st_is_pole_head': bool(capabilities.get('st_is_pole_head') or is_head(post)),
    }


def audit_scope_for(post):
    """Portées d'audit lisibles par un poste, selon A.9."""
    number = _post_number(post)
    if number is None:
        return set()
    if number in (1, 2, 3, 4, 5):
        return AUDIT_SCOPES['coordination']
    if number in (13, 14):
        return AUDIT_SCOPES['coechef_pole_3']
    if number == 18:
        return AUDIT_SCOPES['admin_systeme']
    if number in (8, 10, 17):
        return AUDIT_SCOPES['chef_pole_1_2_4']
    return AUDIT_SCOPES['membre_pole']


def can_read_audit(post, target_scope):
    return target_scope in audit_scope_for(post)
