from django.urls import path

from . import views

app_name = 'public'

urlpatterns = [
    path('enquete/<int:norme_id>/', views.PublicInquiryFormView.as_view(), name='inquiry_form'),
    path('enquete/<int:norme_id>/merci/', views.PublicInquiryThanksView.as_view(), name='inquiry_thanks'),
]
