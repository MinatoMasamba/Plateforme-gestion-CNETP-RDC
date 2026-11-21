"""Recette visuelle Flutter et inventaire API sur une base de test isolée."""
import json
import os
import sys
import subprocess
import time
import urllib.request
from io import BytesIO
from PIL import Image
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_test'
os.environ['SQLITE_NAME'] = '/tmp/expert_beta_review.sqlite3'
os.environ['APPSTORE_PACKAGES_ROOT'] = '/tmp/expert_beta_packages'
os.environ['CLIENT_DIAGNOSTICS_DIR'] = '/tmp/expert_beta_diagnostics'
import django
django.setup()
from apps.core.models import User
from apps.mobileapp.models import ClientDiagnostic
from django.test import Client
from rest_framework_simplejwt.tokens import RefreshToken
from playwright.sync_api import sync_playwright

iteration = sys.argv[1] if len(sys.argv) > 1 else '1'
output = Path('reports/expert_beta')
output.mkdir(parents=True, exist_ok=True)
web_dir = Path(os.environ.get('EXPERT_REVIEW_WEB_DIR', 'flutter_app/build/web')).resolve()
web_port = int(os.environ.get('EXPERT_REVIEW_PORT', '8084'))
api_port = int(os.environ.get('EXPERT_REVIEW_API_PORT', '1119'))
if f'http://127.0.0.1:{api_port}' not in (web_dir / 'main.dart.js').read_text():
    raise RuntimeError('La compilation Flutter ne cible pas le serveur de recette demandé.')
servers = []
import atexit
def stop_servers():
    for server in servers:
        if server.poll() is None:
            server.terminate()
        server.wait(timeout=10)
