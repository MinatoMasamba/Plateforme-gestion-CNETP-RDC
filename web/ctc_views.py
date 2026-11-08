"""
Vues de compatibilité de l'ancien circuit CTC et de la Coordination du Secrétariat technique.

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
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.conf import settings
from django.urls import reverse

from apps.experts.models import Expert
from apps.governance.phoenix_runtime import active_st_mandate
from web.pilotage_views import get_pilotage_context
from apps.governance.models import (
    TechnicalCell, CTCMembership, CTCOperationalRequest,
    PilotageMembreship, PosteNominatifCTC, CTM, CTCProcessus, PlatformFreeze,
    Demande, JournalDemande, CopilRapport, WG, Tache,
)
from apps.mobileapp.signals import create_notification_for_user
from apps.validation.models import (
    ISOReview, EcologicalReview, EconomicReview,
    ScheduleReview, IndustrialConsultation, LegisticReview,
)
from apps.norms.models import Norme, NormeComment, NormeVersion


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

def _effective_ctc_sub_role(expert, role, acronym):
    mandate = active_st_mandate(expert)
    if mandate and mandate.poste.st_sub_role:
        return mandate.poste.st_sub_role
    # Pas de mandat Phoenix : repli sur l'adhésion CTC historique, dont le
    # rôle et la structure d'origine déterminent le pôle et l'interface.
    return _resolve_ctc_sub_role(role, acronym)


def _resolve_ctc_sub_role(ctc_role: str, acronym: str) -> str:
    """Dérive le sous-rôle précis à partir du rôle CTCMembership + acronyme structure."""
    role_map = _CTC_ROLE_STRUCTURE_TO_SUB.get(ctc_role)
    if not role_map:
        return ctc_role.lower()
    return role_map.get(acronym) or role_map.get(None) or ctc_role.lower()


def _initialize_ctc_reviews(norme):
    """Crée les examens CTC requis et les attribue aux postes disponibles."""
    simulation = norme.source_reference == 'SIMULATION — SANS VALEUR OFFICIELLE'

    def eligible_members(role):
        members = CTCMembership.objects.filter(role=role)
        if simulation:
            return members.filter(expert__user__username__endswith='@example.invalid')
        return members.exclude(expert__user__username__endswith='@example.invalid')

    assignments = {
        'legistic_review': (LegisticReview, 'legist', 'LEGAL', 'Examen légistique CTC'),
        'iso_review': (ISOReview, 'expert', 'ISO_EXPERT', 'Examen ISO / SADC'),
        'ecological_review': (EcologicalReview, 'expert', 'ENVIRONMENTAL', 'Examen environnemental et social'),
        'economic_review': (EconomicReview, 'expert', 'ECONOMIST', 'Évaluation économique'),
        'industrial_consultation': (IndustrialConsultation, 'expert', 'INDUSTRIAL', 'Consultation industrielle FEC'),
    }
    created = []
    for relation, (model, expert_field, membership_role, label) in assignments.items():
        member = (
            eligible_members(membership_role)
            .select_related('expert__user')
            .order_by('id')
            .first()
        )
        defaults = {'status': 'PENDING'}
        if member:
            defaults[expert_field] = member.expert
        review, was_created = model.objects.get_or_create(norme=norme, defaults=defaults)
        if member and not getattr(review, f'{expert_field}_id'):
            setattr(review, expert_field, member.expert)
            review.save(update_fields=[expert_field, 'updated_at'])
            was_created = True
        if was_created and member:
            create_notification_for_user(
                member.expert.user,
                f'{label} attribué',
                f'Le dossier {norme.reference_number} vous a été attribué dans le circuit CTC.',
                'SYSTEM',
                priority='HIGH',
                data={'norme_id': norme.id, 'review_id': review.id, 'review_type': relation},
            )
        created.append(review)

    schedule_member = {
        'planner': eligible_members('PLANNER').select_related('expert__user').order_by('id').first(),
        'scientist': eligible_members('SCIENTIFIC').select_related('expert__user').order_by('id').first(),
    }
    schedule, was_created = ScheduleReview.objects.get_or_create(
        norme=norme,
        defaults={
            'planner': schedule_member['planner'].expert if schedule_member['planner'] else None,
            'scientist': schedule_member['scientist'].expert if schedule_member['scientist'] else None,
            'planner_status': 'PENDING',
            'scientist_status': 'PENDING',
        },
    )
    changed_fields = []
    for field, member in schedule_member.items():
        if member and not getattr(schedule, f'{field}_id'):
            setattr(schedule, field, member.expert)
            changed_fields.append(field)
    if changed_fields:
        schedule.save(update_fields=changed_fields + ['updated_at'])
    for field, member in schedule_member.items():
        if (was_created or field in changed_fields) and member:
            create_notification_for_user(
                member.expert.user,
                'Examen chronogramme attribué',
                f'Le dossier {norme.reference_number} vous a été attribué pour validation {field}.',
                'SYSTEM',
                priority='HIGH',
                data={'norme_id': norme.id, 'review_id': schedule.id, 'review_type': 'schedule'},
            )
    return created + [schedule]


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
    mandate = active_st_mandate(expert)
    # Mandat Phoenix prioritaire ; à défaut, une adhésion CTC active suffit
    # (affectation admin immédiatement effective, interface legacy par rôle/pôle).
    if not membership and not mandate:
        return None

    role    = membership.role if membership else ''
    acronym = (expert.structure.acronym or '').upper() if expert.structure else ''

    sub_role = _effective_ctc_sub_role(expert, role, acronym)

    # ── Détermination du pôle ──────────────────────────────────────────────
    from apps.governance.st_matrix import ROLE_POLES, POLES
    # Avec un mandat Phoenix, le pôle est l'espace de la matrice ST v3 ;
    # sans mandat, on retombe sur les 4 pôles historiques dérivés du rôle CTC.
    pole = ROLE_POLES.get(sub_role, _pole_for_sub_role(sub_role)) if mandate else _pole_for_sub_role(sub_role)

    is_direction  = sub_role in _DIRECTION_SUBS
    is_analyse    = sub_role in _ANALYSE_SUBS
    is_logistique = sub_role in _LOGISTIQUE_SUBS
    is_numerique  = sub_role in _NUMERIQUE_SUBS

    # ── Poste de la matrice Phoenix (24 postes du ST), sinon ancien référentiel ──
    mandate = active_st_mandate(expert)
    poste = (
        mandate.poste if mandate
        else PosteNominatifCTC.objects.filter(holder=expert).select_related('required_structure').first()
    )

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
        'pole_label':    POLES.get(pole, 'Compétence d’examen' if pole == 'expertise' else POLE_LABELS.get(pole, 'Membre CTC')),
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

    from apps.governance.st_matrix import mandate_capabilities
    ctx.update(mandate_capabilities(mandate))

    sidebar_nav_config = {
        'principal': [
            {'view': 'dashboard', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
            {'view': 'dossiers', 'label': 'Dossiers normatifs', 'icon': 'folders'},
            {'view': 'assignations', 'label': 'Mes Assignations', 'icon': 'file-check'},
            {'view': 'ctc_requests', 'label': 'Demandes à Traiter', 'icon': 'send'},
        ],
        'system': [
            {'view': 'archives', 'label': 'Archives', 'icon': 'history'},
            {'view': 'parametres', 'label': 'Paramètres', 'icon': 'settings'},
        ],
        'pole': sub_role,
    }
    if ctx.get('can_grand_livre'):
        sidebar_nav_config['principal'] = [
            {'view': 'dashboard', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
            {'view': 'financial', 'label': 'Budget & Comptabilité', 'icon': 'banknote'},
            {'view': 'assignations', 'label': 'Mes Assignations', 'icon': 'file-check'},
            {'view': 'ctc_requests', 'label': 'Demandes à Traiter', 'icon': 'send'},
        ]
    elif sub_role == 'assistant_executif':
        sidebar_nav_config['principal'] = [
            {'view': 'dashboard', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
            {'view': 'assistant_executif', 'label': 'Assistant Exécutif', 'icon': 'inbox'},
            {'view': 'assignations', 'label': 'Mes Assignations', 'icon': 'file-check'},
        ]
    elif ctx.get('can_admin_system'):
        sidebar_nav_config['principal'] = [
            {'view': 'dashboard', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
            {'view': 'dossiers', 'label': 'Dossiers normatifs', 'icon': 'folders'},
            {'view': 'assignations', 'label': 'Mes Assignations', 'icon': 'file-check'},
            {'view': 'ctc_requests', 'label': 'Demandes à Traiter', 'icon': 'send'},
            {'view': 'drive', 'label': 'Espace Drive', 'icon': 'hard-drive'},
        ]
    sidebar_nav_config['principal'].append({'view': 'matrice_st', 'label': 'Organisation du ST', 'icon': 'network'})
    sidebar_nav_config['system'] = [
        {'view': 'archives', 'label': 'Archives', 'icon': 'history'},
        {'view': 'parametres', 'label': 'Paramètres', 'icon': 'settings'},
    ]
    sidebar_nav_config['supervision'] = [
        {'view': 'statistiques', 'label': 'Suivi statistique', 'icon': 'chart-no-axes-combined'},
        {'view': 'experts', 'label': 'Experts et affectations', 'icon': 'users'},
        {'view': 'tracabilite', 'label': 'Traçabilité', 'icon': 'scroll-text'},
        {'view': 'homologations', 'label': 'Homologations', 'icon': 'shield-check'},
    ]
    sidebar_nav_config['outils'] = [
        {'view': 'instructions', 'label': 'Instruction', 'icon': 'clipboard-list'},
        {'view': 'reunions', 'label': 'Réunions', 'icon': 'calendar-days'},
    ]
    ctx['sidebar_nav_config'] = sidebar_nav_config

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
    if ctx.get('st_can_follow'):
        visible_stages = [stage for stage, label in CTCProcessus.STAGE_CHOICES]
    elif ctx.get('st_matrix_v3') and ctx.get('can_fast_entry'):
        visible_stages = ['RECEPTION']
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

    # ── Verrouillage plateforme CTC/CTM (action souveraine du Président) ────
    freeze = PlatformFreeze.get_solo()
    ctx.update({
        'platform_locked':    freeze.is_locked,
        'platform_locked_by': freeze.locked_by.user.get_full_name() if freeze.locked_by else '',
        'platform_locked_at': freeze.locked_at,
    })

    from apps.governance.st_matrix import mandate_capabilities
    ctx.update(mandate_capabilities(mandate))

    if ctx.get('st_matrix_v3'):
        from apps.governance.st_spaces import space_context, audit_scope_for
        from apps.governance.st_workday import build_workday, build_space_dashboard
        from apps.governance.st_status import STATUS_CHOICES
        ctx.update(space_context(poste, ctx))
        ctx['st_audit_scope'] = sorted(audit_scope_for(poste))
        ctx['st_status_choices'] = STATUS_CHOICES
        ctx['st_workday'] = build_workday(expert, ctx)
        ctx['st_space_dashboard'] = build_space_dashboard(expert, ctx)
        # Menu de l'espace : 5 à 7 entrées de travail, puis les accès système.
        sidebar_nav_config = {
            'principal': ctx.get('st_space_menu', []),
            'supervision': [],
            'outils': [],
            'system': [
                {'view': 'parametres', 'label': 'Paramètres', 'icon': 'settings'},
            ],
        }
        ctx['sidebar_nav_config'] = sidebar_nav_config
    if not ctx.get('st_matrix_v3'):
        ctx['sidebar_nav_config'].setdefault('outils', []).append({'view': 'rapports', 'label': 'Rapports', 'icon': 'file-chart-column'})
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
    from apps.governance.models import CTCOperationalRequest
    ctx = get_ctc_context(expert)
    if ctx is None:
        return None

    # Ces préférences sont celles effectivement consultées par le service
    # de dispatch, et non un état local de l'interface.
    from apps.mobileapp.models import NotificationPreference
    ctx['ctc_notification_preferences'] = (
        NotificationPreference.objects.filter(user=expert.user).first()
        or NotificationPreference(user=expert.user)
    )
    ctx['ctc_backup_available'] = (
        ctx.get('can_admin_system')
        and settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3'
    )
    ctx['ctc_drive_credentials_present'] = all((
        settings.GDRIVE_CLIENT_ID,
        settings.GDRIVE_CLIENT_SECRET,
        settings.GDRIVE_REFRESH_TOKEN,
    ))
    ctx['ctc_drive_folder_configured'] = bool(settings.GDRIVE_ROOT_FOLDER_ID)
    from apps.documents.models import DriveSyncAttempt, DriveSyncSettings
    from apps.documents.drive_sync import candidate_count
    ctx['ctc_drive_sync_settings'] = (
        DriveSyncSettings.objects.filter(pk=1).first()
        or DriveSyncSettings(pk=1, include_adopted=True)
    )
    ctx['ctc_drive_candidate_count'] = candidate_count()
    ctx['ctc_drive_recent_attempts'] = DriveSyncAttempt.objects.order_by('-created_at')[:5]

    # CTMs pour le hub de routage (Direction) et la modale CTM
    ctms = CTM.objects.filter(number__in=range(1, 8)).prefetch_related('working_groups').order_by('number')
    ctms_list = [
        {
            'ctm': c,
            'wg_count': c.working_groups.count(),
            'member_count': c.affectations.count(),
            'normes_en_cours': list(
                c.normes.exclude(status='PUBLISHED')
                .select_related('wg')
                .order_by('wg__number', '-created_at')
            ),
            'normes_publiees': list(
                c.normes.filter(status='PUBLISHED')
                .select_related('wg')
                .order_by('-publication_date')
            ),
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
        m_sub_role = _effective_ctc_sub_role(m.expert, m.role, m_acronym)
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
    pilotage_ctx = get_pilotage_context(expert)
    ctc_processus_tasks = ctx.get('active_processus', [])
    for processus in ctc_processus_tasks:
        stage_label = processus.get_current_stage_display()
        assignation_tasks.append({
            'type_label': "Traitement CTC",
            'icon': 'file-search',
            'reference': processus.norme.reference_number,
            'title': processus.norme.title,
            'status_display': stage_label,
            'view_target': 'dossiers',
            'detail_url': reverse('web:ctc_norme_read', args=[processus.norme_id]),
            'anchor': None,
            'category': 'personnelle',
            'category_label': "Mes Assignations Personnelles",
            'source_label': "Norme votée puis reçue par la CTC",
        })

    # Compléments d'examen pour les rôles analytiques
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
            'view_target': 'dossiers',
            'detail_url': reverse('web:ctc_norme_read', args=[review.norme_id]),
            'anchor': meta['anchor'],
            'category': 'personnelle',
            'category_label': "Mes Assignations Personnelles",
            'source_label': "Examen analytique CTC",
        })

    if pilotage_ctx:
        for processus in pilotage_ctx.get('pending_pilotage_reception', []):
            assignation_tasks.append({
                'type_label': "Réception Pilotage",
                'icon': 'shield-check',
                'reference': processus.norme.reference_number,
                'title': processus.norme.title,
                'status_display': "En attente de réception par le Pilotage",
                'view_target': 'dossiers',
                'anchor': 'widget-pending-reception',
                'category': 'pilotage',
                'category_label': 'Mes Assignations Pilotage',
                'source_label': "Norme transmise au Pilotage après sortie CTC",
            })

    for item in ctx.get('my_external_assignments', []):
        assignation_tasks.append({
            'type_label': item.get('type_label', 'Assignation externe'),
            'icon': item.get('icon', 'users'),
            'reference': item.get('reference', ''),
            'title': item.get('title', ''),
            'status_display': item.get('status_display', 'En attente'),
            'view_target': item.get('view_target', 'dashboard'),
            'anchor': item.get('anchor'),
            'category': 'externe',
            'category_label': 'Mes Assignations à un Expert Extérieur',
            'source_label': "Expert extérieur",
        })

    for task in Tache.objects.filter(assigned_to=expert,
                                    status__in=['PLANNED', 'IN_PROGRESS', 'BLOCKED', 'ON_HOLD'])\
                             .select_related('norme', 'target_sc').order_by('due_date', 'pk'):
        assignation_tasks.append({
            'type_label': 'Tâche attribuée',
            'icon': 'clipboard-check',
            'reference': task.norme.reference_number if task.norme else '',
            'title': task.titre,
            'status_display': task.get_status_display(),
            'view_target': 'dossiers',
            'detail_url': reverse('web:ctc_norme_read', args=[task.norme_id]) if task.norme_id else None,
            'category': 'personnelle',
            'category_label': 'Tâche de mon poste',
            'source_label': f'Échéance {task.due_date:%d/%m/%Y}' if task.due_date else 'Échéance à fixer',
        })

    if ctx.get('st_matrix_v3'):
        from apps.governance.st_permissions import visible_tasks
        assignation_tasks = []
        for task in visible_tasks(expert, ctx).filter(status__in=[
            'PLANNED', 'IN_PROGRESS', 'BLOCKED', 'ON_HOLD',
        ]).select_related('norme', 'assigned_to__user').order_by('due_date', 'pk'):
            assignation_tasks.append({
                'type_label': 'Tâche attribuée', 'icon': 'clipboard-check',
                'reference': task.norme.reference_number if task.norme_id else '',
                'title': task.titre, 'status_display': task.get_status_display(),
                'view_target': 'assignations',
                'detail_url': reverse('web:ctc_norme_read', args=[task.norme_id]) if task.norme_id else None,
                'category': 'personnelle', 'category_label': 'Travaux de mon espace',
                'source_label': task.assigned_to.full_name if task.assigned_to_id else 'Sans titulaire',
            })

    # Pipeline complet des dossiers normatifs (vue "Dossiers Normatifs")
    dossiers = (
        CTCProcessus.objects
        .select_related('norme', 'norme__ctm', 'received_by__user')
        .order_by('-updated_at')
    )
    if ctx.get('st_matrix_v3'):
        from apps.governance.st_permissions import visible_processus
        dossiers = visible_processus(expert, ctx)
    from apps.governance.st_status import with_display_status
    for _processus in dossiers:
        with_display_status(_processus)
    catalogue_normes = (
        Norme.all_objects
        .select_related('ctm')
        .prefetch_related('organisation_bindings__sc')
        .order_by('reference_number', 'pk')
    )
    if ctx.get('st_matrix_v3'):
        catalogue_normes = catalogue_normes.filter(pk__in=dossiers.values('norme_id'))
    sc_tasks = list(Tache.objects.filter(target_sc__isnull=False, assigned_to__isnull=True)
                    .select_related('norme', 'target_sc').order_by('target_sc__code', 'norme__reference_number'))
    ctc_assigned = list(Tache.objects.filter(target_sc__isnull=False, assigned_to__isnull=False)
                        .select_related('assigned_to__user', 'norme', 'target_sc').order_by('pk'))
    if ctx.get('st_matrix_v3') and not ctx.get('st_is_supervisor'):
        from apps.governance.st_permissions import visible_tasks
        visible_ids = visible_tasks(expert, ctx).values_list('pk', flat=True)
        sc_tasks = [task for task in sc_tasks if task.pk in visible_ids]
        ctc_assigned = [task for task in ctc_assigned if task.pk in visible_ids]
    ctc_roles_by_expert = dict(CTCMembership.objects.filter(
        expert_id__in=[task.assigned_to_id for task in ctc_assigned]
    ).values_list('expert_id', 'role'))
    ctc_role_distribution = {}
    for task in ctc_assigned:
        role = ctc_roles_by_expert.get(task.assigned_to_id, 'À vérifier')
        ctc_role_distribution[role] = ctc_role_distribution.get(role, 0) + 1

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
        'blocked_political', 'st_matrix_v3', 'st_post_code', 'st_is_pole_head',
        'st_can_confirm', 'st_can_follow', 'st_can_manage_ptn', 'st_can_audit_st', 'st_can_audit_sc',
        'pending_ctc_requests_count', 'active_processus_count', 'my_pending_reviews_count',
        'platform_locked',
    )
    _json_safe_keys += ('st_space', 'st_space_label', 'st_space_home', 'st_audit_scope', 'st_allowed_views')
    ctc_ctx_json = {k: ctx.get(k) for k in _json_safe_keys}

    from web.ctc_statistics import build_ctc_statistics
    from web.ctc_experts import build_expert_directory, build_traceability
    from apps.governance.activity_supervision import activity_access_for
    ctc_statistics = build_ctc_statistics()
    expert_directory = build_expert_directory(expert)
    traceability = build_traceability(expert)
    ctc_activity_access = activity_access_for(expert.user)

    # ── Instructions CTC (onglet « Instruction ») ───────────────────────────
    from apps.governance.models import CopilRapport, Demande
    global_instruction = (
        Demande.objects.filter(type='INSTRUCTION', sous_commission__isnull=True, groupe__isnull=True)
        .select_related('emetteur__user')
        .order_by('-created_at').first()
    )
    ctms_instructions = []
    for ctm in ctms:
        last = (
            Demande.objects.filter(type='INSTRUCTION', sous_commission=ctm)
            .select_related('emetteur__user')
            .order_by('-created_at').first()
        )
        ctms_instructions.append({'ctm': ctm, 'last_instruction': last or global_instruction})
    copil_rapports = list(CopilRapport.objects.select_related('emetteur__user').order_by('-date_rapport', '-created_at'))

    from apps.governance.st_matrix import POSTS, POLES
    from apps.meetings.models import Reunion
    matrix_rows = [dict(number=n, pole=POLES[p], title=t, role=r, name=name, origin=o, head=h)
                   for n, p, t, r, name, o, h in POSTS]
    now = timezone.now()
    if ctx.get('st_matrix_v3'):
        from apps.governance.st_permissions import visible_meetings
        meeting_qs = visible_meetings(expert, ctx)
    else:
        meeting_qs = Reunion.objects.all()
    upcoming_meetings = list(meeting_qs.filter(date__gte=now).select_related(
        'organisateur__user', 'ctm', 'wg').order_by('date')[:12])
    is_st_space = ctx.get('st_space') == 'ST'
    is_p2_space = ctx.get('st_space') == 'ST-P2'
    indexation_queue = [
        p for p in dossiers
        if getattr(p, 'display_status', {}).get('code') in ('RAPPORT_RECU',)
    ][:30] if is_p2_space and ctx.get('can_fast_entry') else []
    coordination_queue = [
        p for p in dossiers
        if getattr(p, 'display_status', {}).get('code') in
        ('INDEXATION_TERMINEE', 'EXAMEN_EN_COURS', 'CONSOLIDATION_TERMINEE')
    ][:30] if is_st_space else []
    coordination_delays = [
        p for p in dossiers
        if p.received_at and not p.signed_out_at and (now - p.received_at).days >= 14
    ][:30] if is_st_space else []
    pending_ctc_requests_all = list(
        CTCOperationalRequest.objects.filter(status='PENDING')
        .select_related('requester__user', 'requester__structure').order_by('-created_at')[:30]
    ) if is_st_space else []
    from apps.governance.st_operations import visible_records
    ptn_records = list(
        visible_records(expert.user).filter(kind='PTN').select_related('created_by').order_by('-updated_at')[:60]
    ) if (is_p2_space and (ctx.get('st_can_manage_ptn') or ctx.get('st_is_pole_head'))) else []
    st_space_records = []
    if ctx.get('st_matrix_v3'):
        records = visible_records(expert.user).filter(pole=ctx.get('ctc_pole'))
        if ctx.get('ctc_pole') == 'ST-P2':
            records = records.filter(kind='PTN')
        st_space_records = records.prefetch_related('versions__confirmation').order_by('-updated_at')[:100]
    consolidation_queue = [
        p for p in dossiers
        if p.current_stage == 'MULTI_REVIEW' and not p.consolidation_completed_at
    ][:30] if (is_p2_space and ctx.get('st_is_pole_head')) else []
    ged_versions = list(
        NormeVersion.all_objects.select_related('norme', 'version_author').order_by('-created_at')[:100]
    ) if is_p2_space else []
    codification_norms = list(
        Norme.all_objects.select_related('ctm').order_by('reference_number')[:150]
    ) if is_p2_space else []
    reception_dossiers = []
    post6_dashboard = {}
    if ctx.get('st_post_code') == 'ST-V3-06':
        from apps.governance.st_admin_dashboard import dashboard
        post6_dashboard = dashboard(expert, ctx)
        from apps.governance.st_ged import tome_label

        reception_dossiers = list(
            dossiers.filter(norme__circuit_version='LEGACY')
            .select_related(
                'received_by__user', 'norme__wg', 'norme__ctm',
                'administrative_reception__sc', 'administrative_reception__group',
            )
            .prefetch_related('administrative_reception__pieces', 'ged_files', 'norme__versions')
        )
        for p in reception_dossiers:
            reception = getattr(p, 'administrative_reception', None)
            if reception and reception.sc_id:
                p.reception_tome = tome_label(reception.sc.code)
                p.reception_sc = reception.sc.code
            else:
                p.reception_tome = 'Tome à confirmer'
                p.reception_sc = 'SC à confirmer'
            if p.received_at:
                p.reception_state, p.reception_status = 'done', 'Réception enregistrée'
            elif reception and reception.state == 'ANOMALIE':
                p.reception_state, p.reception_status = 'anomaly', 'Anomalie signalée'
            elif reception:
                p.reception_state, p.reception_status = 'draft', 'Brouillon de réception'
            else:
                p.reception_state, p.reception_status = 'pending', 'À réceptionner'
            p.reception_group = (
                reception.group.name if reception and reception.group_id
                else (p.norme.wg.name if p.norme.wg_id else 'Groupe à confirmer')
            )
            p.reception_piece_count = len(reception.pieces.all()) if reception else 0
            p.reception_ged_count = len(p.ged_files.all())
            version = next(iter(p.norme.versions.all()), None)
            p.reception_version = f'v{version.version_number}' if version else '—'
    return {
        'post6_dashboard': post6_dashboard,
        'reception_dossiers': reception_dossiers,
        'reception_pending_count': sum(not p.received_at for p in reception_dossiers),
        'reception_done_count': sum(bool(p.received_at) for p in reception_dossiers),
        'reception_draft_count': sum(p.reception_state == 'draft' for p in reception_dossiers),
        'reception_anomaly_count': sum(p.reception_state == 'anomaly' for p in reception_dossiers),
        'upcoming_meetings': upcoming_meetings,
        'coordination_queue': coordination_queue,
        'indexation_queue': indexation_queue,
        'consolidation_queue': consolidation_queue,
        'ged_versions': ged_versions,
        'codification_norms': codification_norms,
        'coordination_delays': coordination_delays,
        'pending_ctc_requests_all': pending_ctc_requests_all,
        'ptn_records': ptn_records,
        'st_space_records': st_space_records,
        'st_matrix_rows': matrix_rows,
        'expert': expert,
        'ctms_list': ctms_list,
        'my_ctc_requests': my_ctc_requests,
        'ctc_directory': ctc_directory,
        'dossiers': dossiers,
        'catalogue_normes': catalogue_normes,
        'sc_tasks': sc_tasks,
        'ctc_assigned_count': len(ctc_assigned),
        'ctc_assigned_tasks': ctc_assigned,
        'ctc_account_name': expert.full_name or expert.user.username,
        'ctc_role_distribution': sorted(ctc_role_distribution.items()),
        'assignation_tasks': assignation_tasks,
        'ctc_statistics': ctc_statistics,
        'expert_directory': expert_directory,
        'traceability': traceability,
        'ctc_activity_access': ctc_activity_access,
        'ctc_can_view_task_sources': activity_access_for(expert.user)['can_view_contributions'],
        'dashboard_dossiers_count': dossiers.count(),
        'dashboard_assignations_count': len(assignation_tasks),
        'homologated_norms': Norme.all_objects.filter(status__in=['HOMOLOGATED', 'PUBLISHED']).order_by('-homologation_date', 'reference_number'),
        'archived_norms': Norme.all_objects.filter(status='ARCHIVED').order_by('-updated_at', 'reference_number'),
        'ctc_ctx_json': ctc_ctx_json,
        'sidebar_pole': POLES.get(ctx.get('ctc_pole')) or _SIDEBAR_POLE_MAP.get(ctx.get('ctc_pole'), ''),
        'global_instruction': global_instruction,
        'ctms_instructions': ctms_instructions,
        'copil_rapports': copil_rapports,
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

    def get(self, request, view=None):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        context = _ctc_shared_context(expert)
        if context is None:
            messages.info(
                request,
                "Vous ne faites pas partie de la Coordination du Secrétariat technique. "
                "Accédez à votre espace de travail habituel."
            )
            return redirect('web:app')

        if view:
            # Le filtrage par poste ne s'applique qu'aux espaces de la matrice
            # ST v3 ; les profils CTC historiques gardent leur navigation.
            if context.get('st_matrix_v3') and view not in context.get('st_allowed_views', []):
                return HttpResponse('Ce module ne relève pas de votre poste.', status=403)
            context['st_initial_view'] = view
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCCtmDetailView(View):
    """Vue détaillée d'un CTM pour les membres CTC."""

    template_name = 'ctc/ctm_detail.html'

    def get(self, request, number):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        priv = get_ctc_context(expert)
        if not priv or not priv.get('is_ctc_member'):
            messages.info(request, "Le détail des CTM est réservé aux membres de la CTC.")
            return redirect('web:ctc_dashboard')

        ctm = get_object_or_404(CTM, number=number)

        from web.ctc_statistics import _performance, _performance_color, _legacy_coordination
        from apps.governance.models import Tache
        from apps.norms.models import Norme

        wgs_with_stats = []
        for wg in ctm.working_groups.select_related(
            'president__user', 'rapporteur__user', 'secretary__user'
        ).order_by('number'):
            tasks = list(Tache.objects.filter(working_group=wg).select_related('norme').order_by('due_date', 'titre'))
            norms = list(Norme.all_objects.filter(wg=wg).order_by('title'))
            performance = _performance(tasks)
            wgs_with_stats.append({
                'wg': wg,
                'member_count': wg.affectations.count(),
                'performance': performance,
                'color': _performance_color(performance),
                'norms': norms,
            })

        affectations = (
            ctm.affectations
            .select_related('expert__user', 'expert__structure', 'wg')
            .order_by('wg__number', 'expert__user__last_name')
        )

        normes_en_cours = (
            ctm.normes.exclude(status='PUBLISHED')
            .select_related('wg')
            .prefetch_related('comments__author__user')
            .order_by('wg__number', '-created_at')
        )
        normes_publiees = (
            ctm.normes.filter(status='PUBLISHED')
            .select_related('wg')
            .order_by('-publication_date')
        )

        context = {
            'ctm': ctm,
            'coordination': _legacy_coordination(ctm),
            'wgs_with_stats': wgs_with_stats,
            'affectations': affectations,
            'normes_en_cours': normes_en_cours,
            'normes_publiees': normes_publiees,
            **priv,
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
        if PlatformFreeze.get_solo().is_locked:
            return JsonResponse(
                {'ok': False, 'error': "Plateforme verrouillée par le Président du Comité de Pilotage — action suspendue."},
                status=423
            )

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
        create_notification_for_user(
            expert.user,
            'Demande CTC transmise',
            f'Votre demande « {resource} » a été transmise à l\'Assistant Exécutif.',
            'SYSTEM',
            data={'request_id': str(req.id), 'status': 'PENDING', 'resource': resource},
        )
        for membership in CTCMembership.objects.select_related('expert__user', 'expert__structure'):
            member_acronym = (membership.expert.structure.acronym or '').upper() if membership.expert.structure else ''
            if _resolve_ctc_sub_role(membership.role, member_acronym) == 'assistant_executif':
                create_notification_for_user(
                    membership.expert.user,
                    'Nouvelle demande CTC',
                    f'{expert.full_name} demande l\'accès à « {resource} ».',
                    'SYSTEM',
                    priority='HIGH',
                    data={'request_id': str(req.id), 'status': 'PENDING', 'resource': resource},
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

    @transaction.atomic
    def post(self, request, pk):
        if PlatformFreeze.get_solo().is_locked:
            return JsonResponse(
                {'ok': False, 'error': "Plateforme verrouillée par le Président du Comité de Pilotage — action suspendue."},
                status=423
            )

        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        acronym  = (expert.structure.acronym or '').upper() if expert.structure else ''
        membership = CTCMembership.objects.filter(expert=expert).first()
        if not membership and not active_st_mandate(expert):
            return JsonResponse({'ok': False, 'error': 'Non membre CTC.'}, status=403)

        sub_role = _effective_ctc_sub_role(expert, membership.role if membership else '', acronym)
        if sub_role != 'assistant_executif':
            return JsonResponse(
                {'ok': False, 'error': "Réservé à l'Assistant Exécutif de la Direction des Opérations."},
                status=403
            )

        req      = get_object_or_404(CTCOperationalRequest.objects.select_for_update(), pk=pk, status='PENDING')
        decision = (request.POST.get('decision') or '').strip().upper()
        comment  = (request.POST.get('comment') or '').strip()

        if decision not in ('APPROVED', 'REJECTED') or not comment:
            return JsonResponse({'ok': False, 'error': 'Décision et commentaire obligatoires.'}, status=400)

        req.status      = decision
        req.reviewed_by = expert
        req.reviewed_at = timezone.now()
        req.review_comment = comment
        req.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_comment'])
        from apps.core.models import AuditLog
        AuditLog.objects.create(user=request.user, action='APPROVE' if decision == 'APPROVED' else 'REJECT',
            content_type='CTCOperationalRequest', object_id=req.pk, object_repr=str(req.pk),
            changes={'scope': 'ctc', 'decision': decision, 'comment': comment, 'permission_granted': False})

        create_notification_for_user(
            req.requester.user,
            'Décision sur votre demande CTC',
            f'Votre demande « {req.restricted_resource} » a été {"approuvée" if decision == "APPROVED" else "refusée"}.',
            'SYSTEM',
            priority='HIGH' if decision == 'APPROVED' else 'NORMAL',
            data={'request_id': str(req.id), 'status': decision, 'comment': comment},
        )

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
        if PlatformFreeze.get_solo().is_locked:
            return JsonResponse(
                {'ok': False, 'error': "Plateforme verrouillée par le Président du Comité de Pilotage — action suspendue."},
                status=423
            )

        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        membership = CTCMembership.objects.filter(expert=expert).first()
        if not membership and not active_st_mandate(expert):
            return JsonResponse({'ok': False, 'error': 'Non membre CTC.'}, status=403)

        acronym  = (expert.structure.acronym or '').upper() if expert.structure else ''
        sub_role = _effective_ctc_sub_role(expert, membership.role if membership else '', acronym)

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

        processus = CTCProcessus.objects.filter(norme=review.norme).first()
        reviews_completed = processus.check_all_reviews() if processus else False
        if reviews_completed:
            coordinators = (
                CTCMembership.objects
                .filter(role__in=('COORDINATOR', 'VICE_COORDINATOR'))
                .select_related('expert__user')
            )
            for coordinator in coordinators:
                create_notification_for_user(
                    coordinator.expert.user,
                    'Examens CTC terminés',
                    f'Les examens parallèles de {review.norme.reference_number} sont terminés. Le dossier peut passer à la consultation industrielle.',
                    'SYSTEM',
                    priority='HIGH',
                    data={'norme_id': review.norme_id, 'processus_id': processus.id, 'stage': 'INDUSTRIAL'},
                )

        return JsonResponse({
            'ok': True,
            'message': 'Enregistré avec succès.',
            'status': status,
            'current_stage': processus.current_stage if processus else None,
            'reviews_completed': reviews_completed,
        })


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCReviewActionView(View):
    """Enregistre l'acceptation ou le refus d'un examen analytique CTC."""

    REVIEW_CONFIG = {
        'iso': (ISOReview, 'veille_acgt', 'harmonization_notes'),
        'ecologique': (EcologicalReview, 'sauvegardes_ci', 'comments'),
        'economique': (EconomicReview, 'economiste_foner', 'comments'),
    }

    def post(self, request, review_type, pk):
        if PlatformFreeze.get_solo().is_locked:
            return JsonResponse({'ok': False, 'error': 'Plateforme verrouillée : action suspendue.'}, status=423)

        config = self.REVIEW_CONFIG.get(review_type)
        if not config:
            return JsonResponse({'ok': False, 'error': 'Type d’examen inconnu.'}, status=404)
        model, required_role, notes_field = config
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)
        membership = CTCMembership.objects.filter(expert=expert).first()
        if not membership and not active_st_mandate(expert):
            return JsonResponse({'ok': False, 'error': 'Non membre CTC.'}, status=403)
        acronym = (expert.structure.acronym or '').upper() if expert.structure else ''
        if _effective_ctc_sub_role(expert, membership.role if membership else '', acronym) != required_role:
            return JsonResponse({'ok': False, 'error': 'Action réservée au poste chargé de cet examen.'}, status=403)

        review = get_object_or_404(model.objects.select_related('norme'), pk=pk, expert=expert)
        processus = get_object_or_404(CTCProcessus, norme=review.norme)
        if processus.current_stage != 'MULTI_REVIEW':
            return JsonResponse({'ok': False, 'error': 'Le dossier n’est pas dans la phase des examens parallèles.'}, status=400)

        decision = (request.POST.get('status') or '').strip().upper()
        if decision not in {'APPROVED', 'REJECTED'}:
            return JsonResponse({'ok': False, 'error': 'Décision invalide.'}, status=400)
        setattr(review, 'status', decision)
        setattr(review, notes_field, (request.POST.get('feedback') or '').strip())
        review.review_start_date = review.review_start_date or timezone.now().date()
        review.review_end_date = timezone.now().date()
        review.save(update_fields=['status', notes_field, 'review_start_date', 'review_end_date', 'updated_at'])
        reviews_completed = processus.check_all_reviews()
        return JsonResponse({
            'ok': True,
            'message': 'Examen accepté.' if decision == 'APPROVED' else 'Examen refusé.',
            'status': decision,
            'current_stage': processus.current_stage,
            'reviews_completed': reviews_completed,
        })


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCIndustrialActionView(View):
    """Enregistre l'acceptation ou le refus de la consultation industrielle FEC."""

    def post(self, request, pk):
        if PlatformFreeze.get_solo().is_locked:
            return JsonResponse({'ok': False, 'error': 'Plateforme verrouillée : action suspendue.'}, status=423)

        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        membership = CTCMembership.objects.filter(expert=expert).first()
        if not membership and not active_st_mandate(expert):
            return JsonResponse({'ok': False, 'error': 'Non membre CTC.'}, status=403)
        acronym = (expert.structure.acronym or '').upper() if expert.structure else ''
        if _effective_ctc_sub_role(expert, membership.role if membership else '', acronym) != 'liaison_fec':
            return JsonResponse({'ok': False, 'error': 'Réservé à la liaison industrielle FEC.'}, status=403)

        review = get_object_or_404(IndustrialConsultation.objects.select_related('norme'), pk=pk, expert=expert)
        processus = get_object_or_404(CTCProcessus, norme=review.norme, current_stage='INDUSTRIAL')
        decision = (request.POST.get('status') or '').strip().upper()
        feedback = (request.POST.get('feedback') or '').strip()
        if decision not in {'APPROVED', 'REJECTED'}:
            return JsonResponse({'ok': False, 'error': 'Décision invalide.'}, status=400)

        review.status = decision
        review.fec_feedback = feedback
        review.review_end_date = timezone.now().date()
        review.save(update_fields=['status', 'fec_feedback', 'review_end_date', 'updated_at'])
        if decision == 'APPROVED':
            processus.industrial_completed_at = timezone.now()
            processus.save(update_fields=['industrial_completed_at', 'updated_at'])

        return JsonResponse({
            'ok': True,
            'message': 'Consultation industrielle acceptée.' if decision == 'APPROVED' else 'Consultation industrielle refusée.',
            'status': decision,
            'current_stage': processus.current_stage,
        })


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCTransmitPilotageView(View):
    """Transmet un dossier CTC réellement terminé au Comité de Pilotage."""

    def post(self, request, pk):
        if PlatformFreeze.get_solo().is_locked:
            return JsonResponse({'ok': False, 'error': 'Plateforme verrouillée : action suspendue.'}, status=423)

        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)
        membership = CTCMembership.objects.filter(expert=expert).first()
        if not membership and not active_st_mandate(expert):
            return JsonResponse({'ok': False, 'error': 'Non membre CTC.'}, status=403)
        acronym = (expert.structure.acronym or '').upper() if expert.structure else ''
        if _effective_ctc_sub_role(expert, membership.role if membership else '', acronym) not in {'coordonnateur_principal', 'coordonnateur_adjoint'}:
            return JsonResponse({'ok': False, 'error': 'Réservé au Coordonnateur Technique.'}, status=403)

        processus = get_object_or_404(CTCProcessus.objects.select_related('norme'), pk=pk)
        if processus.current_stage != 'INDUSTRIAL':
            return JsonResponse(
                {'ok': False, 'error': f"Le dossier est à l'étape {processus.get_current_stage_display()}, pas à l'étape industrielle."},
                status=400,
            )
        if not processus.all_reviews_completed:
            return JsonResponse({'ok': False, 'error': 'Tous les examens CTC doivent être acceptés avant la transmission.'}, status=400)
        if not processus.industrial_completed_at:
            return JsonResponse({'ok': False, 'error': 'La consultation industrielle FEC doit être acceptée avant la transmission.'}, status=400)
        if processus.signed_out_at:
            return JsonResponse({'ok': False, 'error': 'Dossier déjà transmis au Pilotage.'}, status=400)

        processus.mark_signed_out(expert)
        pilotage_members = (
            PilotageMembreship.objects
            .filter(role__in=('PRESIDENT', 'RAPPORTEUR'))
            .select_related('expert__user')
        )
        for member in pilotage_members:
            create_notification_for_user(
                member.expert.user,
                'Dossier transmis au Pilotage',
                f'{processus.norme.reference_number} a été signé et transmis par la CTC.',
                'SYSTEM',
                priority='HIGH',
                data={'norme_id': processus.norme_id, 'processus_id': processus.id, 'stage': 'SIGNED_OUT'},
            )

        return JsonResponse({
            'ok': True,
            'message': f'{processus.norme.reference_number} transmis au Comité de Pilotage.',
            'current_stage': processus.current_stage,
            'transmitted_at': processus.transmitted_to_pilotage_at.isoformat(),
        })


