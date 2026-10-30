from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone

from apps.experts.models import Expert
from apps.norms.models import Norme
from apps.governance.models import CTCProcessus, CTCOperationalRequest, PlatformFreeze, CTM, Demande
from apps.mobileapp.signals import create_notification_for_user
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
            'sidebar_nav_config': ctx.get('sidebar_nav_config', {}),
            'can_admin_system': ctx.get('can_admin_system', False),
            'blocked_political': ctx.get('blocked_political', False),
            'counts': {
                'dossiers': dossiers.count(),
                'assignations': len(assignation_tasks),
                'normes_suivies': stats.get('norm_count', 0),
                'taches_en_retard': stats.get('overdue_count', 0),
                'demandes_en_attente': ctx.get('pending_ctc_requests_count', 0),
                'sous_commissions': stats.get('sc_count', 0),
                'groupes': stats.get('group_count', 0),
                'taches': stats.get('task_count', 0),
            },
            'stage_rows': stats.get('stage_rows', []),
            'group_norm_rows': stats.get('group_norm_rows', []),
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

    @action(detail=False, methods=['get'])
    def experts(self, request):
        ctx, error = self._context_or_error(request)
        if error:
            return error
        from web.ctc_experts import build_expert_directory
        directory = build_expert_directory(self._expert(request))
        return Response({
            'count': directory['total'],
            'complete': directory['complete'],
            'incomplete': directory['incomplete'],
            'without_login': directory['without_login'],
            'results': [
                {key: row[key] for key in (
                    'id', 'name', 'structure', 'sc_code', 'sc_name',
                    'affectation_label', 'profile_status',
                )}
                for row in directory['rows']
            ],
            'referential': directory['referential'],
        })

    @action(detail=False, methods=['get'])
    def tracabilite(self, request):
        ctx, error = self._context_or_error(request)
        if error:
            return error
        from web.ctc_experts import build_traceability
        rows = build_traceability(self._expert(request))
        return Response({
            'count': len(rows),
            'results': [
                {key: row[key] for key in (
                    'id', 'timestamp', 'actor', 'action', 'object',
                    'reference', 'title', 'channel',
                )}
                for row in rows
            ],
        })

    @action(detail=False, methods=['get'])
    def instructions(self, request):
        ctx, error = self._context_or_error(request)
        if error:
            return error
        instructions = list(Demande.objects.filter(type='INSTRUCTION').select_related('emetteur__user').order_by('-created_at'))
        general = next((item for item in instructions if item.sous_commission_id is None and item.groupe_id is None), None)
        specific = {}
        for item in instructions:
            if item.sous_commission_id and item.sous_commission_id not in specific:
                specific[item.sous_commission_id] = item

        def serialize(item):
            if item is None:
                return None
            return {
                'id': item.pk,
                'objet': item.objet,
                'message': item.message,
                'statut': item.get_statut_display(),
                'emetteur': item.emetteur.full_name if item.emetteur else None,
                'echeance': item.echeance.isoformat() if item.echeance else None,
                'nb_normes': item.nb_normes,
                'portee': 'Spécifique' if item.sous_commission_id else 'Générale',
            }

        ctms = CTM.objects.filter(number__in=range(1, 8)).order_by('number')
        return Response({
            'general': serialize(general),
            'ctms': [
                {
                    'id': ctm.pk,
                    'number': ctm.number,
                    'name': ctm.name,
                    'last_instruction': serialize(specific.get(ctm.pk) or general),
                }
                for ctm in ctms
            ],
        })

    def _norme_results(self, statuses):
        rows = Norme.all_objects.filter(status__in=statuses).order_by('-updated_at', 'reference_number')
        return {
            'count': rows.count(),
            'results': [
                {
                    'id': norme.pk,
                    'reference': norme.reference_number,
                    'title': norme.title,
                    'status': norme.get_status_display(),
                    'updated_at': norme.updated_at.isoformat() if norme.updated_at else None,
                }
                for norme in rows
            ],
        }

    @action(detail=False, methods=['get'])
    def homologations(self, request):
        ctx, error = self._context_or_error(request)
        if error:
            return error
        return Response(self._norme_results(['HOMOLOGATED', 'PUBLISHED']))

    @action(detail=False, methods=['get'])
    def archives(self, request):
        ctx, error = self._context_or_error(request)
        if error:
            return error
        return Response(self._norme_results(['ARCHIVED']))

    @action(detail=False, methods=['get'])
    def requests(self, request):
        ctx, error = self._context_or_error(request)
        if error:
            return error
        pending = ctx.get('pending_ctc_requests', []) if ctx.get('ctc_sub_role') == 'assistant_executif' else []
        results = [{
            'id': item.pk,
            'restricted_resource': item.restricted_resource,
            'reason': item.reason,
            'requester': item.requester.full_name or item.requester.user.email,
            'created_at': item.created_at.isoformat(),
            'status': item.status,
            'status_label': item.get_status_display(),
        } for item in pending]
        return Response({'count': len(results), 'results': results})

    @action(detail=True, methods=['post'])
    def review_request(self, request, pk=None):
        ctx, error = self._context_or_error(request)
        if error:
            return error
        if ctx.get('ctc_sub_role') != 'assistant_executif':
            return Response({'detail': "Réservé à l'Assistant Exécutif de la Direction des Opérations."}, status=status.HTTP_403_FORBIDDEN)
        if PlatformFreeze.get_solo().is_locked:
            return Response({'detail': 'Plateforme verrouillée par le Président du Comité de Pilotage — action suspendue.'}, status=423)
        decision = str(request.data.get('decision', '')).strip().upper()
        if decision not in {'APPROVED', 'REJECTED'}:
            return Response({'detail': 'Décision invalide.'}, status=status.HTTP_400_BAD_REQUEST)
        comment = str(request.data.get('comment', '')).strip()
        with transaction.atomic():
            item = CTCOperationalRequest.objects.select_for_update().select_related('requester__user').filter(pk=pk).first()
            if item is None:
                return Response({'detail': 'Demande introuvable.'}, status=status.HTTP_404_NOT_FOUND)
            if item.status != 'PENDING':
                return Response({'detail': 'Cette demande a déjà été traitée.'}, status=status.HTTP_409_CONFLICT)
            item.status = decision
            item.reviewed_by = self._expert(request)
            item.reviewed_at = timezone.now()
            item.review_comment = comment
            item.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_comment'])
            transaction.on_commit(lambda: create_notification_for_user(
                item.requester.user,
                'Décision sur votre demande CTC',
                f'Votre demande « {item.restricted_resource} » a été {"approuvée" if decision == "APPROVED" else "refusée"}.',
                'SYSTEM',
                priority='HIGH' if decision == 'APPROVED' else 'NORMAL',
                data={'request_id': str(item.pk), 'status': decision, 'comment': comment},
            ))
        return Response({'ok': True, 'message': 'Décision enregistrée.', 'new_status': decision})
