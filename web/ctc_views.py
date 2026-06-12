"""
Vues dynamiques de la Cellule Technique de Coordination / Secrétariat Technique (20 postes).

Logique : chaque expert CTC se voit attribuer un `ctc_sub_role` dérivé de son rôle
CTCMembership ET de l'acronyme de sa structure d'origine. Ce sous-rôle alimente des
booléens de privilèges injectés dans le contexte du template, qui masque ou déverrouille
les modules de son pôle.

4 pôles — 4 profils de privilèges :
  Profil 1 — Direction des Opérations          (3 postes)
  Profil 2 — Pôle Analyse & Ingénierie Doc.    (7 postes)
  Profil 3 — Pôle Logistique, Comm. & Ext.     (4 postes)
  Profil 4 — Bureau Appui Technique Numérique  (6 postes)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from apps.experts.models import Expert
from apps.governance.models import (
    TechnicalCell, CTCMembership, CTCOperationalRequest,
    PosteNominatifCTC, CTM, CTCProcessus,
)
from apps.validation.models import (
    ISOReview, EcologicalReview, EconomicReview,
    ScheduleReview, IndustrialConsultation, LegisticReview,
)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES DE MAPPAGE  role × structure → sous-rôle CTC
# ─────────────────────────────────────────────────────────────────────────────

# Pour les rôles ayant 2 postes issus de structures différentes,
# on affine via l'acronyme de structure.
_CTC_ROLE_STRUCTURE_TO_SUB = {
    # Direction des Opérations
    'COORDINATOR':      {None: 'coordonnateur_principal'},
    'VICE_COORDINATOR': {None: 'coordonnateur_adjoint'},
    'EXECUTIVE':        {None: 'assistant_executif'},

    # Pôle Analyse — veille : 2 experts (ACGT / SG-ITP)
    'ISO_EXPERT': {
        'ACGT':   'veille_acgt',
        None:     'veille_sg',      # SG-ITP ou tout autre
    },
    'LEGAL':        {None: 'expert_juridique'},
    'ENVIRONMENTAL':{None: 'sauvegardes_ci'},
    'PLANNER':      {None: 'planification_recons'},
    'ECONOMIST':    {None: 'economiste_foner'},
    'SCIENTIFIC':   {None: 'scientifique_inbtp'},

    # Pôle Logistique
    'ACCOUNTANT':       {None: 'gaf'},
    'ENQUIRY_MANAGER':  {None: 'responsable_enquetes'},
    'INDUSTRIAL':       {None: 'liaison_fec'},
    'COMMUNICATOR':     {None: 'communicateur'},

    # Bureau Numérique — cartographes : BEAU / OVD
    'CARTOGRAPHER': {
        'BEAU': 'sig_beau',
        'OVD':  'sig_ovd',
        None:   'sig_beau',
    },
    'DATA_ENTRY': {None: 'operateur_saisie'},
    # IT : BTC / SG-ITP
    'IT_ADMIN': {
        'BTC':  'it_btc',
        None:   'it_sg_itp',
    },
}

# Pôles et sous-rôles associés
_DIRECTION_SUBS  = {'coordonnateur_principal', 'coordonnateur_adjoint', 'assistant_executif'}
_ANALYSE_SUBS    = {'veille_acgt', 'veille_sg', 'expert_juridique', 'sauvegardes_ci',
                    'planification_recons', 'economiste_foner', 'scientifique_inbtp'}
_LOGISTIQUE_SUBS = {'gaf', 'responsable_enquetes', 'liaison_fec', 'communicateur'}
_NUMERIQUE_SUBS  = {'sig_beau', 'sig_ovd', 'operateur_saisie', 'it_btc', 'it_sg_itp'}

POLE_LABELS = {
    'direction':   'Direction des Opérations',
    'analyse':     "Pôle d'Analyse et d'Ingénierie Documentaire",
    'logistique':  'Pôle Logistique, Communication et Relations Extérieures',
    'numerique':   "Bureau d'Appui Technique et Numérique",
}

POLE_BADGE_COLORS = {
    'direction':  'bg-amber-500/15 text-amber-400 border-amber-500/30',
    'analyse':    'bg-blue-500/15 text-blue-400 border-blue-500/30',
    'logistique': 'bg-purple-500/15 text-purple-400 border-purple-500/30',
    'numerique':  'bg-teal-500/15 text-teal-400 border-teal-500/30',
}

# Pôle CTC (backend) → pôle de la sidebar du nouveau prototype (templates/ctc/app/)
_SIDEBAR_POLE_MAP = {
    'direction':  'operations',
    'analyse':    'analyse',
    'logistique': 'logistique',
    'numerique':  'technique',
}

# Modèle de review → libellé affiché dans « Mes Assignations » + icône Lucide +
# ancre du widget correspondant sur le tableau de bord (pour le bouton "Traiter")
_REVIEW_TASK_META = {
    ISOReview:             {'label': 'Traduction & Alignement ISO',        'icon': 'languages',     'anchor': 'widget-traduction-iso'},
    LegisticReview:        {'label': 'Contrôle de Légistique',             'icon': 'scale',         'anchor': 'widget-legistique'},
    EcologicalReview:      {'label': 'Sauvegardes Éco-Environnementales',  'icon': 'leaf',          'anchor': 'widget-eco-env'},
    EconomicReview:        {'label': 'Évaluation Économique',              'icon': 'banknote',      'anchor': 'widget-eco-env'},
    ScheduleReview:        {'label': 'Méthodologie & Chronogramme',        'icon': 'calendar-days', 'anchor': 'widget-methodologie'},
    IndustrialConsultation:{'label': 'Consultation Industrielle (FEC)',    'icon': 'briefcase',     'anchor': 'widget-cadrage-industriel'},
}


# ─────────────────────────────────────────────────────────────────────────────
# RÉSOLUTION DU SOUS-RÔLE
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_ctc_sub_role(ctc_role: str, acronym: str) -> str:
    """Dérive le sous-rôle précis à partir du rôle CTCMembership + acronyme structure."""
    role_map = _CTC_ROLE_STRUCTURE_TO_SUB.get(ctc_role)
    if not role_map:
        return ctc_role.lower()
    return role_map.get(acronym) or role_map.get(None) or ctc_role.lower()


def _pole_for_sub_role(sub_role: str) -> str:
    """Détermine le pôle CTC (backend) auquel appartient un sous-rôle."""
    return (
        'direction'  if sub_role in _DIRECTION_SUBS  else
        'analyse'    if sub_role in _ANALYSE_SUBS    else
        'logistique' if sub_role in _LOGISTIQUE_SUBS else
        'numerique'  if sub_role in _NUMERIQUE_SUBS  else
        'membre'
    )


# ─────────────────────────────────────────────────────────────────────────────
# MOTEUR DE PRIVILÈGES CTC
# ─────────────────────────────────────────────────────────────────────────────

def get_ctc_context(expert: Expert) -> dict | None:
    """
    Calcule et retourne le dictionnaire complet de contexte de privilèges
    pour un expert membre de la Cellule Technique de Coordination.

    Retourne None si l'expert n'est pas membre de la CTC.
    """
    membership = (
        CTCMembership.objects
        .filter(expert=expert)
        .select_related('ctc')
        .first()
    )
    if not membership:
        return None

    role    = membership.role
    acronym = (expert.structure.acronym or '').upper() if expert.structure else ''

    sub_role = _resolve_ctc_sub_role(role, acronym)

    # ── Détermination du pôle ──────────────────────────────────────────────
    pole = _pole_for_sub_role(sub_role)

    is_direction  = sub_role in _DIRECTION_SUBS
    is_analyse    = sub_role in _ANALYSE_SUBS
    is_logistique = sub_role in _LOGISTIQUE_SUBS
    is_numerique  = sub_role in _NUMERIQUE_SUBS

    # ── Poste nominatif CTC (si disponible) ──────────────────────────────
    poste = PosteNominatifCTC.objects.filter(holder=expert).select_related('required_structure').first()

    # ── Demandes opérationnelles en attente (Assistant Exécutif) ─────────
    pending_ctc_requests = (
        CTCOperationalRequest.objects
        .filter(status='PENDING')
        .select_related('requester__user', 'requester__structure')
        .order_by('-created_at')
        if sub_role == 'assistant_executif' else []
    )

    # ─────────────────────────────────────────────────────────────────────
    # BOOLÉENS DE PRIVILÈGES
    # ─────────────────────────────────────────────────────────────────────
    ctx = {
        # ── Identification ───────────────────────────────────────────────
        'is_ctc_member': True,
        'ctc_sub_role':  sub_role,
        'ctc_pole':      pole,
        'pole_label':    POLE_LABELS.get(pole, 'Membre CTC'),
        'pole_badge':    POLE_BADGE_COLORS.get(pole, ''),
        'poste':         poste,
        'membership':    membership,

        # ── Profil 1 : Direction des Opérations ──────────────────────────
        'is_direction':           is_direction,
        # Hub de Routage Documentaire
        'can_route_documents':    is_direction,
        # Console d'Arbitrage des Retards (Coordonnateurs seulement)
        'can_arbitrate_delays':   sub_role in {'coordonnateur_principal', 'coordonnateur_adjoint'},
        # Transmission dossier final → Bureau Directoire Pilotage
        'can_transmit_directoire': sub_role in {'coordonnateur_principal', 'coordonnateur_adjoint'},
        # Approbation des demandes opérationnelles CTC
        'can_approve_ctc_requests': sub_role == 'assistant_executif',
        # Aucun blocage de lecture pour la Direction
        'direction_full_read':    is_direction,

        # ── Profil 2 : Pôle Analyse & Ingénierie Documentaire ────────────
        'is_analyste':            is_analyse,
        # Traduction & Alignement ISO
        'can_translate_iso':      sub_role in {'veille_acgt', 'veille_sg'},
        # Légistique CTC (conformité réglementaire RDC)
        'can_legistique_ctc':     sub_role == 'expert_juridique',
        # Matrice Impacts Éco-Environnementaux
        'can_eco_env_matrix':     sub_role in {'economiste_foner', 'sauvegardes_ci'},
        # Méthodologie & Chronogramme (validation planning + état de l'art scientifique)
        'can_methodologie_chronogramme': sub_role in {'planification_recons', 'scientifique_inbtp'},
        # Lecture seule sur données logistiques / financières
        'readonly_logistique':    is_analyse,
        # WG modification → Note d'amendement obligatoire
        'must_use_amendment':     is_analyse,

        # ── Profil 3 : Pôle Logistique, Comm. & Relations Ext. ───────────
        'is_logistique':          is_logistique,
        # Console Modération Enquête Publique
        'can_enquete_publique':   sub_role == 'responsable_enquetes',
        # Livre de Cadrage Industriel
        'can_cadrage_industriel': sub_role == 'liaison_fec',
        # Grand Livre Comptable
        'can_grand_livre':        sub_role == 'gaf',
        # Textes lois / calculs géotechniques → bloqué
        'blocked_scientific_write': is_logistique,

        # ── Profil 4 : Bureau Appui Technique & Numérique ─────────────────
        'is_numerique':           is_numerique,
        # Serveur SIG / Géospatial
        'can_upload_maps':        sub_role in {'sig_beau', 'sig_ovd'},
        # Console Administration Système
        'can_admin_system':       sub_role in {'it_btc', 'it_sg_itp'},
        # Interface Saisie Massive (Fast-Entry)
        'can_fast_entry':         sub_role == 'operateur_saisie',
        # Validations politiques / chronogramme → bloqué
        'blocked_political':      is_numerique,

        # ── Données pour l'Assistant Exécutif ────────────────────────────
        'pending_ctc_requests':       pending_ctc_requests,
        'pending_ctc_requests_count': len(pending_ctc_requests) if sub_role == 'assistant_executif' else 0,
    }

    # ── Données workflow CTCProcessus ──────────────────────────────────────
    # Normes actives dans le circuit CTC, filtrées selon le rôle de l'expert
    _STAGE_FOR_ROLE = {
        'assistant_executif':      ['RECEPTION'],
        'operateur_saisie':        ['RECEPTION'],
        'coordonnateur_principal': ['RECEPTION', 'GEOSPATIAL', 'MULTI_REVIEW', 'INDUSTRIAL', 'SIGNED_OUT'],
        'coordonnateur_adjoint':   ['RECEPTION', 'GEOSPATIAL', 'MULTI_REVIEW', 'INDUSTRIAL', 'SIGNED_OUT'],
        'sig_beau':                ['GEOSPATIAL'],
        'sig_ovd':                 ['GEOSPATIAL'],
        'it_btc':                  ['GEOSPATIAL'],
        'it_sg_itp':               ['GEOSPATIAL'],
        'veille_acgt':             ['MULTI_REVIEW'],
        'veille_sg':               ['MULTI_REVIEW'],
        'expert_juridique':        ['MULTI_REVIEW'],
        'sauvegardes_ci':          ['MULTI_REVIEW'],
        'economiste_foner':        ['MULTI_REVIEW'],
        'planification_recons':    ['MULTI_REVIEW'],
        'scientifique_inbtp':      ['MULTI_REVIEW'],
        'liaison_fec':             ['INDUSTRIAL'],
        'communicateur':           [],
        'responsable_enquetes':    [],
        'gaf':                     [],
    }
    visible_stages = _STAGE_FOR_ROLE.get(sub_role, [])
    active_processus = (
        CTCProcessus.objects
        .filter(current_stage__in=visible_stages)
        .select_related('norme', 'received_by')
        .order_by('-created_at')
        if visible_stages else []
    )

    # Examens en attente assignés à cet expert (selon son rôle)
    _review_model_for_sub = {
        'veille_acgt':         (ISOReview, 'expert'),
        'veille_sg':           (ISOReview, 'expert'),
        'expert_juridique':    (LegisticReview, 'legist'),
        'sauvegardes_ci':      (EcologicalReview, 'expert'),
        'economiste_foner':    (EconomicReview, 'expert'),
        'planification_recons': (ScheduleReview, 'planner'),
        'scientifique_inbtp':  (ScheduleReview, 'scientist'),
        'liaison_fec':         (IndustrialConsultation, 'expert'),
    }
    my_pending_reviews = []
    if sub_role in _review_model_for_sub:
        model_cls, field = _review_model_for_sub[sub_role]
        status_field = f'{field}_status' if model_cls is ScheduleReview else 'status'
        my_pending_reviews = list(
            model_cls.objects
            .filter(**{field: expert, f'{status_field}__in': ['PENDING', 'ASSIGNED', 'IN_REVIEW']})
            .select_related('norme')
            .order_by('-created_at')
        )

    ctx.update({
        'active_processus':      active_processus,
        'active_processus_count': len(active_processus) if visible_stages else 0,
        'my_pending_reviews':    my_pending_reviews,
        'my_pending_reviews_count': len(my_pending_reviews),
    })

    return ctx


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXTE PARTAGÉ DASHBOARD + COMPOSANTS AJAX
# ─────────────────────────────────────────────────────────────────────────────

def _ctc_shared_context(expert: Expert) -> dict | None:
    """
    Contexte commun au shell CTC (`ctc/app/app.html`) et à tous les
    composants chargés en AJAX (`ctc_component_api_view`).

    Retourne None si l'expert n'est pas membre de la CTC.
    """
    ctx = get_ctc_context(expert)
    if ctx is None:
        return None

    # CTMs pour le hub de routage (Direction) et la modale CTM
    ctms = CTM.objects.prefetch_related('working_groups').order_by('number')
    ctms_list = [
        {
            'ctm': c,
            'wg_count': c.working_groups.count(),
            'member_count': c.affectations.count(),
        }
        for c in ctms
    ]

    # Mes demandes opérationnelles (autres pôles)
    my_ctc_requests = (
        CTCOperationalRequest.objects
        .filter(requester=expert)
        .order_by('-created_at')[:10]
    )

    # Annuaire des membres CTC
    ctc_directory = []
    for m in CTCMembership.objects.select_related('expert__user', 'expert__structure'):
        m_acronym = (m.expert.structure.acronym or '').upper() if m.expert.structure else ''
        m_sub_role = _resolve_ctc_sub_role(m.role, m_acronym)
        ctc_directory.append({
            'name': m.expert.user.get_full_name(),
            'email': m.expert.user.email,
            'role_label': m.get_role_display(),
            'structure': m.expert.structure.acronym if m.expert.structure else '',
            'pole': _SIDEBAR_POLE_MAP.get(_pole_for_sub_role(m_sub_role), ''),
            'is_me': m.expert_id == expert.id,
        })

    # Tâches personnelles en attente (vue "Mes Assignations")
    assignation_tasks = []
    for review in ctx.get('my_pending_reviews', []):
        meta = _REVIEW_TASK_META.get(type(review), {'label': 'Examen', 'icon': 'file-text', 'anchor': None})
        if isinstance(review, ScheduleReview):
            status_display = (
                review.get_planner_status_display() if ctx['ctc_sub_role'] == 'planification_recons'
                else review.get_scientist_status_display()
            )
        else:
            status_display = review.get_status_display()
        assignation_tasks.append({
            'type_label': meta['label'],
            'icon': meta['icon'],
            'reference': review.norme.reference_number,
            'title': review.norme.title,
            'status_display': status_display,
            'view_target': 'dashboard',
            'anchor': meta['anchor'],
        })

    if ctx['ctc_sub_role'] == 'assistant_executif':
        for req in ctx.get('pending_ctc_requests', []):
            assignation_tasks.append({
                'type_label': "Demande d'Accès Inter-Pôles",
                'icon': 'user-check',
                'reference': '',
                'title': f"{req.requester.user.get_full_name()} — {req.restricted_resource}",
                'status_display': req.get_status_display(),
                'view_target': 'dashboard',
                'anchor': 'widget-pending-requests',
            })
        for p in ctx.get('active_processus', []):
            assignation_tasks.append({
                'type_label': 'Réception & Cadrage',
                'icon': 'inbox',
                'reference': p.norme.reference_number,
                'title': p.norme.title,
                'status_display': p.get_current_stage_display(),
                'view_target': 'dossiers',
                'anchor': None,
            })

    # Pipeline complet des dossiers normatifs (vue "Dossiers Normatifs")
    dossiers = (
        CTCProcessus.objects
        .select_related('norme', 'norme__ctm', 'received_by__user')
        .order_by('-updated_at')
    )

    # Sous-ensemble JSON-safe du contexte de privilèges, injecté côté client
    # via `{{ ctc_ctx_json|json_script:"ctc-ctx-data" }}` (window.CTC_CTX).
    _json_safe_keys = (
        'is_ctc_member', 'ctc_sub_role', 'ctc_pole', 'pole_label',
        'is_direction', 'can_route_documents', 'can_arbitrate_delays',
        'can_transmit_directoire', 'can_approve_ctc_requests', 'direction_full_read',
        'is_analyste', 'can_translate_iso', 'can_legistique_ctc', 'can_eco_env_matrix',
        'can_methodologie_chronogramme',
        'readonly_logistique', 'must_use_amendment',
        'is_logistique', 'can_enquete_publique', 'can_cadrage_industriel',
        'can_grand_livre', 'blocked_scientific_write',
        'is_numerique', 'can_upload_maps', 'can_admin_system', 'can_fast_entry',
        'blocked_political',
        'pending_ctc_requests_count', 'active_processus_count', 'my_pending_reviews_count',
    )
    ctc_ctx_json = {k: ctx.get(k) for k in _json_safe_keys}

    return {
        'expert': expert,
        'ctms_list': ctms_list,
        'my_ctc_requests': my_ctc_requests,
        'ctc_directory': ctc_directory,
        'dossiers': dossiers,
        'assignation_tasks': assignation_tasks,
        'ctc_ctx_json': ctc_ctx_json,
        'sidebar_pole': _SIDEBAR_POLE_MAP.get(ctx.get('ctc_pole'), ''),
        **ctx,
    }


# ─────────────────────────────────────────────────────────────────────────────
# VUE PRINCIPALE DU TABLEAU DE BORD CTC
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCDashboardView(View):
    """
    Tableau de bord principal pour les 20 membres de la Cellule Technique
    de Coordination / Secrétariat Technique.
    """
    template_name = 'ctc/app/app.html'

    def get(self, request):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        context = _ctc_shared_context(expert)
        if context is None:
            messages.info(
                request,
                "Vous n'êtes pas membre de la Cellule Technique de Coordination. "
                "Accédez à votre espace de travail habituel."
            )
            return redirect('web:app')

        return render(request, self.template_name, context)


# ─────────────────────────────────────────────────────────────────────────────
# VUE DEMANDE OPÉRATIONNELLE CTC (blocage intracellulaire)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCOperationalRequestView(View):
    """
    Soumet une demande d'ouverture de droits temporaires ou de transmission urgente.
    Routée vers l'Assistant Exécutif de la Direction des Opérations.
    """

    def post(self, request):
        expert = Expert.objects.filter(user=request.user).first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        if not CTCMembership.objects.filter(expert=expert).exists():
            return JsonResponse({'ok': False, 'error': 'Accès non autorisé.'}, status=403)

        resource = (request.POST.get('restricted_resource') or '').strip()
        reason   = (request.POST.get('reason') or '').strip()

        if not resource or not reason:
            return JsonResponse({'ok': False, 'error': 'Ressource et motif requis.'}, status=400)

        existing = CTCOperationalRequest.objects.filter(
            requester=expert, restricted_resource=resource, status='PENDING'
        ).first()
        if existing:
            return JsonResponse({
                'ok': True,
                'message': 'Une demande est déjà en cours de traitement.',
                'request_id': existing.id,
            })

        req = CTCOperationalRequest.objects.create(
            requester=expert, restricted_resource=resource, reason=reason
        )
        return JsonResponse({
            'ok': True,
            'message': "Votre demande a été transmise à l'Assistant Exécutif.",
            'request_id': req.id,
        })


# ─────────────────────────────────────────────────────────────────────────────
# VUE APPROBATION / REJET (Assistant Exécutif uniquement)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCApproveRequestView(View):
    """
    Approuve ou rejette une demande opérationnelle CTC.
    Réservée à l'Assistant Exécutif de la Direction des Opérations.
    """

    def post(self, request, pk):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        acronym  = (expert.structure.acronym or '').upper() if expert.structure else ''
        membership = CTCMembership.objects.filter(expert=expert).first()
        if not membership:
            return JsonResponse({'ok': False, 'error': 'Non membre CTC.'}, status=403)

        sub_role = _resolve_ctc_sub_role(membership.role, acronym)
        if sub_role != 'assistant_executif':
            return JsonResponse(
                {'ok': False, 'error': "Réservé à l'Assistant Exécutif de la Direction des Opérations."},
                status=403
            )

        req      = get_object_or_404(CTCOperationalRequest, pk=pk, status='PENDING')
        decision = (request.POST.get('decision') or '').strip().upper()
        comment  = (request.POST.get('comment') or '').strip()

        if decision not in ('APPROVED', 'REJECTED'):
            return JsonResponse({'ok': False, 'error': 'Décision invalide.'}, status=400)

        req.status      = decision
        req.reviewed_by = expert
        req.reviewed_at = timezone.now()
        req.review_comment = comment
        req.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_comment'])

        action = 'approuvée' if decision == 'APPROVED' else 'refusée'
        return JsonResponse({
            'ok': True,
            'message': f"Demande de {req.requester.full_name} {action}.",
            'new_status': decision,
        })


# ─────────────────────────────────────────────────────────────────────────────
# VUE MÉTHODOLOGIE & CHRONOGRAMME (ScheduleReview — Planificateur / Scientifique)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCMethodologyActionView(View):
    """
    Met à jour les notes et le statut de validation chronogramme (Planificateur)
    ou de validation scientifique (Conseiller Scientifique INBTP) d'un ScheduleReview.
    """

    def post(self, request, pk):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        membership = CTCMembership.objects.filter(expert=expert).first()
        if not membership:
            return JsonResponse({'ok': False, 'error': 'Non membre CTC.'}, status=403)

        acronym  = (expert.structure.acronym or '').upper() if expert.structure else ''
        sub_role = _resolve_ctc_sub_role(membership.role, acronym)

        review = get_object_or_404(ScheduleReview, pk=pk)
        notes  = (request.POST.get('notes') or '').strip()
        status = (request.POST.get('status') or '').strip().upper()

        valid_statuses = {choice[0] for choice in ScheduleReview.PLANNER_STATUS_CHOICES}
        if status not in valid_statuses:
            return JsonResponse({'ok': False, 'error': 'Statut invalide.'}, status=400)

        if sub_role == 'planification_recons':
            if review.planner_id != expert.id:
                return JsonResponse({'ok': False, 'error': "Ce dossier n'est pas assigné à votre poste."}, status=403)
            review.planner_notes = notes
            review.planner_status = status
            review.save(update_fields=['planner_notes', 'planner_status'])
        elif sub_role == 'scientifique_inbtp':
            if review.scientist_id != expert.id:
                return JsonResponse({'ok': False, 'error': "Ce dossier n'est pas assigné à votre poste."}, status=403)
            review.scientist_notes = notes
            review.scientist_status = status
            review.save(update_fields=['scientist_notes', 'scientist_status'])
        else:
            return JsonResponse(
                {'ok': False, 'error': "Réservé au pôle Analyse (Planification & Sciences)."},
                status=403
            )

        return JsonResponse({'ok': True, 'message': 'Enregistré avec succès.', 'status': status})


# ─────────────────────────────────────────────────────────────────────────────
# VUE API : CONTEXTE CTC JSON
# ─────────────────────────────────────────────────────────────────────────────

@login_required(login_url='/se-connecter/')
def ctc_context_api(request):
    """Retourne le contexte de privilèges CTC en JSON pour les composants JS."""
    expert = Expert.objects.filter(user=request.user).select_related('structure').first()
    if not expert:
        return JsonResponse({'is_ctc_member': False})

    ctx = get_ctc_context(expert)
    if not ctx:
        return JsonResponse({'is_ctc_member': False})

    payload = {k: v for k, v in ctx.items() if isinstance(v, (bool, str, int, list, type(None)))}
    return JsonResponse(payload)
