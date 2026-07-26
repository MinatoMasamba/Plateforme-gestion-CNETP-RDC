from django.db.models import Count

from apps.experts.models import Expert
from apps.norms.models import Norme, NormeVote
from apps.public.models import PublicAmendement

from ..models import AgentArtifact
from . import register
from .governance_tools import detect_inter_ctm_overlap, detect_wg_overlap

CHART_PALETTE = [
    "#1a3a5c", "#c8a84b", "#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4",
]


def _palette(n):
    if n <= len(CHART_PALETTE):
        return CHART_PALETTE[:n]
    return [CHART_PALETTE[i % len(CHART_PALETTE)] for i in range(n)]


def _bar_chart(labels, data, label):
    return {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{"label": label, "data": data, "backgroundColor": _palette(len(labels))}],
        },
        "options": {"responsive": True, "plugins": {"legend": {"display": False}}},
    }


def _doughnut_chart(labels, data, label):
    return {
        "type": "doughnut",
        "data": {
            "labels": labels,
            "datasets": [{"label": label, "data": data, "backgroundColor": _palette(len(labels))}],
        },
        "options": {"responsive": True},
    }


GET_CHART_DATA_SCHEMA = {
    "type": "object",
    "properties": {
        "metric": {
            "type": "string",
            "enum": [
                "normes_by_status",
                "normes_by_ctm",
                "votes_participation",
                "public_inquiry_status",
                "experts_by_structure",
                "wg_overlap_summary",
                "inter_ctm_overlap_summary",
            ],
        },
        "filters": {
            "type": "object",
            "properties": {
                "norme_id": {"type": "integer"},
                "ctm_id": {"type": "integer"},
            },
        },
    },
    "required": ["metric"],
}


@register(
    "get_chart_data",
    "Génère un graphique (spécification Chart.js) à partir d'une métrique CNETP "
    "prédéfinie. Crée immédiatement un artefact CHART affiché à l'utilisateur.",
    GET_CHART_DATA_SCHEMA,
    scopes=["pilotage"],
)
def get_chart_data(session, metric, filters=None):
    filters = filters or {}
    status_labels = dict(Norme.STATUS_CHOICES)
    vote_labels = dict(NormeVote.VOTE_CHOICES)
    inquiry_labels = dict(PublicAmendement.STATUS_CHOICES)

    if metric == "normes_by_status":
        rows = Norme.objects.values('status').annotate(count=Count('id')).order_by('-count')
        labels = [status_labels.get(r['status'], r['status']) for r in rows]
        data = [r['count'] for r in rows]
        chart_spec = _bar_chart(labels, data, "Normes par statut")
        title = "Répartition des normes par statut"

    elif metric == "normes_by_ctm":
        rows = (
            Norme.objects.values('ctm__number', 'ctm__name')
            .annotate(count=Count('id'))
            .order_by('ctm__number')
        )
        labels = [f"CTM {r['ctm__number']} — {r['ctm__name']}" for r in rows]
        data = [r['count'] for r in rows]
        chart_spec = _bar_chart(labels, data, "Normes par CTM")
        title = "Répartition des normes par CTM"

    elif metric == "votes_participation":
        qs = NormeVote.objects.all()
        if filters.get('norme_id'):
            qs = qs.filter(norme_id=filters['norme_id'])
        rows = qs.values('vote').annotate(count=Count('id'))
        labels = [vote_labels.get(r['vote'], r['vote']) for r in rows]
        data = [r['count'] for r in rows]
        chart_spec = _doughnut_chart(labels, data, "Participation aux votes")
        title = "Participation aux votes"

    elif metric == "public_inquiry_status":
        qs = PublicAmendement.objects.all()
        if filters.get('norme_id'):
            qs = qs.filter(norme_id=filters['norme_id'])
        rows = qs.values('status').annotate(count=Count('id'))
        labels = [inquiry_labels.get(r['status'], r['status']) for r in rows]
        data = [r['count'] for r in rows]
        chart_spec = _doughnut_chart(labels, data, "Enquête publique par statut")
        title = "Statut des amendements publics"

    elif metric == "experts_by_structure":
        rows = (
            Expert.objects.filter(status='ACTIVE')
            .values('structure__acronym')
            .annotate(count=Count('id'))
            .order_by('-count')[:12]
        )
        labels = [r['structure__acronym'] or '—' for r in rows]
        data = [r['count'] for r in rows]
        chart_spec = _bar_chart(labels, data, "Experts actifs par structure")
        title = "Experts actifs par structure"

    elif metric == "wg_overlap_summary":
        overlaps = detect_wg_overlap(session, ctm_id=filters.get('ctm_id'))
        counts = {}
        for o in overlaps:
            key = f"CTM {o['ctm_number']}"
            counts[key] = counts.get(key, 0) + 1
        labels = list(counts.keys())
        data = list(counts.values())
        chart_spec = _bar_chart(labels, data, "Paires WG potentiellement en chevauchement")
        title = "Chevauchements potentiels par CTM"

    elif metric == "inter_ctm_overlap_summary":
        overlaps = detect_inter_ctm_overlap(session)
        counts = {}
        for o in overlaps:
            key = f"CTM {o['wg_a']['ctm_number']} ↔ CTM {o['wg_b']['ctm_number']}"
            counts[key] = counts.get(key, 0) + 1
        labels = list(counts.keys())
        data = list(counts.values())
        chart_spec = _bar_chart(labels, data, "Paires WG en chevauchement inter-CTM")
        title = "Chevauchements potentiels entre CTM différents"

    else:
        return {"error": f"Métrique inconnue : {metric}"}

    artifact = AgentArtifact.objects.create(
        session=session,
        artifact_type='CHART',
        title=title,
        payload={"metric": metric, "chart_spec": chart_spec},
        status='APPROVED',
    )

    return {"artifact_id": artifact.id, "title": title, "chart_spec": chart_spec}
