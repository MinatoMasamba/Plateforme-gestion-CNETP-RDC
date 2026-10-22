"""Circuit de demandes d'analyse, séparé des instructions de production."""

import logging
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.experts.models import Expert
from apps.governance.models import (
    CTCMembership, DemandeAnalyse, JournalAnalyse, MandatOrganisation, Organe,
    PieceAnalyse, PilotageMembreship,
)
from apps.mobileapp.models import Notification
from web.president_sc_views import _sc_bureau_ids


logger = logging.getLogger(__name__)
DIRECTOIRE = {'PRESIDENT', 'VICE_PRESIDENT', 'SECRETARY', 'RAPPORTEUR'}
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.png', '.jpg', '.jpeg'}


def _expert(request):
    expert = Expert.objects.filter(user=request.user, status='ACTIVE', user__is_active=True).first()
    if not expert:
        raise PermissionDenied
    return expert


def _roles(expert):
    pilotage = set(PilotageMembreship.objects.filter(expert=expert).values_list('role', flat=True))
    ctc = set(CTCMembership.objects.filter(expert=expert).values_list('role', flat=True))
    sc_ids = _sc_bureau_ids(expert, timezone.localdate())
    return {
        'conseiller': 'CONSEILLER' in pilotage,
        'directoire': bool(pilotage & DIRECTOIRE),
        'ctc': bool(ctc & {'COORDINATOR', 'VICE_COORDINATOR'}),
        'sc_ids': sc_ids,
    }


def _valid_uploads(request):
    files = request.FILES.getlist('pieces')
    if len(files) > 3:
        raise ValueError('Joignez au maximum trois fichiers.')
    for file in files:
        if file.size > MAX_FILE_SIZE or Path(file.name).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValueError('Pièce refusée : utilisez PDF, DOCX, PNG ou JPG (10 Mo maximum).')
    return files


def _attach(event, files):
    for file in files:
        PieceAnalyse.objects.create(
            journal=event, fichier=file,
            nom_original=Path(file.name).name[:255], taille=file.size,
        )


