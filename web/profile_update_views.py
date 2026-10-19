"""Parcours autonome de mise à jour du profil expert (style candidature)."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from apps.experts.models import Expert
from apps.governance.models import OrganisationVersion
from web.forms import ExpertProfileUpdateForm
from web.views import expert_workspace_url_name


class ExpertProfileUpdateNoticeView(View):
    """Communiqué invitant les experts à mettre à jour leur profil."""

    template_name = 'expert/communique_update.html'

    def get(self, request):
        return render(request, self.template_name, {
            'profile_update_url': reverse('web:expert_profile_update'),
        })


class ExpertProfileUpdateView(LoginRequiredMixin, View):
    """Nouveau formulaire de mise à jour du profil, indépendant du wizard Phoenix."""

    login_url = '/se-connecter/'
    template_name = 'expert/profil/expert_profile_update.html'

    @staticmethod
    def _expert(request):
        return (
            Expert.objects.filter(user=request.user)
            .select_related('structure', 'user').first()
        )

    @staticmethod
    def _version():
        return (
            OrganisationVersion.objects.exclude(status='ARCHIVED')
            .order_by('-activated_at', '-id').first()
        )

    def get_context(self, request, *, bound=False):
        expert = self._expert(request)
        version = self._version()
        data = request.POST if bound else None
        files = request.FILES if bound else None
        form = ExpertProfileUpdateForm(
            data, files, user=request.user, expert=expert, version=version,
        )
        return {
            'expert': expert,
            'version': version,
            'form': form,
        }

    def get(self, request):
        if not self._expert(request):
            messages.error(request, "Profil expert introuvable.")
            return redirect('web:expert_login')
        return render(request, self.template_name, self.get_context(request))

    def post(self, request):
        if not self._expert(request):
            messages.error(request, "Profil expert introuvable.")
            return redirect('web:expert_login')

        context = self.get_context(request, bound=True)
        form = context['form']

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Votre profil a été mis à jour. Vous êtes redirigé vers votre espace de travail.",
            )
            return redirect(expert_workspace_url_name(request.user))

        steps = (
            (1, ('first_name', 'last_name', 'phone', 'province', 'whatsapp_number')),
            (2, ('specialties', 'bio', 'cv')),
            (3, ('sc', 'wg')),
        )
        context['wizard_start_step'] = 1
        for step, names in steps:
            if any(name in form.errors for name in names):
                context['wizard_start_step'] = step
                break
        return render(request, self.template_name, context, status=400)
