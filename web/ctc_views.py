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


# ─────────────────────────────────────────────────────────────────────────────
# RÉSOLUTION DU SOUS-RÔLE
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_ctc_sub_role(ctc_role: str, acronym: str) -> str:
    """Dérive le sous-rôle précis à partir du rôle CTCMembership + acronyme structure."""
    role_map = _CTC_ROLE_STRUCTURE_TO_SUB.get(ctc_role)
    if not role_map:
        return ctc_role.lower()
    return role_map.get(acronym) or role_map.get(None) or ctc_role.lower()


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
    pole = (
        'direction'  if sub_role in _DIRECTION_SUBS  else
        'analyse'    if sub_role in _ANALYSE_SUBS    else
        'logistique' if sub_role in _LOGISTIQUE_SUBS else
        'numerique'  if sub_role in _NUMERIQUE_SUBS  else
        'membre'
    )

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
        my_pending_reviews = list(
            model_cls.objects
            .filter(**{field: expert, 'status__in': ['PENDING', 'ASSIGNED', 'IN_REVIEW']})
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
# VUE PRINCIPALE DU TABLEAU DE BORD CTC
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCDashboardView(View):
    """
    Tableau de bord principal pour les 20 membres de la Cellule Technique
    de Coordination / Secrétariat Technique.
    """
    template_name = 'ctc/dashboard.html'

    def get(self, request):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        ctx = get_ctc_context(expert)
        if not ctx:
            messages.info(
                request,
                "Vous n'êtes pas membre de la Cellule Technique de Coordination. "
                "Accédez à votre espace de travail habituel."
            )
            return redirect('web:app')

        # CTMs pour le hub de routage (Direction)
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

        context = {
            'expert': expert,
            'ctms_list': ctms_list,
            'my_ctc_requests': my_ctc_requests,
            **ctx,
        }
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
