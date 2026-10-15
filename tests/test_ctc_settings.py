import json
from unittest.mock import Mock, patch

from django.test import RequestFactory, SimpleTestCase

from web.ctc_settings_views import CTCBackupView, CTCDriveSettingsView, CTCNotificationSettingsView


class CTCSettingsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = Mock(is_authenticated=True, pk=23)

    def test_notification_change_requires_ctc_membership(self):
        request = self.factory.post(
            '/ctc/parametres/notifications/',
            data=json.dumps({'key': 'enable_system', 'enabled': False}),
            content_type='application/json',
        )
        request.user = self.user
        with patch('web.ctc_settings_views._membership_context', return_value=None):
            response = CTCNotificationSettingsView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_notification_change_rejects_unrecognized_setting(self):
        request = self.factory.post(
            '/ctc/parametres/notifications/',
            data=json.dumps({'key': 'delegation', 'enabled': True}),
            content_type='application/json',
        )
        request.user = self.user
        with patch('web.ctc_settings_views._membership_context', return_value={'is_ctc_member': True}):
            response = CTCNotificationSettingsView.as_view()(request)
        self.assertEqual(response.status_code, 400)

    def test_notification_change_persists_and_audits(self):
        request = self.factory.post(
            '/ctc/parametres/notifications/',
            data=json.dumps({'key': 'enable_system', 'enabled': False}),
            content_type='application/json',
        )
        request.user = self.user
        preference = Mock(enable_system=True)
        with (
            patch('web.ctc_settings_views._membership_context', return_value={'is_ctc_member': True}),
            patch('web.ctc_settings_views.NotificationPreference.objects.get_or_create', return_value=(preference, False)),
            patch('web.ctc_settings_views._audit') as audit,
        ):
            response = CTCNotificationSettingsView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        preference.save.assert_called_once_with(update_fields=['enable_system', 'updated_at'])
        audit.assert_called_once_with(request, 'enable_system', True, False)

    def test_backup_requires_it_post(self):
        request = self.factory.post('/ctc/parametres/sauvegarde/')
        request.user = self.user
        with patch('web.ctc_settings_views._membership_context', return_value={'can_admin_system': False}):
            response = CTCBackupView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_backup_reports_verified_service_result(self):
        request = self.factory.post('/ctc/parametres/sauvegarde/')
        request.user = self.user
        with (
            patch('web.ctc_settings_views._membership_context', return_value={'can_admin_system': True}),
            patch('web.ctc_settings_views.prepare_backup', return_value='/tmp/verified') as backup,
            patch('web.ctc_settings_views._audit') as audit,
        ):
            response = CTCBackupView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        backup.assert_called_once_with()
        audit.assert_called_once()

    def test_drive_activation_requires_it_post(self):
        request = self.factory.post(
            '/ctc/parametres/drive/',
            data=json.dumps({'enabled': True}), content_type='application/json',
        )
        request.user = self.user
        with patch('web.ctc_settings_views._membership_context', return_value={'can_admin_system': False}):
            response = CTCDriveSettingsView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_drive_activation_schedules_backlog_and_audits(self):
        request = self.factory.post(
            '/ctc/parametres/drive/',
            data=json.dumps({'enabled': True}), content_type='application/json',
        )
        request.user = self.user
        config = Mock(enabled=False)
        with (
            patch('web.ctc_settings_views._membership_context', return_value={'can_admin_system': True}),
            patch('web.ctc_settings_views.configured', return_value=True),
            patch('web.ctc_settings_views.DriveSyncSettings.objects.get_or_create', return_value=(config, False)),
            patch('web.ctc_settings_views.sync_drive_backlog.delay') as task,
            patch('web.ctc_settings_views.candidate_count', return_value=0),
            patch('web.ctc_settings_views._audit') as audit,
        ):
            response = CTCDriveSettingsView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(config.enabled)
        task.assert_called_once_with()
        audit.assert_called_once_with(request, 'drive_sync', False, True)
