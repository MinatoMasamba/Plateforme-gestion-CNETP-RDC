from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone

from apps.governance.models import (
    OrganisationVersion, Organe, PosteOrganisation, CorrespondanceStructure,
    CorrespondanceGroupe, WG, GroupeCible, AffectationSousCommission,
)
from apps.governance.phoenix_services import propose_mapping
from apps.governance.phoenix_runtime import current_organisation_version
from apps.governance.organisation_permissions import can_manage_organisation, can_prepare_organisation, can_activate_organisation
from apps.governance.phoenix_operations import journal as record_journal
from .supervision_views import supervisor_context


def preferred_version():
    version = current_organisation_version()
    if not version:
        raise Http404("Aucune version d'organisation n'est enregistrée.")
    return version


def preparation_context(request):
    can_prepare = can_prepare_organisation(request.user)
    context = {} if can_prepare or can_activate_organisation(request.user) else supervisor_context(request)
    return {**context, 'can_prepare': can_prepare, 'can_manage': can_manage_organisation(request.user),
            'can_activate': can_activate_organisation(request.user)}


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PhoenixOrganisationView(View):
    def get(self, request):
        context = preparation_context(request)
        version = current_organisation_version()
        if version:
            version.name = 'Organisation CNE-ITP'
            organes = list(version.organes.prefetch_related(
                'postes__mandates__expert__user', 'groupes',
                'expert_assignments__expert__user', 'expert_assignments__expert__structure',
                'expert_assignments__source_ctm', 'expert_assignments__source_wg__ctm',
            ).all())
            today = timezone.localdate()
            for organe in organes:
                for poste in organe.postes.all():
                    poste.current_holders = [mandate for mandate in poste.mandates.all()
                        if mandate.status == 'ACTIVE' and mandate.capacity == 'ORGANISATION'
                        and mandate.start_date and mandate.start_date <= today
                        and (not mandate.end_date or mandate.end_date >= today)
                        and mandate.expert.status == 'ACTIVE' and mandate.expert.user.is_active]
                    poste.proposed_holders = [mandate for mandate in poste.mandates.all()
                        if mandate.status == 'PROPOSED']
            copil = next((organe for organe in organes if organe.type == 'COPIL'), None)
            st = next((organe for organe in organes if organe.type == 'ST'), None)
            poles = [organe for organe in organes if organe.type == 'ST_POLE']
            sc_list = [organe for organe in organes if organe.type == 'SC']
            sc_list.sort(key=lambda organe: organe.composition.get('tome', 99))
            for sc in sc_list:
                sc.migrated_experts = [
                    assignment for assignment in sc.expert_assignments.all()
                    if assignment.status == AffectationSousCommission.Status.MIGRATED
                ]
            pending_experts = list(version.expert_assignments.filter(
                status=AffectationSousCommission.Status.REVIEW,
            ).select_related('expert__user', 'source_ctm', 'source_wg').order_by(
                'expert__user__last_name', 'expert__user__first_name', 'expert_id',
            ))
            for assignment in pending_experts:
                if assignment.source_snapshot.get('source_status') != 'ACTIVE':
                    assignment.ui_reason = 'Activer ou confirmer le profil avant affectation.'
                elif assignment.source_kind == 'NO_SOURCE':
                    assignment.ui_reason = 'Renseigner le périmètre technique.'
                else:
                    assignment.ui_reason = 'Choisir la sous-commission correspondante.'
            entries = list(version.journal.select_related('actor')[:50])
            operation_labels = {'PREPARE_REFERENCE': 'Préparation du référentiel',
                'PREPARE_ADOPTED_REPORT': 'Préparation du rapport adopté',
                'PREPARE_SC_BUREAUX': 'Préparation des bureaux de sous-commission',
                'PREPARE_ANNEXE_ROLES': 'Fonctions nominatives proposées',
                'PROPOSE_MAPPING': 'Modification d’une correspondance',
                'VALIDATE_MAPPING': 'Validation d’une correspondance', 'PREPARATION_NOTE': 'Note de préparation',
                'CONFIGURE_VERSION': 'Référentiel', 'CONFIGURE_ORGANE': 'Organe', 'CONFIGURE_POSTE': 'Poste',
                'CONFIGURE_GT': 'Groupe de travail', 'CONFIGURE_MANDAT': 'Nomination', 'CONFIGURE_HABILITATION': 'Habilitation',
                'CONFIGURE_CIRCUIT': 'Circuit', 'CONFIGURE_RATTACHEMENT': 'Rattachement documentaire'}
            operation_labels.update({'MIGRATE_EXPERTS': 'Migration des experts vers les SC',
                                     'ROLLBACK_EXPERTS': 'Clôture d’un lot de migration'})
            for entry in entries:
                entry.operation_label = operation_labels.get(entry.operation, 'Décision sur l’organisation')
            context.update({
                'version': version, 'copil': copil, 'st': st,
                'copil_groups': [{'label': label, 'posts': [post for post in copil.postes.all() if post.category == code]}
                                 for code, label in PosteOrganisation.Category.choices] if copil else [],
                'copil_post_count': len(copil.postes.all()) if copil else 0,
                'st_post_count': (len(st.postes.all()) if st else 0) + sum(len(pole.postes.all()) for pole in poles),
                'poles': poles,
                'sc_list': sc_list,
                'migrated_expert_count': sum(len(sc.migrated_experts) for sc in sc_list),
                'pending_experts': pending_experts,
                'ctm_mappings': version.ctm_mappings.select_related('ctm', 'sc').order_by('ctm__number', 'nature'),
                'wg_mappings': version.wg_mappings.select_related('wg__ctm', 'sc', 'gt').order_by('wg__ctm__number', 'wg__number'),
                'journal': entries,
                'legacy_group_count': WG.objects.count(),
            })
        return render(request, 'pilotage/organisation.html', context)

    def post(self, request):
        if not can_manage_organisation(request.user):
            raise PermissionDenied('La gestion de l’organisation CNE-ITP exige une habilitation.')
        version = preferred_version()
        reason = request.POST.get('reason', '').strip()
        if request.POST.get('operation') != 'note' or not reason or len(reason) > 5000:
            messages.error(request, 'Renseigner une note de préparation de 1 à 5 000 caractères.')
        else:
            record_journal(request.user, version, 'PREPARATION_NOTE', 'organisation', reason=reason)
            messages.success(request, 'La note a été enregistrée au journal.')
        return redirect('/pilotage/organisation/#journal')


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PhoenixMappingView(View):
    def dispatch(self, request, *args, **kwargs):
        if not can_prepare_organisation(request.user):
            raise PermissionDenied('Une habilitation de préparation CNE-ITP est nécessaire.')
        return super().dispatch(request, *args, **kwargs)

    def mapping(self, kind, pk):
        if kind not in ('ctm', 'wg'):
            raise Http404
        model = CorrespondanceStructure if kind == 'ctm' else CorrespondanceGroupe
        return get_object_or_404(model.objects.select_related('version', 'sc'), pk=pk, version=preferred_version())

    def context(self, request, mapping, kind, error=''):
        return {'mapping': mapping, 'kind': kind, 'error': error,
                'can_manage': can_manage_organisation(request.user),
                'sc_list': mapping.version.organes.filter(type='SC'),
                'groups': GroupeCible.objects.filter(sc__version=mapping.version, status__in=['VALIDATED', 'ACTIVE'])}

    def get(self, request, kind, pk):
        self.mapping(kind, pk)
        return redirect('/pilotage/organisation/#sc')

    def post(self, request, kind, pk):
        mapping = self.mapping(kind, pk)
        try:
            sc_id = int(request.POST['sc_id']) if request.POST.get('sc_id') else None
            propose_mapping(request.user, kind, mapping.pk, sc_id, request.POST.get('domain', ''), request.POST.get('justification', ''))
        except (ValidationError, ValueError, Organe.DoesNotExist, IntegrityError) as error:
            message = '; '.join(error.messages) if isinstance(error, ValidationError) else 'La cible ou le périmètre proposé est invalide.'
            return render(request, 'pilotage/organisation_mapping.html', self.context(request, mapping, kind, message), status=400)
        return redirect('/pilotage/organisation/#sc')
