from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .auth.views import AuthViewSet, UserListViewSet
from .experts.views import ExpertViewSet, StructureViewSet
from .documents.bridge_views import DocumentsAPIView, CollaboratorsAPIView
from .experts.registration_views import ExpertPublicRegistrationViewSet
from .governance.views import CTMViewSet, WGViewSet, AffectationViewSet, RoleCTMViewSet, ComitePilotageViewSet
from .hierarchy.views import (
    ExecutiveLevelViewSet, SteeringCommitteeViewSet, TechnicalCellViewSet,
    OriginStructureViewSet, HierarchyViewSet
)
from .norms.views import NormeViewSet, NormeVersionViewSet, ChangementVersionViewSet
from .amendments.views import AmendementViewSet, VoteViewSet, ResultatVoteViewSet
from .meetings.views import ReunionViewSet, PresenceViewSet, ProcessusVerbauxViewSet, ReunionVoteViewSet
from .payments.views import CotisationViewSet, PaiementViewSet, JetonPresenceViewSet
from .mobile.views import (
    MobileAuthViewSet, PushTokenViewSet, NotificationPreferenceViewSet,
    NotificationViewSet, MobileProfileViewSet, MobilePublicViewSet
)
from .validation.views import LegisticReviewViewSet
from .documents.views import DocumentFileViewSet
from .public.views import PublicAmendementViewSet
from .messaging.views import MessageViewSet
from .sidebar.views import (
    UserProfileViewSet, WorkingGroupSidebarViewSet, ExpertSidebarViewSet,
    TaskDetailViewSet, DocumentSidebarViewSet, MeetingSidebarViewSet,
    BudgetSidebarViewSet, DocumentHistoryViewSet, DashboardKPIsViewSet,
    ExpertActionsViewSet
)

# Créer le router et enregistrer les viewsets
router = DefaultRouter()

# Auth routes
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserListViewSet, basename='users')
router.register(r'profile', UserProfileViewSet, basename='user-profile')

# Experts routes
router.register(r'structures', StructureViewSet, basename='structures')
router.register(r'experts', ExpertViewSet, basename='experts')
router.register(r'expert-registration', ExpertPublicRegistrationViewSet, basename='expert-registration')

# Governance routes
router.register(r'ctm', CTMViewSet, basename='ctm')
router.register(r'wg', WGViewSet, basename='wg')
router.register(r'affectations', AffectationViewSet, basename='affectations')
router.register(r'roles-ctm', RoleCTMViewSet, basename='roles-ctm')
router.register(r'comite-pilotage', ComitePilotageViewSet, basename='comite-pilotage')

# Hierarchy routes
router.register(r'hierarchy/executive-level', ExecutiveLevelViewSet, basename='executive-level')
router.register(r'hierarchy/steering-committee', SteeringCommitteeViewSet, basename='steering-committee')
router.register(r'hierarchy/technical-cell', TechnicalCellViewSet, basename='technical-cell')
router.register(r'hierarchy/origin-structures', OriginStructureViewSet, basename='origin-structures')
router.register(r'hierarchy', HierarchyViewSet, basename='hierarchy')

# Norms routes
router.register(r'norms', NormeViewSet, basename='norms')
router.register(r'norm-versions', NormeVersionViewSet, basename='norm-versions')
router.register(r'norm-changes', ChangementVersionViewSet, basename='norm-changes')

# Amendments routes
router.register(r'amendments', AmendementViewSet, basename='amendments')
router.register(r'votes', VoteViewSet, basename='votes')
router.register(r'vote-results', ResultatVoteViewSet, basename='vote-results')

# Meetings routes
router.register(r'reunions', ReunionViewSet, basename='reunions')
router.register(r'presences', PresenceViewSet, basename='presences')
router.register(r'reunion-votes', ReunionVoteViewSet, basename='reunion-votes')
router.register(r'pv', ProcessusVerbauxViewSet, basename='pv')

# Payments routes
router.register(r'cotisations', CotisationViewSet, basename='cotisations')
router.register(r'paiements', PaiementViewSet, basename='paiements')
router.register(r'jetons', JetonPresenceViewSet, basename='jetons')

# Validation routes (Legistic review)
router.register(r'legistic-reviews', LegisticReviewViewSet, basename='legistic-reviews')

# Documents routes
router.register(r'documents', DocumentsAPIView, basename='documents')
router.register(r'collaborators', CollaboratorsAPIView, basename='collaborators')

# Messaging routes
router.register(r'messages', MessageViewSet, basename='messages')

# Public amendments routes
router.register(r'public-amendments', PublicAmendementViewSet, basename='public-amendments')

# SIDEBAR API ROUTES (Cahier des Charges Co-Gouvernance)
router.register(r'working-groups', WorkingGroupSidebarViewSet, basename='working-groups-sidebar')
router.register(r'experts', ExpertSidebarViewSet, basename='experts-sidebar')
router.register(r'documents', DocumentSidebarViewSet, basename='documents-sidebar')
router.register(r'meetings', MeetingSidebarViewSet, basename='meetings-sidebar')
router.register(r'budgets', BudgetSidebarViewSet, basename='budgets-sidebar')
router.register(r'dashboard/kpis', DashboardKPIsViewSet, basename='dashboard-kpis')
router.register(r'tasks', TaskDetailViewSet, basename='tasks-sidebar')
router.register(r'document-history', DocumentHistoryViewSet, basename='document-history')
router.register(r'expert-actions', ExpertActionsViewSet, basename='expert-actions')

# Mobile routes (v2 API)
router.register(r'mobile/auth', MobileAuthViewSet, basename='mobile-auth')
router.register(r'mobile/push-tokens', PushTokenViewSet, basename='push-tokens')
router.register(r'mobile/notification-preferences', NotificationPreferenceViewSet, basename='notification-preferences')
router.register(r'mobile/notifications', NotificationViewSet, basename='notifications')
router.register(r'mobile/profile', MobileProfileViewSet, basename='mobile-profile')
router.register(r'mobile/public', MobilePublicViewSet, basename='mobile-public')

urlpatterns = [
    # Routes principales
    path('', include(router.urls)),

    # Documentation API
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
