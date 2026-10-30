from django.urls import path

from . import views

app_name = 'reporting'

urlpatterns = [
    path('', views.index, name='index'),
    path('nouveau/', views.create, name='create'),
    path('<uuid:pk>/', views.detail, name='detail'),
    path('<uuid:pk>/champs/', views.save_fields, name='save_fields'),
    path('<uuid:pk>/pieces/', views.add_evidence, name='add_evidence'),
    path('pieces/<int:pk>/telecharger/', views.download_evidence, name='download_evidence'),
    path('<uuid:pk>/finances/', views.add_financial_line, name='add_financial_line'),
    path('<uuid:pk>/transition/', views.transition, name='transition'),
    path('<uuid:pk>/revision/', views.revise, name='revise'),
    path('<uuid:pk>/export/<str:fmt>/', views.export, name='export'),
]
