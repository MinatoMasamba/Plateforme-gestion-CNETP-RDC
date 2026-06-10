"""
Vues dynamiques du Comité de Pilotage Élargi (27 postes).

Logique : chaque expert du Comité de Pilotage se voit attribuer un `pilotage_sub_role`
dérivé de son rôle PilotageMembreship ET de l'acronyme de sa structure d'origine.
Ce sous-rôle alimente des booléens de privilèges injectés dans le contexte du template,
qui masque ou déverrouille les modules en conséquence.

4 collèges — 4 profils de privilèges :
  Profil 1 — Bureau Directoire          (5 postes)
  Profil 2 — Conseillers Institutionnels (12 postes)
  Profil 3 — Administrateurs Tech. & Fin.(5 postes)
  Profil 4 — Partenaires & Société Civile(5 postes)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from apps.experts.models import Expert
from apps.governance.models import (
    ComitePilotage, PilotageMembreship, PosteNominatif,
    CTM, WG, PermissionRequest, CTCProcessus, NormeCadrage,
)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES DE MAPPAGE STRUCTURE → SOUS-RÔLE
# ─────────────────────────────────────────────────────────────────────────────

# Structures dont l'acronyme (en majuscules) détermine un sous-rôle spécialisé
# pour les collèges ATF et Partenaires.
_STRUCTURE_ACRONYM_TO_SUB = {
    # Collège ATF (5 postes)
    'FONER': 'foner',
    'BTC':   'btc',
    'OVD':   'ovd',
    'OR':    'atf_or',
    'ACGT':  'acgt',
    # Collège Partenaires (5 postes)
    'FEC':   'fec',
    'OCC':   'occ',
    'SCOT':  'occ',  # Poste 27 : structure réelle en base = SCOT (OCC n'existe pas comme acronyme distinct)
    'ONA':   'ona',
    'BEAU':  'beau',
}

# Rôles du Bureau Directoire
_DIRECTOIRE_ROLES = {'PRESIDENT', 'VICE_PRESIDENT', 'SECRETARY', 'RAPPORTEUR'}


def _vp_sub_role_from_title(poste_title_lower: str) -> str:
    """
    Distingue le 1er Vice-Président (ONIC, giron Ingénierie) du 2nd
    Vice-Président (AIBTP/CNIRS-BTP, giron Construction) à partir de
    l'intitulé exact de leur PosteNominatif (Manuel Organisationnel 2026).
    """
    return 'vice_president_onic' if 'onic' in poste_title_lower else 'vice_president_btp'


# Cadrage Bureau Directoire (NormeCadrage) : pour chaque sous-rôle du Directoire,
# liste des (current_stage, action, libellé) représentant une action en attente.
_CADRAGE_ACTIONS_BY_SUBROLE = {
    'president': [
        ('PROPOSED', 'open', "Phase 1.1 — Ouvrir le chantier (orientation stratégique)"),
        ('FINAL_VALIDATION', 'final_validate', "Phase 2.3 — Validation finale & signature de la résolution"),
    ],
    'vice_president_onic': [
        ('EXPERTS_REVIEW', 'validate_onic', "Phase 1.2 — Valider les experts WG (giron Ingénierie)"),
        ('CONFORMITY_QUITUS', 'quitus_onic', "Phase 2.2 — Quitus de conformité technique"),
    ],
    'vice_president_btp': [
        ('EXPERTS_REVIEW', 'validate_btp', "Phase 1.2 — Valider le mandat des experts WG (secteur BTP)"),
        ('CONFORMITY_QUITUS', 'quitus_btp', "Phase 2.2 — Quitus de conformité technique"),
    ],
    'secretary': [
        ('MANDATE_FORMALIZATION', 'formalize_mandate', "Phase 1.3 — Formaliser le mandat opérationnel"),
        ('PV_VERIFICATION', 'verify_pv', "Phase 2.1 — Vérifier le PV de l'Assemblée Plénière"),
    ],
    'rapporteur': [
        ('SCHEDULED', 'schedule', "Phase 1.4 — Chronogramme & ordre de service à la CTC"),
    ],
}

# Pour les étapes à double validateur, champ à vérifier pour exclure les
# cadrages déjà traités par CET acteur précis (l'autre VP doit encore agir).
_CADRAGE_ACTION_EXCLUDE_FIELD = {
    'validate_onic': 'onic_validated_at',
    'validate_btp':  'btp_validated_at',
    'quitus_onic':   'onic_quitus_at',
    'quitus_btp':    'btp_quitus_at',
}

# CTMs couverts par chaque spécialiste ATF (accès privilégié sans demande de permission)
_ATF_SPECIALTY_CTM = {
    'atf_or': [1],        # Office des Routes → CTM 1 Géotechnique/Chaussées
    'ovd':    [7],        # OVD → CTM 7 Assainissement & Macro-drainage
    'acgt':   [1, 2, 3],  # ACGT → CTM 1 à 3 (Normes & Innovation)
    'btc':    list(range(1, 9)),  # BTC a un contrôle transverse sur tous les CTM
    'foner':  [],         # FONER : rôle financier, pas de CTM direct
}

# Libellés des collèges pour l'interface
COLLEGE_LABELS = {
    'directoire':          'Bureau Directoire',
    'conseiller_politique': 'Collège des Conseillers Institutionnels et Politiques',
    'atf':                 'Collège des Administrateurs Techniques et Financiers',
    'partenaire':          'Collège des Partenaires Sectoriels et de la Société Civile',
}

COLLEGE_BADGE_COLORS = {
    'directoire':          'bg-amber-500/15 text-amber-400 border-amber-500/30',
    'conseiller_politique': 'bg-blue-500/15 text-blue-400 border-blue-500/30',
    'atf':                 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    'partenaire':          'bg-purple-500/15 text-purple-400 border-purple-500/30',
}


# ─────────────────────────────────────────────────────────────────────────────
# MOTEUR DE PRIVILÈGES
# ─────────────────────────────────────────────────────────────────────────────

def get_pilotage_context(expert: Expert) -> dict | None:
    """
    Calcule et retourne le dictionnaire complet de contexte de privilèges
    pour un expert membre du Comité de Pilotage.

    Retourne None si l'expert n'est pas membre du Comité de Pilotage.
    """
    membership = (
        PilotageMembreship.objects
        .filter(expert=expert)
        .select_related('comite')
        .first()
    )
    if not membership:
        return None

    role = membership.role  # ex: 'PRESIDENT', 'ADMIN_TECH_FIN', …
    acronym = (expert.structure.acronym or '').upper() if expert.structure else ''

    # ── Détermination du collège ──────────────────────────────────────────────
    is_directoire = role in _DIRECTOIRE_ROLES
    is_conseiller = role == 'CONSEILLER_POLITIQUE'
    is_atf        = role == 'ADMIN_TECH_FIN'
    is_partenaire = role == 'PARTENAIRE_SOC_CIV'

    college = (
        'directoire'           if is_directoire else
        'conseiller_politique' if is_conseiller else
        'atf'                  if is_atf        else
        'partenaire'           if is_partenaire else
        'membre'
    )

    # ── Poste nominatif (si disponible) ──────────────────────────────────────
    poste = PosteNominatif.objects.filter(holder=expert).select_related('required_structure').first()
    poste_title_lower = poste.title.lower() if poste else ''

    # ── Sous-rôle précis ─────────────────────────────────────────────────────
    if is_directoire:
        if role == 'VICE_PRESIDENT':
            sub_role = _vp_sub_role_from_title(poste_title_lower)
        else:
            sub_role = role.lower()  # 'president', 'secretary', 'rapporteur'
    elif is_atf or is_partenaire:
        # On dérive depuis la structure d'origine
        sub_role = _STRUCTURE_ACRONYM_TO_SUB.get(acronym, role.lower())
    elif is_conseiller:
        # Conseillers Juridiques : identifiés par leur PosteNominatif ou structure
        title_lower = poste_title_lower + acronym.lower()
        sub_role = 'juridique' if ('juridique' in title_lower or 'lgistique' in title_lower) else 'conseiller_politique'
    else:
        sub_role = role.lower()

    # ── CTMs de spécialité (ATF uniquement) ──────────────────────────────────
    specialty_ctm_ids = _ATF_SPECIALTY_CTM.get(sub_role, [])
    specialty_ctms = CTM.objects.filter(number__in=specialty_ctm_ids) if specialty_ctm_ids else []

    # ── Demandes de permission en attente (Directoire seulement) ─────────────
    pending_requests = (
        PermissionRequest.objects
        .filter(status='PENDING')
        .select_related('requester__user', 'requester__structure')
        .order_by('-created_at')
        if is_directoire else []
    )

    # ── Étape 5 : normes transmises par la CTC en attente de réception ───────
    # Section 5.4.3 — le Président (Poste 16) et le Rapporteur Général (Poste 1)
    # réceptionnent officiellement la norme nettoyée par la CTC.
    can_acknowledge_reception = role in ('PRESIDENT', 'RAPPORTEUR')
    pending_pilotage_reception = []
    if can_acknowledge_reception:
        ack_filter = (
            {'received_by_president__isnull': True} if role == 'PRESIDENT'
            else {'received_by_rapporteur__isnull': True}
        )
        pending_pilotage_reception = list(
            CTCProcessus.objects
            .filter(current_stage='SIGNED_OUT', **ack_filter)
            .select_related('norme', 'signed_out_by')
            .order_by('-signed_out_at')
        )

    # ── Cadrage Bureau Directoire (Phases 1 & 2 — Postes 1 à 5) ───────────────
    pending_cadrages = []
    if is_directoire:
        for stage, action, label in _CADRAGE_ACTIONS_BY_SUBROLE.get(sub_role, []):
            qs = NormeCadrage.objects.filter(current_stage=stage)
            exclude_field = _CADRAGE_ACTION_EXCLUDE_FIELD.get(action)
            if exclude_field:
                qs = qs.filter(**{f'{exclude_field}__isnull': True})
            for cadrage in qs.select_related('norme').order_by('-created_at'):
                pending_cadrages.append({'cadrage': cadrage, 'action': action, 'label': label})

    # ─────────────────────────────────────────────────────────────────────────
    # BOOLÉENS DE PRIVILÈGES (injectés dans le template)
    # ─────────────────────────────────────────────────────────────────────────
    ctx = {
        # Identification
        'is_pilotage':     True,
        'user_sub_role':   sub_role,
        'pilotage_college': college,
        'college_label':   COLLEGE_LABELS.get(college, 'Membre'),
        'college_badge':   COLLEGE_BADGE_COLORS.get(college, ''),
        'poste':           poste,
        'membership':      membership,

        # ── Profil 1 : Bureau Directoire ─────────────────────────────────────
        # Bouton d'Action Maître — validation des étapes 1→7
        'can_trigger_steps':      is_directoire,
        # Console Globale — visibilité totale sur CTMs + WGs
        'can_view_global_console': is_directoire,
        # Gestion accès experts (déblocage / suspension)
        'can_manage_access':      is_directoire,
        # Approbation des demandes de permission
        'can_approve_requests':   is_directoire,

        # ── Profil 2 : Conseillers Institutionnels ───────────────────────────
        # Module Légistique — édition projets d'Arrêtés Ministériels
        'can_edit_legistique':    (sub_role == 'juridique'),
        # Widget Planification — jalons Enquête Publique Nationale
        'can_use_planification':  is_conseiller,
        # Téléversement rapports institutionnels
        'can_upload_reports':     is_conseiller,

        # ── Profil 3 : Administrateurs Techniques & Financiers ───────────────
        # Console Audit Technique — CTMs de spécialité
        'can_audit_ctm':          is_atf,
        'specialty_ctms':         specialty_ctms,
        'specialty_ctm_ids':      specialty_ctm_ids,
        # Widget Validation Financière — exclusif FONER
        'can_audit_financials':   (sub_role == 'foner'),
        # Module Contrôle Labo — exclusif BTC
        'can_control_labo':       (sub_role == 'btc'),
        # Accès CTM tiers = demande de permission
        'atf_requires_permission_for_tiers': is_atf,

        # ── Profil 4 : Partenaires & Société Civile ──────────────────────────
        # Widget Avis Secteur Privé — exclusif FEC
        'can_avis_prive':         (sub_role == 'fec'),
        # Console Agréation Métrologique — exclusif OCC
        'can_agrement_metro':     (sub_role == 'occ'),
        # Blocage total sur processus décisionnels administratifs
        'blocked_admin_decisions': is_partenaire,

        # ── Lecture seule WG/documents ───────────────────────────────────────
        # Tous les membres pilotage : lecture seule sur brouillons WG
        'can_read_wg_drafts':     True,
        'can_edit_wg_drafts':     False,  # réservé aux experts WG

        # ── Données pour le Directoire ────────────────────────────────────────
        'pending_requests':       pending_requests,
        'pending_requests_count': len(pending_requests) if is_directoire else 0,

        # ── Étape 5 : réception des normes transmises par la CTC ─────────────
        'can_acknowledge_reception':       can_acknowledge_reception,
        'pending_pilotage_reception':       pending_pilotage_reception,
        'pending_pilotage_reception_count': len(pending_pilotage_reception),

        # ── Cadrage Bureau Directoire (Phases 1 & 2) ──────────────────────────
        'pending_cadrages':       pending_cadrages,
        'pending_cadrages_count': len(pending_cadrages),
    }

    return ctx


# ─────────────────────────────────────────────────────────────────────────────
# VUE PRINCIPALE DU TABLEAU DE BORD PILOTAGE
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageDashboardView(View):
    """
    Tableau de bord principal pour les 27 membres du Comité de Pilotage Élargi.
    Adapte dynamiquement les modules affichés selon le profil de privilèges.
    """
    template_name = 'pilotage/dashboard.html'

    def get(self, request):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        priv = get_pilotage_context(expert)
        if not priv:
            messages.info(
                request,
                "Vous n'êtes pas membre du Comité de Pilotage. "
                "Accédez à votre espace de travail habituel."
            )
            return redirect('web:app')

        # Données globales pour le Directoire (console de supervision)
        ctms = CTM.objects.prefetch_related('working_groups').order_by('number')
        ctms_with_stats = []
        total_wgs = 0
        for ctm in ctms:
            wgs = ctm.working_groups.all()
            wg_count = wgs.count()
            total_wgs += wg_count
            ctms_with_stats.append({
                'ctm': ctm,
                'wg_count': wg_count,
                'member_count': ctm.affectations.count(),
            })

        # My permission requests (autres collèges)
        my_requests = (
            PermissionRequest.objects
            .filter(requester=expert)
            .order_by('-created_at')[:10]
        )

        context = {
            'expert': expert,
            'ctms_with_stats': ctms_with_stats,
            'total_wgs': total_wgs,
            'total_ctms': len(ctms_with_stats),
            'my_permission_requests': my_requests,
            **priv,
        }
        return render(request, self.template_name, context)


# ─────────────────────────────────────────────────────────────────────────────
# VUE DEMANDE DE PERMISSION (blocage intelligent)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotagePermissionRequestView(View):
    """
    Soumet une demande de dérogation d'accès.
    Affichée automatiquement quand un membre tente d'accéder à un module restreint.
    La demande est routée vers le Bureau Directoire (statut PENDING).
    """

    def post(self, request):
        expert = Expert.objects.filter(user=request.user).first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        # Vérifier que l'expert est bien du Comité de Pilotage
        if not PilotageMembreship.objects.filter(expert=expert).exists():
            return JsonResponse({'ok': False, 'error': 'Accès non autorisé.'}, status=403)

        restricted_resource = (request.POST.get('restricted_resource') or '').strip()
        reason = (request.POST.get('reason') or '').strip()

        if not restricted_resource or not reason:
            return JsonResponse(
                {'ok': False, 'error': 'Veuillez renseigner la ressource et le motif.'},
                status=400
            )

        # Éviter les doublons : une seule demande PENDING par ressource
        existing = PermissionRequest.objects.filter(
            requester=expert,
            restricted_resource=restricted_resource,
            status='PENDING',
        ).first()
        if existing:
            return JsonResponse({
                'ok': True,
                'message': 'Une demande est déjà en cours de traitement pour cette ressource.',
                'request_id': existing.id,
            })

        perm_req = PermissionRequest.objects.create(
            requester=expert,
            restricted_resource=restricted_resource,
            reason=reason,
        )

        return JsonResponse({
            'ok': True,
            'message': 'Votre demande a été transmise au Bureau Directoire.',
            'request_id': perm_req.id,
        })


# ─────────────────────────────────────────────────────────────────────────────
# VUE APPROBATION / REJET (Bureau Directoire uniquement)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageApproveRequestView(View):
    """
    Approuve ou rejette une demande de permission.
    Réservée aux membres du Bureau Directoire.
    """

    def post(self, request, pk):
        expert = Expert.objects.filter(user=request.user).first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        # Vérifier que c'est bien un membre du Directoire
        membership = PilotageMembreship.objects.filter(
            expert=expert, role__in=_DIRECTOIRE_ROLES
        ).first()
        if not membership:
            return JsonResponse(
                {'ok': False, 'error': 'Action réservée au Bureau Directoire.'},
                status=403
            )

        perm_req = get_object_or_404(PermissionRequest, pk=pk, status='PENDING')
        decision = (request.POST.get('decision') or '').strip().upper()
        comment  = (request.POST.get('comment') or '').strip()

        if decision not in ('APPROVED', 'REJECTED'):
            return JsonResponse({'ok': False, 'error': 'Décision invalide.'}, status=400)

        perm_req.status      = decision
        perm_req.reviewed_by = expert
        perm_req.reviewed_at = timezone.now()
        perm_req.review_comment = comment
        perm_req.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_comment'])

        action = 'approuvée' if decision == 'APPROVED' else 'refusée'
        return JsonResponse({
            'ok': True,
            'message': f'La demande de {perm_req.requester.full_name} a été {action}.',
            'new_status': decision,
        })


# ─────────────────────────────────────────────────────────────────────────────
# VUE RÉCEPTION CTC (Étape 5 — Président & Rapporteur Général uniquement)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageAcknowledgeReceptionView(View):
    """
    Accuse réception officielle d'une norme transmise par la CTC (Étape 5,
    Section 5.4.3). Réservée au Président du Comité de Pilotage Élargi
    (Poste 16) et à son Rapporteur Général (Poste 1).
    """

    def post(self, request, pk):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        membership = PilotageMembreship.objects.filter(expert=expert).first()
        if not membership or membership.role not in ('PRESIDENT', 'RAPPORTEUR'):
            return JsonResponse(
                {'ok': False, 'error': 'Réservé au Président et au Rapporteur Général du Comité de Pilotage.'},
                status=403
            )

        processus = get_object_or_404(CTCProcessus, pk=pk, current_stage='SIGNED_OUT')

        if membership.role == 'PRESIDENT':
            processus.mark_received_by_president(expert)
        else:
            processus.mark_received_by_rapporteur(expert)

        return JsonResponse({
            'ok': True,
            'message': f"Réception de {processus.norme.reference_number} confirmée.",
            'reception_complete': processus.pilotage_reception_complete,
        })


# ─────────────────────────────────────────────────────────────────────────────
# VUE CADRAGE BUREAU DIRECTOIRE (Phases 1 & 2 — Postes 1 à 5)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageCadrageActionView(View):
    """
    Traite les actions de cadrage du Bureau Directoire sur un NormeCadrage :

      Phase 1 — 'open' (Président), 'validate_onic'/'validate_btp' (1er/2nd VP),
                'formalize_mandate' (Secrétaire), 'schedule' (Rapporteur Général)
      Phase 2 — 'verify_pv' (Secrétaire), 'quitus_onic'/'quitus_btp' (1er/2nd VP),
                'final_validate' (Président)

    Chaque action n'est acceptée que si elle correspond au rôle (et, pour les
    Vice-Présidents, au sous-rôle ONIC/BTP déduit du PosteNominatif) ET à
    l'étape courante (`current_stage`) du cadrage.
    """

    def post(self, request, pk):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        membership = PilotageMembreship.objects.filter(expert=expert, role__in=_DIRECTOIRE_ROLES).first()
        if not membership:
            return JsonResponse({'ok': False, 'error': 'Action réservée au Bureau Directoire.'}, status=403)

        cadrage = get_object_or_404(NormeCadrage, pk=pk)
        action = (request.POST.get('action') or '').strip()
        role = membership.role

        poste = PosteNominatif.objects.filter(holder=expert).first()
        is_onic_vp = role == 'VICE_PRESIDENT' and _vp_sub_role_from_title(poste.title.lower() if poste else '') == 'vice_president_onic'
        is_btp_vp = role == 'VICE_PRESIDENT' and not is_onic_vp

        if action == 'open' and role == 'PRESIDENT' and cadrage.current_stage == 'PROPOSED':
            cadrage.mark_opened(expert, orientation=(request.POST.get('strategic_orientation') or '').strip())

        elif action == 'validate_onic' and is_onic_vp and cadrage.current_stage == 'EXPERTS_REVIEW':
            cadrage.mark_onic_validated(expert, notes=(request.POST.get('notes') or '').strip())

        elif action == 'validate_btp' and is_btp_vp and cadrage.current_stage == 'EXPERTS_REVIEW':
            cadrage.mark_btp_validated(expert, notes=(request.POST.get('notes') or '').strip())

        elif action == 'formalize_mandate' and role == 'SECRETARY' and cadrage.current_stage == 'MANDATE_FORMALIZATION':
            cadrage.mark_mandate_formalized(expert, mandate_text=(request.POST.get('operational_mandate') or '').strip())

        elif action == 'schedule' and role == 'RAPPORTEUR' and cadrage.current_stage == 'SCHEDULED':
            cadrage.mark_scheduled(
                expert,
                deadline_ctm_review=parse_date(request.POST.get('deadline_ctm_review') or ''),
                deadline_ctc_handoff=parse_date(request.POST.get('deadline_ctc_handoff') or ''),
                deadline_pilotage_review=parse_date(request.POST.get('deadline_pilotage_review') or ''),
            )

        elif action == 'verify_pv' and role == 'SECRETARY' and cadrage.current_stage == 'PV_VERIFICATION':
            cadrage.mark_pv_verified(expert, pv_reference=(request.POST.get('pv_reference') or '').strip())

        elif action == 'quitus_onic' and is_onic_vp and cadrage.current_stage == 'CONFORMITY_QUITUS':
            cadrage.mark_onic_quitus(expert)

        elif action == 'quitus_btp' and is_btp_vp and cadrage.current_stage == 'CONFORMITY_QUITUS':
            cadrage.mark_btp_quitus(expert)

        elif action == 'final_validate' and role == 'PRESIDENT' and cadrage.current_stage == 'FINAL_VALIDATION':
            cadrage.mark_final_validated(expert, resolution_reference=(request.POST.get('resolution_reference') or '').strip())

        else:
            return JsonResponse(
                {'ok': False, 'error': "Action invalide, ou non autorisée pour votre rôle à cette étape."},
                status=400
            )

        return JsonResponse({
            'ok': True,
            'message': f"Cadrage {cadrage.norme.reference_number} mis à jour.",
            'new_stage': cadrage.current_stage,
            'new_stage_label': cadrage.get_current_stage_display(),
        })


# ─────────────────────────────────────────────────────────────────────────────
# VUE API : CONTEXTE PILOTAGE (pour appels AJAX depuis le dashboard existant)
# ─────────────────────────────────────────────────────────────────────────────

@login_required(login_url='/se-connecter/')
def pilotage_context_api(request):
    """
    Retourne le contexte de privilèges en JSON.
    Permet aux composants JS de connaître les droits de l'utilisateur courant.
    """
    expert = Expert.objects.filter(user=request.user).select_related('structure').first()
    if not expert:
        return JsonResponse({'is_pilotage': False})

    priv = get_pilotage_context(expert)
    if not priv:
        return JsonResponse({'is_pilotage': False})

    # Sérialiser uniquement les champs JSON-compatibles
    payload = {k: v for k, v in priv.items() if isinstance(v, (bool, str, int, list, type(None)))}
    payload['specialty_ctm_ids'] = list(priv.get('specialty_ctm_ids', []))
    return JsonResponse(payload)
