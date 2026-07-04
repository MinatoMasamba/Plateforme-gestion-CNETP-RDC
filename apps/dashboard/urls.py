from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('ajax/structure/<int:pk>/', views.ajax_structure, name='ajax_structure'),
]
