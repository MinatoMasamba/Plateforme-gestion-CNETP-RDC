from django.urls import path, re_path
from .views import ReactAppView, ExpertRegistrationView, api_documents, api_collaborators, api_experts, api_working_groups, api_meetings, api_votes, api_financial, api_validation, api_legistique, api_versions, api_app_data

app_name = 'web'

urlpatterns = [
    # ========== API Endpoints for React Components ==========
    path('api/documents/', api_documents, name='api-documents'),
    path('api/collaborators/', api_collaborators, name='api-collaborators'),
    path('api/experts/', api_experts, name='api-experts'),
    path('api/working-groups/', api_working_groups, name='api-working-groups'),
    path('api/meetings/', api_meetings, name='api-meetings'),
    path('api/votes/', api_votes, name='api-votes'),
    path('api/financial/', api_financial, name='api-financial'),
    path('api/validation/', api_validation, name='api-validation'),
    path('api/legistique/', api_legistique, name='api-legistique'),
    path('api/versions/', api_versions, name='api-versions'),
    path('api/app-data/', api_app_data, name='api-app-data'),
    
    # ========== Template Pages ==========
    path('inscription-expert/', ExpertRegistrationView.as_view(), name='expert-registration'),
    path('inscription-expert', ExpertRegistrationView.as_view(), name='expert-registration-no-slash'),
    
    # ========== React SPA Routes ==========
    path('', ReactAppView.as_view(), name='index'),
    path('auth/login/', ReactAppView.as_view(), name='login'),
    path('auth/register/', ReactAppView.as_view(), name='register'),
    re_path(r'^app/.*', ReactAppView.as_view(), name='app'),
    re_path(r'^.*$', ReactAppView.as_view(), name='catch_all'),
]
