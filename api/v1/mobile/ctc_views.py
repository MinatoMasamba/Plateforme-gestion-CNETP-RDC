from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.experts.models import Expert
from apps.governance.models import CTCProcessus
from web.ctc_views import get_ctc_context


class MobileCTCViewSet(viewsets.ViewSet):
    """Endpoints JSON pour l'espace Coordination technique (CTC).

    Réutilise la logique de contexte/privilèges du web (`get_ctc_context`)
    et les statistiques partagées (`build_ctc_statistics`).
    """

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
        ctx = get_ctc_context(expert)
        if not ctx:
            return None, Response(
                {'detail': "Accès réservé aux membres de la Coordination technique."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return ctx, None

    def _serialize_dossier(self, processus):
        norme = processus.norme
        return {
            'id': processus.id,
            'norme_id': norme.id if norme else None,
            'reference': norme.reference_number if norme else '',
            'title': norme.title if norme else '',
            'stage': processus.current_stage,
            'stage_label': processus.get_current_stage_display(),
            'updated_at': processus.updated_at.isoformat() if processus.updated_at else None,
        }

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        ctx, error = self._context_or_error(request)
        if error:
            return error

        from web.ctc_statistics import build_ctc_statistics
        stats = build_ctc_statistics()

        dossiers = (
            CTCProcessus.objects
            .select_related('norme')
            .order_by('-updated_at')
        )

        assignation_tasks = []
        for processus in ctx.get('active_processus', []):
            assignation_tasks.append({
                'type_label': 'Traitement CTC',
                'reference': processus.norme.reference_number if processus.norme else '',
                'title': processus.norme.title if processus.norme else '',
                'status_display': processus.get_current_stage_display(),
            })

        return Response({
            'is_ctc': True,
            'ctc_sub_role': ctx.get('ctc_sub_role'),
            'pole_label': ctx.get('pole_label'),
            'counts': {
                'dossiers': dossiers.count(),
                'assignations': len(assignation_tasks),
                'normes_suivies': stats.get('norm_count', 0),
                'taches_en_retard': stats.get('overdue_count', 0),
            },
            'dossiers': [self._serialize_dossier(d) for d in dossiers[:20]],
            'assignations': assignation_tasks[:20],
        })

    @action(detail=False, methods=['get'])
    def dossiers(self, request):
        ctx, error = self._context_or_error(request)
        if error:
            return error

        qs = (
            CTCProcessus.objects
            .select_related('norme')
            .order_by('-updated_at')
        )
        return Response({
            'count': qs.count(),
            'results': [self._serialize_dossier(d) for d in qs],
        })

    @action(detail=False, methods=['get'])
    def assignations(self, request):
        ctx, error = self._context_or_error(request)
        if error:
            return error

        tasks = []
        for processus in ctx.get('active_processus', []):
            tasks.append({
                'type_label': 'Traitement CTC',
                'reference': processus.norme.reference_number if processus.norme else '',
                'title': processus.norme.title if processus.norme else '',
                'status_display': processus.get_current_stage_display(),
            })
        return Response({'count': len(tasks), 'results': tasks})
