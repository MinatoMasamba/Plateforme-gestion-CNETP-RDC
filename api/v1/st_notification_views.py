from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from apps.governance import st_notifications as service
from apps.governance.st_notification_models import STNotificationRead
from apps.mobileapp.models import Notification
from .st_admin_views import AdminBase


class STNotificationViewSet(AdminBase):
    def list(self, request):
        return Response(service.notifications(request.user))

    @action(detail=False, methods=['post'], url_path='read')
    def read(self, request):
        key = serializers.CharField(max_length=100).run_validation(request.data.get('key'))
        if key.startswith('notification:'):
            uid = serializers.UUIDField().run_validation(key.removeprefix('notification:'))
            item = get_object_or_404(Notification.objects.filter(user=request.user), pk=uid)
            Notification.objects.filter(pk=item.pk, user=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
        else:
            if not any(row['key'] == key for row in service.cases(request.user)):
                raise NotFound('Notification absente de votre périmètre.')
            STNotificationRead.objects.get_or_create(user=request.user, key=key)
        return Response(service.notifications(request.user))
