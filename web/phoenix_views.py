import csv
import io
from collections import Counter
from datetime import date, datetime, timedelta
from uuid import uuid4

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.governance.models import (OrganisationVersion, Organe, PosteOrganisation, GroupeCible, MandatOrganisation,
                                   HabilitationAction, RattachementDocumentaire, CircuitOrganisation, PiecePhoenix, DecisionPhoenix, JournalMigration, ParticipationPhoenix)
from apps.governance.phoenix_operations import CONFIG_MODELS, configure, object_version, readiness, activate, suspend, validate_mapping
from apps.governance.phoenix_rules import ACTIONS
from apps.governance.phoenix_services import has_organisation_action
from apps.governance.organisation_permissions import can_manage_organisation, can_activate_organisation
from apps.governance.phoenix_workflow import (accessible_dossiers, mandates_for, permitted_transitions, create_dossier,
    save_version, attach_piece, decide, save_inquiry, set_document_lock, plan_meeting, record_presence, PhoenixConflict, selected_mandate)
from apps.norms.models import NormeVersion
from apps.norms.diff_utils import build_inline_diff_segments
from .phoenix_forms import configuration_form, DossierCreateForm, ActivationForm
from .organisation_views import preparation_context, preferred_version


def version_context(request):
    version = preferred_version()
    # Le code technique historique n'est jamais exposé comme nom de produit.
    version.name = 'Organisation CNE-ITP'
    return {'version': version, 'can_manage': can_manage_organisation(request.user),
            'can_activate': can_activate_organisation(request.user)}


def error_message(error):
    return '; '.join(error.messages) if isinstance(error, ValidationError) else 'Les informations sont invalides ou le dossier a changé. Actualiser la page.'


FORM_SECTIONS = {
    'version': [('Référentiel', 'Nom et document source de cette édition de l’organisation.', ['name', 'source_document'])],
    'organe': [
        ('Identification', 'Identité de l’organe et dénomination confirmée par la source.', ['code', 'name', 'official_name']),
        ('Positionnement', 'Type et place de l’organe dans la structure CNE-ITP.', ['type', 'parent']),
        ('Périmètre', 'Étendue de compétence et effectifs prévus.', ['domain', 'composition']),
        ('Statut et traçabilité', 'État de préparation et source officielle de la décision.', ['status', 'source_reference']),
    ],
    'poste': [
        ('Rattachement', 'Organe auquel ce poste appartient.', ['organe']),
        ('Identification', 'Code, catégorie et fonction confirmée.', ['code', 'category', 'title']),
        ('Origine institutionnelle', 'Provenance de la proposition et structure requise.', ['origin_label', 'required_structure']),
        ('Statut et traçabilité', 'État de préparation et source officielle.', ['status', 'source_reference']),
        ('Dates affichées', 'Corriger l’affichage sans changer les horodatages d’audit enregistrés par le système.', ['display_created_at', 'display_updated_at', 'audit_date_reason']),
    ],
    'gt': [
        ('Rattachement', 'Sous-commission de rattachement du groupe de travail.', ['sc']),
        ('Identification', 'Code, intitulé et nature de l’activité.', ['code', 'name', 'activity']),
        ('Statut et traçabilité', 'État de préparation et source officielle.', ['status', 'source_reference']),
    ],
    'mandat': [
        ('Périmètre du mandat', 'Personne nommée et cible du mandat.', ['expert', 'poste', 'groupe']),
        ('Fonction exercée', 'Qualité et intitulé de la fonction.', ['function', 'capacity']),
        ('Nomination', 'Acte de nomination, période et état du mandat.', ['appointment_reference', 'start_date', 'end_date', 'status']),
    ],
    'habilitation': [
        ('Mandat', 'Mandat auquel l’habilitation est rattachée.', ['mandat']),
        ('Action et périmètre', 'Action autorisée et périmètre d’exercice.', ['action', 'perimeter']),
        ('Validité', 'Décision, dates de validité et état.', ['decision_reference', 'start_date', 'end_date', 'enabled']),
        ('Délégation', 'Habilitation source lorsque le pouvoir est délégué.', ['delegated_from']),
    ],
    'circuit': [
        ('Identification', 'Code et intitulé du circuit versionné.', ['code', 'name']),
        ('Configuration', 'États, transitions et conditions approuvés.', ['configuration']),
        ('Validation', 'Décision d’approbation et statut du circuit.', ['decision_reference', 'status']),
    ],
    'rattachement': [
        ('Document', 'Norme rattachée au dispositif.', ['norme']),
        ('Périmètre', 'Sous-commission, groupe et rôle documentaire.', ['sc', 'gt', 'role']),
        ('Validité', 'Décision, dates et état du rattachement.', ['decision_reference', 'effective_from', 'effective_to', 'status']),
    ],
}


