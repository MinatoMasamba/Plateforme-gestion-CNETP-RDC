"""Accusés de lecture personnels des alertes de supervision ST."""
from django.conf import settings
from django.db import models


class STNotificationRead(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'key'], name='st_notification_read_unique')]
