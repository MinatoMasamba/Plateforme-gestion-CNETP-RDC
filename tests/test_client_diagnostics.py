import json
import os
import stat

import pytest
from rest_framework.test import APIClient

from apps.mobileapp.models import ClientDiagnostic
from api.v1.mobile.diagnostics import DiagnosticThrottle


@pytest.mark.django_db
def test_diagnostic_is_authenticated_sanitized_and_idempotent(user_factory, settings, tmp_path):
    settings.CLIENT_DIAGNOSTICS_DIR = tmp_path / 'private-journal'
    client = APIClient()
    url = '/api/v1/mobile/diagnostics/'
    assert client.post(url, {}, format='json').status_code in (401, 403)
    user = user_factory(username='diagnostic_user')
    client.force_authenticate(user)
    data = {'event_id': 'test_incident_001', 'category': 'network', 'app_version': '1.0-beta',
            'platform': 'android', 'message': 'password=privatevalue Bearer privatebearer me@example.test',
            'stack': 'https://example.test/path?token=privatetoken',
            'path': '/api/v1/norms/123/?token=privatetoken', 'method': 'GET',
            'route': 'localProxy', 'duration_ms': 2500, 'status_code': 502,
            'headers': {'Authorization': 'privateheader'}, 'body': 'privatebody'}
    assert client.post(url, data, format='json').status_code == 201
    assert client.post(url, data, format='json').status_code == 200
    incident = ClientDiagnostic.objects.get(user=user)
    assert incident.journal_written
    files = list(settings.CLIENT_DIAGNOSTICS_DIR.rglob('*.txt'))
    assert len(files) == 1
    text = files[0].read_text()
    for secret in ('privatevalue', 'privatebearer', 'privatetoken', 'privateheader', 'privatebody', 'me@example.test'):
        assert secret not in text
    assert json.loads(text)['path'] == '/api/v1/norms/:id/'
    if os.name == 'posix':
        assert stat.S_IMODE(files[0].stat().st_mode) == 0o600
    assert client.get(url).status_code == 405


@pytest.mark.django_db
def test_diagnostic_rejects_large_or_invalid_payload(user_factory):
    client = APIClient()
    client.force_authenticate(user_factory(username='bad_diagnostic'))
    url = '/api/v1/mobile/diagnostics/'
    assert client.post(url, {'message': 'x' * 21000}, format='json').status_code == 413
    assert client.post(url, {'event_id': '../../etc/passwd'}, format='json').status_code == 400
    assert not ClientDiagnostic.objects.exists()


@pytest.mark.django_db
def test_diagnostic_accepts_body_already_parsed_by_drf(user_factory, settings, tmp_path, monkeypatch):
    settings.CLIENT_DIAGNOSTICS_DIR = tmp_path / 'private-journal'
    client = APIClient()
    client.force_authenticate(user_factory(username='parsed_diagnostic'))

    def parse_before_view(self, request, view):
        assert request.data['event_id'] == 'already_parsed_001'
        return True

    monkeypatch.setattr(DiagnosticThrottle, 'allow_request', parse_before_view)
    response = client.post('/api/v1/mobile/diagnostics/', {
        'event_id': 'already_parsed_001', 'category': 'flutter',
        'app_version': '1.0.0-beta.1+4', 'platform': 'android',
        'message': 'Incident avec flux déjà consommé.',
    }, format='json')
    assert response.status_code == 201
    assert ClientDiagnostic.objects.get().journal_written