def configuration_sections(form, kind):
    layout = FORM_SECTIONS.get(kind, [])
    rendered, used = [], set()
    for title, description, names in layout:
        fields = [form[name] for name in names if name in form.fields]
        if fields:
            used.update(names)
            rendered.append({'title': title, 'description': description, 'fields': fields})
    extra = [field for name, field in form.fields.items() if name not in used]
    if extra:
        rendered.append({'title': 'Informations complémentaires', 'description': 'Autres champs de cette fiche.', 'fields': extra})
    return rendered


def configuration_summary(instance, kind):
    if not instance:
        return {}
    summary = {'updated_at': instance.updated_at, 'updated_by': instance.updated_by, 'created_at': instance.created_at}
    if kind == 'organe':
        summary.update({'poste_count': instance.postes.count(), 'groupe_count': instance.groupes.count()})
    elif kind == 'poste':
        summary.update({'mandate_count': instance.mandates.count(),
                        'display_created_at': instance.display_created_at or instance.created_at,
                        'display_updated_at': instance.display_updated_at or instance.updated_at,
                        'created_date_corrected': bool(instance.display_created_at),
                        'updated_date_corrected': bool(instance.display_updated_at)})
    return summary


def configuration_return(kind, obj=None):
    if kind in ('habilitation', 'circuit', 'rattachement'):
        return reverse('web:phoenix_management')
    organ = None
    if obj:
        if kind == 'organe':
            organ = obj
        elif kind == 'poste':
            organ = obj.organe
        elif kind == 'gt':
            organ = obj.sc
        elif kind == 'mandat':
            organ = obj.poste.organe if obj.poste_id else obj.groupe.sc
    section = {'COPIL': 'copil', 'ST': 'st', 'ST_POLE': 'st', 'SC': 'sc'}.get(
        organ.type if organ else '', 'sc' if kind in ('gt', 'organe') else 'copil')
    return reverse('web:phoenix_organisation') + '#' + section


class PhoenixView(LoginRequiredMixin, View):
    login_url = '/se-connecter/'


class PhoenixManagementView(PhoenixView):
    def get(self, request):
        context = version_context(request)
        if not context['can_manage'] and not context['can_activate']:
            preparation_context(request)
        version = context['version']
        mandates = MandatOrganisation.objects.filter(Q(poste__organe__version=version) | Q(groupe__sc__version=version)).select_related('expert__user', 'poste__organe', 'groupe__sc')
        grants = HabilitationAction.objects.filter(mandat__in=mandates).select_related('mandat__expert__user', 'perimeter')
        for grant in grants:
            grant.action_label = ACTIONS.get(grant.action, grant.action)
        context.update({'readiness': readiness(version), 'organes': version.organes.all(),
            'posts': PosteOrganisation.objects.filter(organe__version=version).select_related('organe'),
            'groups': GroupeCible.objects.filter(sc__version=version).select_related('sc'), 'mandates': mandates,
            'grants': grants, 'circuits': version.circuits.all(),
            'bindings': RattachementDocumentaire.objects.filter(version=version).select_related('norme', 'sc', 'gt'),
            'kind_titles': [('poste', 'Poste'), ('gt', 'Groupe de travail'), ('mandat', 'Nomination'), ('habilitation', 'Habilitation'), ('circuit', 'Circuit'), ('rattachement', 'Rattachement documentaire')]})
        return render(request, 'pilotage/phoenix/management.html', context)


