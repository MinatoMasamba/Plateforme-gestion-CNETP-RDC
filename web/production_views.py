"""Module « Production » — instructions, actions et signalements (Demande).

Lot 1 : instructions et tâches (scénarios A1, A2, C2). Un seul modèle de base
``Demande`` fait circuler le travail du Directoire vers les groupes. Chaque
création et chaque changement de statut est journalisé dans ``JournalDemande``.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models as db_models
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from apps.experts.models import Expert
from apps.governance.models import CTM, Demande, JournalDemande, WG
from apps.mobileapp.signals import create_notification_for_user
from apps.norms.models import Norme
from web.pilotage_views import get_pilotage_context

STATUT_BADGE = {
    'ENVOYEE': 'bg-slate-100 text-slate-700',
    'LUE': 'bg-blue-100 text-blue-700',
    'EN_COURS': 'bg-amber-100 text-amber-800',
    'EXECUTEE': 'bg-emerald-100 text-emerald-700',
}


def _group_leader_ids(expert):
    """Groupes dont l'expert est président, rapporteur ou secrétaire."""
    return list(WG.objects.filter(
        db_models.Q(president=expert) | db_models.Q(rapporteur=expert) | db_models.Q(secretary=expert)
    ).values_list('pk', flat=True))


def demandes_visibles(expert, priv):
    """Queryset des demandes visibles par l'utilisateur connecté."""
    if priv and priv.get('can_view_global_console'):
        return Demande.objects.select_related(
            'emetteur__user', 'destinataire__user', 'groupe__ctm', 'sous_commission', 'norme'
        ).all()
    groupe_ids = _group_leader_ids(expert)
    return Demande.objects.filter(
        db_models.Q(destinataire=expert) | db_models.Q(groupe_id__in=groupe_ids)
    ).select_related('emetteur__user', 'destinataire__user', 'groupe__ctm', 'sous_commission', 'norme')


def peut_emettre(expert, priv):
    """Le Directoire (DG confondu avec le Président du COPIL) émet les instructions."""
    return bool(priv and priv.get('can_trigger_steps'))


def peut_transitionner(expert, priv, demande, groupe_ids=None):
    """Le Directoire, le responsable désigné ou le responsable du groupe peuvent avancer le statut."""
    if priv and priv.get('can_trigger_steps'):
        return True
    if demande.destinataire_id == expert.id:
        return True
    if demande.groupe_id and demande.groupe_id in (groupe_ids if groupe_ids is not None else _group_leader_ids(expert)):
        return True
    return False


def _notifier_destinataires(demande, emetteur):
    """Notifie le responsable désigné ou le responsable du groupe concerné."""
    destinataires = []
    if demande.destinataire:
        destinataires.append(demande.destinataire)
    if demande.groupe:
        destinataires.extend(filter(None, [demande.groupe.president, demande.groupe.rapporteur, demande.groupe.secretary]))
    for expert in {e for e in destinataires if e and e.user_id != emetteur.user_id}:
        create_notification_for_user(
            expert.user,
            "Nouvelle instruction",
            f"{emetteur.full_name} vous adresse : « {demande.objet} ».",
            "SYSTEM",
            priority="HIGH",
            data={"demande_id": demande.id, "statut": demande.statut},
        )


@login_required(login_url='/se-connecter/')
@require_POST
@csrf_protect
def instruction_create(request):
    """Crée une instruction (vers un groupe/une sous-commission) ou une action (vers un responsable)."""
    expert = Expert.objects.filter(user=request.user).select_related('structure').first()
    if not expert:
        return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)
    priv = get_pilotage_context(expert)
    if not peut_emettre(expert, priv):
        return JsonResponse({'ok': False, 'error': 'Action réservée au Bureau Directoire.'}, status=403)

    type_demande = (request.POST.get('type') or 'INSTRUCTION').strip().upper()
    if type_demande not in ('INSTRUCTION', 'ACTION'):
        return JsonResponse({'ok': False, 'error': 'Type de demande invalide.'}, status=400)

    objet = (request.POST.get('objet') or '').strip()
    message = (request.POST.get('message') or '').strip()
    if not objet:
        return JsonResponse({'ok': False, 'error': "L'objet est obligatoire."}, status=400)

    groupe_id = (request.POST.get('groupe_id') or '').strip()
    sous_commission_id = (request.POST.get('sous_commission_id') or '').strip()
    destinataire_id = (request.POST.get('destinataire_id') or '').strip()
    norme_id = (request.POST.get('norme_id') or '').strip()

    groupe = WG.objects.filter(pk=groupe_id).first() if groupe_id.isdigit() else None
    sous_commission = CTM.objects.filter(pk=sous_commission_id).first() if sous_commission_id.isdigit() else None
    destinataire = Expert.objects.filter(pk=destinataire_id).first() if destinataire_id.isdigit() else None
    norme = Norme.objects.filter(pk=norme_id).first() if norme_id.isdigit() else None

    if type_demande == 'INSTRUCTION' and not (groupe or sous_commission):
        return JsonResponse({'ok': False, 'error': 'Choisissez un groupe ou une sous-commission destinataire.'}, status=400)
    if type_demande == 'ACTION' and not destinataire:
        return JsonResponse({'ok': False, 'error': "Choisissez un responsable pour l'action."}, status=400)

    echeance = parse_date(request.POST.get('echeance') or '') if (request.POST.get('echeance') or '').strip() else None

    demande = Demande.objects.create(
        type=type_demande, emetteur=expert, destinataire=destinataire,
        groupe=groupe, sous_commission=sous_commission, norme=norme,
        objet=objet, message=message, echeance=echeance, statut='ENVOYEE',
        created_by=request.user, updated_by=request.user,
    )
    JournalDemande.objects.create(demande=demande, statut_avant='', statut_apres='ENVOYEE', acteur=expert, commentaire='Création')
    _notifier_destinataires(demande, expert)

    return JsonResponse({'ok': True, 'message': 'Instruction envoyée.', 'demande_id': demande.id})


