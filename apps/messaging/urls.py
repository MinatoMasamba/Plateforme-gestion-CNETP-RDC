from rest_framework.routers import DefaultRouter
from django.urls import path, include
from api.v1.messaging.views import MessageViewSet

router = DefaultRouter()
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
]