class PhoenixConfigurationView(PhoenixView):
    def context(self, request, kind, pk=None, data=None):
        if not can_manage_organisation(request.user):
            raise PermissionDenied('Une habilitation de gestion CNE-ITP est nécessaire.')
        context = version_context(request)
        if kind not in CONFIG_MODELS or (kind == 'version' and not pk):
            raise Http404
        instance = get_object_or_404(CONFIG_MODELS[kind], pk=pk) if pk else None
        if instance and object_version(instance).pk != context['version'].pk:
            raise Http404
        form = configuration_form(kind, context['version'], data=data, instance=instance)
        renewal_id = request.POST.get('renew_from') if data is not None else request.GET.get('renouveler')
        renewal_source = None
        if kind == 'mandat' and not instance and renewal_id and renewal_id.isdecimal():
            candidate = MandatOrganisation.objects.select_related('expert__user', 'poste__organe', 'groupe__sc').filter(pk=int(renewal_id)).first()
            if candidate and candidate.organisation_version.pk == context['version'].pk:
                renewal_source = candidate
                form.initial['status'] = 'PROPOSED'
                form.fields['status'].choices = [('PROPOSED', 'Proposé')]
                form.fields['status'].disabled = True
                form.fields['start_date'].required = True
                form.fields['start_date'].help_text = (
                    f'Date prévue du renouvellement, après la fin du mandat actuel ({candidate.end_date:%d/%m/%Y}).'
                    if candidate.end_date else
                    'Date prévue du renouvellement. Le mandat actuel doit être terminé avant son activation.'
                )
                form.fields['appointment_reference'].help_text = 'À compléter lorsque l’acte officiel sera disponible ; obligatoire pour passer au statut « En cours ».'
                if data is None:
                    form.initial.update({
                        'expert': candidate.expert_id, 'poste': candidate.poste_id,
                        'groupe': candidate.groupe_id, 'function': candidate.function,
                        'capacity': candidate.capacity,
                    })
        context.update({'kind': kind, 'instance': instance, 'form': form,
                        'sections': configuration_sections(form, kind) if kind in CONFIG_MODELS else [],
                        'summary': configuration_summary(instance, kind),
                        'is_new': instance is None,
                        'return_url': configuration_return(kind, instance),
                        'renewal_source': renewal_source,
                        'post_mandates': list(instance.mandates.select_related('expert__user').order_by('-created_at')) if kind == 'poste' and instance else [],
                        'page_title': {'version': 'Référentiel CNE-ITP', 'organe': 'Organe et périmètre', 'poste': 'Fonction et origine du poste', 'gt': 'Catalogue des GT', 'mandat': 'Nomination et mandat', 'habilitation': 'Pouvoirs et délégations', 'circuit': 'Règles du circuit', 'rattachement': 'Rattachement documentaire'}[kind]})
        if not data and not instance:
            for name in ('organe', 'sc', 'poste', 'groupe'):
                field = context['form'].fields.get(name)
                value = request.GET.get(name, '')
                if field and value.isdigit() and field.queryset.filter(pk=value).exists():
                    context['form'].initial[name] = value
        return context

    def get(self, request, kind, pk=None):
        return render(request, 'pilotage/phoenix/form.html', self.context(request, kind, pk))

    def post(self, request, kind, pk=None):
        context = self.context(request, kind, pk, request.POST)
        def invalid_form():
            if getattr(request, 'mobile_json', False):
                return JsonResponse({'errors': context['form'].errors.get_json_data()}, status=400)
            return render(request, 'pilotage/phoenix/form.html', context, status=400)
        if context['form'].is_valid():
            try:
                source = context['renewal_source']
                if request.POST.get('renew_from') and not source:
                    raise ValidationError('Le mandat à renouveler est introuvable dans cette édition.')
                if source:
                    cleaned = context['form'].cleaned_data
                    if (pk or cleaned['expert'].pk != source.expert_id or
                            getattr(cleaned.get('poste'), 'pk', None) != source.poste_id or
                            getattr(cleaned.get('groupe'), 'pk', None) != source.groupe_id or
                            cleaned['capacity'] != source.capacity or cleaned['status'] != 'PROPOSED'):
                        raise ValidationError('Le renouvellement conserve le titulaire, la cible et la qualité du mandat précédent ; il démarre comme proposition.')
                    if not cleaned['start_date']:
                        raise ValidationError('Indiquer la date prévue du renouvellement.')
                    if source.end_date and cleaned['start_date'] <= source.end_date:
                        context['form'].add_error(
                            'start_date',
                            f'La date prévue doit être postérieure à la fin du mandat actuel ({source.end_date:%d/%m/%Y}).',
                        )
                        return invalid_form()
                correction_reason = ''
                if kind == 'poste' and context['instance']:
                    cleaned = context['form'].cleaned_data
                    original_post = PosteOrganisation.objects.get(pk=pk)
                    corrected = any(cleaned[name] != getattr(original_post, name)
                                    for name in ('display_created_at', 'display_updated_at'))
                    if corrected:
                        motive = cleaned['audit_date_reason'].strip()
                        if not motive:
                            raise ValidationError('Préciser le motif de correction des dates affichées.')
                        shown_creation = cleaned['display_created_at'] or original_post.created_at
                        shown_update = cleaned['display_updated_at'] or timezone.now()
                        if shown_update < shown_creation:
                            raise ValidationError('La date de modification affichée ne peut pas précéder la date de création affichée.')
                        correction_reason = f'Correction des dates affichées du poste. Motif : {motive}'
                obj = configure(request.user, context['version'], kind, context['form'].cleaned_data, pk=pk,
                                reason=f'Renouvellement proposé du mandat {source.pk} ; mandat précédent conservé.' if source else correction_reason or 'Modification du référentiel CNE-ITP.')
                if getattr(request, 'mobile_json', False):
                    return JsonResponse({'id': obj.pk, 'message': 'Informations enregistrées.'})
                if source:
                    return redirect('web:phoenix_config_edit', kind='mandat', pk=obj.pk)
                return redirect(configuration_return(kind, obj))
            except (ValidationError, IntegrityError) as error:
                context['form'].add_error(None, error_message(error))
        return invalid_form()


