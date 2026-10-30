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
    if sub_role == 'gaf':
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
    elif sub_role in {'it_btc', 'it_sg_itp'}:
        sidebar_nav_config['principal'] = [
            {'view': 'dashboard', 'label': 'Tableau de bord', 'icon': 'layout-dashboard'},
            {'view': 'dossiers', 'label': 'Dossiers normatifs', 'icon': 'folders'},
            {'view': 'assignations', 'label': 'Mes Assignations', 'icon': 'file-check'},
            {'view': 'ctc_requests', 'label': 'Demandes à Traiter', 'icon': 'send'},
            {'view': 'drive', 'label': 'Espace Drive', 'icon': 'hard-drive'},
        ]
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

    # Pipeline complet des dossiers normatifs (vue "Dossiers Normatifs")
    dossiers = (
        CTCProcessus.objects
        .select_related('norme', 'norme__ctm', 'received_by__user')
        .order_by('-updated_at')
    )
    catalogue_normes = (
        Norme.all_objects
        .select_related('ctm')
        .prefetch_related('organisation_bindings__sc')
        .order_by('reference_number', 'pk')
    )
    sc_tasks = list(Tache.objects.filter(target_sc__isnull=False, assigned_to__isnull=True)
                    .select_related('norme', 'target_sc').order_by('target_sc__code', 'norme__reference_number'))
    ctc_assigned = list(Tache.objects.filter(target_sc__isnull=False, assigned_to__isnull=False)
                        .select_related('assigned_to__user', 'norme', 'target_sc').order_by('pk'))
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
        'blocked_political',
        'pending_ctc_requests_count', 'active_processus_count', 'my_pending_reviews_count',
        'platform_locked',
    )
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

    return {
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
        'sidebar_pole': _SIDEBAR_POLE_MAP.get(ctx.get('ctc_pole'), ''),
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

    def get(self, request):
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
        if not membership:
            return JsonResponse({'ok': False, 'error': 'Non membre CTC.'}, status=403)
        acronym = (expert.structure.acronym or '').upper() if expert.structure else ''
        if _resolve_ctc_sub_role(membership.role, acronym) != required_role:
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
        if not membership:
            return JsonResponse({'ok': False, 'error': 'Non membre CTC.'}, status=403)
        acronym = (expert.structure.acronym or '').upper() if expert.structure else ''
        if _resolve_ctc_sub_role(membership.role, acronym) != 'liaison_fec':
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
        if not membership:
            return JsonResponse({'ok': False, 'error': 'Non membre CTC.'}, status=403)
        acronym = (expert.structure.acronym or '').upper() if expert.structure else ''
        if _resolve_ctc_sub_role(membership.role, acronym) not in {'coordonnateur_principal', 'coordonnateur_adjoint'}:
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
        if not membership:
            return JsonResponse({'ok': False, 'error': 'Non membre CTC.'}, status=403)

        acronym  = (expert.structure.acronym or '').upper() if expert.structure else ''
        sub_role = _resolve_ctc_sub_role(membership.role, acronym)

        processus = get_object_or_404(CTCProcessus, pk=pk)
        if processus.current_stage != 'RECEPTION':
            return JsonResponse({'ok': False, 'error': "Ce dossier n'est plus à l'étape de Réception."}, status=400)

        action = (request.POST.get('action') or '').strip()

        if action == 'receive':
            if sub_role != 'assistant_executif':
                return JsonResponse({'ok': False, 'error': "Réservé à l'Assistant Exécutif."}, status=403)
            if processus.received_at:
                return JsonResponse({'ok': False, 'error': 'Dossier déjà enregistré.'}, status=400)
            processus.mark_received(expert)
            message = "Dossier enregistré et réceptionné."

        elif action == 'index':
            if sub_role != 'operateur_saisie':
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
        if not membership:
            messages.info(request, "Accès réservé aux membres de la CTC.")
            return redirect('web:app')

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
