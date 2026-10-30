"""
Endpoints API pour la Sidebar et l'Interface de Co-Gouvernance CNETP
Correspond exactement au cahier des charges frontend avec structures JSON imbriquées
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, F, Case, When, Value, FloatField, Sum
from django.db.models.functions import Coalesce
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from apps.experts.models import Expert
from apps.governance.models import CTM, WG, Affectation, Tache
from apps.governance.activity_models import ActivityPulse, ActivitySession
from apps.norms.models import Norme, NormeVersion
from apps.meetings.models import Reunion
from apps.payments.models import Cotisation
from apps.amendments.models import Amendement

from ..experts.serializers import ExpertBasicSerializer
from ..permissions import user_ctm_scope
from .serializers import (
    WorkingGroupSidebarSerializer, ExpertSidebarSerializer, TaskSerializer,
    DocumentSidebarSerializer, MeetingSidebarSerializer, BudgetSidebarSerializer
)


# =========================================================================
# 1. PROFIL UTILISATEUR CONNECTÉ (Le Contexte Utilisateur)
# =========================================================================
class UserProfileViewSet(viewsets.ViewSet):
    """
    GET /api/v1/users/me/profile/
    Retourne les infos exactes de l'utilisateur connecté pour calculer les badges
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Récupérer le profil de l'utilisateur connecté"""
        try:
            expert = Expert.objects.select_related('user', 'ctm').get(user=request.user)

            affectation = Affectation.objects.filter(expert=expert).select_related('wg__ctm').first()

            wg_code = ""
            wg_title = ""
            if affectation and affectation.wg:
                wg = affectation.wg
                wg_code = f"WG {wg.ctm.number}.{wg.number}"
                wg_title = wg.name

            return Response({
                "id": f"exp-{expert.id}",
                "name": expert.user.get_full_name(),
                "email": expert.user.email,
                "roleId": "EXPERT",
                "ctm": expert.ctm.name if expert.ctm else "",
                "ctmId": expert.ctm.id if expert.ctm else None,
                "wg": wg_title,
                "wgCode": wg_code,
                "theme_preference": expert.theme_preference
            })
        except Expert.DoesNotExist:
            return Response(
                {"detail": "Expert profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['patch'])
    def preferences(self, request):
        """PATCH /api/v1/users/me/preferences/ - Mettre à jour les préférences UI"""
        try:
            expert = Expert.objects.get(user=request.user)
            if 'theme' in request.data:
                expert.theme_preference = request.data['theme']
                expert.save()
            return Response({"theme": expert.theme_preference})
        except Expert.DoesNotExist:
            return Response(
                {"detail": "Expert profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )


# =========================================================================
# 2. GROUPES DE TRAVAIL & NORMES PARALLÈLES
# =========================================================================
class WorkingGroupSidebarViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/working-groups/
    Liste des WGs avec normes parallèles imbriquées et recherche multicritères
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'ctm__name']

    def get_queryset(self):
        qs = WG.objects.select_related('ctm').prefetch_related(
            'normes', 'affectations__expert'
        ).annotate(
            expert_count=Count('affectations__expert', distinct=True)
        )
        scope = user_ctm_scope(self.request.user)
        if scope is None:
            return qs
        if not scope:
            return qs.none()
        return qs.filter(ctm_id__in=scope)

    def get_serializer_class(self):
        return WorkingGroupSidebarSerializer

    def list(self, request, *args, **kwargs):
        """Override pour ajouter les normes parallèles et KPIs"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        data = serializer.data
        for wg_data in data:
            wg_id = wg_data['id']
            try:
                wg = WG.objects.get(id=wg_id)

                norms = wg.normes.all()
                wg_data['parallel_norms'] = [
                    f"{norm.reference_number} ({norm.title})" for norm in norms
                ]

                tasks = Tache.objects.filter(working_group=wg)
                total_tasks = tasks.count()
                completed_tasks = tasks.filter(status='COMPLETED').count()
                average_progress = 0
                if total_tasks > 0:
                    average_progress = int((completed_tasks / total_tasks) * 100)

                wg_data['tasks_progress'] = {
                    'total': total_tasks,
                    'completed': completed_tasks,
                    'average_progress': average_progress
                }
            except WG.DoesNotExist:
                pass

        return Response(data)


# =========================================================================
# 3. EXPERTS ET ACCRÉDITATIONS
# =========================================================================
class ExpertSidebarViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/experts/
    Liste des experts avec recherche multicritères et badges d'accréditation
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'structure__name', 'ctm__name']
    ordering_fields = ['user__last_name', 'inscription_date']
    ordering = ['user__last_name']

    def get_queryset(self):
        qs = Expert.objects.select_related(
            'user', 'structure', 'ctm'
        ).prefetch_related('governance_affectations')
        scope = user_ctm_scope(self.request.user)
        if scope is None:
            return qs
        if not scope:
            return qs.none()
        return qs.filter(
            Q(ctm_id__in=scope) | Q(governance_affectations__ctm_id__in=scope)
        ).distinct()

    def get_serializer_class(self):
        return ExpertSidebarSerializer


# =========================================================================
# 4. TÂCHES & PROGRESS BAR
# =========================================================================
class TaskDetailViewSet(viewsets.ViewSet):
    """
    GET /api/v1/working-groups/{id}/tasks/
    Tâches pour un WG spécifique (checklist & progress bar)
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='working-groups/(?P<wg_id>[^/.]+)/tasks')
    def wg_tasks(self, request, wg_id=None):
        """Récupérer les tâches d'un WG"""
        try:
            wg = WG.objects.get(id=wg_id)
            tasks = Tache.objects.filter(working_group=wg).select_related('norme')

            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data)
        except WG.DoesNotExist:
            return Response(
                {"detail": "Working group not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['patch'], url_path='tasks/(?P<task_id>[^/.]+)')
    def update_task(self, request, task_id=None):
        """PATCH /api/v1/tasks/{id}/ - Mettre à jour le statut d'une tâche"""
        try:
            task = Tache.objects.select_related('working_group').get(id=task_id)
            scope = user_ctm_scope(request.user)
            if scope is not None:
                task_ctm_id = task.working_group.ctm_id if task.working_group_id else None
                if task_ctm_id not in scope:
                    return Response(
                        {"detail": "Cette tâche n'est pas dans votre sous-commission."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            if 'status' in request.data:
                task.status = request.data['status']
                task.progress = request.data.get('progress', task.progress)
                task.save()

            serializer = TaskSerializer(task)
            return Response(serializer.data)
        except Tache.DoesNotExist:
            return Response(
                {"detail": "Task not found"},
                status=status.HTTP_404_NOT_FOUND
            )


# =========================================================================
# 5. DOCUMENTS & NORMES (Sidebar Onglet "Éditeur")
# =========================================================================
class DocumentSidebarViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/documents/
    Documents/Normes pour la sidebar avec recherche
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['reference_number', 'title', 'description']

    def get_queryset(self):
        qs = Norme.objects.select_related('created_by').order_by('-created_at')
        scope = user_ctm_scope(self.request.user)
        if scope is None:
            return qs
        if not scope:
            return qs.none()
        return qs.filter(ctm_id__in=scope)

    def get_serializer_class(self):
        return DocumentSidebarSerializer


# =========================================================================
# 6. RÉUNIONS (Sidebar Onglet "Réunions")
# =========================================================================
class MeetingSidebarViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/meetings/
    Réunions planifiées pour la sidebar
    """
    permission_classes = [IsAuthenticated]
    ordering_fields = ['date']
    ordering = ['-date']

    def get_queryset(self):
        return Reunion.objects.order_by('-date')

    def get_serializer_class(self):
        return MeetingSidebarSerializer

    @action(detail=False, methods=['post'])
    def create_meeting(self, request):
        """POST /api/v1/meetings/ - Planifier une réunion"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# =========================================================================
# 7. BUDGETS & COTISATIONS (Sidebar Onglet "Financier")
# =========================================================================
class BudgetSidebarViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/budgets/
    Cotisations et budgets pour la sidebar
    """
    permission_classes = [IsAuthenticated]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Cotisation.objects.order_by('-created_at')

    def get_serializer_class(self):
        return BudgetSidebarSerializer

    @action(detail=False, methods=['post'])
    def declare_budget(self, request):
        """POST /api/v1/budgets/ - Déclarer une ligne budgétaire"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# =========================================================================
# 8. HISTORIQUE & ÉDITEURS (Sidebar Onglet "Historique")
# =========================================================================
class DocumentHistoryViewSet(viewsets.ViewSet):
    """
    GET /api/v1/documents/{id}/history-authors/
    Regrouper les versions par auteur avec comptage
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='documents/(?P<doc_id>[^/.]+)/history-authors')
    def document_authors(self, request, doc_id=None):
        """Récupérer les éditeurs historiques d'une norme"""
        try:
            norme = Norme.objects.get(id=doc_id)
            authors = (
                NormeVersion.objects
                .filter(norme=norme, version_author__isnull=False)
                .values(
                    'version_author__first_name',
                    'version_author__last_name',
                    'version_author__email',
                )
                .annotate(count=Count('id'))
                .order_by('-count')
            )
            data = [
                {
                    'name': f"{a['version_author__first_name']} {a['version_author__last_name']}".strip(),
                    'email': a['version_author__email'],
                    'role': 'Éditeur',
                    'count': a['count'],
                }
                for a in authors
            ]
            return Response(data)
        except Norme.DoesNotExist:
            return Response(
                {"detail": "Document not found"},
                status=status.HTTP_404_NOT_FOUND
            )


# =========================================================================
# 9. KPIs GLOBAUX (Footer Dashboard)
# =========================================================================
class DashboardKPIsViewSet(viewsets.ViewSet):
    """
    GET /api/v1/dashboard/kpis/
    Métriques globales pour le footer de la sidebar
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def kpis(self, request):
        """Récupérer les KPIs globaux"""
        total_ctm = CTM.objects.count()
        active_ctm = total_ctm
        total_wg = WG.objects.count()
        experts_approved = Expert.objects.filter(status='ACTIVE').count()
        experts_total = Expert.objects.count()

        all_norms = Norme.objects.exclude(status='ARCHIVED')
        total_norms = all_norms.count()
        global_norms_progress = 0
        if total_norms > 0:
            completed_norms = all_norms.filter(status='PUBLISHED').count()
            global_norms_progress = (completed_norms / total_norms) * 100

        meetings_planned = Reunion.objects.filter(
            status__in=['PLANNED', 'IN_PROGRESS']
        ).count()

        active_votes = Amendement.objects.filter(
            status='UNDER_REVIEW'
        ).count()

        return Response({
            "total_ctm": total_ctm,
            "active_ctm": active_ctm,
            "total_wg": total_wg,
            "experts_approved": experts_approved,
            "experts_total": experts_total,
            "global_norms_progress_percent": round(global_norms_progress, 1),
            "meetings_planned": meetings_planned,
            "active_votes": active_votes
        })


# =========================================================================
# 10. ACTIONS SPÉCIFIQUES (Mutations)
# =========================================================================
class ExpertActionsViewSet(viewsets.ViewSet):
    """Actions spécifiques sur les experts"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['patch'], url_path='experts/(?P<expert_id>[^/.]+)/approve')
    def approve_expert(self, request, expert_id=None):
        """PATCH /api/v1/experts/{id}/approve/ - Accréditer un expert"""
        try:
            expert = Expert.objects.get(id=expert_id)
            expert.status = 'ACTIVE'
            expert.save()

            serializer = ExpertSidebarSerializer(expert)
            return Response(serializer.data)
        except Expert.DoesNotExist:
            return Response(
                {"detail": "Expert not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['delete'], url_path='experts/(?P<expert_id>[^/.]+)')
    def delete_expert(self, request, expert_id=None):
        """DELETE /api/v1/experts/{id}/ - Détacher un expert"""
        try:
            expert = Expert.objects.get(id=expert_id)
            expert.status = 'INACTIVE'
            expert.save()
            return Response({"detail": "Expert detached successfully"})
        except Expert.DoesNotExist:
            return Response(
                {"detail": "Expert not found"},
                status=status.HTTP_404_NOT_FOUND
            )


# =========================================================================
# 11. COMPTEUR D'ACTIVITÉ (Temps & éditions) — espace expert
# =========================================================================
class ActivityCounterViewSet(viewsets.ViewSet):
    """GET /api/v1/activity/my-counter/

    Compteur personnel de l'expert connecté :
      - temps observé (``active_seconds``) via les sessions/battements ;
      - nombre d'éditions (versions de normes créées par l'expert).
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='my-counter')
    def my_counter(self, request):
        user = request.user
        start_today = timezone.localtime(timezone.now()).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        sessions = ActivitySession.objects.filter(user=user)
        active_seconds_total = sessions.aggregate(total=Sum('active_seconds')).get('total') or 0
        active_seconds_today = ActivityPulse.objects.filter(
            session__user=user, bucket__gte=start_today
        ).aggregate(total=Sum('credited_seconds')).get('total') or 0

        versions = NormeVersion.all_objects.filter(version_author=user)
        editions_total = versions.count()
        editions_today = versions.filter(created_at__gte=start_today).count()

        last_session = sessions.order_by('-last_seen_at').first()

        return Response({
            'active_seconds_total': int(active_seconds_total),
            'active_seconds_today': int(active_seconds_today),
            'editions_total': editions_total,
            'editions_today': editions_today,
            'last_activity': last_session.last_seen_at.isoformat() if last_session else None,
        })