class PhoenixActivationView(PhoenixView):
    def context(self, request, data=None):
        context = version_context(request)
        if not context['can_activate']:
            raise PermissionDenied('Une habilitation de mise en service de l’organisation est nécessaire.')
        context.update({'form': ActivationForm(data), 'page_title': 'Mise en service CNE-ITP', 'readiness': readiness(context['version']), 'is_activation': True})
        return context

    def get(self, request):
        return render(request, 'pilotage/phoenix/form.html', self.context(request))

    def post(self, request):
        context = self.context(request, request.POST)
        try:
            if request.POST.get('operation') == 'suspend':
                suspend(request.user, context['version'], request.POST.get('reason', ''))
                return redirect('web:phoenix_management')
            if context['form'].is_valid():
                activate(request.user, context['version'], context['form'].cleaned_data)
                return redirect('web:phoenix_management')
        except (ValidationError, IntegrityError) as error:
            context['form'].add_error(None, error_message(error))
        return render(request, 'pilotage/phoenix/form.html', context, status=400)


class PhoenixMappingDecisionView(PhoenixView):
    def post(self, request, kind, pk):
        try:
            validate_mapping(request.user, kind, pk, request.POST.get('decision_reference', ''),
                             request.POST.get('sc_id') or None, request.POST.get('gt_id') or None)
        except ValidationError as error:
            return HttpResponse(error_message(error), status=400, content_type='text/plain; charset=utf-8')
        return redirect('web:phoenix_organisation')


