from apps.amendments.models import Vote
from apps.experts.models import Expert
from apps.governance.models import Affectation, WG
from apps.norms.models import NormeVote

from ..models import AgentArtifact
from . import register

GET_EXPERT_DOSSIER_SCHEMA = {
    "type": "object",
    "properties": {
        "expert_id": {"type": "integer", "description": "Identifiant de l'expert (Expert.id)"},
    },
    "required": ["expert_id"],
}


@register(
    "get_expert_dossier",
    "Récupère le dossier complet d'un expert : profil, extrait de son CV, affectations "
    "CTM/WG avec ses rôles, et historique de ses votes sur les normes et amendements.",
    GET_EXPERT_DOSSIER_SCHEMA,
    scopes=["expert", "ctc", "pilotage"],
)
def get_expert_dossier(session, expert_id):
    expert = Expert.objects.select_related('user', 'structure', 'ctm').get(id=expert_id)

    cv_excerpt = ""
    if expert.cv:
        try:
            import fitz

            with expert.cv.open('rb') as f:
                data = f.read()
            doc = fitz.open(stream=data, filetype="pdf")
            cv_excerpt = "\n".join(page.get_text() for page in doc)[:6000]
        except Exception:
            cv_excerpt = ""

    affectations = [
        {
            "ctm": f"CTM {a.ctm.number} - {a.ctm.name}",
            "wg": f"WG {a.wg.ctm.number}.{a.wg.number} - {a.wg.name}" if a.wg else None,
            "ctm_role": a.ctm_role,
            "wg_role": a.wg_role,
        }
        for a in Affectation.objects.filter(expert=expert).select_related('ctm', 'wg', 'wg__ctm')
    ]

    norme_votes = [
        {
            "norme": v.norme.reference_number,
            "title": v.norme.title,
            "vote": v.get_vote_display(),
            "justification": v.justification,
        }
        for v in NormeVote.objects.filter(voter=expert).select_related('norme')[:20]
    ]

    amendement_votes = [
        {
            "amendement": v.amendement.title,
            "norme": v.amendement.norme.reference_number,
            "vote": v.get_vote_display(),
            "justification": v.justification,
        }
        for v in Vote.objects.filter(voter=expert).select_related('amendement__norme')[:20]
    ]

    return {
        "expert_id": expert.id,
        "full_name": expert.full_name,
        "structure": expert.structure.name if expert.structure else None,
        "structure_acronym": expert.structure.acronym if expert.structure else None,
        "specialties": expert.specialties,
        "ctm_principal": f"CTM {expert.ctm.number} - {expert.ctm.name}" if expert.ctm else None,
        "status": expert.status,
        "cv_excerpt": cv_excerpt,
        "affectations": affectations,
        "norme_votes": norme_votes,
        "amendement_votes": amendement_votes,
    }


LIST_WG_OPTIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "ctm_id": {"type": "integer", "description": "Filtrer sur un CTM précis (optionnel)"},
    },
}


@register(
    "list_wg_options",
    "Liste les groupes de travail (WG) disponibles, avec leur CTM, leur description et "
    "les références ISO/ARSO du CTM. Filtrable par CTM.",
    LIST_WG_OPTIONS_SCHEMA,
    scopes=["expert", "ctc", "pilotage"],
)
def list_wg_options(session, ctm_id=None):
    qs = WG.objects.select_related('ctm')
    if ctm_id:
        qs = qs.filter(ctm_id=ctm_id)

    return [
        {
            "id": wg.id,
            "ctm_id": wg.ctm_id,
            "ctm_number": wg.ctm.number,
            "ctm_name": wg.ctm.name,
            "wg_number": wg.number,
            "name": wg.name,
            "description": wg.description,
            "iso_reference": wg.ctm.iso_reference,
            "arso_reference": wg.ctm.arso_reference,
        }
        for wg in qs
    ]


DRAFT_WG_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "expert_id": {"type": "integer"},
        "target_wg_id": {"type": "integer"},
        "justification": {
            "type": "string",
            "description": "Texte de justification basé sur le CV et les compétences de l'expert",
        },
    },
    "required": ["expert_id", "target_wg_id", "justification"],
}


@register(
    "draft_wg_attribution_request",
    "Crée un brouillon de demande d'attribution d'un expert à un groupe de travail (WG), "
    "avec une justification basée sur son CV et ses compétences. Crée un artefact "
    "WG_REQUEST en statut brouillon, téléchargeable en PDF.",
    DRAFT_WG_REQUEST_SCHEMA,
    scopes=["expert"],
)
def draft_wg_attribution_request(session, expert_id, target_wg_id, justification):
    expert = Expert.objects.select_related('user', 'structure').get(id=expert_id)
    wg = WG.objects.select_related('ctm').get(id=target_wg_id)

    artifact = AgentArtifact.objects.create(
        session=session,
        artifact_type='WG_REQUEST',
        title=f"Demande WG {wg.ctm.number}.{wg.number} — {expert.full_name}",
        payload={
            "expert_id": expert.id,
            "expert_name": expert.full_name,
            "wg_id": wg.id,
            "wg_label": f"WG {wg.ctm.number}.{wg.number} - {wg.name}",
            "ctm_id": wg.ctm_id,
            "ctm_number": wg.ctm.number,
            "justification": justification,
        },
        status='DRAFT',
    )

    return {
        "artifact_id": artifact.id,
        "status": artifact.status,
        "title": artifact.title,
        "message": (
            "Brouillon de demande d'attribution créé. L'utilisateur peut le télécharger "
            "en PDF et préparer un email à l'attention de la CTC."
        ),
    }
