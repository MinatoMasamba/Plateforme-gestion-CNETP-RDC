"""
Outils d'accès global à la plateforme CNETP :
membres CTM, CV, présences, votes, contacts, statistiques globales.
"""
from apps.experts.models import Expert
from apps.governance.models import Affectation, CTM, WG
from apps.norms.models import Norme, NormeVote

from . import register


# ─── list_ctm_members ─────────────────────────────────────────────────────────

LIST_CTM_MEMBERS_SCHEMA = {
    "type": "object",
    "properties": {
        "ctm_id": {
            "type": "integer",
            "description": "ID du CTM (Comité Technique Miroir). Obligatoire.",
        },
        "include_contacts": {
            "type": "boolean",
            "description": "Inclure email, téléphone, WhatsApp (défaut: true).",
        },
        "filter_status": {
            "type": "string",
            "enum": ["ACTIVE", "PENDING", "INACTIVE", "SUSPENDED", "REJECTED", "ALL"],
            "description": "Filtrer par statut expert (défaut: ALL).",
        },
    },
    "required": ["ctm_id"],
}


@register(
    "list_ctm_members",
    "Liste tous les membres (experts) d'un Comité Technique Miroir (CTM) avec leur statut, "
    "présence ou absence de CV, nombre de présences aux sessions, votes, contacts,sa description et competance "
    "(email, téléphone, WhatsApp), structure d'origine et rôle dans le ctc ,pilotage , CTM/WG. "
    "Permet de savoir qui a déposé son CV, combien sont actifs, leurs coordonnées, le contenue du cvetc.",
    LIST_CTM_MEMBERS_SCHEMA,
    scopes=["expert", "ctc", "pilotage"],
)
def list_ctm_members(session, ctm_id, include_contacts=True, filter_status="ALL"):
    try:
        ctm = CTM.objects.get(id=ctm_id)
    except CTM.DoesNotExist:
        return {"error": f"CTM {ctm_id} introuvable."}

    # Experts dont le CTM principal est ce CTM
    qs = Expert.objects.filter(ctm_id=ctm_id).select_related(
        'user', 'structure'
    ).prefetch_related('governance_affectations__wg')

    if filter_status and filter_status != "ALL":
        qs = qs.filter(status=filter_status)

    members = []
    for expert in qs:
        # Rôle CTM via affectation
        role = "Membre CTM"
        if ctm.scientific_president_id == expert.id:
            role = "Président scientifique CTM"
        elif ctm.rapporteur_id == expert.id:
            role = "Rapporteur CTM"
        elif ctm.secretary_id == expert.id:
            role = "Secrétaire CTM"

        # WG affecté
        wg_info = []
        for aff in expert.governance_affectations.filter(ctm_id=ctm_id):
            wg_info.append(f"WG {ctm.number}.{aff.wg.number} — {aff.wg.name} ({aff.wg_role})")

        # Activité votes
        norme_vote_count = NormeVote.objects.filter(voter=expert).count()

        record = {
            "expert_id": expert.id,
            "full_name": expert.full_name,
            "structure": expert.structure.acronym if expert.structure else "—",
            "status": expert.status,
            "role_ctm": role,
            "wg_affectations": wg_info,
            "has_cv": bool(expert.cv),
            "cv_filename": expert.cv.name.split('/')[-1] if expert.cv else None,
            "presence_count": expert.presence_count,
            "norme_vote_count": norme_vote_count,
            "appointment_decree": expert.appointment_decree_number or None,
            "inscription_date": expert.inscription_date.strftime('%d/%m/%Y') if expert.inscription_date else None,
        }

        if include_contacts:
            record["email"] = expert.user.email or None
            record["phone"] = expert.user.phone or None
            record["whatsapp"] = expert.mobile_money_number or expert.whatsapp_number or None
            record["province"] = expert.user.province or None

        members.append(record)

    # Résumé
    total = len(members)
    cv_count = sum(1 for m in members if m["has_cv"])
    active_count = sum(1 for m in members if m["status"] == "ACTIVE")

    return {
        "ctm_id": ctm.id,
        "ctm_number": ctm.number,
        "ctm_name": ctm.name,
        "total_members": total,
        "active_members": active_count,
        "cv_uploaded": cv_count,
        "cv_missing": total - cv_count,
        "members": members,
    }


# ─── search_experts ───────────────────────────────────────────────────────────

SEARCH_EXPERTS_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Nom, spécialité, structure ou numéro de téléphone à rechercher.",
        },
        "status": {
            "type": "string",
            "enum": ["ACTIVE", "PENDING", "INACTIVE", "SUSPENDED", "REJECTED", "ALL"],
            "description": "Filtrer par statut (défaut: ALL).",
        },
        "ctm_id": {
            "type": "integer",
            "description": "Limiter la recherche à un CTM précis (optionnel).",
        },
        "has_cv": {
            "type": "boolean",
            "description": "Si true : seulement ceux avec CV et dire le contenu. Si false : seulement sans CV.",
        },
    },
    "required": ["query"],
}