atexit.register(stop_servers)
for port, command, cwd in [
    (api_port, [sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{api_port}', '--settings=config.settings_test', '--noreload'], '.'),
    (web_port, [sys.executable, '-m', 'http.server', str(web_port), '--bind', '127.0.0.1'], str(web_dir)),
]:
    try:
        urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=2)
    except Exception:
        env = dict(os.environ, CORS_ALLOWED_ORIGINS=f'http://127.0.0.1:{web_port}', CORS_ALLOW_ALL_ORIGINS='False')
        servers.append(subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    for attempt in range(60):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=2)
            break
        except Exception:
            time.sleep(1)
    else:
        raise RuntimeError(f'Serveur de recette indisponible : {port}')
user = User.objects.get(username='beta_review')
inject_diagnostic = os.environ.get('EXPERT_REVIEW_INJECT_DIAGNOSTIC') == '1'
diagnostic_before = set(ClientDiagnostic.objects.filter(user=user).values_list('id', flat=True))
refresh = RefreshToken.for_user(user)
session = {'access': str(refresh.access_token), 'refresh': str(refresh), 'userId': user.pk, 'email': user.email, 'fullName': user.get_full_name(), 'userType': 'expert', 'space': 'expert'}
client = Client()
client.force_login(user)
paths = ['/api/v1/sidebar/documents/', '/api/v1/activity/my-counter/', '/api/v1/experts/me/', '/api/v1/experts/my-affiliation/', '/api/v1/wg/', '/api/v1/experts/', '/api/v1/mobile/expert/meetings/', '/api/v1/cotisations/dashboard/', '/api/v1/cotisations/', '/api/v1/paiements/', '/api/v1/jetons/', '/api/v1/legistic-reviews/workspace/', '/api/v1/legistic-reviews/legistique-workspace/', '/api/v1/mobile/notifications/', '/api/v1/messages/contacts/', '/api/v1/experts/pending-count-for-my-ctm/']
audit = []
for path in paths:
    response = client.get(path)
    audit.append({'path': path, 'status': response.status_code, 'body': response.content.decode()[:400]})
(output / 'api_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2))
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    sizes = ((1440, 1000), (390, 844))
    requested_width = os.environ.get('EXPERT_REVIEW_WIDTH')
    if requested_width:
        sizes = tuple(size for size in sizes if str(size[0]) == requested_width)
    tabs = [int(value) for value in os.environ.get('EXPERT_REVIEW_TABS', '0,1,2,3,4,5,6,7,8,9').split(',')]
    for width, height in sizes:
        context = browser.new_context(viewport={'width': width, 'height': height}, accept_downloads=True)
        context.add_init_script('localStorage.setItem("flutter.cnetp_session", ' + json.dumps(json.dumps(json.dumps(session))) + ');')
        page = context.new_page()
        if inject_diagnostic:
            page.route('**/api/v1/mobile/notifications/unread_count/',
                       lambda route: route.fulfill(status=503, content_type='application/json', body='{"detail":"Erreur de recette contrôlée"}'), times=1)
        errors = []
        responses = []
        page.on('response', lambda response: responses.append({'status': response.status, 'url': response.url}) if '/api/' in response.url else None)
        page.on('pageerror', lambda error: errors.append(str(error)))
        def is_light():
            shot = page.screenshot()
            pixel = Image.open(BytesIO(shot)).convert('RGB').getpixel((5, height // 2))
            return sum(pixel) >= 500
        def toggle_theme():
            if width == 1440:
                target = page.get_by_text('THÈME', exact=True)
                if target.count():
                    target.first.click()
                else:
                    page.mouse.click(width - 200, 36)
            else:
                target = page.get_by_role('button', name='Actions', exact=True)
                if target.count():
                    target.click()
                else:
                    page.mouse.click(320, 36)
                page.wait_for_timeout(300)
                page.screenshot(path=str(output / f'{iteration}_menu_{width}.png'))
                target = page.get_by_text('Thème', exact=True)
                if target.count():
                    target.click()
                else:
                    page.mouse.click(290, 36)
            page.wait_for_timeout(500)
        for tab in tabs:
            page.goto(f'http://127.0.0.1:{web_port}/#/expert?tab={tab}', wait_until='domcontentloaded')
            if tab == 0:
                page.reload(wait_until='domcontentloaded')
            page.wait_for_timeout(2500 if tab else 12000)
            placeholder = page.locator('flt-semantics-placeholder')
            if placeholder.count():
                placeholder.evaluate('(e) => e.click()')
            page.wait_for_load_state('networkidle', timeout=90000)
            if tab == 0:
                for attempt in range(120):
                    if any('/api/v1/norms/1/' in item['url'] and item['status'] == 200 for item in responses):
                        break
                    page.wait_for_timeout(250)
                else:
                    raise RuntimeError('Le document de recette n’a pas été chargé par Flutter.')
            page.wait_for_timeout(2000)
            placeholder = page.locator('flt-semantics-placeholder')
            if placeholder.count():
                placeholder.evaluate('(e) => e.click()')
                page.wait_for_timeout(500)
            if is_light():
                toggle_theme()
            page.mouse.move(width - 10, height - 10)
            page.wait_for_timeout(800)
            page.screenshot(path=str(output / f'{iteration}_tab{tab}_{width}_dark.png'))
            print(f'CAPTURE {iteration} tab={tab} width={width}', flush=True)
            if not is_light():
                toggle_theme()
            if not is_light():
                toggle_theme()
            if not is_light():
                raise RuntimeError(f'Le thème clair n’a pas été activé : {width}, onglet {tab}')
            page.mouse.move(width - 10, height - 10)
            page.wait_for_timeout(800)
            page.screenshot(path=str(output / f'{iteration}_tab{tab}_{width}_light.png'))
            print(f'CAPTURE LIGHT {iteration} tab={tab} width={width}', flush=True)
            if is_light():
                toggle_theme()
            if tab == 3:
                details = page.get_by_role('button', name='Détails et participation', exact=True)
                if details.count():
                    details.first.click()
                elif width == 1440:
                    page.mouse.click(420, 563)
                else:
                    (output / f'{iteration}_semantics_{width}.html').write_text(page.content())
                    continue
                page.wait_for_timeout(1800)
                page.screenshot(path=str(output / f'{iteration}_participation_{width}_dark.png'))
                assert page.get_by_text('Préparer la séance', exact=True).count() == 0
                assert page.get_by_text('Clore le scrutin et générer le PV', exact=True).count() == 0
                page.mouse.move(width - 45, height // 2)
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(400)
                page.screenshot(path=str(output / f'{iteration}_participation_suite_{width}_dark.png'))
            if tab == 8:
                page.mouse.move(width - 60, height // 2)
                page.mouse.wheel(0, 1800)
                page.wait_for_timeout(500)
                page.screenshot(path=str(output / f'{iteration}_profile_settings_{width}_dark.png'))
        for route in ('ctc', 'pilotage', 'pilotage/directoire'):
            page.goto(f'http://127.0.0.1:{web_port}/#/{route}')
            page.wait_for_timeout(800)
            assert 'acces-restreint' in page.url, page.url
        page.screenshot(path=str(output / f'{iteration}_restricted_{width}.png'))
        (output / f'{iteration}_errors_{width}.json').write_text(json.dumps(errors))
        (output / f'{iteration}_responses_{width}.json').write_text(json.dumps(responses, indent=2))
        failed = [item for item in responses if item['status'] >= 400 and not (
            inject_diagnostic and item['status'] == 503 and '/notifications/unread_count/' in item['url']
        )]
        if errors or failed:
            raise RuntimeError(f'Erreurs de recette : {errors}, HTTP : {failed}')
        context.close()
    browser.close()
if inject_diagnostic:
    incident = ClientDiagnostic.objects.filter(user=user, category='network', journal_written=True).exclude(pk__in=diagnostic_before).first()
    assert incident is not None, 'Flutter n’a pas transmis l’erreur contrôlée au journal serveur.'
    assert incident.details.get('status_code') == 503
    assert Path('/tmp/expert_beta_diagnostics/flutter_errors.txt').exists()
    (output / f'{iteration}_diagnostic.json').write_text(json.dumps({'id': str(incident.pk), 'status': 503, 'journal_written': True}))
(output / f'{iteration}_complete.json').write_text(json.dumps({
    'widths': [size[0] for size in sizes], 'tabs': tabs,
    'themes': ['dark', 'light'],
    'blocked_routes': ['/ctc', '/pilotage', '/pilotage/directoire'],
    'completed': True,
}, indent=2))
print(json.dumps([{'path': x['path'], 'status': x['status']} for x in audit]), flush=True)
