from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import Prefetch

from apps.experts.models import Expert
from apps.governance.models import (
    AffectationSousCommission, CTCProcessus, Organe, OrganisationVersion,
    PermissionRequest,
)
from apps.governance.phoenix_runtime import current_organisation_version
from apps.norms.models import Norme
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

        return Response({
            'college': ctx.get('pilotage_college'),
            'college_label': ctx.get('college_label'),
            'sub_role': ctx.get('user_sub_role'),
            'sub_role_label': ctx.get('user_sub_role_label'),
            'counts': {
                'sous_commissions': len(scs),
                'experts': migrated_expert_count,
                'a_examiner': pending_sc_expert_count,
                'normes_travaillees': normes_travaillees_count,
            },
            'scs': scs,
            'pending': {
                'cadrages': 0,
                'reception': pending_reception_count,
                'adhesions': pending_experts.count(),
                'derogations': pending_requests.count(),
            },
        })