# ─────────────────────────────────────────────────────────────────────────────
# VUE ACTIONS ÉTAPE 1 — RÉCEPTION, NUMÉRISATION & CADRAGE (CTCProcessus)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCReceptionActionView(View):
    """
    Actions de l'Étape 1 du circuit CTCProcessus (Réception, Numérisation & Cadrage) :
    - Assistant Exécutif : enregistrement du dossier (mark_received)
    - Opérateurs de Saisie : fin de mise en page / indexation (mark_indexed)
    - Coordonnateur (Principal/Adjoint) : validation de l'introduction dans le circuit
      (mark_intake_validated → avance vers GEOSPATIAL ou MULTI_REVIEW)
    """

    @transaction.atomic
    def post(self, request, pk):
        if PlatformFreeze.get_solo().is_locked:
            return JsonResponse(
                {'ok': False, 'error': "Plateforme verrouillée par le Président du Comité de Pilotage — action suspendue."},
                status=423
            )

        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        membership = CTCMembership.objects.filter(expert=expert).first()
        if not membership and not active_st_mandate(expert):
            return JsonResponse({'ok': False, 'error': 'Non membre CTC.'}, status=403)

        acronym  = (expert.structure.acronym or '').upper() if expert.structure else ''
        sub_role = _effective_ctc_sub_role(expert, membership.role if membership else '', acronym)

        processus = get_object_or_404(CTCProcessus.objects.select_for_update(), pk=pk)
        if processus.current_stage != 'RECEPTION':
            return JsonResponse({'ok': False, 'error': "Ce dossier n'est plus à l'étape de Réception."}, status=400)

        action = (request.POST.get('action') or '').strip()
        context = get_ctc_context(expert) or {}
        if context.get('st_matrix_v3') and processus.norme.circuit_version != 'LEGACY':
            return JsonResponse({'ok': False, 'error': 'Utiliser le circuit Phoenix pour ce dossier.'}, status=400)
        if context.get('st_post_code') == 'ST-V3-06' and action == 'receive':
            return JsonResponse({'ok': False, 'error': 'Utiliser le formulaire de réception contrôlée avec vote et justificatifs.'}, status=400)
        if action == 'record_sc_report' and hasattr(processus, 'administrative_reception'):
            return JsonResponse({'ok': False, 'error': 'Joindre le rapport vérifié à la réception administrative existante.'}, status=400)
        if action == 'record_sc_report':
            if sub_role != 'assistant_executif' and not context.get('st_can_follow'):
                return JsonResponse({'ok': False, 'error': 'Réservé à la réception et au pôle 1.'}, status=403)
            reference = (request.POST.get('reference') or '').strip()
            if not processus.received_at or not reference or len(reference) > 500:
                return JsonResponse({'ok': False, 'error': 'Réception et référence du rapport obligatoires (500 caractères maximum).'}, status=400)
            if processus.sc_report_received_at:
                return JsonResponse({'ok': False, 'error': 'Rapport déjà enregistré.'}, status=409)
            processus.sc_report_reference = reference
            processus.sc_report_received_at = timezone.now()
            processus.sc_report_received_by = expert
            processus.save(update_fields=['sc_report_reference', 'sc_report_received_at', 'sc_report_received_by', 'updated_at'])
            from apps.core.models import AuditLog
            AuditLog.objects.create(user=request.user, action='UPDATE', content_type='CTCProcessus',
                object_id=processus.pk, object_repr=str(processus.norme.reference_number),
                changes={'scope': 'ctc', 'action': 'record_sc_report', 'reference': reference})
            return JsonResponse({'ok': True, 'message': 'Référence du rapport de SC enregistrée.'})
        if context.get('st_matrix_v3') and action in ('index', 'validate_intake') and not processus.sc_report_received_at:
            return JsonResponse({'ok': False, 'error': 'Le rapport de revue de la sous-commission doit être déposé avant l’indexation et les examens.'}, status=400)

        if action == 'receive':
            if sub_role != 'assistant_executif':
                return JsonResponse({'ok': False, 'error': "Réservé à l'Assistant Exécutif."}, status=403)
            if processus.received_at:
                return JsonResponse({'ok': False, 'error': 'Dossier déjà enregistré.'}, status=400)
            processus.mark_received(expert)
            message = "Dossier enregistré et réceptionné."

        elif action == 'index':
            if context.get('st_matrix_v3'):
                return JsonResponse({'ok': False, 'error': 'Utiliser l’espace GED : rapport réel, code autorisé, fichier et version sont obligatoires.'}, status=400)
            if not get_ctc_context(expert).get('can_fast_entry'):
                return JsonResponse({'ok': False, 'error': "Réservé aux Opérateurs de Saisie."}, status=403)
            if not processus.received_at:
                return JsonResponse({'ok': False, 'error': "Le dossier doit d'abord être réceptionné par l'Assistant Exécutif."}, status=400)
            if processus.indexed_at:
                return JsonResponse({'ok': False, 'error': 'Mise en page et indexation déjà finalisées.'}, status=400)
            processus.mark_indexed()
            message = "Mise en page et indexation finalisées."

        elif action == 'validate_intake':
            if sub_role not in ('coordonnateur_principal', 'coordonnateur_adjoint'):
                return JsonResponse({'ok': False, 'error': "Réservé au Coordonnateur Technique (Principal/Adjoint)."}, status=403)
            if context.get('st_matrix_v3'):
                from apps.governance.st_ged import confirmed_for_intake, report_for
                if not report_for(processus) or not confirmed_for_intake(processus):
                    return JsonResponse({'ok': False, 'error': 'Pièce du rapport de SC et confirmation documentaire du pôle 2 requises.'}, status=400)
            if not processus.indexed_at:
                return JsonResponse({'ok': False, 'error': "L'indexation du dossier doit d'abord être finalisée par les Opérateurs de Saisie."}, status=400)
            if processus.intake_validated_at:
                return JsonResponse({'ok': False, 'error': 'Introduction dans le circuit déjà validée.'}, status=400)
            processus.mark_intake_validated(expert)
            _initialize_ctc_reviews(processus.norme)
            message = f"Dossier validé — transmis à l'étape « {processus.get_current_stage_display()} »."

        else:
            return JsonResponse({'ok': False, 'error': 'Action invalide.'}, status=400)

        return JsonResponse({
            'ok': True,
            'message': message,
            'current_stage': processus.current_stage,
            'current_stage_display': processus.get_current_stage_display(),
            'received_at': processus.received_at.isoformat() if processus.received_at else None,
            'indexed_at': processus.indexed_at.isoformat() if processus.indexed_at else None,
            'intake_validated_at': processus.intake_validated_at.isoformat() if processus.intake_validated_at else None,
        })


