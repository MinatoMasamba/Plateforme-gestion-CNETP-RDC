"""Profil personnel des membres du Comité de Pilotage."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.experts.models import Expert
from apps.governance.models import Demande
from web.forms import UserProfileForm
from web.pilotage_views import get_pilotage_context


@login_required(login_url='/se-connecter/')
@require_http_methods(['GET', 'POST'])
def pilotage_profile(request):
    expert = Expert.objects.filter(user=request.user).select_related('user', 'structure').first()
    if not expert:
        return HttpResponseForbidden('Profil expert requis.')
    pilotage = get_pilotage_context(expert)
    if not pilotage:
        return HttpResponseForbidden('Profil réservé aux membres du Comité de Pilotage.')

    form = UserProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vos informations personnelles ont été mises à jour.')
        return redirect('web:pilotage_profile')

    return render(request, 'pilotage/profile.html', {
        'expert': expert,
        'pilotage': pilotage,
        'is_pilotage': True,
        'form': form,
        'instructions_emises': Demande.objects.filter(emetteur=expert).count(),
        'actions_recues': Demande.objects.filter(destinataire=expert).count(),
    })