@register(
    "search_experts",
    "Recherche des experts de la plateforme par nom, spécialité, structure ou téléphone. "
    "Permet aussi de filtrer par statut, CTM ou présence d'un CV. "
    "Retourne leurs contacts, présences, votes et rôles.",
    SEARCH_EXPERTS_SCHEMA,
    scopes=["ctc", "pilotage", "expert"],
)
def search_experts(session, query="", status="ALL", ctm_id=None, has_cv=None):
    from django.db.models import Q

    qs = Expert.objects.select_related('user', 'structure', 'ctm')

    if query:
        qs = qs.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(specialties__icontains=query)
            | Q(structure__name__icontains=query)
            | Q(structure__acronym__icontains=query)
            | Q(user__phone__icontains=query)
            | Q(whatsapp_number__icontains=query)
        )

    if status and status != "ALL":
        qs = qs.filter(status=status)

    if ctm_id:
        qs = qs.filter(ctm_id=ctm_id)

    if has_cv is True:
        qs = qs.exclude(cv='').exclude(cv=None)
    elif has_cv is False:
        qs = qs.filter(Q(cv='') | Q(cv=None))

    results = []
    for expert in qs[:30]:
        results.append({
            "expert_id": expert.id,
            "full_name": expert.full_name,
            "email": expert.user.email,
            "phone": expert.user.phone or None,
            "whatsapp": expert.whatsapp_number or None,
            "province": expert.user.province or None,
            "structure": expert.structure.acronym if expert.structure else "—",
            "ctm": f"CTM {expert.ctm.number}" if expert.ctm else None,
            "specialties": expert.specialties,
            "status": expert.status,
            "has_cv": bool(expert.cv),
            "presence_count": expert.presence_count,
            "norme_vote_count": NormeVote.objects.filter(voter=expert).count(),
        })

    return {"total_found": len(results), "results": results}


# ─── get_platform_overview ────────────────────────────────────────────────────

GET_OVERVIEW_SCHEMA = {"type": "object", "properties": {}}


@register(
    "get_platform_overview",
    "Retourne une vue d'ensemble complète de la plateforme CNETP : nombre total d'experts "
    "par statut, taux de dépôt de CV, présences cumulées, répartition par CTM, "
    "nombre de normes par statut, votes et amendements. Point d'entrée pour toute "
    "question générale sur l'état de la plateforme.",
    GET_OVERVIEW_SCHEMA,
    scopes=["ctc", "pilotage"],
)
def get_platform_overview(session):
    from django.db.models import Count, Q, Sum

    total_exp = Expert.objects.count()
    active_exp = Expert.objects.filter(status='ACTIVE').count()
    pending_exp = Expert.objects.filter(status='PENDING').count()
    inactive_exp = Expert.objects.filter(status='INACTIVE').count()
    with_cv = Expert.objects.exclude(cv='').exclude(cv=None).count()
    total_presences = Expert.objects.aggregate(s=Sum('presence_count'))['s'] or 0

    # Par CTM
    ctm_breakdown = []
    for ctm in CTM.objects.all().order_by('number'):
        members = Expert.objects.filter(ctm=ctm)
        ctm_breakdown.append({
            "ctm": f"CTM {ctm.number} — {ctm.name}",
            "total": members.count(),
            "active": members.filter(status='ACTIVE').count(),
            "with_cv": members.exclude(cv='').exclude(cv=None).count(),
        })

    # Normes
    from apps.norms.models import Norme, NormeVote
    norm_stats = list(
        Norme.objects.values('status').annotate(count=Count('id')).order_by('-count')
    )
    total_norms = Norme.objects.count()
    total_votes = NormeVote.objects.count()

    return {
        "experts": {
            "total": total_exp,
            "active": active_exp,
            "pending": pending_exp,
            "inactive": inactive_exp,
            "with_cv": with_cv,
            "without_cv": total_exp - with_cv,
            "cv_rate_pct": round(with_cv / total_exp * 100, 1) if total_exp else 0,
            "total_presences": total_presences,
        },
        "experts_by_ctm": ctm_breakdown,
        "norms": {
            "total": total_norms,
            "by_status": norm_stats,
            "total_votes": total_votes,
        },
    }


# ─── get_expert_contacts ──────────────────────────────────────────────────────

GET_CONTACTS_SCHEMA = {
    "type": "object",
    "properties": {
        "expert_id": {"type": "integer", "description": "ID de l'expert."},
    },
    "required": ["expert_id"],
}


@register(
    "get_expert_contacts",
    "Retourne les coordonnées complètes d'un expert : email, téléphone, WhatsApp, "
    "province, informations bancaires (pour jetons de présence), "
    "date d'inscription et statut de confirmation email.",
    GET_CONTACTS_SCHEMA,
    scopes=["ctc", "pilotage"],
)
def get_expert_contacts(session, expert_id):
    try:
        expert = Expert.objects.select_related('user', 'structure').get(id=expert_id)
    except Expert.DoesNotExist:
        return {"error": f"Expert {expert_id} introuvable."}

    return {
        "expert_id": expert.id,
        "full_name": expert.full_name,
        "email": expert.user.email,
        "email_confirmed": expert.user.email_confirmed,
        "phone": expert.user.phone or None,
        "whatsapp": expert.whatsapp_number or None,
        "mobile_money": expert.mobile_money_number or None,
        "province": expert.user.province or None,
        "structure": expert.structure.name if expert.structure else None,
        "bank_name": expert.bank_name or None,
        "bank_account": expert.bank_account or None,
        "status": expert.status,
        "has_cv": bool(expert.cv),
        "presence_count": expert.presence_count,
        "daily_rate_usd": float(expert.daily_rate),
        "monthly_allowance_usd": float(expert.monthly_research_allowance),
        "inscription_date": expert.inscription_date.strftime('%d/%m/%Y %H:%M') if expert.inscription_date else None,
        "activation_date": expert.activation_date.strftime('%d/%m/%Y') if expert.activation_date else None,
        "appointment_decree": expert.appointment_decree_number or None,
    }
