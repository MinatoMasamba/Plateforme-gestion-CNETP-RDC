from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from ..models import AgentArtifact
from . import register

CREATE_EMAIL_DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "to_email": {"type": "string"},
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "related_artifact_id": {
            "type": "integer",
            "description": "ID d'un artefact lié de cette session (ex: WG_REQUEST) à joindre en PDF si applicable",
        },
    },
    "required": ["to_email", "subject", "body"],
}


@register(
    "create_email_draft",
    "Crée un brouillon d'email à destination d'un destinataire donné. Reste en statut "
    "brouillon jusqu'à validation et envoi manuel par l'utilisateur — ne déclenche "
    "jamais l'envoi.",
    CREATE_EMAIL_DRAFT_SCHEMA,
    scopes=["expert", "ctc", "pilotage"],
)
def create_email_draft(session, to_email, subject, body, related_artifact_id=None):
    try:
        validate_email(to_email or "")
    except ValidationError:
        return {"error": f"Adresse email invalide : {to_email!r}"}

    if related_artifact_id is not None:
        if not AgentArtifact.objects.filter(id=related_artifact_id, session=session).exists():
            return {"error": "related_artifact_id introuvable dans cette session."}

    artifact = AgentArtifact.objects.create(
        session=session,
        artifact_type='EMAIL_DRAFT',
        title=subject,
        payload={
            "to": to_email,
            "subject": subject,
            "body": body,
            "related_artifact_id": related_artifact_id,
        },
        status='DRAFT',
    )

    return {
        "artifact_id": artifact.id,
        "status": artifact.status,
        "message": (
            "Brouillon d'email préparé, en attente de validation et d'envoi manuel par "
            "l'utilisateur (il n'a pas été envoyé)."
        ),
    }
