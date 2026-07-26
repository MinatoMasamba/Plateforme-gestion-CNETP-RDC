from django.contrib.contenttypes.models import ContentType

from apps.norms.models import Norme
from apps.public.models import PublicAmendement

from ..models import AgentArtifact
from . import register

SYNTHESIZE_PUBLIC_INQUIRY_SCHEMA = {
    "type": "object",
    "properties": {
        "norme_id": {"type": "integer"},
        "limit": {
            "type": "integer",
            "description": "Nombre maximum d'amendements pris en compte (défaut 50)",
        },
        "persist": {
            "type": "boolean",
            "description": (
                "Si vrai (défaut), sauvegarde la synthèse dans un artefact "
                "PUBLIC_INQUIRY_SYNTHESIS traçable pour la CTC."
            ),
        },
    },
    "required": ["norme_id"],
}

THEME_KEYWORDS = {
    "drainage_assainissement": ["drainage", "assainissement", "évacuation", "collecteur", "pluvial", "égout"],
    "securite": ["sécurité", "incendie", "risque", "protection", "accident"],
    "materiaux": ["matériau", "matériaux", "béton", "acier", "bois", "latérite", "granulat"],
    "geotechnique_fondations": ["fondation", "sol", "géotechnique", "portance", "tassement"],
    "routes_ouvrages": ["route", "pont", "chaussée", "ouvrage", "voirie", "revêtement"],
    "batiments": ["bâtiment", "batiment", "logement", "construction", "immeuble"],
}


def _classify_theme(*texts):
    text_lower = " ".join(t or "" for t in texts).lower()
    for theme, keywords in THEME_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return theme
    return "autre"


@register(
    "synthesize_public_inquiry",
    "Récupère les amendements publics soumis pour une norme (enquête publique), "
    "regroupés par statut et par thématique, afin que tu puisses en produire une "
    "synthèse. Par défaut, sauvegarde la synthèse dans un artefact traçable pour la CTC.",
    SYNTHESIZE_PUBLIC_INQUIRY_SCHEMA,
    scopes=["ctc", "pilotage"],
)
def synthesize_public_inquiry(session, norme_id, limit=50, persist=True):
    items = list(PublicAmendement.objects.filter(norme_id=norme_id).order_by('-created_at')[:limit])

    by_status = {}
    by_theme = {}
    for a in items:
        entry = {
            "title": a.title,
            "description": (a.description or "")[:400],
            "justification": (a.justification or "")[:300],
            "organization": a.proposed_by_organization,
        }
        by_status.setdefault(a.get_status_display(), []).append(entry)

        theme = _classify_theme(a.title, a.description, a.justification)
        by_theme.setdefault(theme, []).append(entry)

    result = {"norme_id": norme_id, "total": len(items), "by_status": by_status, "by_theme": by_theme}

    if persist:
        artifact = AgentArtifact.objects.create(
            session=session,
            artifact_type='PUBLIC_INQUIRY_SYNTHESIS',
            title=f"Synthèse enquête publique — norme #{norme_id}",
            payload=result,
            status='DRAFT',
            content_type=ContentType.objects.get_for_model(Norme),
            object_id=norme_id,
        )
        result["artifact_id"] = artifact.id

    return result
