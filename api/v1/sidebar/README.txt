Module: sidebar
===============
Endpoints pour la sidebar et l'interface de co-gouvernance CNETP (cahier des charges frontend).

Contenu:
- serializers.py : WorkingGroupSidebarSerializer, ExpertSidebarSerializer, TaskSerializer,
                   DocumentSidebarSerializer, MeetingSidebarSerializer, BudgetSidebarSerializer,
                   EditorHistorySerializer, UserProfileSerializer.
- views.py       : UserProfileViewSet (me/preferences),
                   WorkingGroupSidebarViewSet (list avec normes parallèles + KPIs),
                   ExpertSidebarViewSet (list avec badges d'accréditation),
                   TaskDetailViewSet (wg_tasks/update_task),
                   DocumentSidebarViewSet (list normes),
                   MeetingSidebarViewSet (list + create_meeting),
                   BudgetSidebarViewSet (list + declare_budget),
                   DocumentHistoryViewSet (document_authors),
                   DashboardKPIsViewSet (kpis),
                   ExpertActionsViewSet (approve_expert/delete_expert).

Endpoints principaux:
  GET        /api/v1/profile/me/
  PATCH      /api/v1/profile/preferences/
  GET        /api/v1/working-groups/
  GET        /api/v1/experts/
  GET        /api/v1/documents/
  GET        /api/v1/meetings/
  GET        /api/v1/budgets/
  GET        /api/v1/dashboard/kpis/kpis/