class PhoenixWorkspaceView(PhoenixView):
    def get(self, request):
        context = version_context(request)
        dossiers = accessible_dossiers(request.user).filter(circuit__version=context['version']).order_by('-updated_at')
        sc = request.GET.get('sc', '')
        if sc.isdecimal():
            dossiers = dossiers.filter(gt__sc_id=int(sc))
        types = Counter(dossiers.values_list('state', flat=True))
        today = timezone.localdate()
        try:
            start = parse_date(request.GET.get('from', '')) or today - timedelta(days=29)
            end = parse_date(request.GET.get('to', '')) or today
        except ValueError:
            start, end = today - timedelta(days=29), today
        if start > end:
            start, end = end, start
        if (end - start).days > 365:
            start = end - timedelta(days=365)
        events = JournalMigration.objects.filter(version=context['version'], target__in=[f'dossier:{pk}' for pk in dossiers.values_list('pk', flat=True)],
            created_at__date__gte=start, created_at__date__lte=end).select_related('actor', 'mandate__poste__organe', 'mandate__groupe__sc')
        user_options = list(events.exclude(actor_id__isnull=True).order_by().values('actor_id', 'actor_name').distinct())
        if request.GET.get('user', '').isdecimal():
            events = events.filter(actor_id=int(request.GET['user']))
        if request.GET.get('mandate', '').isdecimal():
            events = events.filter(mandate_id=int(request.GET['mandate']))
        if request.GET.get('organe', '').isdecimal():
            organe = get_object_or_404(Organe, pk=int(request.GET['organe']), version=context['version'])
            events = events.filter(Q(mandate__poste__organe=organe) | Q(mandate__poste__organe__parent=organe) | Q(mandate__groupe__sc=organe))
        if request.GET.get('action'):
            events = events.filter(operation=request.GET['action'][:100])
        if request.GET.get('document'):
            identifiers = list(dossiers.filter(Q(norme__title__icontains=request.GET['document'][:200]) | Q(norme__reference_number__icontains=request.GET['document'][:200])).values_list('pk', flat=True))
            events = events.filter(target__in=[f'dossier:{pk}' for pk in identifiers])
        entries = list(events.order_by('-created_at'))
        counts = Counter((event.actor_id, event.actor_name or 'Auteur non enregistré') for event in entries)
        actions = Counter(event.operation for event in entries)
        days = Counter(timezone.localdate(event.created_at).isoformat() for event in entries)
        labels = {'CREATE_DOSSIER':'Ouverture de dossier', 'EDIT_DOCUMENT':'Édition du texte', 'ATTACH_PIECE':'Pièce documentaire',
                  'TRANSITION':'Transition réalisée', 'RECORD_APPROVAL':'Avis enregistré', 'PUBLIC_INQUIRY':'Enquête publique',
                  'PLAN_MEETING':'Réunion planifiée', 'MEETING_PRESENCE':'Présence en réunion', 'LOCK_DOCUMENT':'Verrouillage', 'UNLOCK_DOCUMENT':'Libération du dossier'}
        dossier_references = {f'dossier:{d.pk}': d.norme.reference_number for d in dossiers}
        for entry in entries:
            entry.display_operation = labels.get(entry.operation, 'Opération du dossier')
            entry.dossier_url = reverse('web:phoenix_dossier', args=[int(entry.target.split(':')[1])])
            entry.dossier_reference = dossier_references.get(entry.target, '')
            document_version_id = entry.after.get('version_id') or entry.before.get('version_id')
            if document_version_id:
                entry.dossier_url += '?v2=' + str(document_version_id)
        query = request.GET.copy()
        query.pop('page', None)
        query.pop('activity_page', None)
        context.update({'page_title': 'Espace CNE-ITP', 'dossier_page': Paginator(dossiers, 25).get_page(request.GET.get('page')),
                        'mandates': mandates_for(request.user), 'organe_options': context['version'].organes.filter(type='SC'),
                        'selected_sc': sc, 'events': Paginator(entries, 25).get_page(request.GET.get('activity_page')),
                        'from': start.isoformat(), 'to': end.isoformat(), 'event_count': len(entries), 'organe_filters':context['version'].organes.all(),
                        'user_options': user_options, 'action_options': labels.items(), 'query':query.urlencode(),
                        'chart_data': {'stages': [{'label': key, 'count': value} for key, value in types.items()],
                                       'users': [{'label': key[1], 'count': value} for key, value in counts.items()],
                                       'actions': [{'label': labels.get(key, 'Opération'), 'count': value} for key, value in actions.items()],
                                       'timeline': [{'date':(start+timedelta(days=offset)).isoformat(), 'label':(start+timedelta(days=offset)).strftime('%d/%m'), 'count':days[(start+timedelta(days=offset)).isoformat()]} for offset in range((end-start).days+1)]}})
        return render(request, 'pilotage/phoenix/workspace.html', context)


