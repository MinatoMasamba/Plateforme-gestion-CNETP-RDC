from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import PasswordResetCode, User
from apps.experts.models import Expert, Structure
from apps.governance.models import CTCMembership, PilotageMembreship


pytestmark = pytest.mark.django_db
REQUEST = '/api/v1/mobile/auth/password-reset/request/'
CONFIRM = '/api/v1/mobile/auth/password-reset/confirm/'
REGISTER = '/api/v1/expert-registration/candidature/'
LOGIN = '/api/v1/mobile/auth/login/'


@pytest.fixture
def client():
    cache.clear()
    return APIClient()


def confirmation(user, code):
    return {'email': user.email, 'code': code, 'password': 'A-new-passphrase-2026!',
            'password2': 'A-new-passphrase-2026!'}


def test_reset_changes_password_once(client, user_factory):
    user = user_factory()
    # Expired stored credentials must not prevent account recovery.
    client.credentials(HTTP_AUTHORIZATION='Bearer expired')
    assert client.post(REQUEST, {'email': user.email}, format='json').status_code == 200
    reset = PasswordResetCode.objects.get(user=user)
    assert len(mail.outbox) == 1
    assert reset.code in mail.outbox[0].body
    payload = confirmation(user, reset.code)
    assert client.post(CONFIRM, payload, format='json').status_code == 200
    user.refresh_from_db()
    assert user.check_password(payload['password'])
    assert client.post(CONFIRM, payload, format='json').status_code == 400


def test_unknown_email_gets_neutral_response(client):
    response = client.post(REQUEST, {'email': 'unknown@example.test'}, format='json')
    assert response.status_code == 200
    assert response.data == {'ok': True}
    assert not PasswordResetCode.objects.exists()


def test_login_resolves_duplicate_email_by_password(client, user_factory):
    user_factory(
        username='duplicate-old',
        email='duplicate@example.test',
        password='old-passphrase-2026!',
    )
    target = user_factory(
        username='duplicate-new',
        email='duplicate@example.test',
        password='new-passphrase-2026!',
    )
    payload = {
        'email': 'duplicate@example.test',
        'password': 'new-passphrase-2026!',
        'device_id': 'test-device',
        'device_type': 'web',
    }

    response = client.post(LOGIN, payload, format='json')

    assert response.status_code == 200, response.data
    assert response.data['user']['id'] == target.id

    payload['password'] = 'wrong-password'
    assert client.post(LOGIN, payload, format='json').status_code == 400


@pytest.mark.parametrize('email', ['', 'not-an-email', [], None])
def test_reset_rejects_malformed_input(client, email):
    assert client.post(REQUEST, {'email': email}, format='json').status_code == 400


def test_reset_resend_invalidates_previous_code(client, user_factory):
    user = user_factory()
    previous = PasswordResetCode.generate_for(user)
    assert client.post(REQUEST, {'email': user.email}, format='json').status_code == 200
    previous.refresh_from_db()
    assert previous.is_used
    assert PasswordResetCode.objects.filter(user=user, is_used=False).count() == 1


def test_reset_attempt_limit_and_expiry(client, user_factory):
    user = user_factory()
    reset = PasswordResetCode.generate_for(user)
    wrong = '000000' if reset.code != '000000' else '111111'
    for _ in range(3):
        assert client.post(CONFIRM, confirmation(user, wrong), format='json').status_code == 400
    assert client.post(CONFIRM, confirmation(user, reset.code), format='json').status_code == 400
    reset.refresh_from_db()
    assert reset.attempts == 3
    cache.clear()
    expired = PasswordResetCode.generate_for(user)
    expired.expires_at = timezone.now() - timedelta(seconds=1)
    expired.save(update_fields=['expires_at'])
    assert client.post(CONFIRM, confirmation(user, expired.code), format='json').status_code == 400
    user.refresh_from_db()
    assert user.check_password('testpass123')


def test_mismatched_passwords_do_not_consume_code(client, user_factory):
    user = user_factory()
    reset = PasswordResetCode.generate_for(user)
    payload = confirmation(user, reset.code)
    payload['password2'] = 'Different-password!'
    assert client.post(CONFIRM, payload, format='json').status_code == 400
    reset.refresh_from_db()
    assert not reset.is_used
    assert reset.attempts == 0


def test_mail_failure_reported_and_code_invalidated(client, user_factory):
    user = user_factory()
    with patch('api.v1.mobile.password_reset.send_mail', side_effect=OSError('mail unavailable')):
        assert client.post(REQUEST, {'email': user.email}, format='json').status_code == 503
    assert not PasswordResetCode.objects.filter(user=user, is_used=False).exists()


def candidature_payload():
    structure = Structure.objects.create(name='Organisation de test', acronym='TEST', category='ADMIN')
    return {
        'first_name': 'Alice', 'last_name': 'Test', 'email': 'candidate@example.test',
        'password': 'Candidate-passphrase-2026!', 'password_confirm': 'Candidate-passphrase-2026!',
        'structure': structure.pk, 'whatsapp_number': '+243810000000',
        'specialties': 'Géotechnique',
    }


def test_candidature_matches_web_pending_without_mandates(client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    payload = candidature_payload()
    payload.update({'ctm': 1, 'ctc_member': True, 'ctc_role': 'COORDINATOR',
                    'pilotage_member': True, 'pilotage_role': 'PRESIDENT'})
    payload['cv'] = SimpleUploadedFile('cv.pdf', b'%PDF-1.4 test CV', content_type='application/pdf')
    response = client.post(REGISTER, payload, format='multipart')
    assert response.status_code == 201, response.data
    expert = Expert.objects.get(pk=response.data['id'])
    assert expert.status == 'PENDING'
    assert expert.ctm_id is None
    assert expert.whatsapp_number == '+243810000000'
    assert expert.cv.name.endswith('.pdf')
    assert expert.user.check_password(payload['password'])
    assert not CTCMembership.objects.filter(expert=expert).exists()
    assert not PilotageMembreship.objects.filter(expert=expert).exists()
    assert client.post(REGISTER, {k: v for k, v in payload.items() if k != 'cv'}, format='json').status_code == 400
    assert User.objects.filter(email=payload['email']).count() == 1


def test_candidature_validation_does_not_create_accounts(client):
    payload = candidature_payload()
    payload['password_confirm'] = 'different-password'
    assert client.post(REGISTER, payload, format='json').status_code == 400
    assert not User.objects.filter(email=payload['email']).exists()
    payload['password_confirm'] = payload['password']
    payload['cv'] = SimpleUploadedFile('cv.exe', b'test')
    assert client.post(REGISTER, payload, format='multipart').status_code == 400
    assert not User.objects.filter(email=payload['email']).exists()
