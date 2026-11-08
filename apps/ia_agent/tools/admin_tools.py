"""Outils d'administration de Neuronne : comptes, adhésions, diffusion, rapport."""
from . import register

NEURONNE_ADMIN_TOOLS = {
    'create_platform_user',
    'add_user_to_organisation',
    'send_message_to_sc_gt',
    'send_message_to_user',
    'generate_neuronne_daily_report',
}

CREATE_USER_SCHEMA = {
    'type': 'object',
    'properties': {
        'email': {'type': 'string', 'description': 'Email exact du nouveau compte.'},
        'first_name': {'type': 'string'},
        'last_name': {'type': 'string'},
        'username': {'type': 'string', 'description': 'Optionnel ; dérivé de l’email sinon.'},
        'phone': {'type': 'string'},
        'province': {'type': 'string'},
        'is_expert': {'type': 'boolean', 'description': 'Créer aussi la fiche expert.'},
        'structure_id': {'type': 'integer', 'description': 'Obligatoire si is_expert=true.'},
        'expert_status': {'type': 'string', 'description': 'PENDING (défaut), ACTIVE, etc.'},
        'send_email': {'type': 'boolean', 'description': 'Envoyer le code de définition du mot de passe.'},
    },
    'required': ['email'],
}


@register(
    'create_platform_user',
    "Crée un compte utilisateur sur la plateforme. Réservé à Neuronne/admin. "
    "Si is_expert=true, structure_id est obligatoire. Un email avec code de "
    "réinitialisation est envoyé sauf send_email=false.",
    CREATE_USER_SCHEMA,
    scopes=['expert', 'ctc', 'pilotage'],
)
def create_platform_user_tool(
    session, email, first_name='', last_name='', username=None, phone='',
    province='', is_expert=False, structure_id=None, expert_status='PENDING',
    send_email=True,
):
    from ..services.neuronne_admin import create_platform_user

    return create_platform_user(
        session.user, email=email, first_name=first_name, last_name=last_name,
        username=username, phone=phone, province=province, is_expert=is_expert,
        structure_id=structure_id, expert_status=expert_status,
        send_email=send_email,
    )


ADD_ORGANISATION_SCHEMA = {
    'type': 'object',
    'properties': {
        'user_identifier': {'type': 'string', 'description': 'Email exact ou identifiant numérique.'},
        'target': {'type': 'string', 'enum': ['CTC', 'COPIL', 'EXPERT', 'SC', 'GT', 'CTM', 'WG']},
        'role': {'type': 'string', 'description': 'Rôle métier (CTC/COPIL) ou fonction (GT).'},
        'reference': {'type': 'string', 'description': 'Référence de nomination pour SC/GT.'},
        'start_date': {'type': 'string', 'description': 'AAAA-MM-JJ, défaut aujourd’hui.'},
        'ctc_id': {'type': 'integer'},
        'ctc_name': {'type': 'string'},
        'comite_id': {'type': 'integer'},
        'comite_name': {'type': 'string'},
        'sc_id': {'type': 'integer'},
        'sc_code': {'type': 'string'},
        'gt_id': {'type': 'integer'},
        'gt_code': {'type': 'string'},
        'ctm_id': {'type': 'integer'},
        'ctm_number': {'type': 'integer'},
        'wg_id': {'type': 'integer'},
        'wg_number': {'type': 'integer'},
        'structure_id': {'type': 'integer', 'description': 'Si la fiche expert doit être créée.'},
    },
    'required': ['user_identifier', 'target'],
}


@register(
    'add_user_to_organisation',
    "Ajoute un compte existant à une CTC, au COPIL, à une SC, un GT, un CTM ou un WG, "
    "ou l’active comme expert. Réservé à Neuronne/admin. Les emails de nomination "
    "partent automatiquement. Utiliser l’email exact ou l’identifiant numérique, "
    "jamais un nom supposé.",
    ADD_ORGANISATION_SCHEMA,
    scopes=['expert', 'ctc', 'pilotage'],
)
def add_user_to_organisation_tool(session, user_identifier, target, **kwargs):
    from ..services.neuronne_admin import add_user_to_organisation

    allowed = {
        'role', 'reference', 'start_date', 'ctc_id', 'ctc_name', 'comite_id',
        'comite_name', 'sc_id', 'sc_code', 'gt_id', 'gt_code', 'ctm_id',
        'ctm_number', 'wg_id', 'wg_number', 'structure_id',
    }
    values = {key: value for key, value in kwargs.items() if key in allowed}
    return add_user_to_organisation(
        session.user, user_identifier=user_identifier, target=target, **values,
    )


SC_GT_MESSAGE_SCHEMA = {
    'type': 'object',
    'properties': {
        'subject': {'type': 'string'},
        'body': {'type': 'string'},
        'sc_id': {'type': 'integer', 'description': 'Cible SC (exclusif avec gt_id).'},
        'sc_code': {'type': 'string', 'description': 'Code SC, alternative à sc_id.'},
        'gt_id': {'type': 'integer', 'description': 'Cible GT (exclusif avec sc_id).'},
        'gt_code': {'type': 'string', 'description': 'Code GT, alternative à gt_id.'},
    },
    'required': ['subject', 'body'],
}


@register(
    'send_message_to_sc_gt',
    "Envoie un email et une notification interne aux membres actifs d’une SC ou d’un GT. "
    "Fournir exactement sc_id ou gt_id. Réservé à Neuronne/admin.",
    SC_GT_MESSAGE_SCHEMA,
    scopes=['expert', 'ctc', 'pilotage'],
)
def send_message_to_sc_gt_tool(
    session, subject, body, sc_id=None, gt_id=None, sc_code=None, gt_code=None,
):
    from ..services.neuronne_admin import send_message_to_sc_gt

    return send_message_to_sc_gt(
        session.user, subject=subject, body=body, sc_id=sc_id, gt_id=gt_id,
        sc_code=sc_code, gt_code=gt_code,
    )


DIRECT_MESSAGE_SCHEMA = {
    'type': 'object',
    'properties': {
        'user_identifier': {'type': 'string', 'description': 'Email exact ou identifiant numérique.'},
        'subject': {'type': 'string'},
        'body': {'type': 'string'},
    },
    'required': ['user_identifier', 'subject', 'body'],
}


@register(
    'send_message_to_user',
    "Envoie un email et une notification interne à une personne précise, identifiée "
    "par son email exact ou son identifiant numérique. Réservé à Neuronne/admin.",
    DIRECT_MESSAGE_SCHEMA,
    scopes=['expert', 'ctc', 'pilotage'],
)
def send_message_to_user_tool(session, user_identifier, subject, body):
    from ..services.neuronne_admin import send_message_to_user

    return send_message_to_user(
        session.user, user_identifier=user_identifier, subject=subject, body=body,
    )


DAILY_REPORT_SCHEMA = {
    'type': 'object',
    'properties': {
        'day': {'type': 'string', 'description': 'AAAA-MM-JJ ; défaut aujourd’hui.'},
    },
}


@register(
    'generate_neuronne_daily_report',
    "Génère et envoie immédiatement le rapport quotidien des actions Neuronne "
    "(email + notification aux administrateurs). Réservé à Neuronne/admin.",
    DAILY_REPORT_SCHEMA,
    scopes=['expert', 'ctc', 'pilotage'],
)
def generate_neuronne_daily_report_tool(session, day=None):
    from ..services.neuronne_admin import send_daily_report

    return send_daily_report(session.user, day=day)
