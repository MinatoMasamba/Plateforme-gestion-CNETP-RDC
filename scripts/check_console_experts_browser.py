"""Contrôle visuel et fonctionnel de l'annuaire sur le serveur local existant."""
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from apps.experts.models import Expert
from playwright.sync_api import expect, sync_playwright

BASE = 'http://127.0.0.1:1111'
DIRECTORY = BASE + '/dashboard/administration/modeles/experts/expert/'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    user = get_user_model().objects.filter(is_active=True, is_superuser=True).first()
    if not user:
        raise RuntimeError('Aucun compte administrateur local disponible.')
    expected_total = Expert.objects.count()
    expected_pending = Expert.objects.filter(status='PENDING').count()
    client = Client()
    client.force_login(user, backend='django.contrib.auth.backends.ModelBackend')
    cookie = client.cookies[settings.SESSION_COOKIE_NAME].value
    output = Path('reports/console_experts_redesign')
    output.mkdir(parents=True, exist_ok=True)
    errors = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='chrome', headless=True)
            context = browser.new_context(viewport={'width': 1440, 'height': 1000})
            context.add_cookies([{'name': settings.SESSION_COOKIE_NAME, 'value': cookie, 'url': BASE}])
            context.add_init_script("localStorage.setItem('theme-preference', 'light');")
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))

            def visit(query=''):
                response = page.goto(DIRECTORY + query, wait_until='networkidle')
                assert response.status == 200
                page.wait_for_timeout(250)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), page.viewport_size
                assert page.get_by_role('heading', name='Gestion des experts', exact=True).count() == 1

            def capture(name):
                page.screenshot(path=str(output / (name + '.png')))

            visit()
            assert int(page.locator('.console-metric > strong').first.inner_text()) == expected_total
            assert page.locator('.console-metric').count() in (4, 5)
            assert page.locator('.expert-status').count() <= 25
            capture('desktop_light')
            if page.locator('#result_list tbody tr').count():
                scroll = page.locator('.expert-table-scroll')
                top = page.locator('#result_list thead').evaluate('(el) => el.getBoundingClientRect().top')
                scroll.evaluate('(el) => el.scrollTop = 180')
                page.wait_for_timeout(100)
                sticky_top = page.locator('#result_list thead th').first.evaluate('(el) => el.getBoundingClientRect().top')
                assert abs(sticky_top - top) <= 2
                scroll.evaluate('(el) => el.scrollTop = 0')
                page.locator('[data-console-row-menu] summary').first.click()
                panel = page.locator('body > .console-row-menu-panel')
                panel.wait_for(state='visible')
                box = panel.bounding_box()
                assert box['x'] >= 0 and box['x'] + box['width'] <= 1440
                assert panel.get_by_role('link', name='Voir la fiche').count() == 1
                expect(panel.get_by_role('link', name='Voir la fiche')).to_be_focused()
                page.keyboard.press('ArrowDown')
                expect(panel.get_by_role('link', name='Modifier', exact=True)).to_be_focused()
                capture('desktop_actions')
                page.keyboard.press('Escape')
                assert not page.locator('[data-console-row-menu][open]').count()

            page.locator('[data-structure-filter] summary').click()
            structure_search = page.get_by_role('searchbox', name='Rechercher une structure')
            structure_search.fill('structure-introuvable-000')
            assert page.locator('[data-structure-empty]').is_visible()
            structure_search.fill('')
            checkboxes = page.locator('.expert-structure-option input')
            if checkboxes.count() >= 2:
                labels = [page.locator('.expert-structure-option > span').nth(i).inner_text().split('\n')[0] for i in range(2)]
                checkboxes.nth(0).check()
                checkboxes.nth(1).check()
                assert page.locator('[data-structure-count]').inner_text() == '2'
                capture('desktop_structures')
                page.locator('.expert-structures [data-popover-close]').click()
                page.get_by_label('Statut', exact=True).select_option('ACTIVE')
                page.get_by_role('button', name='Appliquer', exact=True).click()
                page.wait_for_url('**/*status__exact=ACTIVE*')
                page.wait_for_load_state('networkidle')
                assert page.locator('.expert-structure-option input:checked').count() == 2
                assert len(parse_qs(urlparse(page.url).query)['structure__id__in']) == 2
                page.get_by_role('link', name='Retirer le filtre ' + labels[0], exact=True).click()
                page.wait_for_load_state('networkidle')
                assert page.locator('.expert-structure-option input:checked').count() == 1
                assert page.get_by_label('Statut', exact=True).input_value() == 'ACTIVE'

            visit('?status=PENDING')
            assert page.get_by_label('Statut', exact=True).input_value() == 'PENDING'
            if expected_pending == 0:
                assert page.get_by_role('heading', name='Aucun expert trouvé').is_visible()
            capture('pending_light')

            page.set_viewport_size({'width': 1024, 'height': 900})
            visit()
            assert page.locator('#console-sidebar').bounding_box()['width'] == 82
            capture('tablet_light')
            page.set_viewport_size({'width': 390, 'height': 844})
            visit()
            assert page.locator('#console-sidebar').evaluate('(el) => el.inert')
            capture('mobile_light')
            page.get_by_role('button', name='Afficher ou masquer le menu').click()
            expect(page.get_by_role('button', name='Fermer le menu', exact=True)).to_be_focused()
            capture('mobile_navigation')
            page.keyboard.press('Shift+Tab')
            assert page.evaluate('Boolean(document.activeElement.closest("#console-sidebar"))')
            page.keyboard.press('Escape')
            expect(page.get_by_role('button', name='Afficher ou masquer le menu')).to_be_focused()
            assert page.locator('#console-sidebar').evaluate('(el) => el.inert')
            page.set_viewport_size({'width': 1440, 'height': 1000})
            visit()
            page.get_by_role('button', name='Activer le thème sombre').click()
            assert page.locator('html').evaluate('(el) => el.classList.contains("dark")')
            capture('desktop_dark')
            assert not errors, errors
            print('DIRECTORY_DESKTOP_TABLET_MOBILE_FILTERS_ACTIONS_AND_THEMES_OK')
            print('Captures :', output)
            browser.close()
    finally:
        client.logout()


if __name__ == '__main__':
    main()
