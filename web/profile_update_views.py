"""Parcours autonome de mise à jour du profil expert (style candidature)."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from apps.experts.models import Expert
from apps.experts.profile_updates import transition
from apps.governance.models import Affectation, CTM, OrganisationVersion, Organe, WG
from web.forms import ExpertProfileUpdateForm
from web.president_sc_views import _sc_bureau_ids
from web.views import expert_workspace_url_name


def ctm_bureau_ids(expert):
    """CTM/SC dont l'expert est membre du bureau (président, vice-président,
    rapporteur ou secrétaire)."""
    if not expert:
        return set()
    ids = set()
    sc_ids = _sc_bureau_ids(expert, timezone.localdate())
    if sc_ids:
        names = set()
        for organe in Organe.objects.filter(pk__in=sc_ids):
            names.add(organe.name)
            names.add(organe.official_name)
        names.discard('')
        names.discard(None)
        if names:
            ids.update(CTM.objects.filter(name__in=names).values_list('id', flat=True))
    ids.update(
        CTM.objects.filter(
            Q(scientific_president=expert) | Q(rapporteur=expert) | Q(secretary=expert)
        ).values_list('id', flat=True)
    )
    return ids


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
            'mon_profil_url': reverse(expert_workspace_url_name(request.user)),
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
            with transaction.atomic():
                form.save()
                state = getattr(context['expert'], 'profile_update', None)
                if state is None or state.status == 'NOT_STARTED':
                    transition(context['expert'], 'IN_PROGRESS', request.user, version=context['version'])
                elif state.status == 'COMPLETE':
                    transition(context['expert'], 'EXPIRED', request.user, version=context['version'], comment='Modification du profil')
            messages.success(
                request,
                "Vos informations ont été enregistrées. La conformité du profil reste à vérifier séparément.",
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


class ExpertAffectationUpdateView(LoginRequiredMixin, View):
    """Enregistre le CTM/SC unique et le ou les WG de l'expert connecté.

    Les membres du bureau d'un CTM/SC (président, vice-président, rapporteur,
    secrétaire) peuvent choisir plusieurs WG de cette même sous-commission ;
    les autres experts n'en choisissent qu'un.
    """

    login_url = '/se-connecter/'

    def post(self, request):
        expert = Expert.objects.filter(user=request.user).first()
        if expert is None:
            return JsonResponse({'ok': False, 'error': 'Profil expert introuvable.'}, status=404)

        raw_ctm = (request.POST.get('ctm') or '').strip()
        ctm = CTM.objects.filter(pk=int(raw_ctm)).first() if raw_ctm.isdecimal() else None
        if ctm is None:
            return JsonResponse({'ok': False, 'error': 'Sélectionnez une sous-commission valide.'}, status=400)

        raw_wg_ids = request.POST.getlist('wg')
        if any(not value.isdecimal() for value in raw_wg_ids):
            return JsonResponse(
                {'ok': False, 'error': 'Groupe de travail invalide pour cette sous-commission.'},
                status=400,
            )
        wg_ids = list(dict.fromkeys(int(value) for value in raw_wg_ids))
        wgs = list(WG.objects.filter(pk__in=wg_ids, ctm=ctm).order_by('number'))
        if len(wgs) != len(wg_ids):
            return JsonResponse(
                {'ok': False, 'error': 'Groupe de travail invalide pour cette sous-commission.'},
                status=400,
            )
        if not wgs and WG.objects.filter(ctm=ctm).exists():
            return JsonResponse(
                {'ok': False, 'error': 'Sélectionnez au moins un groupe de travail.'},
                status=400,
            )
        if len(wgs) > 1 and ctm.pk not in ctm_bureau_ids(expert):
            return JsonResponse(
                {'ok': False, 'error': 'Un seul groupe de travail est autorisé pour ce profil.'},
                status=400,
            )

        with transaction.atomic():
            Affectation.objects.filter(expert=expert).delete()
            Affectation.objects.bulk_create([
                Affectation(
                    expert=expert, ctm=ctm, wg=wg,
                    is_primary_ctm=True, is_primary_wg=True,
                )
                for wg in (wgs or [None])
            ])
            if expert.ctm_id != ctm.pk:
                expert.ctm = ctm
                expert.save(update_fields=['ctm'])

        return JsonResponse({'ok': True, 'ctm': ctm.pk, 'wgs': [wg.pk for wg in wgs]})
