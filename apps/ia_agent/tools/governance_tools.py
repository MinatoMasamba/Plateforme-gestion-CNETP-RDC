import re

from apps.governance.models import CTM, WG
from apps.norms.models import Norme

from ..models import AgentArtifact
from . import register

_STOPWORDS_FR = {
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "ou", "à", "au", "aux",
    "pour", "dans", "sur", "par", "avec", "sans", "ce", "ces", "cette", "son", "sa",
    "ses", "leur", "leurs", "est", "sont", "qui", "que", "quoi", "norme", "normes",
    "technique", "techniques", "construction", "national", "nationale", "congolais",
    "congolaise", "groupe", "travail",
}


def _keywords(*texts):
    words = re.findall(r"[a-zàâäéèêëïîôöùûüçœ]{4,}", " ".join(t or "" for t in texts).lower())
    return {w for w in words if w not in _STOPWORDS_FR}


LIST_CTM_NORMS_SCHEMA = {
    "type": "object",
    "properties": {
        "ctm_id": {"type": "integer", "description": "Filtrer sur un CTM (optionnel)"},
        "status": {"type": "string", "description": "Filtrer sur un statut de norme (optionnel)"},
    },
}


@register(
    "list_ctm_norms",
    "Liste les normes (avec leur CTM et leur WG), filtrables par CTM et/ou par statut.",
    LIST_CTM_NORMS_SCHEMA,
    scopes=["ctc", "pilotage"],
)
def list_ctm_norms(session, ctm_id=None, status=None):
    qs = Norme.objects.select_related('ctm', 'wg')
    if ctm_id:
        qs = qs.filter(ctm_id=ctm_id)
    if status:
        qs = qs.filter(status=status)

    return [
        {
            "id": n.id,
            "reference_number": n.reference_number,
            "title": n.title,
            "description": (n.description or "")[:300],
            "ctm_id": n.ctm_id,
            "ctm_number": n.ctm.number,
            "wg_id": n.wg_id,
            "wg_number": n.wg.number,
            "wg_name": n.wg.name,
            "status": n.get_status_display(),
            "tags": n.tags,
            "iso_reference": n.iso_reference,
            "arso_reference": n.arso_reference,
        }
        for n in qs[:200]
    ]


DETECT_WG_OVERLAP_SCHEMA = {
    "type": "object",
    "properties": {
        "ctm_id": {"type": "integer", "description": "Limiter la détection à un CTM (optionnel)"},
    },
}


@register(
    "detect_wg_overlap",
    "Détecte des paires de groupes de travail (WG) d'un même CTM dont les normes "
    "traitent potentiellement de sujets proches (similarité lexicale sur titres, "
    "descriptions et tags). Retourne des candidats à analyser — c'est à toi de juger de "
    "la pertinence réelle du chevauchement avant de le signaler.",
    DETECT_WG_OVERLAP_SCHEMA,
    scopes=["ctc", "pilotage"],
)
def detect_wg_overlap(session, ctm_id=None):
    ctms = CTM.objects.filter(id=ctm_id) if ctm_id else CTM.objects.all()
    candidates = []

    for ctm in ctms:
        wgs = list(WG.objects.filter(ctm=ctm))
        normes_by_wg = {wg.id: list(Norme.objects.filter(wg=wg)) for wg in wgs}
        keywords_by_wg = {}
        for wg in wgs:
            kw = _keywords(wg.name, wg.description)
            for n in normes_by_wg[wg.id]:
                kw |= _keywords(n.title, n.description, n.tags)
            keywords_by_wg[wg.id] = kw

        for i in range(len(wgs)):
            for j in range(i + 1, len(wgs)):
                wg_a, wg_b = wgs[i], wgs[j]
                kw_a, kw_b = keywords_by_wg[wg_a.id], keywords_by_wg[wg_b.id]
                if not kw_a or not kw_b:
                    continue

                shared = kw_a & kw_b
                ratio = len(shared) / max(len(kw_a | kw_b), 1)
                if ratio < 0.15 and len(shared) < 3:
                    continue

                candidates.append({
                    "ctm_id": ctm.id,
                    "ctm_number": ctm.number,
                    "wg_a": {"id": wg_a.id, "label": f"WG {ctm.number}.{wg_a.number} - {wg_a.name}"},
                    "wg_b": {"id": wg_b.id, "label": f"WG {ctm.number}.{wg_b.number} - {wg_b.name}"},
                    "shared_keywords": sorted(shared)[:15],
                    "similarity_score": round(ratio, 2),
                    "normes_a": [
                        {"id": n.id, "reference_number": n.reference_number, "title": n.title}
                        for n in normes_by_wg[wg_a.id]
                    ],
                    "normes_b": [
                        {"id": n.id, "reference_number": n.reference_number, "title": n.title}
                        for n in normes_by_wg[wg_b.id]
                    ],
                })

    candidates.sort(key=lambda c: c["similarity_score"], reverse=True)
    return candidates[:20]


FLAG_NORM_OVERLAP_SCHEMA = {
    "type": "object",
    "properties": {
        "ctm_id": {"type": "integer"},
        "wg_a_id": {"type": "integer"},
        "wg_b_id": {"type": "integer"},
        "analysis_text": {"type": "string", "description": "Ton analyse du chevauchement constaté"},
        "recommendation": {"type": "string", "description": "Ta recommandation pour la CTC"},
    },
    "required": ["ctm_id", "wg_a_id", "wg_b_id", "analysis_text", "recommendation"],
}


@register(
    "flag_norm_overlap",
    "Crée un signalement (brouillon) de chevauchement entre deux groupes de travail d'un "
    "même CTM, à destination de la CTC, accompagné de ton analyse et d'une recommandation.",
    FLAG_NORM_OVERLAP_SCHEMA,
    scopes=["ctc", "pilotage"],
)
def flag_norm_overlap(session, ctm_id, wg_a_id, wg_b_id, analysis_text, recommendation):
    ctm = CTM.objects.get(id=ctm_id)
    wg_a = WG.objects.get(id=wg_a_id)
    wg_b = WG.objects.get(id=wg_b_id)

    artifact = AgentArtifact.objects.create(
        session=session,
        artifact_type='NORM_OVERLAP',
        title=f"Chevauchement CTM {ctm.number} — WG {wg_a.number} / WG {wg_b.number}",
        payload={
            "ctm_id": ctm.id,
            "ctm_number": ctm.number,
            "wg_a": {"id": wg_a.id, "label": f"WG {ctm.number}.{wg_a.number} - {wg_a.name}"},
            "wg_b": {"id": wg_b.id, "label": f"WG {ctm.number}.{wg_b.number} - {wg_b.name}"},
            "analysis": analysis_text,
            "recommendation": recommendation,
        },
        status='DRAFT',
    )

    return {"artifact_id": artifact.id, "status": artifact.status, "title": artifact.title}
