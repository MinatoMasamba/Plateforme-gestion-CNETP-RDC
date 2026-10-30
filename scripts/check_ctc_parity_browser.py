"""Capture Django and Flutter CTC dashboards with one local CTC identity."""
import json
import os
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.conf import settings
from django.test import Client
from apps.experts.models import Expert
from playwright.sync_api import sync_playwright
from rest_framework_simplejwt.tokens import RefreshToken
from web.ctc_views import get_ctc_context


def main():
    iteration = sys.argv[1] if len(sys.argv) > 1 else '1'
    output = Path('reports/ctc_parity')
    output.mkdir(parents=True, exist_ok=True)
    requested_role = os.environ.get('CTC_ROLE')
    target_view = os.environ.get('CTC_TARGET_VIEW')
    expert = next(
        (item for item in Expert.objects.select_related('user').filter(user__is_active=True)
         if (context := get_ctc_context(item)) and
         (requested_role is None or context.get('ctc_sub_role') == requested_role)), None,
    )
    if expert is None:
        raise RuntimeError('Aucun compte CTC actif dans la base locale.')
    ctc = get_ctc_context(expert)
    client = Client()
    client.force_login(expert.user, backend='django.contrib.auth.backends.ModelBackend')
    refresh = RefreshToken.for_user(expert.user)
    session = {
        'access': str(refresh.access_token), 'refresh': str(refresh),
        'userId': expert.user_id, 'email': expert.user.email,
        'fullName': expert.full_name, 'userType': 'expert',
        'space': 'ctc', 'isCtc': True,
        'ctcRole': ctc.get('pole_label'),
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        for width, height in ((1440, 900), (390, 844)):
            errors = []
            if os.environ.get('CTC_SKIP_WEB') != '1':
                context = browser.new_context(viewport={'width': width, 'height': height})
                context.add_cookies([{
                    'name': settings.SESSION_COOKIE_NAME,
                    'value': client.cookies[settings.SESSION_COOKIE_NAME].value,
                    'url': 'http://127.0.0.1:1111/',
                }])
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('requestfailed', lambda request: errors.append(f'{request.failure}: {request.url}'))
                page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
                page.goto('http://127.0.0.1:1111/ctc/', wait_until='domcontentloaded', timeout=90000)
                page.wait_for_timeout(1500)
                if target_view or os.environ.get('CTC_CHECK_STATS') == '1':
                    page.evaluate('(view) => window.switchView(view)', target_view or 'statistiques')
                    page.wait_for_timeout(1200)
                page.screenshot(path=str(output / f'{iteration}_web_{width}.png'), full_page=True)
                print('WEB', width, page.url, page.locator('body').inner_text()[:350].replace('\n', ' '), flush=True)
                context.close()

            context = browser.new_context(viewport={'width': width, 'height': height})
            # shared_preferences_web JSON-encodes string values in localStorage.
            context.add_init_script('localStorage.setItem("flutter.cnetp_session", '
                                    + json.dumps(json.dumps(json.dumps(session))) + ');')
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('requestfailed', lambda request: errors.append(f'{request.failure}: {request.url}'))
            page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
            responses = []
            page.on('response', lambda response: responses.append((response.status, response.url)))
            flutter_port = os.environ.get('CTC_FLUTTER_PORT', '8083')
            page.goto(f'http://127.0.0.1:{flutter_port}/#/ctc', wait_until='domcontentloaded')
            page.wait_for_timeout(15000)
            placeholder = page.locator('flt-semantics-placeholder')
            if placeholder.count():
                placeholder.evaluate('(element) => element.click()')
            page.wait_for_timeout(500)
            page.screenshot(path=str(output / f'{iteration}_flutter_{width}.png'), full_page=True)
            print('FLUTTER', width, page.url, page.locator('body').inner_text()[:350].replace('\n', ' '), flush=True)
            print('ERRORS', width, errors[:5], flush=True)
            print('RESPONSES', width, responses[-12:], flush=True)
            print('API_RESPONSES', width, [item for item in responses if '/api/' in item[1]], flush=True)
            print('DOCUMENT', width, page.evaluate('({ready: document.readyState, children: document.body.children.length, text: document.body.innerText.slice(0,100)})'), flush=True)
            print('STORAGE', width, page.evaluate('Object.keys(localStorage)'), flush=True)
            print('STORAGE_SHAPE', width, page.evaluate('(() => { const x = localStorage.getItem("flutter.cnetp_session"); try { const y = JSON.parse(x); return {length:x.length, type:typeof y, keys:typeof y === "object" ? Object.keys(y) : []}; } catch(e) { return {length:x.length, error:String(e)}; } })()'), flush=True)
            if width == 1440 and (target_view or os.environ.get('CTC_CHECK_STATS') == '1'):
                target_name = {'experts': 'Experts et affectations', 'tracabilite': 'Traçabilité', 'instructions': 'Instruction', 'homologations': 'Homologations', 'archives': 'Archives'}.get(target_view, 'Suivi statistique')
                page.get_by_role('button', name=target_name).click()
                if target_view:
                    pattern = (r'Sous-commissions \(CTM\) · \d+' if target_view == 'instructions'
                               else r'\d+ norme\(s\)' if target_view in {'homologations', 'archives'}
                               else r'\d+ résultat\(s\)')
                    page.get_by_text(re.compile(pattern)).wait_for(timeout=90000)
                else:
                    page.wait_for_timeout(800)
                page.screenshot(path=str(output / f'{iteration}_flutter_{target_view or "stats"}_1440.png'))
                print('DESKTOP_VIEW', page.locator('body').inner_text()[:350].replace('\n', ' '), flush=True)
                print('DESKTOP_API', [item for item in responses if '/api/v1/mobile/ctc/' in item[1]], flush=True)
            if width == 390 and os.environ.get('CTC_CHECK_NAV') == '1':
                page.get_by_role('button', name='Ouvrir le menu').click()
                page.screenshot(path=str(output / f'{iteration}_flutter_menu_390.png'))
                target = ({'experts': 'Experts et affectations', 'tracabilite': 'Traçabilité', 'instructions': 'Instruction', 'homologations': 'Homologations', 'archives': 'Archives'}[target_view] if target_view
                          else 'Suivi statistique' if os.environ.get('CTC_CHECK_STATS') == '1'
                          else 'Assistant Exécutif' if requested_role == 'assistant_executif'
                          else 'Dossiers normatifs')
                page.get_by_role('button', name=target).click()
                if target_view:
                    pattern = (r'Sous-commissions \(CTM\) · \d+' if target_view == 'instructions'
                               else r'\d+ norme\(s\)' if target_view in {'homologations', 'archives'}
                               else r'\d+ résultat\(s\)')
                    page.get_by_text(re.compile(pattern)).wait_for(timeout=90000)
                else:
                    page.wait_for_timeout(800)
                suffix = (target_view if target_view
                          else 'stats' if os.environ.get('CTC_CHECK_STATS') == '1'
                          else 'requests' if requested_role == 'assistant_executif' else 'dossiers')
                page.screenshot(path=str(output / f'{iteration}_flutter_{suffix}_390.png'))
                print('MOBILE_NAV', page.locator('body').inner_text()[:350].replace('\n', ' '), flush=True)
                print('MOBILE_API', [item for item in responses if '/api/v1/mobile/ctc/' in item[1]], flush=True)
            context.close()
        browser.close()


if __name__ == '__main__':
    main()
