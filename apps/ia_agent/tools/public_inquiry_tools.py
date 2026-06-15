from apps.public.models import PublicAmendement

from . import register

SYNTHESIZE_PUBLIC_INQUIRY_SCHEMA = {
    "type": "object",
    "properties": {
        "norme_id": {"type": "integer"},
    },
    "required": ["norme_id"],
}


@register(
    "synthesize_public_inquiry",
    "Récupère les amendements publics soumis pour une norme (enquête publique), "
    "regroupés par statut, afin que tu puisses en produire une synthèse thématique.",
    SYNTHESIZE_PUBLIC_INQUIRY_SCHEMA,
    scopes=["ctc", "pilotage"],
)
def synthesize_public_inquiry(session, norme_id):
    items = list(PublicAmendement.objects.filter(norme_id=norme_id).order_by('-created_at')[:50])

    by_status = {}
    for a in items:
        by_status.setdefault(a.get_status_display(), []).append({
            "title": a.title,
            "description": (a.description or "")[:400],
            "justification": (a.justification or "")[:300],
            "organization": a.proposed_by_organization,
        })

    return {"norme_id": norme_id, "total": len(items), "by_status": by_status}