# ─────────────────────────────────────────────────────────────────────────────
# DÉCISIONS ST v3 — CONSOLIDATION, VALIDATION, RENVOI
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCConsolidationActionView(View):
    """Consolidation des avis par le chef du pôle 2, sans décision finale."""

    @transaction.atomic
    def post(self, request, pk):
        from apps.core.models import AuditLog
        if PlatformFreeze.get_solo().is_locked:
            return JsonResponse({'ok': False, 'error': 'Plateforme verrouillée.'}, status=423)
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        context = get_ctc_context(expert) if expert else None
        if not context or not context.get('st_is_pole_head') or context.get('ctc_pole') != 'ST-P2':
            return JsonResponse({'ok': False, 'error': 'Consolidation réservée au chef du pôle 2.'}, status=403)
        comment = (request.POST.get('comment') or '').strip()
        if not comment:
            return JsonResponse({'ok': False, 'error': 'Le commentaire de consolidation est obligatoire.'}, status=400)
        processus = get_object_or_404(CTCProcessus.objects.select_for_update().select_related('norme'), pk=pk)
        if processus.norme.circuit_version != 'LEGACY':
            return JsonResponse({'ok': False, 'error': 'Utiliser le circuit Phoenix pour ce dossier.'}, status=400)
        if processus.current_stage not in ('MULTI_REVIEW', 'INDUSTRIAL') or not processus.all_reviews_completed:
            return JsonResponse({'ok': False, 'error': 'Les examens requis doivent être terminés avant la consolidation.'}, status=400)
        if processus.consolidation_completed_at:
            return JsonResponse({'ok': False, 'error': 'Consolidation déjà enregistrée.'}, status=409)
        processus.consolidation_completed_by = expert
        processus.consolidation_completed_at = timezone.now()
        processus.validation_comment = comment
        processus.save(update_fields=['consolidation_completed_by', 'consolidation_completed_at', 'validation_comment', 'updated_at'])
        AuditLog.objects.create(user=request.user, action='UPDATE', content_type='CTCProcessus',
            object_id=processus.pk, object_repr=str(processus.norme.reference_number),
            changes={'scope': 'ctc', 'action': 'consolidate', 'comment': comment})
        return JsonResponse({'ok': True, 'message': 'Consolidation enregistrée et versée au dossier.'})


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCValidationActionView(View):
    """Validation ou renvoi par un coordonnateur, avec commentaire obligatoire."""

    @transaction.atomic
    def post(self, request, pk):
        from apps.core.models import AuditLog
        if PlatformFreeze.get_solo().is_locked:
            return JsonResponse({'ok': False, 'error': 'Plateforme verrouillée.'}, status=423)
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        context = get_ctc_context(expert) if expert else None
        if not context or context.get('ctc_sub_role') not in ('coordonnateur_principal', 'coordonnateur_adjoint'):
            return JsonResponse({'ok': False, 'error': 'Validation réservée aux coordonnateurs.'}, status=403)
        action = (request.POST.get('action') or '').strip()
        comment = (request.POST.get('comment') or '').strip()
        if action not in ('validate', 'return') or not comment:
            return JsonResponse({'ok': False, 'error': 'Action et commentaire obligatoires.'}, status=400)
        processus = get_object_or_404(CTCProcessus.objects.select_for_update().select_related('norme'), pk=pk)
        if processus.norme.circuit_version != 'LEGACY':
            return JsonResponse({'ok': False, 'error': 'Utiliser le circuit Phoenix pour ce dossier.'}, status=400)
        if processus.validated_at or processus.returned_to_sc_at:
            return JsonResponse({'ok': False, 'error': 'Une décision existe déjà. Une reprise explicite du dossier est requise.'}, status=409)
        if action == 'validate':
            if not processus.received_at or not processus.indexed_at or not processus.sc_report_received_at:
                return JsonResponse({'ok': False, 'error': 'Réception, rapport de SC et indexation requis avant validation.'}, status=400)
            from apps.governance.st_ged import confirmed_for_intake, report_for
            if context.get('st_matrix_v3') and (not report_for(processus) or not confirmed_for_intake(processus)):
                return JsonResponse({'ok': False, 'error': 'Pièce du rapport de SC et confirmation documentaire du pôle 2 requises.'}, status=400)
            if processus.current_stage == 'RECEPTION' and not processus.intake_validated_at:
                processus.mark_intake_validated(expert)
            else:
                if not processus.intake_validated_at or not processus.all_reviews_completed or not processus.consolidation_completed_at:
                    return JsonResponse({'ok': False, 'error': 'Entrée validée, examens terminés et consolidation requis avant la décision finale.'}, status=400)
                # Le commentaire du pôle 1 n'a pas encore de circuit persistant.
                # Ne pas présenter une validation incomplète comme conforme.
                return JsonResponse({'ok': False, 'error': 'Le circuit de commentaire du chef du pôle 1 doit être raccordé avant la validation finale.'}, status=409)
            message = 'Dossier validé.'
        else:
            processus.returned_to_sc_by = expert
            processus.returned_to_sc_at = timezone.now()
            processus.validated_at = None
            processus.validated_by = None
            processus.validation_comment = comment
            processus.save(update_fields=['returned_to_sc_by', 'returned_to_sc_at', 'validated_at',
                'validated_by', 'validation_comment', 'updated_at'])
            message = 'Dossier renvoyé à la sous-commission.'
        AuditLog.objects.create(user=request.user, action='UPDATE', content_type='CTCProcessus',
            object_id=processus.pk, object_repr=str(processus.norme.reference_number),
            changes={'scope': 'ctc', 'action': action, 'comment': comment})
        return JsonResponse({'ok': True, 'message': message})


