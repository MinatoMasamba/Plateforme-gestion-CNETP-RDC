"""Page de salle de réunion LiveKit."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.experts.models import Expert
from apps.meetings.models import Reunion, ReunionParticipant


@login_required
def salle_reunion(request, pk):
    """Afficher la salle uniquement aux invités de la réunion."""
    expert = Expert.objects.filter(user=request.user).first()
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
