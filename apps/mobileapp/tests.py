"""
Tests pour le système de notifications
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.mobileapp.models import (
    Notification, NotificationLog, PushToken, NotificationPreference
)

User = get_user_model()


@pytest.mark.django_db
class TestNotificationSystem(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        NotificationPreference.objects.create(
            user=self.user,
            enable_norm_updates=True,
            enable_payments=True
        )
        self.push_token = PushToken.objects.create(
            user=self.user,
            token='fcm_token_test_123',
            device_type='android'
        )
    
    def test_create_notification(self):
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            body='Body',
            notification_type='NORM_PUBLISHED',
            priority='HIGH'
        )
        assert notification.id is not None
        assert notification.is_read is False
    
    def test_mark_notification_as_read(self):
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            body='Body',
            notification_type='SYSTEM'
        )
        notification.mark_as_read()
        assert notification.is_read is True
        assert notification.read_at is not None
    
    def test_notification_types(self):
        types = ['NORM_PUBLISHED', 'PAYMENT_DUE', 'EXPERT_INVITE', 'REUNION_INVITE']
        for notif_type in types:
            notification = Notification.objects.create(
                user=self.user,
                title='Test',
                body='Body',
                notification_type=notif_type
            )
            assert notification.notification_type == notif_type
    
    def test_multiple_tokens_per_user(self):
        token2 = PushToken.objects.create(
            user=self.user,
            token='second_token',
            device_type='ios'
        )
        tokens = PushToken.objects.filter(user=self.user)
        assert tokens.count() == 2
    
    def test_notification_log(self):
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            body='Body',
            notification_type='SYSTEM'
        )
        log = NotificationLog.objects.create(
            notification=notification,
            push_token=self.push_token,
            status='SENT',
            provider='FCM',
            sent_at=timezone.now()
        )
        assert log.status == 'SENT'
        assert log.provider == 'FCM'