# ─────────────────────────────────────────────────────────────────────────────
# VUE LECTURE NORMALE CTC
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class CTCNormeReadView(View):
    """
    Page de lecture d'une norme reçue par la CTC.
    Affiche le texte, les versions et le contexte du dossier sans permettre d'édition.
    """

    template_name = 'ctc/app/norme_read.html'

    def get(self, request, pk):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        membership = CTCMembership.objects.filter(expert=expert).first()
        if not membership and not active_st_mandate(expert):
            messages.info(request, "Accès réservé aux membres de la CTC.")
            return redirect('web:app')

        mandate = active_st_mandate(expert)
        if mandate:
            from apps.governance.st_matrix import mandate_capabilities
            from apps.governance.st_spaces import space_context
            from apps.governance.st_permissions import visible_processus
            ctx = {**mandate_capabilities(mandate), **space_context(mandate.poste),
                   'poste': mandate.poste, 'ctc_pole': mandate.poste.organe.code}
            if not visible_processus(expert, ctx).filter(norme_id=pk).exists():
                return HttpResponse('Ce dossier ne relève pas de votre poste.', status=403)

        norme = get_object_or_404(
            Norme.all_objects.select_related('ctm', 'wg'),
            pk=pk,
        )
        processus = (
            CTCProcessus.objects
            .filter(norme=norme)
            .select_related('received_by', 'received_by__structure')
            .first()
        )
        versions = (
            NormeVersion.all_objects.filter(norme=norme)
            .select_related('version_author')
            .order_by('-version_number')[:8]
        )
        latest_version = versions[0] if versions else None
        if request.GET.get('version'):
            latest_version = get_object_or_404(
                NormeVersion.all_objects.select_related('version_author'),
                norme=norme, pk=request.GET['version'] if request.GET['version'].isdigit() else 0,
            )
        comments = (
            NormeComment.objects
            .filter(norme=norme)
            .select_related('author', 'author__structure')
            .order_by('-created_at')[:10]
        )

        return render(request, self.template_name, {
            'expert': expert,
            'norme': norme,
            'processus': processus,
            'latest_version': latest_version,
            'ged_entry': getattr(latest_version,'ged_indexation',None) if latest_version else None,
            'versions': versions,
            'comments': comments,
        })


