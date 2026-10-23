from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('ajax/structure/<int:pk>/', views.ajax_structure, name='ajax_structure'),
    path('intelligence/', views.intelligence, name='intelligence'),
    path('intelligence/activite-experts/', views.expert_activity_report, name='expert_activity_report'),
    path('intelligence/assistant/', views.intelligence_assistant, name='intelligence_assistant'),
    path('intelligence/rapport/word/', views.intelligence_report_word, name='intelligence_report_word'),
    path('intelligence/document/<int:pk>/telecharger/', views.intelligence_document, name='intelligence_document'),
]
