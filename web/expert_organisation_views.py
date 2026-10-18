import json
import re

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.experts.models import Expert
from apps.governance.models import (
    ChoixOrganisationExpert, CorrespondanceGroupe, GroupeCible, MandatOrganisation, Organe, WG,
)
from web.forms import ExpertCVUserForm, ExpertOrganisationChoiceForm, ExpertProfileForm
from web.organisation_views import preferred_version


class ExpertSubcommissionView(LoginRequiredMixin, View):
    login_url = '/se-connecter/'
    template_name = 'expert/subcommission.html'

    def get(self, request, pk):
        expert = Expert.objects.filter(user=request.user).first()
        if not expert:
            raise Http404('Profil expert introuvable.')
        sc = get_object_or_404(Organe, pk=pk, type=Organe.Type.SC)
        mandates = list(MandatOrganisation.objects.filter(expert=expert).filter(
            Q(poste__organe=sc) | Q(groupe__sc=sc)
        ).select_related('poste', 'groupe').order_by('-created_at'))
        if not mandates:
            raise Http404('Aucune affectation à cette sous-commission.')
        return render(request, self.template_name, {
            'expert': expert,
            'sc': sc,
            'mandates': mandates,
            'groups': sc.groupes.order_by('code'),
        })


class ExpertOrganisationUpdateView(LoginRequiredMixin, View):
    login_url = '/se-connecter/'
    template_name = 'expert/organisation_update.html'

    def get_context(self, request, *, bound=False):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            raise Http404('Profil expert introuvable.')
        version = preferred_version()
        if not version:
            raise Http404('Aucune organisation disponible.')
        latest = (
            ChoixOrganisationExpert.objects.filter(expert=expert, version=version)
            .select_related('sc', 'groupe', 'source_wg').first()
        )
        data = request.POST if bound else None
        files = request.FILES if bound else None
        initial = None
        if latest and not bound:
            initial = {
                'sc': latest.sc_id,
                'source_wg': latest.source_wg_id,
                'groupe': latest.groupe_id,
            }
        choice_form = ExpertOrganisationChoiceForm(data, version=version, initial=initial)
        scs = list(Organe.objects.filter(version=version, type='SC').exclude(status='ARCHIVED'))
        groups = []
        if choice_form.uses_adopted_gt:
            for gt in GroupeCible.objects.filter(sc__version=version).select_related('sc').order_by('sc__code', 'code'):
                groups.append({'id': gt.pk, 'label': gt.name, 'sc_id': gt.sc_id})
        else:
            mappings = {}
            for item in CorrespondanceGroupe.objects.filter(version=version).exclude(status='REJECTED').select_related('sc'):
                mappings.setdefault(item.wg_id, []).append(item)
            own_groups = set(expert.governance_affectations.exclude(wg__isnull=True).values_list('wg_id', flat=True))
            for wg in WG.objects.select_related('ctm').order_by('ctm__number', 'number', 'name'):
                suggested = set()
                for mapping in mappings.get(wg.pk, []):
                    if mapping.sc_id:
                        suggested.add(mapping.sc_id)
                    else:
                        domain = mapping.domain.upper()
                        for sc in scs:
                            token = sc.code.removeprefix('SC-').upper()
                            if re.search(r'(?<!\w)' + re.escape(token) + r'(?!\w)', domain):
                                suggested.add(sc.pk)
                groups.append({
                    'id': wg.pk,
                    'label': f'CTM {wg.ctm.number} · WG {wg.ctm.number}.{wg.number} — {wg.name}',
                    'suggested_sc_ids': sorted(suggested),
                    'own': wg.pk in own_groups,
                })
        return {
            'expert': expert,
            'version': version,
            'latest_choice': latest,
            'user_form': ExpertCVUserForm(data, files, instance=request.user),
            'expert_form': ExpertProfileForm(data, files, instance=expert),
            'choice_form': choice_form,
            'groups_json': json.dumps(groups),
            'has_groups': bool(groups),
            'uses_adopted_gt': choice_form.uses_adopted_gt,
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context(request))

    def post(self, request):
        context = self.get_context(request, bound=True)
        user_form = context['user_form']
        expert_form = context['expert_form']
        choice_form = context['choice_form']
        valid = all((user_form.is_valid(), expert_form.is_valid(), choice_form.is_valid()))
        if valid:
            with transaction.atomic():
                user_form.save()
                expert_form.save()
                ChoixOrganisationExpert.objects.create(
                    expert=context['expert'],
                    version=context['version'],
                    sc=choice_form.cleaned_data['sc'],
                    source_wg=choice_form.cleaned_data['source_wg'],
                    groupe=choice_form.cleaned_data['groupe'],
                    created_by=request.user,
                )
            messages.success(request, 'Profil mis à jour et choix transmis pour examen.')
            return redirect('web:expert_organisation_update')
        if any(name in user_form.errors for name in ('first_name', 'last_name', 'phone', 'province', 'profile_picture')):
            context['wizard_start_step'] = 1
        elif 'bio' in user_form.errors or any(name in expert_form.errors for name in ('specialties', 'cv', 'whatsapp_number')):
            context['wizard_start_step'] = 2
        else:
            context['wizard_start_step'] = 3
        return render(request, self.template_name, context, status=400)