@login_required(login_url='/se-connecter/')
@require_POST
@csrf_protect
def demande_transition(request, pk):
    """Avance le statut d'une demande (lue → en cours → exécutée) et journalise."""
    expert = Expert.objects.filter(user=request.user).first()
    if not expert:
        return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)
    priv = get_pilotage_context(expert)
    demande = get_object_or_404(Demande.objects.select_related('groupe'), pk=pk)
    if not peut_transitionner(expert, priv, demande):
        return JsonResponse({'ok': False, 'error': 'Vous ne pouvez pas faire évoluer cette demande.'}, status=403)

    nouveau = (request.POST.get('statut') or '').strip().upper()
    commentaire = (request.POST.get('commentaire') or '').strip()
    try:
        demande.transition(nouveau, acteur=expert, commentaire=commentaire)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('web:instructions')

    messages.success(request, 'Statut mis à jour.')
    return redirect('web:instructions')


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class InstructionDashboardView(View):
    """Console des instructions : liste, création et suivi de statut."""
    template_name = 'pilotage/instructions.html'

    def get(self, request):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            from django.shortcuts import redirect
            return redirect('web:home')

        priv = get_pilotage_context(expert)
        demandes = demandes_visibles(expert, priv)

        type_filter = request.GET.get('type', '')
        if type_filter in ('INSTRUCTION', 'ACTION', 'SIGNALEMENT'):
            demandes = demandes.filter(type=type_filter)
        statut_filter = request.GET.get('statut', '')
        if statut_filter in dict(Demande.STATUS_CHOICES):
            demandes = demandes.filter(statut=statut_filter)

        demandes = demandes.prefetch_related('journal').order_by('-created_at')

        status_labels = dict(Demande.STATUS_CHOICES)
        groupe_ids = _group_leader_ids(expert)
        rows = [
            {
                'demande': demande,
                'badge_class': STATUT_BADGE.get(demande.statut, 'bg-slate-100 text-slate-700'),
                'prochaines': (
                    [(s, status_labels[s]) for s in Demande.TRANSITIONS.get(demande.statut, [])]
                    if peut_transitionner(expert, priv, demande, groupe_ids) else []
                ),
                'journal': list(demande.journal.all()),
            }
            for demande in demandes
        ]
        counts = {
            'total': len(rows),
            'a_traiter': sum(row['demande'].statut in ('ENVOYEE', 'LUE') for row in rows),
            'en_cours': sum(row['demande'].statut == 'EN_COURS' for row in rows),
            'executees': sum(row['demande'].statut == 'EXECUTEE' for row in rows),
        }

        context = {
            'page_title': 'Instructions',
            'rows': rows,
            'counts': counts,
            'statuts': Demande.STATUS_CHOICES,
            'types': Demande.TYPE_CHOICES,
            'peut_emettre': peut_emettre(expert, priv),
            'is_pilotage': bool(priv),
            'groupes': WG.objects.select_related('ctm').order_by('ctm__number', 'number'),
            'sous_commissions': CTM.objects.order_by('number'),
            'experts': Expert.objects.filter(status='ACTIVE').select_related('user').order_by('user__last_name'),
            'normes': Norme.objects.order_by('-updated_at')[:500],
            'type_filter': type_filter,
            'statut_filter': statut_filter,
        }
        return render(request, self.template_name, context)
