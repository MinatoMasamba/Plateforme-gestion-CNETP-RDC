"""Pages publiques de consultation et salle de réunion LiveKit."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.experts.models import Expert
from apps.meetings.models import Reunion, ReunionParticipant


def _current_expert(request):
    return Expert.objects.select_related('structure', 'user').filter(user=request.user).first()


@login_required(login_url='/se-connecter/')
def meeting_list(request):
    """Lister les réunions auxquelles l'expert est convié."""
    expert = _current_expert(request)
    if expert is None:
        messages.error(request, "Seuls les experts invités peuvent consulter les réunions.")
        return redirect('web:app')

    invitations = (
        ReunionParticipant.objects
        .filter(expert=expert)
        .select_related('reunion__ctm', 'reunion__wg', 'reunion__organisateur__user')
        .order_by('-reunion__date')
    )
    now = timezone.now()
    upcoming = [i.reunion for i in invitations if i.reunion.date >= now]
    past = [i.reunion for i in invitations if i.reunion.date < now]

    return render(request, 'reunions/list.html', {
        'expert': expert,
        'upcoming': upcoming,
        'past': past,
    })


@login_required(login_url='/se-connecter/')
def meeting_details(request, pk):
    """Afficher le détail d'une réunion aux invités et à l'organisateur."""
    expert = _current_expert(request)
    if expert is None:
        messages.error(request, "Seuls les experts invités peuvent consulter les réunions.")
        return redirect('web:app')

    reunion = get_object_or_404(
        Reunion.objects.select_related('ctm', 'wg', 'organisateur__user', 'organisateur__structure'),
        pk=pk,
    )
    participant = (
        ReunionParticipant.objects
        .filter(reunion=reunion, expert=expert)
        .first()
    )
    is_organizer = reunion.organisateur_id == expert.pk
    if participant is None and not is_organizer:
        messages.error(request, "Vous n'êtes pas invité à cette réunion.")
        return redirect('web:app')

    participants = (
        reunion.participants
        .select_related('expert__user', 'expert__structure')
        .order_by('role', 'expert__user__last_name', 'expert__user__first_name')
    )
    presences = {
        p.expert_id: p for p in reunion.presences.select_related('expert__user')
    }
    participants_info = []
    for invitation in participants:
        presence = presences.get(invitation.expert_id)
        full_name = invitation.expert.user.get_full_name() or invitation.expert.user.email
        initials = ''.join(part[0] for part in full_name.split()[:2]).upper() or 'EX'
        participants_info.append({
            'name': full_name,
            'initials': initials,
            'structure': invitation.expert.structure.name,
            'acronym': invitation.expert.structure.acronym,
            'role': invitation.get_role_display(),
            'peut_parler': invitation.peut_parler,
            'peut_video': invitation.peut_video,
            'presence_code': presence.status if presence else None,
            'presence': presence.get_status_display() if presence else None,
        })

    documents = []
    for document in reunion.document_links or []:
        if isinstance(document, dict):
            title = document.get('title') or document.get('name') or 'Document'
            url = document.get('url') or document.get('link') or ''
        else:
            title, url = str(document), str(document)
        if url:
            documents.append({'title': title, 'url': url})

    now = timezone.now()
    salle_active = (
        reunion.mode == 'SALLE'
        and reunion.status in ('PLANNED', 'IN_PROGRESS')
        and (reunion.cloture_salle is None or now <= reunion.cloture_salle)
    )
    peut_rejoindre = salle_active and participant is not None

    return render(request, 'reunions/details.html', {
        'reunion': reunion,
        'expert': expert,
        'participant': participant,
        'participants': participants,
        'participants_info': participants_info,
        'documents': documents,
        'presences': presences,
        'salle_active': salle_active,
        'peut_rejoindre': peut_rejoindre,
    })


@login_required(login_url='/se-connecter/')
def salle_reunion(request, pk):
    """Afficher la salle uniquement aux invités de la réunion."""
    expert = _current_expert(request)
    if expert is None:
        messages.error(request, "Seuls les experts invités peuvent rejoindre une salle.")
        return redirect('web:app')

    reunion = get_object_or_404(
        Reunion.objects.select_related('ctm', 'wg', 'organisateur__user'), pk=pk,
    )
    participant = ReunionParticipant.objects.filter(
        reunion=reunion, expert=expert,
    ).first()
    if participant is None:
        messages.error(request, "Vous n'êtes pas invité à cette réunion.")
        return redirect('web:app')

    return render(request, 'reunions/salle.html', {
        'reunion': reunion,
        'participant': participant,
    })
