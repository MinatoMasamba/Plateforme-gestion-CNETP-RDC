"""Tests E2E d'interface (navigateur réel Playwright) : connexion par rôle.

Prérequis : serveur live + base seedée (``python manage.py seed_e2e``).
Lancer avec : ``pytest tests/e2e -m e2e``
"""
import os

import pytest

from tests.e2e.conftest import BASE_URL, E2E_PASSWORD, ROLES


pytestmark = pytest.mark.e2e


def _login(page, email):
    page.goto(f'{BASE_URL}/se-connecter/', wait_until='domcontentloaded')
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', E2E_PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')


@pytest.mark.parametrize('role', ['expert', 'ctc', 'pilotage'])
def test_login_and_landing(page, role, screenshot):
    email, expected = ROLES[role]
    _login(page, email)
    page.wait_for_url(f'**{expected}', timeout=20000)
    assert expected.rstrip('/') in page.url
    assert page.content().strip()
    shot = screenshot(page, f'login_{role}')
    assert os.path.exists(shot)


def test_expert_app_renders_editor(page, screenshot):
    email, _ = ROLES['expert']
    _login(page, email)
    page.wait_for_url('**/app/**', timeout=20000)
    # L'éditeur de norme est présent dans le template /app/
    page.wait_for_selector('#ed-main-textarea', state='attached', timeout=15000)
    screenshot(page, 'expert_app_editor')


def test_ctc_dashboard_renders(page, screenshot):
    email, _ = ROLES['ctc']
    _login(page, email)
    page.wait_for_url('**/ctc/**', timeout=20000)
    assert '/ctc/' in page.url
    screenshot(page, 'ctc_dashboard')


def test_pilotage_directoire_renders(page, screenshot):
    email, _ = ROLES['pilotage']
    _login(page, email)
    page.wait_for_url('**/pilotage/**', timeout=20000)
    assert '/pilotage/' in page.url
    screenshot(page, 'pilotage_directoire')


def test_ctc_norme_read_a4(page, screenshot):
    """La page de lecture CTC doit être un vrai document A4 avec bandeau d'État et pied fixe."""
    email, _ = ROLES['ctc']
    _login(page, email)
    page.wait_for_url('**/ctc/**', timeout=20000)

    link = page.locator('a[href*="/ctc/norme/"][href*="/lecture/"]').first
    link.wait_for(state='attached', timeout=15000)
    href = link.get_attribute('href')
    page.goto(f'{BASE_URL}{href}', wait_until='domcontentloaded')

    page.wait_for_selector('.a4-sheet', state='visible', timeout=15000)
    assert page.locator('.a4-sheet').is_visible()
    # Bandeau d'État RDC + armoiries
    assert page.locator('text=Cellule Technique de Coordination').count() >= 1
    assert page.locator('img[alt*="République Démocratique du Congo"]').count() >= 1
    # Pied de page réglementaire fixé en bas + QR de traçabilité
    assert page.locator('footer.fixed.bottom-0').count() == 1
    assert page.locator('footer img[alt*="QR"]').count() >= 1
    shot = screenshot(page, 'ctc_norme_read_a4')
    assert os.path.exists(shot)
