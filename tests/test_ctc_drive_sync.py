import io
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from apps.documents.drive_sync import sync_one


class DriveSyncTests(SimpleTestCase):
    def test_disabled_sync_never_opens_a_file(self):
        with patch('apps.documents.drive_sync.enabled', return_value=False), patch('apps.documents.drive_sync._source_file') as source:
            self.assertEqual(sync_one('DOCUMENT', 7), 'disabled')
        source.assert_not_called()

    @override_settings(GDRIVE_ROOT_FOLDER_ID='ctc-folder')
    def test_success_records_confirmed_drive_folder(self):
        field = MagicMock()
        field.name = 'norms/version.pdf'
        field.open.return_value.__enter__.return_value = io.BytesIO(b'validated document')
        attempt = MagicMock()
        service = MagicMock()
        service.files.return_value.create.return_value.execute.return_value = {
            'id': 'drive-file', 'parents': ['ctc-folder']
        }
        with (
            patch('apps.documents.drive_sync.enabled', return_value=True),
            patch('apps.documents.drive_sync._source_file', return_value=(field, 'N-1__version.pdf')),
            patch('apps.documents.drive_sync.DriveSyncAttempt.objects.filter') as existing,
            patch('apps.documents.drive_sync.DriveSyncAttempt.objects.create', return_value=attempt),
            patch('apps.documents.drive_sync._drive_service', return_value=service),
            patch('googleapiclient.http.MediaIoBaseUpload'),
        ):
            existing.return_value.exists.return_value = False
            result = sync_one('NORM_CURRENT', 1)
        self.assertEqual(result, 'sent')
        self.assertEqual(attempt.status, 'SENT')
        self.assertEqual(attempt.drive_file_id, 'drive-file')
        attempt.save.assert_called_once()

    @override_settings(GDRIVE_ROOT_FOLDER_ID='ctc-folder')
    def test_wrong_destination_is_recorded_as_failure(self):
        field = MagicMock()
        field.name = 'norms/version.pdf'
        field.open.return_value.__enter__.return_value = io.BytesIO(b'validated document')
        attempt = MagicMock()
        service = MagicMock()
        service.files.return_value.create.return_value.execute.return_value = {
            'id': 'drive-file', 'parents': ['other-folder']
        }
        with (
            patch('apps.documents.drive_sync.enabled', return_value=True),
            patch('apps.documents.drive_sync._source_file', return_value=(field, 'N-1__version.pdf')),
            patch('apps.documents.drive_sync.DriveSyncAttempt.objects.filter') as existing,
            patch('apps.documents.drive_sync.DriveSyncAttempt.objects.create', return_value=attempt),
            patch('apps.documents.drive_sync._drive_service', return_value=service),
            patch('googleapiclient.http.MediaIoBaseUpload'),
        ):
            existing.return_value.exists.return_value = False
            result = sync_one('NORM_CURRENT', 1)
        self.assertEqual(result, 'failed')
        self.assertEqual(attempt.status, 'FAILED')
        attempt.save.assert_called_once()
