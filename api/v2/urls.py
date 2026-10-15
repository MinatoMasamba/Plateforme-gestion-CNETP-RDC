from django.urls import path
from .organisation import ReferenceAPI, ConfigurationAPI, ActivationAPI, DossiersAPI, DossierAPI, DossierOperationAPI, PieceDownloadAPI, ExportAPI

urlpatterns = [
    path('organisation/', ReferenceAPI.as_view()),
    path('organisation/configuration/<str:kind>/', ConfigurationAPI.as_view()),
    path('organisation/configuration/<str:kind>/<int:pk>/', ConfigurationAPI.as_view()),
    path('organisation/mise-en-service/', ActivationAPI.as_view()),
    path('organisation/dossiers/', DossiersAPI.as_view()),
    path('organisation/export/', ExportAPI.as_view()),
    path('organisation/pieces/<int:pk>/', PieceDownloadAPI.as_view()),
    path('organisation/dossiers/<int:pk>/export/', ExportAPI.as_view()),
    path('organisation/dossiers/<int:pk>/', DossierAPI.as_view()),
    path('organisation/dossiers/<int:pk>/operation/', DossierOperationAPI.as_view()),
]
