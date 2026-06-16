from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from apps.experts.models import Expert
from web.pilotage_views import get_pilotage_context

from .models import AgentSession


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageIAConsoleView(View):
    """Page dédiée de l'agent IA pour le Comité de Pilotage : chat large + graphiques."""

    template_name = 'ia_agent/pilotage_console/console.html'

    def get(self, request):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        priv = get_pilotage_context(expert)
        if not priv:
            messages.info(
                request,
                "L'espace « Pilotage IA » est réservé aux membres du Comité de Pilotage."
            )
            return redirect('web:app')

        ia_sessions = AgentSession.objects.filter(user=request.user, scope='pilotage')[:20]

        context = {
            'expert': expert,
            'ia_sessions': ia_sessions,
            **priv,
        }
        return render(request, self.template_name, context)