class PhoenixDossierCreateView(PhoenixView):
    def get(self, request):
        context = version_context(request)
        context.update({'page_title': 'Nouveau dossier CNE-ITP', 'form': DossierCreateForm(user=request.user, version=context['version'])})
        return render(request, 'pilotage/phoenix/form.html', context)

    def post(self, request):
        context = version_context(request)
        form = DossierCreateForm(request.POST, user=request.user, version=context['version'])
        if form.is_valid():
            try:
                data = dict(form.cleaned_data)
                dossier = create_dossier(request.user, **data, origin={'ip':request.META.get('REMOTE_ADDR', ''), 'channel':'Web'})
                return redirect('web:phoenix_dossier', pk=dossier.pk)
            except (ValidationError, IntegrityError) as error:
                form.add_error(None, error_message(error))
        context.update({'page_title': 'Nouveau dossier CNE-ITP', 'form': form})
        return render(request, 'pilotage/phoenix/form.html', context, status=400)


class PhoenixDossierView(PhoenixView):
    def dossier(self, request, pk):
        return get_object_or_404(accessible_dossiers(request.user), pk=pk)

    def context(self, request, dossier):
        context = version_context(request)
        versions = list(NormeVersion.all_objects.filter(norme=dossier.norme).select_related('version_author').order_by('-version_number'))
        for item in versions:
            item.history_author = (item.version_author.get_full_name() or item.version_author.username) if item.version_author else 'Auteur non enregistré'
        selected = dossier.document_version
        previous = versions[1] if len(versions) > 1 else None
        if request.GET.get('v2'):
            if not request.GET['v2'].isdecimal():
                raise Http404
            selected = get_object_or_404(NormeVersion.all_objects, norme=dossier.norme, pk=request.GET['v2'])
            previous = next((item for item in versions if selected and item.version_number < selected.version_number), None)
        if request.GET.get('v1'):
            if not request.GET['v1'].isdecimal():
                raise Http404
            previous = get_object_or_404(NormeVersion.all_objects, norme=dossier.norme, pk=request.GET['v1']) if request.GET['v1'] != '0' else None
        mandates = list(mandates_for(request.user))
        options = []
        for mandate in mandates:
            label = mandate.function or str(mandate.poste or mandate.groupe)
            options.extend({'mandate': mandate, 'label': label, 'rule': rule, 'request_key': uuid4().hex} for rule in permitted_transitions(request.user, mandate, dossier))
        context.update({'page_title': dossier.norme.reference_number, 'dossier': dossier, 'versions': versions, 'selected': selected, 'previous': previous,
            'segments': build_inline_diff_segments(previous.content if previous else '', selected.content if selected else ''),
            'pieces': dossier.pieces.select_related('mandate__expert__user', 'version'),
            'events': dossier.decisions.select_related('expert__user', 'document_version'), 'enquiries': dossier.enquetes.select_related('report'),
            'meetings': dossier.reunions.prefetch_related('participants__mandate__expert__user'),
            'meeting_mandates': MandatOrganisation.objects.filter(Q(poste__organe__version=dossier.circuit.version) | Q(groupe__sc__version=dossier.circuit.version)).select_related('expert__user'),
            'mandates': mandates, 'transition_options': options,
            'can_edit': any(has_organisation_action(request.user, m, 'document.editer', dossier.norme, dossier.gt) for m in mandates),
            'can_attach': any(has_organisation_action(request.user, m, 'document.joindre', dossier.norme, dossier.gt) for m in mandates),
            'can_inquire': any(has_organisation_action(request.user, m, 'st.enquete', dossier.norme, dossier.gt) for m in mandates)})
        context['can_lock'] = any(has_organisation_action(request.user, m, 'document.verrouiller', dossier.norme, dossier.gt) for m in mandates)
        context['can_meet'] = any(has_organisation_action(request.user, m, 'reunion.planifier', dossier.norme, dossier.gt) for m in mandates)
        return context

    def get(self, request, pk):
        return render(request, 'pilotage/phoenix/dossier.html', self.context(request, self.dossier(request, pk)))

    def post(self, request, pk):
        dossier = self.dossier(request, pk)
        try:
            mandate = selected_mandate(request.user, int(request.POST['mandate']))
            revision = int(request.POST['revision'])
            operation = request.POST.get('operation')
            origin = {'ip':request.META.get('REMOTE_ADDR', ''), 'channel':'Web'}
            if operation == 'edit':
                save_version(request.user, mandate, pk, revision, request.POST.get('content', ''), request.POST.get('summary', ''), origin=origin)
            elif operation == 'attach':
                attach_piece(request.user, mandate, pk, revision, request.POST.get('kind', ''), request.POST.get('reference', ''), request.POST.get('content', ''), request.FILES.get('file'), origin=origin)
            elif operation == 'inquiry':
                save_inquiry(request.user, mandate, pk, revision, request.POST.get('reference', ''), date.fromisoformat(request.POST['starts_at']), date.fromisoformat(request.POST['ends_at']), request.POST.get('report_id') or None, origin=origin)
            elif operation in ('lock', 'unlock'):
                set_document_lock(request.user, mandate, pk, revision, operation == 'lock', origin=origin)
            elif operation == 'meeting':
                starts = datetime.fromisoformat(request.POST['starts_at'])
                if timezone.is_naive(starts):
                    starts = timezone.make_aware(starts)
                plan_meeting(request.user, mandate, pk, revision, request.POST.get('title', ''), request.POST.get('agenda', ''), starts, request.POST.get('location', ''), [int(pk) for pk in request.POST.getlist('participants')], origin=origin)
            elif operation == 'presence':
                record_presence(request.user, mandate, pk, revision, int(request.POST['participation_id']), request.POST.get('presence', ''), origin=origin)
            elif operation == 'decide':
                decide(request.user, mandate, pk, revision, request.POST.get('transition', ''), request.POST.get('decision_reference', ''), request.POST.get('reason', ''), request.POST.get('request_key', ''), {'ip': request.META.get('REMOTE_ADDR', ''), 'channel': 'Web'})
            else:
                raise ValidationError('Opération inconnue.')
            return redirect('web:phoenix_dossier', pk=pk)
        except (ValidationError, ValueError, KeyError, MandatOrganisation.DoesNotExist, PiecePhoenix.DoesNotExist, ParticipationPhoenix.DoesNotExist, IntegrityError, OperationalError) as error:
            dossier.refresh_from_db()
            context = self.context(request, dossier)
            context['error'] = error_message(error)
            return render(request, 'pilotage/phoenix/dossier.html', context, status=409 if isinstance(error, (PhoenixConflict, OperationalError)) else 400)


