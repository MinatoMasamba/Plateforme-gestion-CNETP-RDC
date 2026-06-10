from django.urls import path
from .views import (AboutView, App, ContactView, ExpertLoginView, HomeView,
                    ExpertRegistrationView, User_RegistrationView, UserLoginView,
                    component_api_view, wg_redirect,
                    password_reset_request, password_reset_confirm)
from .pilotage_views import (
    PilotageDashboardView,
    PilotagePermissionRequestView,
    PilotageApproveRequestView,
    PilotageAcknowledgeReceptionView,
    PilotageCadrageActionView,
    pilotage_context_api,
)
from .ctc_views import (
    CTCDashboardView,
    CTCOperationalRequestView,
    CTCApproveRequestView,
    ctc_context_api,
)

app_name = 'web'

urlpatterns = [
    # ========== Pages Principales ==========
    path('', HomeView.as_view(), name='home'),
    path('app/', App.as_view(), name='app'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('inscription-simple/', User_RegistrationView.as_view(), name='user_registration'),
    path('inscription-expert/', ExpertRegistrationView.as_view(), name='expert_registration'),
    path('inscription-expert', ExpertRegistrationView.as_view(), name='expert_registration-no-slash'),
    path('se-connecter/', ExpertLoginView.as_view(), name='expert_login'),
    path('se-connecter/', ExpertLoginView.as_view(), name='expert_login-no-slash'),
    path('se-connecter-user/', UserLoginView.as_view(), name='user_login'),
    path('api/components/<str:module_id>/', component_api_view, name='api_components'),
    # Réinitialisation mot de passe
    path('mot-de-passe-oublie/demander/', password_reset_request, name='password_reset_request'),
    path('mot-de-passe-oublie/reinitialiser/', password_reset_confirm, name='password_reset_confirm'),
    # Redirections depuis les liens email vers l'application
    path('wgs/', wg_redirect, name='wg_redirect_index'),
    path('wgs/<int:wg_id>/', wg_redirect, name='wg_redirect'),

    # ─── Comité de Pilotage Élargi ───────────────────────────────────────────
    path('pilotage/', PilotageDashboardView.as_view(), name='pilotage_dashboard'),
    path('pilotage/demande-permission/', PilotagePermissionRequestView.as_view(), name='pilotage_permission_request'),
    path('pilotage/approuver-demande/<int:pk>/', PilotageApproveRequestView.as_view(), name='pilotage_approve_request'),
    path('pilotage/processus/<int:pk>/receptionner/', PilotageAcknowledgeReceptionView.as_view(), name='pilotage_acknowledge_reception'),
    path('pilotage/cadrage/<int:pk>/action/', PilotageCadrageActionView.as_view(), name='pilotage_cadrage_action'),
    path('api/pilotage/contexte/', pilotage_context_api, name='pilotage_context_api'),

    # ─── Cellule Technique de Coordination ───────────────────────────────────
    path('ctc/', CTCDashboardView.as_view(), name='ctc_dashboard'),
    path('ctc/demande-operationnelle/', CTCOperationalRequestView.as_view(), name='ctc_operational_request'),
    path('ctc/approuver-demande/<int:pk>/', CTCApproveRequestView.as_view(), name='ctc_approve_request'),
    path('api/ctc/contexte/', ctc_context_api, name='ctc_context_api'),
]
