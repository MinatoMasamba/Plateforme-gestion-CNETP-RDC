from django.urls import path

from . import console_views as views

app_name = 'console'

urlpatterns = [
    path('', views.home, name='home'),
    path('modeles/', views.models_index, name='models'),
    path(
        'modeles/<str:app_label>/<str:model_name>/creer/',
        views.model_create,
        name='model_create',
    ),
    path(
        'modeles/<str:app_label>/<str:model_name>/<str:pk>/modifier/',
        views.model_edit,
        name='model_edit',
    ),
    path(
        'modeles/<str:app_label>/<str:model_name>/<str:pk>/supprimer/',
        views.model_delete,
        name='model_delete',
    ),
    path(
        'modeles/<str:app_label>/<str:model_name>/<str:pk>/',
        views.model_detail,
        name='model_detail',
    ),
    path(
        'modeles/<str:app_label>/<str:model_name>/',
        views.model_list,
        name='model_list',
    ),
    path('utilisateurs/', views.users, name='users'),
    path('utilisateurs/creer/', views.user_create, name='user_create'),
    path('utilisateurs/<int:pk>/', views.user_detail, name='user_detail'),
    path('utilisateurs/<int:pk>/modifier/', views.user_edit, name='user_edit'),
    path('utilisateurs/<int:pk>/mot-de-passe/', views.user_password, name='user_password'),
    path('utilisateurs/<int:pk>/desactiver/', views.user_deactivate, name='user_deactivate'),
    path('utilisateurs/<int:pk>/reactiver/', views.user_reactivate, name='user_reactivate'),
    path('journal/', views.audit, name='audit'),
]
