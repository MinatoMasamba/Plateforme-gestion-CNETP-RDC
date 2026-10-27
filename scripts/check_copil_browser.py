"""Capture the running web reference with an existing local COPIL account."""
import os
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.conf import settings
from django.test import Client
from apps.experts.models import Expert
from web.pilotage_views import get_pilotage_context
from playwright.sync_api import sync_playwright
from rest_framework_simplejwt.tokens import RefreshToken


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    expert = Expert.objects.select_related('user').filter(user__email='ed@gmail.com').first()
    if not expert or not get_pilotage_context(expert):
        expert = next(e for e in Expert.objects.select_related('user').filter(
            user__is_active=True) if (get_pilotage_context(e) or {}).get('can_view_global_console'))
    client = Client()
    client.force_login(expert.user, backend='django.contrib.auth.backends.ModelBackend')
    token = RefreshToken.for_user(expert.user) if '--flutter' in sys.argv else None
    output = Path('reports/copil_parity')
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        context.add_cookies([{'name': settings.SESSION_COOKIE_NAME,
                             'value': client.cookies[settings.SESSION_COOKIE_NAME].value,
                             'url': 'http://127.0.0.1:1111/'}])
        page = context.new_page()
        page.on('requestfailed', lambda req: print('REQUEST_FAILED', req.url, req.failure))
        page.on('console', lambda msg: print('BROWSER_ERROR', msg.text) if msg.type == 'error' else None)
        page.on('response', lambda res: print('HTTP_ERROR', res.status, res.url) if res.status >= 400 else None)
        for name, route in [('supervision', '/pilotage/#panel-sc'),
                            ('activite', '/pilotage/activites/'),
                            ('directoire', '/pilotage/bureau-directoire/'),
                            ('organisation', '/pilotage/organisation/'),
                            ('profil', '/pilotage/profil/')]:
            page.goto('http://127.0.0.1:1111' + route, wait_until='networkidle')
            page.wait_for_timeout(1000)
            page.screenshot(path=str(output / f'web_{name}.png'))
            print(name, page.url, page.locator('body').inner_text()[:700], flush=True)
        page.goto('http://127.0.0.1:1111/pilotage/#panel-sc', wait_until='networkidle')
        page.get_by_role('button', name='Donner une instruction', exact=True).click()
        page.screenshot(path=str(output / 'web_instruction.png'))
        print('INSTRUCTION', page.locator('[data-global-instruction-drawer]').inner_text())
        page.set_viewport_size({'width': 390, 'height': 844})
        page.get_by_role('button', name='Fermer', exact=True).click()
        page.goto('http://127.0.0.1:1111/pilotage/#panel-sc', wait_until='networkidle')
        page.screenshot(path=str(output / 'web_mobile.png'))
        if '--flutter' in sys.argv:
            session = json.dumps({'access': str(token.access_token), 'refresh': str(token),
                                  'userId': expert.user_id, 'email': expert.user.email,
                                  'fullName': expert.full_name, 'userType': 'expert',
                                  'space': 'pilotage', 'isPilotage': True})
            context.add_init_script('localStorage.setItem("flutter.cnetp_session", ' + json.dumps(json.dumps(session)) + ');')
            page.set_viewport_size({'width': 1440, 'height': 900})
            page.goto('http://127.0.0.1:8082/#/pilotage', wait_until='networkidle')
            page.wait_for_timeout(5000)
            page.evaluate("window.location.hash = '/pilotage'")
            page.wait_for_timeout(2000)
            placeholder = page.locator('flt-semantics-placeholder')
            if placeholder.count():
                placeholder.evaluate('(el) => el.click()')
            page.wait_for_timeout(1000)
            page.screenshot(path=str(output / 'flutter_supervision.png'))
            print('FLUTTER', page.locator('body').inner_text()[:5000])
            page.get_by_text('Donner une instruction', exact=True).click()
            page.screenshot(path=str(output / 'flutter_instruction.png'))
            page.get_by_text('Fermer', exact=True).click()
            page.get_by_text('Espace Bureau Directoire', exact=True).click()
            page.wait_for_timeout(1200)
            page.screenshot(path=str(output / 'flutter_directoire.png'))
            assert 'MES FONCTIONS' in page.locator('body').inner_text()
            page.get_by_text('Organisation CNE-ITP', exact=True).click()
            page.wait_for_timeout(1500)
            page.screenshot(path=str(output / 'flutter_organisation.png'))
            # Theme control at the top-right of the organisation reference.
            page.mouse.click(page.viewport_size['width'] - 38, 42)
            page.wait_for_timeout(300)
            page.screenshot(path=str(output / 'flutter_organisation_light.png'))
            page.get_by_text('Secrétariat technique', exact=True).first.click()
            page.wait_for_timeout(300)
            page.screenshot(path=str(output / 'flutter_secretariat.png'))
            print('DIRECTOIRE_ORGANISATION_NAVIGATION_OK')
            page.goto('http://127.0.0.1:8082/#/pilotage', wait_until='networkidle')
            page.wait_for_timeout(1200)
            placeholder = page.locator('flt-semantics-placeholder')
            if placeholder.count():
                placeholder.evaluate('(el) => el.click()')
            page.set_viewport_size({'width': 390, 'height': 844})
            page.wait_for_timeout(500)
            page.screenshot(path=str(output / 'flutter_mobile.png'))
        browser.close()
    client.logout()


if __name__ == '__main__':
    main()
