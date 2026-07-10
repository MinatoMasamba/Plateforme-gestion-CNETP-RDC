from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='gemini_dashboard'),
    path('generate/', views.generate_draft, name='gemini_generate'),
    path('drafts/', views.list_drafts, name='gemini_list_drafts'),
    path('structure/', views.get_structure, name='gemini_structure'),
]