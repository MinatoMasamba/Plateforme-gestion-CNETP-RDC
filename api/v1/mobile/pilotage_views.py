from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import json

from django.db.models import Prefetch
from django.http import HttpRequest, QueryDict
from django.utils import timezone

from apps.experts.models import Expert
from apps.governance.models import (
    AffectationSousCommission, CTCProcessus, MandatOrganisation, Organe,
    OrganisationVersion, PermissionRequest, PosteOrganisation,
)
from apps.governance.phoenix_runtime import current_organisation_version
from apps.norms.models import Norme
from web.organisation_views import preparation_context
from web.pilotage_views import get_pilotage_context


class MobilePilotageViewSet(viewsets.ViewSet):
    """Endpoints JSON pour l'espace Copil (Comité de Pilotage)."""

    permission_classes = [IsAuthenticated]

    def _expert(self, request):
        return Expert.objects.filter(user=request.user).first()

    def _context_or_error(self, request):
        expert = self._expert(request)
        if not expert:
            return None, Response(
                {'detail': 'Profil expert introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        ctx = get_pilotage_context(expert)
        if not ctx:
            return None, Response(
                {'detail': "Accès réservé aux membres du Comité de Pilotage."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return ctx, None

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        ctx, error = self._context_or_error(request)
        if error:
            return error

        organisation = current_organisation_version()
        sc_assignments = AffectationSousCommission.objects.filter(
            version=organisation,
            status__in=[
                AffectationSousCommission.Status.MIGRATED,
                AffectationSousCommission.Status.REVIEW,
            ],
        ).select_related('expert__user')

        scs = []
        if organisation:
            org_scs = organisation.organes.filter(
                type=Organe.Type.SC,
                status__in=[
                    OrganisationVersion.Status.PROPOSED,
                    OrganisationVersion.Status.VALIDATED,
                    OrganisationVersion.Status.ACTIVE,
                ],
            ).prefetch_related(Prefetch(
                'expert_assignments', queryset=sc_assignments,
                to_attr='current_expert_assignments',
            )).order_by('code')
            for sc in org_scs:
                assignments = list(sc.current_expert_assignments)
                scs.append({
                    'id': sc.pk,
                    'code': sc.code,
                    'name': sc.official_name or sc.name,
                    'member_count': len(assignments),
                    'experts': [
                        a.expert.full_name or a.expert.user.username
                        for a in assignments
                    ],
                })

        migrated_expert_count = len({item.expert_id for item in sc_assignments})
        pending_sc_expert_count = (
            AffectationSousCommission.objects.filter(
                version=organisation,
                status=AffectationSousCommission.Status.REVIEW,
            ).count()
            if organisation else 0
        )
        normes_travaillees_count = Norme.objects.exclude(
            status__in=['PUBLISHED', 'ARCHIVED'],
        ).count()

        can_acknowledge = ctx.get('user_sub_role') in ('president', 'rapporteur')
        pending_reception_count = (
            CTCProcessus.objects.filter(
                current_stage='SIGNED_OUT',
                received_by_president__isnull=True,
            ).count()
            if ctx.get('user_sub_role') == 'president'
            else CTCProcessus.objects.filter(
                current_stage='SIGNED_OUT',
                received_by_rapporteur__isnull=True,
            ).count()
            if ctx.get('user_sub_role') == 'rapporteur'
            else 0
        ) if can_acknowledge else 0

        pending_requests = PermissionRequest.objects.filter(status='PENDING')
        pending_experts = Expert.objects.filter(status='PENDING')
        member_count = (
            MandatOrganisation.objects.filter(
                poste__organe__version=organisation,
                poste__organe__type__in=[
                    Organe.Type.COPIL,
                    Organe.Type.ST,
                    Organe.Type.ST_POLE,
                ],
                status='ACTIVE',
                capacity='ORGANISATION',
            ).values('expert_id').distinct().count()
            if organisation else 0
        )
        expert = self._expert(request)
        structure = expert.structure
        structure_label = ''
        if structure:
            structure_label = structure.name
            if structure.acronym:
                structure_label = f'{structure_label} ({structure.acronym})'

        return Response({
            'college': ctx.get('pilotage_college'),
            'college_label': ctx.get('college_label'),
            'sub_role': ctx.get('user_sub_role'),
            'sub_role_label': ctx.get('user_sub_role_label'),
            'member_count': member_count,
            'profile': {
                'full_name': expert.full_name or expert.user.get_full_name(),
                'role': f"{ctx.get('college_label')} · {ctx['poste'].title if ctx.get('poste') else ctx.get('user_sub_role_label')}",
                'structure': structure_label,
                'status': expert.get_status_display(),
                'appointment_date': expert.appointment_date,
            },
            'counts': {
                'sous_commissions': len(scs),
                'experts': migrated_expert_count,
                'a_examiner': pending_sc_expert_count,
                'normes_travaillees': normes_travaillees_count,
            },
            'scs': scs,
            'pending': {
                'cadrages': ctx.get('pending_cadrages_count', 0),
                'reception': pending_reception_count,
                'adhesions': pending_experts.count(),
                'derogations': pending_requests.count(),
            },
            'permissions': {key: value for key, value in ctx.items()
                            if key.startswith('can_') and isinstance(value, bool)},
            'platform_locked': ctx['platform_locked'],
            'panels': {
                'cadrages': [{
                    'id': item['cadrage'].pk,
                    'reference': item['cadrage'].norme.reference_number,
                    'title': item['cadrage'].norme.title,
                    'action': item['action'], 'label': item['label'],
                    'blocked': item['blocked'],
                } for item in ctx['pending_cadrages']],
                'reception': [{
                    'id': item.pk, 'reference': item.norme.reference_number,
                    'title': item.norme.title,
                    'signed_by': item.signed_out_by.full_name if item.signed_out_by else '',
                } for item in ctx['pending_pilotage_reception']],
                'adhesions': [{
                    'id': item.pk, 'name': item.full_name,
                    'email': item.user.email,
                    'structure': item.structure.name if item.structure else '',
                    'date': item.created_at,
                } for item in ctx['pending_experts']],
                'derogations': [{
                    'id': item.pk, 'name': item.requester.full_name,
                    'structure': item.requester.structure.name if item.requester.structure else '',
                    'date': item.created_at, 'resource': item.restricted_resource,
                    'reason': item.reason,
                } for item in ctx['pending_requests']],
            },
        })

    @action(detail=False, methods=['post'])
    def command(self, request):
        """Adapt JSON input to the same authorized business actions as the web UI."""
        from web.pilotage_views import (
            PilotageAcknowledgeReceptionView, PilotageApproveRequestView,
            PilotageCadrageActionView, PilotageExpertStatusActionView,
            PilotagePlatformFreezeToggleView,
        )
        ctx, error = self._context_or_error(request)
        if error:
            return error
        commands = {
            'cadrage': ('can_trigger_steps', PilotageCadrageActionView),
            'reception': ('can_acknowledge_reception', PilotageAcknowledgeReceptionView),
            'adhesion': ('can_manage_access', PilotageExpertStatusActionView),
            'derogation': ('can_approve_requests', PilotageApproveRequestView),
            'freeze': (None, PilotagePlatformFreezeToggleView),
        }
        kind = request.data.get('kind')
        if kind not in commands:
            return Response({'detail': 'Action inconnue.'}, status=400)
        permission, view = commands[kind]
        if permission and not ctx.get(permission):
            return Response({'detail': 'Action non autorisée.'}, status=403)
        if kind != 'freeze':
            try:
                pk = int(request.data.get('id'))
            except (TypeError, ValueError):
                return Response({'detail': 'Identifiant invalide.'}, status=400)
        # Authentication is provided by DRF; each web handler also checks the
        # actor's mandate, stage and platform lock. No session/CSRF bypass URL.
        adapted = HttpRequest()
        adapted.method = 'POST'
        adapted.path = request.path
        adapted.POST = QueryDict('', mutable=True)
        adapted.POST.update({
            key: value for key, value in request.data.items()
            if key not in ('kind', 'id') and isinstance(value, (str, int, bool))
        })
        adapted.user = request.user
        adapted.META['HTTP_HOST'] = request.get_host()
        result = view().post(adapted, **({'pk': pk} if kind != 'freeze' else {}))
        return Response(json.loads(result.content), status=result.status_code)

    @action(detail=False, methods=['get'])
    def directoire(self, request):
        from web.pilotage_views import _BUREAU_DIRECTOIRE_POSTES, _cadrages_for_subrole
        ctx, error = self._context_or_error(request)
        if error:
            return error
        if not ctx['can_trigger_steps']:
            return Response({'detail': 'Accès réservé au Bureau Directoire.'}, status=403)
        return Response({'profile': {'name': request.user.get_full_name(),
                                     'initials': (request.user.first_name[:1] + request.user.last_name[:1]).upper()},
                         'posts': [{
            **meta, 'is_mine': meta['sub_role'] == ctx['user_sub_role'],
            'reception': [{
                'id': proc.pk, 'reference': proc.norme.reference_number,
                'title': proc.norme.title,
                'signed_by': proc.signed_out_by.full_name if proc.signed_out_by else '',
            } for proc in ctx['pending_pilotage_reception']]
                         if meta['sub_role'] == ctx['user_sub_role'] else [],
            'phases': [{
                'phase': group['phase'], 'label': group['label'],
                'items': [{
                    'id': item['cadrage'].pk,
                    'reference': item['cadrage'].norme.reference_number,
                    'title': item['cadrage'].norme.title,
                    'action': item['action'], 'label': item['label'],
                    'blocked': item['blocked'] or meta['sub_role'] != ctx['user_sub_role'],
                } for item in group['items']],
            } for group in _cadrages_for_subrole(meta['sub_role'])],
        } for meta in _BUREAU_DIRECTOIRE_POSTES]})

    @action(detail=False, methods=['get'])
    def instructions(self, request):
        from web.production_views import demandes_visibles, peut_transitionner
        from apps.governance.models import Demande
        ctx, error = self._context_or_error(request)
        if error:
            return error
        expert = self._expert(request)
        return Response({'items': [{
            'id': d.pk, 'type': d.get_type_display(), 'title': d.objet,
            'status': d.get_statut_display(), 'sender': d.emetteur.full_name,
            'recipient': d.destinataire.full_name if d.destinataire else '',
            'transitions': [{'value': s, 'label': dict(Demande.STATUS_CHOICES)[s]}
                            for s in Demande.TRANSITIONS.get(d.statut, [])]
                           if peut_transitionner(expert, ctx, d) else [],
        } for d in demandes_visibles(expert, ctx).order_by('-created_at')]})

    @action(detail=False, methods=['get'])
    def activity(self, request):
        from apps.governance.activity_supervision import (
            activity_access_for, calculate_scope_metrics, historical_sc_rows,
        )
        from web.activity_views import _period
        if not activity_access_for(request.user).get('can_view_aggregates'):
            return Response({'detail': 'Accès non autorisé.'}, status=403)
        start, end = _period(request)
        rows = historical_sc_rows(start, end)
        current_rows = [row for row in rows if row['kind'] == 'current']
        groups = [group for row in current_rows
                  for group in Organe.objects.get(pk=row['id']).groupes.all()]
        return Response({
            'start': start, 'end': end,
            'group_count': len(groups),
            'metrics': calculate_scope_metrics(start=start, end=end,
                                              target_group_ids=[g.pk for g in groups]),
            'subcommissions': [{
                'id': row['id'], 'code': row['code'], 'name': row['name'],
                'group_count': row['group_count'],
            } for row in current_rows],
        })

    @action(detail=False, methods=['get'], url_path='subcommission/(?P<sc_id>[0-9]+)')
    def subcommission(self, request, sc_id=None):
        from django.shortcuts import get_object_or_404
        from apps.governance.activity_supervision import activity_access_for, calculate_scope_metrics
        from web.activity_views import _period, _ctm_for_sc
        from apps.governance.phoenix_models import RattachementDocumentaire
        if not activity_access_for(request.user).get('can_view_aggregates'):
            return Response({'detail': 'Accès non autorisé.'}, status=403)
        sc = get_object_or_404(Organe, pk=sc_id, type=Organe.Type.SC,
                              version=current_organisation_version())
        start, end = _period(request)
        groups = list(sc.groupes.order_by('code'))
        bindings = list(RattachementDocumentaire.objects.filter(sc=sc).select_related('norme', 'gt'))
        norms = {key: [] for key in ('waiting', 'working', 'produced', 'unconfirmed')}
        def add_norm(norme, confirmed=True):
            key = ('unconfirmed' if not confirmed else 'produced'
                   if norme.status in {'ADOPTED', 'HOMOLOGATED', 'PUBLISHED', 'ARCHIVED'}
                   else 'waiting' if norme.status in {'CTM_REVIEW', 'LEGISTIC_REVIEW', 'PUBLIC_INQUIRY', 'PILOTAGE_REVIEW', 'FINAL_REVIEW'}
                   else 'working')
            if not any(n['id'] == norme.pk for n in norms[key]):
                norms[key].append({'id': norme.pk, 'title': norme.title, 'status': norme.get_status_display()})
        for binding in bindings:
            add_norm(binding.norme, binding.status == 'VALIDATED' and (not binding.gt_id or binding.gt.sc_id == sc.pk))
        if not bindings:
            ctm = _ctm_for_sc(sc)
            if ctm:
                for norme in Norme.objects.filter(ctm=ctm).order_by('title'):
                    add_norm(norme)
        today = timezone.localdate()
        def holder(post):
            return next((m.expert.full_name for m in post.mandates.all()
                         if m.status == 'ACTIVE' and m.capacity == 'ORGANISATION'
                         and (not m.start_date or m.start_date <= today)
                         and (not m.end_date or m.end_date >= today)), '')
        return Response({
            'id': sc.pk, 'code': sc.code, 'name': sc.official_name or sc.name,
            'start': start, 'end': end,
            'norms': norms,
            'coordination': [{'title': p.title or p.code, 'holder': holder(p)}
                             for p in sc.postes.prefetch_related('mandates__expert').order_by('code')],
            'groups': [{
                'id': g.pk, 'code': g.code, 'name': g.name,
                'metrics': calculate_scope_metrics(start=start, end=end, target_group=g),
                'tasks': [{'title': t.titre, 'status': t.get_status_display()} for t in g.tasks.all()]
                         if activity_access_for(request.user).get('can_view_contributions') else [],
            } for g in groups],
        })

    @action(detail=False, methods=['get', 'post'], url_path='configuration/(?P<kind>[a-z]+)')
    def configuration(self, request, kind=None):
        from django import forms
        from web.phoenix_views import PhoenixConfigurationView
        adapted = HttpRequest()
        adapted.user = request.user
        adapted.method = request.method
        adapted.mobile_json = True
        adapted.GET = request.query_params.copy()
        adapted.POST = QueryDict('', mutable=True)
        pk = request.query_params.get('id')
        if pk:
            try:
                pk = int(pk)
            except ValueError:
                return Response({'detail': 'Identifiant invalide.'}, status=400)
        view = PhoenixConfigurationView()
        if request.method == 'POST':
            for key, value in request.data.items():
                if isinstance(value, list):
                    adapted.POST.setlist(key, value)
                else:
                    adapted.POST[key] = value if value is not None else ''
            result = view.post(adapted, kind, pk)
            return Response(json.loads(result.content), status=result.status_code)
        context = view.context(adapted, kind, pk)
        form = context['form']
        for name in ('parent', 'type'):
            field = form.fields.get(name)
            value = request.query_params.get(name)
            if field and value:
                if hasattr(field, 'queryset') and value.isdigit() and field.queryset.filter(pk=value).exists():
                    form.initial[name] = value
                elif hasattr(field, 'choices') and value in dict(field.choices):
                    form.initial[name] = value
        def options(choices):
            result = []
            for value, label in choices:
                if isinstance(label, (list, tuple)):
                    result.extend(options(label))
                else:
                    result.append({'value': str(value), 'label': str(label)})
            return result
        fields = []
        for name, field in form.fields.items():
            value = form[name].value()
            if isinstance(value, (dict, list)) and not isinstance(field, forms.MultipleChoiceField):
                value = json.dumps(value, ensure_ascii=False)
            fields.append({
                'name': name, 'label': str(field.label or name),
                'required': field.required, 'disabled': field.disabled,
                'help': str(field.help_text), 'value': value,
                'type': 'boolean' if isinstance(field, forms.BooleanField) else 'choice'
                        if hasattr(field, 'choices') else 'multiline'
                        if isinstance(field.widget, forms.Textarea) else 'text',
                'options': options(field.choices) if hasattr(field, 'choices') else [],
            })
        return Response({'title': context['page_title'], 'fields': fields})

    @action(detail=False, methods=['get'])
    def organisation(self, request):
        expert = self._expert(request)
        if not expert:
            return Response(
                {'detail': 'Profil expert introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        ctx = get_pilotage_context(expert)
        preparation = preparation_context(request)
        if not ctx and not any(
            preparation.get(key)
            for key in ('can_manage', 'can_prepare', 'can_activate')
        ):
            return Response(
                {'detail': "Accès réservé à l'organisation CNE-ITP."},
                status=status.HTTP_403_FORBIDDEN,
            )

        version = current_organisation_version()
        if not version:
            return Response(
                {"detail": "Le référentiel CNE-ITP n'est pas encore chargé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        today = timezone.localdate()
        organes = list(
            version.organes.prefetch_related(
                'postes__mandates__expert__user',
                'postes__mandates__expert__structure',
                'groupes',
                'expert_assignments__expert__user',
                'expert_assignments__expert__structure',
            ).all()
        )
        for organe in organes:
            for poste in organe.postes.all():
                poste.current_holders = [
                    mandate
                    for mandate in poste.mandates.all()
                    if mandate.status == 'ACTIVE'
                    and mandate.capacity == 'ORGANISATION'
                    and mandate.start_date
                    and mandate.start_date <= today
                    and (not mandate.end_date or mandate.end_date >= today)
                    and mandate.expert.status == 'ACTIVE'
                    and mandate.expert.user.is_active
                ]
                poste.proposed_holders = [
                    mandate
                    for mandate in poste.mandates.all()
                    if mandate.status == 'PROPOSED'
                ]

        def expert_name(value):
            return (
                getattr(value.expert, 'full_name', '')
                or value.expert.user.get_full_name()
                or value.expert.user.username
            )

        def holder_payload(mandate):
            return {
                'name': expert_name(mandate),
                'reference': mandate.appointment_reference,
                'start_date': (
                    mandate.start_date.isoformat()
                    if mandate.start_date else None
                ),
            }

        def post_payload(poste):
            return {
                'id': poste.pk,
                'code': poste.code,
                'title': poste.title or 'Fonction à renseigner',
                'origin': poste.origin_label or 'À renseigner',
                'status': poste.get_status_display(),
                'category': poste.category,
                'holders': [
                    holder_payload(mandate)
                    for mandate in poste.current_holders
                ],
                'proposed_holders': [
                    holder_payload(mandate)
                    for mandate in poste.proposed_holders
                ],
            }

        copil = next(
            (organe for organe in organes if organe.type == Organe.Type.COPIL),
            None,
        )
        st = next(
            (organe for organe in organes if organe.type == Organe.Type.ST),
            None,
        )
        poles = [
            organe for organe in organes if organe.type == Organe.Type.ST_POLE
        ]
        sc_list = [
            organe for organe in organes if organe.type == Organe.Type.SC
        ]
        sc_list.sort(
            key=lambda organe: (organe.composition or {}).get('tome', 99)
        )

        copil_groups = []
        if copil:
            copil_posts = list(copil.postes.all())
            for code, label in PosteOrganisation.Category.choices:
                posts = [
                    post_payload(poste)
                    for poste in copil_posts
                    if poste.category == code
                ]
                if posts:
                    copil_groups.append(
                        {'code': code, 'label': label, 'posts': posts}
                    )

        st_groups = []
        if st:
            st_groups.append({
                'code': st.code,
                'label': 'Coordination',
                'posts': [post_payload(poste) for poste in st.postes.all()],
            })
        for pole in poles:
            st_groups.append({
                'code': pole.code,
                'label': pole.official_name or pole.name,
                'posts': [
                    post_payload(poste) for poste in pole.postes.all()
                ],
            })

        scs = []
        for sc in sc_list:
            migrated_experts = [
                assignment
                for assignment in sc.expert_assignments.all()
                if assignment.status == AffectationSousCommission.Status.MIGRATED
            ]
            scs.append({
                'id': sc.pk,
                'code': sc.code,
                'name': sc.name,
                'official_name': sc.official_name or sc.name,
                'status': sc.get_status_display(),
                'domain': sc.domain,
                'proposed_bureau_count': sum(
                    len(poste.proposed_holders) for poste in sc.postes.all()
                ),
                'migrated_experts': [
                    {
                        'name': expert_name(assignment),
                        'structure': (
                            assignment.expert.structure.acronym
                            or assignment.expert.structure.name
                        ),
                    }
                    for assignment in migrated_experts
                ],
                'posts': [
                    post_payload(poste) for poste in sc.postes.all()
                ],
                'groups': [
                    {
                        'id': group.pk,
                        'code': group.code,
                        'name': group.name,
                        'mission': group.mission,
                        'activity': group.get_activity_display(),
                        'status': group.get_status_display(),
                    }
                    for group in sc.groupes.all()
                ],
            })

        pending_experts = list(
            version.expert_assignments.filter(
                status=AffectationSousCommission.Status.REVIEW,
            ).select_related(
                'expert__user',
                'expert__structure',
                'source_ctm',
                'source_wg',
            ).order_by(
                'expert__user__last_name',
                'expert__user__first_name',
                'expert_id',
            )
        )
        pending_payload = []
        for assignment in pending_experts:
            if assignment.source_snapshot.get('source_status') != 'ACTIVE':
                reason = 'Activer ou confirmer le profil avant affectation.'
            elif assignment.source_kind == 'NO_SOURCE':
                reason = 'Renseigner le périmètre technique.'
            else:
                reason = 'Choisir la sous-commission correspondante.'
            pending_payload.append({
                'name': expert_name(assignment),
                'structure': (
                    assignment.expert.structure.acronym
                    or assignment.expert.structure.name
                ),
                'reason': reason,
            })

        operation_labels = {
            'PREPARE_REFERENCE': 'Préparation du référentiel',
            'PREPARE_ADOPTED_REPORT': 'Préparation du rapport adopté',
            'PREPARE_SC_BUREAUX': 'Préparation des bureaux de sous-commission',
            'PREPARE_ANNEXE_ROLES': 'Fonctions nominatives proposées',
            'PROPOSE_MAPPING': "Modification d'une correspondance",
            'VALIDATE_MAPPING': "Validation d'une correspondance",
            'PREPARATION_NOTE': 'Note de préparation',
            'CONFIGURE_VERSION': 'Référentiel',
            'CONFIGURE_ORGANE': 'Organe',
            'CONFIGURE_POSTE': 'Poste',
            'CONFIGURE_GT': 'Groupe de travail',
            'CONFIGURE_MANDAT': 'Nomination',
            'CONFIGURE_HABILITATION': 'Habilitation',
            'CONFIGURE_CIRCUIT': 'Circuit',
            'CONFIGURE_RATTACHEMENT': 'Rattachement documentaire',
            'MIGRATE_EXPERTS': 'Migration des experts vers les SC',
            'ROLLBACK_EXPERTS': "Clôture d'un lot de migration",
        }
        journal_payload = []
        for entry in version.journal.select_related('actor')[:50]:
            actor = entry.actor
            actor_name = (
                actor.get_full_name() or actor.username if actor
                else 'Non enregistré'
            )
            journal_payload.append({
                'created_at': entry.created_at.isoformat(),
                'actor': actor_name,
                'operation': operation_labels.get(
                    entry.operation,
                    "Décision sur l'organisation",
                ),
                'reason': entry.reason,
            })

        copil_post_count = len(copil.postes.all()) if copil else 0
        st_post_count = (
            len(st.postes.all()) if st else 0
        ) + sum(len(pole.postes.all()) for pole in poles)

        return Response({
            'can_manage': bool(preparation.get('can_manage')),
            'ids': {'version': version.pk, 'copil': copil.pk if copil else None,
                    'st': st.pk if st else None},
            'version': {
                'code': version.code,
                'status': version.status,
                'status_label': version.get_status_display(),
                'source_document': version.source_document,
            },
            'counts': {
                'copil_posts': copil_post_count,
                'st_posts': st_post_count,
                'subcommissions': len(sc_list),
                'experts': sum(
                    len(sc['migrated_experts']) for sc in scs
                ),
                'pending': len(pending_payload),
            },
            'copil_groups': copil_groups,
            'st_groups': st_groups,
            'subcommissions': scs,
            'pending_experts': pending_payload,
            'journal': journal_payload,
        })