class PhoenixPieceDownloadView(PhoenixView):
    def get(self, request, pk):
        piece = get_object_or_404(PiecePhoenix.objects.filter(dossier__in=accessible_dossiers(request.user)), pk=pk)
        if not piece.file:
            raise Http404
        return FileResponse(piece.file.open('rb'), as_attachment=True, filename=piece.file.name.rsplit('/', 1)[-1])


class PhoenixExportView(PhoenixView):
    def get(self, request, pk=None):
        dossiers = accessible_dossiers(request.user)
        if pk:
            dossier = get_object_or_404(dossiers, pk=pk)
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from xml.sax.saxutils import escape
            stream = io.BytesIO()
            styles = getSampleStyleSheet()
            story = [Paragraph(escape(dossier.norme.reference_number + ' — ' + dossier.norme.title), styles['Title']),
                     Paragraph(escape(f'{dossier.gt.sc.code} / {dossier.gt.code} · {dossier.circuit.name} · {dossier.state}'), styles['Normal']), Spacer(1, 20)]
            if dossier.document_version:
                story.extend(Paragraph(escape(line) or ' ', styles['Normal']) for line in dossier.document_version.content.splitlines())
            SimpleDocTemplate(stream).build(story)
            stream.seek(0)
            return FileResponse(stream, as_attachment=True, filename='dossier-organisation.pdf', content_type='application/pdf')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="dossiers-organisation.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['Référence', 'Titre', 'SC', 'GT', 'Circuit', 'État'])
        for dossier in dossiers:
            fields = [dossier.norme.reference_number, dossier.norme.title, dossier.gt.sc.code, dossier.gt.code, dossier.circuit.name, dossier.state]
            writer.writerow(["'" + str(value) if str(value).startswith(('=', '+', '-', '@')) else value for value in fields])
        return response
