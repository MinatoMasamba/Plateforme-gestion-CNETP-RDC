from django.urls import path
from .views import AboutView, App, ContactView, ExpertLoginView, HomeView, ExpertRegistrationView, User_RegistrationView, UserLoginView, component_api_view

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
    path('se-connecter-user/',UserLoginView.as_view(), name='user_login'),
    path('api/components/<str:module_id>/', component_api_view, name='api_components'),
]