def _notify(request, recipient, demand, verb):
    url = request.build_absolute_uri(reverse('web:conseiller_analysis_detail', args=[demand.pk]))
    Notification.objects.create(
        user=recipient.user, title=f'Demande d’analyse {verb}',
        body=demand.objet, notification_type='SYSTEM',
        data={'url': url, 'demande_analyse_id': demand.pk},
    )
    if recipient.user.email:
        def deliver():
            try:
                send_mail(
                    f'Demande d’analyse {verb} · CNE-ITP',
                    f'{demand.objet}\n\nConsultez la demande : {url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient.user.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception('Échec de la notification courriel pour la demande %s', demand.pk)
        transaction.on_commit(deliver)


def _visible(expert):
    return DemandeAnalyse.objects.filter(Q(emetteur=expert) | Q(destinataire=expert)).select_related(
        'emetteur__user', 'destinataire__user', 'sc', 'norme',
    ).distinct()


@login_required(login_url='/se-connecter/')
@require_GET
def analysis_list(request):
    expert = _expert(request)
    roles = _roles(expert)
    if not (roles['conseiller'] or roles['directoire'] or roles['ctc'] or roles['sc_ids']):
        raise PermissionDenied
    leaders = []
    if roles['conseiller']:
        mandates = MandatOrganisation.objects.filter(
            status='ACTIVE', capacity='ORGANISATION',
            poste__organe__type='SC', poste__organe__version__status='ACTIVE',
            expert__status='ACTIVE', expert__user__is_active=True,
        ).select_related('expert__user', 'poste__organe').order_by('poste__organe__code')
        seen = set()
        for mandate in mandates:
            pair = (mandate.expert_id, mandate.poste.organe_id)
            if pair not in seen and mandate.poste.organe_id in _sc_bureau_ids(mandate.expert, timezone.localdate()):
                leaders.append({'expert': mandate.expert, 'sc': mandate.poste.organe})
                seen.add(pair)
    return render(request, 'pilotage/conseiller/analyses.html', {
        'expert': expert, 'roles': roles,
        'demandes': _visible(expert)[:100],
        'conseillers': Expert.objects.filter(
            status='ACTIVE', user__is_active=True, pilotagemembreship__role='CONSEILLER',
        ).distinct().select_related('user') if roles['directoire'] else [],
        'coordinateurs': Expert.objects.filter(
            status='ACTIVE', user__is_active=True,
            ctcmembership__role__in=['COORDINATOR', 'VICE_COORDINATOR'],
        ).distinct().select_related('user') if roles['conseiller'] else [],
        'scs': Organe.objects.filter(type='SC', version__status='ACTIVE', status='ACTIVE').order_by('code')
        if roles['conseiller'] else [],
        'sc_bureau': leaders,
        'demandes_directoire': _visible(expert).filter(destinataire=expert, circuit='DIRECTOIRE')[:100]
        if roles['conseiller'] else [],
    })


@login_required(login_url='/se-connecter/')
@require_POST
@transaction.atomic
def analysis_create(request):
    expert = _expert(request)
    roles = _roles(expert)
    circuit = request.POST.get('circuit', '')
    recipient = Expert.objects.filter(pk=request.POST.get('destinataire'), status='ACTIVE', user__is_active=True).first()
    if not recipient or recipient.pk == expert.pk:
        raise PermissionDenied
    if circuit == DemandeAnalyse.Circuit.DIRECTOIRE:
        allowed = roles['directoire'] and _roles(recipient)['conseiller']
    elif circuit == DemandeAnalyse.Circuit.CTC:
        allowed = roles['conseiller'] and _roles(recipient)['ctc']
    elif circuit == DemandeAnalyse.Circuit.SC:
        allowed = roles['conseiller']
    else:
        allowed = False
    if not allowed:
        raise PermissionDenied
    sc = None
    if circuit == DemandeAnalyse.Circuit.SC:
        sc = Organe.objects.filter(
            pk=request.POST.get('sc'), type='SC', status='ACTIVE', version__status='ACTIVE',
        ).first()
        if not sc or sc.pk not in _roles(recipient)['sc_ids']:
            raise PermissionDenied
    source = None
    if request.POST.get('demande_source'):
        source = get_object_or_404(_visible(expert), pk=request.POST['demande_source'], destinataire=expert,
                                   circuit=DemandeAnalyse.Circuit.DIRECTOIRE)
        if not roles['conseiller'] or circuit == DemandeAnalyse.Circuit.DIRECTOIRE:
            raise PermissionDenied
    objet = request.POST.get('objet', '').strip()
    contexte = request.POST.get('contexte', '').strip()
    if not objet or not contexte or len(objet) > 250:
        messages.error(request, 'Renseignez un objet et une demande d’analyse.')
        return redirect('web:conseiller_analysis_list')
    try:
        files = _valid_uploads(request)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('web:conseiller_analysis_list')
    due_raw = request.POST.get('echeance', '').strip()
    try:
        due = timezone.datetime.strptime(due_raw, '%Y-%m-%d').date() if due_raw else None
    except ValueError:
        messages.error(request, 'La date d’échéance est invalide.')
        return redirect('web:conseiller_analysis_list')
    demand = DemandeAnalyse.objects.create(
        emetteur=expert, destinataire=recipient, circuit=circuit,
        objet=objet, contexte=contexte, echeance=due, sc=sc, demande_source=source,
    )
    event = JournalAnalyse.objects.create(demande=demand, acteur=expert, action='ENVOI', texte=contexte)
    _attach(event, files)
    _notify(request, recipient, demand, 'reçue')
    messages.success(request, 'La demande d’analyse a été envoyée.')
    return redirect('web:conseiller_analysis_detail', pk=demand.pk)


@login_required(login_url='/se-connecter/')
@require_GET
def analysis_detail(request, pk):
    expert = _expert(request)
    demand = get_object_or_404(_visible(expert).prefetch_related('journal__pieces', 'sous_demandes'), pk=pk)
    return render(request, 'pilotage/conseiller/analyse_detail.html', {
        'expert': expert, 'demande': demand, 'journal': demand.journal.select_related('acteur__user'),
        'can_view_source': bool(demand.demande_source_id and _visible(expert).filter(pk=demand.demande_source_id).exists()),
        'is_sender': demand.emetteur_id == expert.pk,
        'is_recipient': demand.destinataire_id == expert.pk,
    })


@login_required(login_url='/se-connecter/')
@require_POST
@transaction.atomic
def analysis_transition(request, pk):
    expert = _expert(request)
    demand = get_object_or_404(DemandeAnalyse.objects.select_for_update(), pk=pk)
    if expert.pk not in (demand.emetteur_id, demand.destinataire_id):
        raise PermissionDenied
    action = request.POST.get('action')
    text = request.POST.get('texte', '').strip()
    try:
        files = _valid_uploads(request)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('web:conseiller_analysis_detail', pk=pk)
    recipient_action = expert.pk == demand.destinataire_id
    if action == 'EN_COURS' and recipient_action and demand.statut == 'ENVOYEE':
        demand.statut = 'EN_COURS'
        event_action = JournalAnalyse.Action.PRISE_EN_CHARGE
    elif action == 'REPONDUE' and recipient_action and demand.statut in ('ENVOYEE', 'EN_COURS') and text:
        demand.statut = 'REPONDUE'
        demand.repondue_le = timezone.now()
        event_action = JournalAnalyse.Action.REPONSE
    elif action == 'CLOTUREE' and not recipient_action and demand.statut == 'REPONDUE':
        demand.statut = 'CLOTUREE'
        demand.cloturee_le = timezone.now()
        event_action = JournalAnalyse.Action.CLOTURE
    else:
        raise PermissionDenied
    demand.save(update_fields=['statut', 'repondue_le', 'cloturee_le', 'updated_at'])
    event = JournalAnalyse.objects.create(demande=demand, acteur=expert, action=event_action, texte=text)
    _attach(event, files)
    if action == 'REPONDUE':
        _notify(request, demand.emetteur, demand, 'répondue')
    messages.success(request, 'Le suivi de la demande a été mis à jour.')
    return redirect('web:conseiller_analysis_detail', pk=pk)


@login_required(login_url='/se-connecter/')
@require_GET
def analysis_piece(request, pk):
    expert = _expert(request)
    piece = get_object_or_404(PieceAnalyse.objects.select_related('journal__demande'), pk=pk)
    demand = piece.journal.demande
    if expert.pk not in (demand.emetteur_id, demand.destinataire_id):
        raise PermissionDenied
    try:
        return FileResponse(piece.fichier.open('rb'), as_attachment=True, filename=piece.nom_original)
    except FileNotFoundError as exc:
        raise Http404 from exc