# ─────────────────────────────────────────────────────────────────────────────
# QR DE TRAÇABILITÉ D'UNE NORME (pied de page du lecteur CTC)
# ─────────────────────────────────────────────────────────────────────────────

@login_required(login_url='/se-connecter/')
def ctc_norme_qr_view(request, pk):
    """Génère un QR code PNG encodant le lien de lecture + la référence de la norme."""
    norme = get_object_or_404(Norme, pk=pk)
    base = (settings.SITE_URL or '').rstrip('/')
    payload = f"{base}/ctc/norme/{norme.id}/lecture/ | {norme.reference_number}"

    try:
        import qrcode
        from io import BytesIO

        img = qrcode.make(payload)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return HttpResponse(buffer.getvalue(), content_type='image/png')
    except Exception:
        # Repli : QR minimal en SVG si la librairie n'est pas disponible.
        return HttpResponse(status=204)


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


# ─────────────────────────────────────────────────────────────────────────────
# INSTRUCTIONS CTC (onglet « Instruction »)
# ─────────────────────────────────────────────────────────────────────────────

@login_required(login_url='/se-connecter/')
def ctc_instruction_create(request):
    """Crée une instruction de production (globale ou pour un CTM précis)."""
    expert = Expert.objects.filter(user=request.user).select_related('structure').first()
    if not expert:
        return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)
    if not CTCMembership.objects.filter(expert=expert).exists():
        return JsonResponse({'ok': False, 'error': 'Accès réservé aux membres de la CTC.'}, status=403)
    if PlatformFreeze.get_solo().is_locked:
        return JsonResponse({'ok': False, 'error': 'Plateforme verrouillée.'}, status=423)

    objet = (request.POST.get('objet') or '').strip()
    message = (request.POST.get('message') or '').strip()
    if not objet and not message:
        return JsonResponse({'ok': False, 'error': "Le texte de l'instruction est requis."}, status=400)

    ctm_id = (request.POST.get('ctm_id') or '').strip()
    ctm = CTM.objects.filter(pk=ctm_id).first() if ctm_id.isdigit() else None

    nb_normes = request.POST.get('nb_normes') or ''
    nb_normes = int(nb_normes) if nb_normes.isdigit() else None
    echeance = parse_date(request.POST.get('echeance') or '') if (request.POST.get('echeance') or '').strip() else None

    demande = Demande.objects.create(
        type='INSTRUCTION',
        emetteur=expert,
        sous_commission=ctm,
        objet=objet or message[:120],
        message=message or objet,
        echeance=echeance,
        nb_normes=nb_normes,
        province=(request.POST.get('province') or '').strip(),
        commune=(request.POST.get('commune') or '').strip(),
        territoire=(request.POST.get('territoire') or '').strip(),
        district=(request.POST.get('district') or '').strip(),
        quartier=(request.POST.get('quartier') or '').strip(),
        avenue_rue=(request.POST.get('avenue_rue') or '').strip(),
        statut='ENVOYEE',
        created_by=request.user,
        updated_by=request.user,
    )
    JournalDemande.objects.create(
        demande=demande, statut_avant='', statut_apres='ENVOYEE', acteur=expert, commentaire='Création'
    )

    scope = f"CTM {ctm.number} — {ctm.name}" if ctm else "toutes les sous-commissions"
    return JsonResponse({'ok': True, 'message': f'Instruction envoyée à {scope}.', 'demande_id': demande.id})


@login_required(login_url='/se-connecter/')
def ctc_copil_rapport(request, pk=None):
    """Affiche le rapport COPIL au format A4 (lecture, multi-pages par défilement)."""
    if pk:
        rapport = get_object_or_404(CopilRapport, pk=pk)
    else:
        rapport = CopilRapport.objects.select_related('emetteur__user').order_by('-date_rapport', '-created_at').first()

    return render(request, 'ctc/copil_rapport.html', {'rapport': rapport})
