"""Fixtures et utilitaires pour la campagne de tests E2E.

Les tests E2E s'exécutent contre un serveur live (daphne) sur ``E2E_BASE_URL``
(défaut http://localhost:8000) et la base de données seedée par ``seed_e2e``.
"""
import os
import re

import pytest
import requests

BASE_URL = os.environ.get('E2E_BASE_URL', 'http://localhost:8000')
E2E_PASSWORD = os.environ.get('E2E_PASSWORD', 'Cnetp2026!')
REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'reports', 'e2e')

ROLES = {
    'expert': ('expert1@cnetp.cd', '/app/'),
    'ctc': ('ctc1@cnetp.cd', '/ctc/'),
    'pilotage': ('pilote1@cnetp.cd', '/pilotage/bureau-directoire/'),
    'ministre': ('ministre1@cnetp.cd', '/pilotage/'),
}


def _extract_csrf(session, html):
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
    if match:
        return match.group(1)
    return session.cookies.get('csrftoken')


@pytest.fixture(scope='session')
def base_url():
    return BASE_URL


@pytest.fixture
def api_login():
    """Retourne une fonction de connexion qui renvoie une session requests authentifiée."""
    def _login(email, password=None):
        session = requests.Session()
        resp = session.get(f'{BASE_URL}/se-connecter/', timeout=15)
        token = _extract_csrf(session, resp.text)
        session.post(
            f'{BASE_URL}/se-connecter/',
            data={'email': email, 'password': password or E2E_PASSWORD,
                  'csrfmiddlewaretoken': token},
            headers={'Referer': f'{BASE_URL}/se-connecter/'},
            timeout=15,
        )
        return session
    return _login


def api(session, method, path, **kwargs):
    """Appel API authentifié (ajoute le jeton CSRF)."""
    headers = kwargs.pop('headers', {})
    headers['X-CSRFToken'] = session.cookies.get('csrftoken', '')
    headers['Referer'] = BASE_URL
    return session.request(method, f'{BASE_URL}{path}', headers=headers, timeout=30, **kwargs)


@pytest.fixture
def screenshot():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    def _shot(page, name):
        path = os.path.join(REPORTS_DIR, f'{name}.png')
        page.screenshot(path=path)
        return path
    return _shot
