from django.urls import path
from .views import HomeView, ExpertRegistrationView

app_name = 'web'

urlpatterns = [
    # ========== Pages Principales ==========
    path('', HomeView.as_view(), name='home'),
    path('inscription-expert/', ExpertRegistrationView.as_view(), name='expert-registration'),
    path('inscription-expert', ExpertRegistrationView.as_view(), name='expert-registration-no-slash'),
]
