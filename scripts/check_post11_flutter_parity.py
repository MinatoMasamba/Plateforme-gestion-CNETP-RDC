"""Capture Django and Flutter CTC dashboards with one local CTC identity."""
import json
import os
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if not os.environ.get('SQLITE_NAME', '').startswith('/tmp/'):
    raise RuntimeError('La recette exige une copie SQLite dans /tmp via SQLITE_NAME.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')
import django
django.setup()

from django.conf import settings
from django.test import Client
from apps.experts.models import Expert
from playwright.sync_api import sync_playwright
from rest_framework_simplejwt.tokens import RefreshToken
from web.ctc_views import get_ctc_context


def sync_db(callback):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(callback).result()


def main():
    import threading
    from socketserver import ThreadingMixIn
    from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.wsgi import get_wsgi_application
    settings.DEBUG = True
    settings.CORS_ALLOW_ALL_ORIGINS = True
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    class Server(ThreadingMixIn, WSGIServer):
        daemon_threads = True
        allow_reuse_address = True
    class Quiet(WSGIRequestHandler):
        def log_message(self, *args):
            pass
    server = make_server('127.0.0.1', 1117, StaticFilesHandler(get_wsgi_application()), server_class=Server, handler_class=Quiet)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    from functools import partial
    from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
    flutter_server = ThreadingHTTPServer(('127.0.0.1', 8083), partial(SimpleHTTPRequestHandler, directory=os.environ.get('POST11_BUILD_DIR', str(Path(__file__).resolve().parents[1] / 'flutter_app/build/web'))))
    threading.Thread(target=flutter_server.serve_forever, daemon=True).start()

    iteration = sys.argv[1] if len(sys.argv) > 1 else '1'
    output = Path('reports/poste11_flutter')
    output.mkdir(parents=True, exist_ok=True)
    requested_role = os.environ.get('CTC_ROLE')
    from apps.governance.models import MandatOrganisation
    user_ids = MandatOrganisation.objects.filter(poste__code='ST-V3-11', status='ACTIVE').values_list('expert__user_id', flat=True)
    target_view = os.environ.get('CTC_TARGET_VIEW')
    expert = next(
        (item for item in Expert.objects.select_related('user').filter(user__is_active=True, user_id__in=user_ids)
         if (context := get_ctc_context(item)) and
         (requested_role is None or context.get('ctc_sub_role') == requested_role)), None,
    )
    if expert is None:
        raise RuntimeError('Aucun compte CTC actif dans la base locale.')
    ctc = get_ctc_context(expert)
    assert ctc.get('st_post_code') == 'ST-V3-11', 'Le compte doit résoudre le mandat de recette poste 11'
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
        sizes = ((1440, 900), (390, 844))
        for width, height in sizes:
            if os.environ.get('POST11_WIDTH') and width != int(os.environ['POST11_WIDTH']):
                continue
            errors = []
            if os.environ.get('CTC_SKIP_WEB') != '1':
                context = browser.new_context(viewport={'width': width, 'height': height})
                context.add_cookies([{
                    'name': settings.SESSION_COOKIE_NAME,
                    'value': client.cookies[settings.SESSION_COOKIE_NAME].value,
                    'url': 'http://127.0.0.1:1117/',
                }])
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('requestfailed', lambda request: errors.append(f'{request.failure}: {request.url}'))
                page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
                page.goto('http://127.0.0.1:1117/ctc/', wait_until='domcontentloaded', timeout=90000)
                page.locator('[data-ged-workspace][aria-busy=false]').wait_for(timeout=90000)
                page.wait_for_timeout(1000)
                if target_view or os.environ.get('CTC_CHECK_STATS') == '1':
                    page.evaluate('(view) => window.switchView(view)', target_view or 'statistiques')
                    page.wait_for_timeout(1200)
                page.screenshot(path=str(output / f'{iteration}_web_{width}.png'), full_page=True)
                print('WEB', width, page.url, page.locator('body').inner_text()[:350].replace('\n', ' '), flush=True)
                if os.environ.get('POST11_PANELS') == '1':
                    for panel in ['work', 'library', 'versions_todo', 'history', 'codes', 'anomalies', 'activity']:
                        page.evaluate('(panel) => window.stGEDOpenMode(panel)', {'work':'indexation', 'library':'ged', 'versions_todo':'ged_versions_todo', 'history':'versions', 'codes':'codification', 'anomalies':'ged_anomalies', 'activity':'ged_activity'}[panel])
                        if panel == 'work':
                            page.locator('[data-ged-queue][aria-busy=false]').wait_for(timeout=90000)
                        page.wait_for_timeout(1800)
                        page.screenshot(path=str(output / f'{iteration}_web_{panel}_{width}.png'))
                context.close()

            context = browser.new_context(viewport={'width': width, 'height': height})
            if os.environ.get('POST11_PROXY_API') == '1':
                context.route('http://127.0.0.1:1111/api/**', lambda route: route.fulfill(response=route.fetch(url=route.request.url.replace('127.0.0.1:1111', '127.0.0.1:1117'))))
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
            page.wait_for_timeout(18000)
            placeholder = page.locator('flt-semantics-placeholder')
            if placeholder.count():
                placeholder.evaluate('(element) => element.click()')
            page.get_by_text('Espace documentaire', exact=True).wait_for(timeout=90000)
            page.wait_for_timeout(1000)
            page.screenshot(path=str(output / f'{iteration}_flutter_{width}.png'), full_page=False)
            print('FLUTTER', width, page.url, page.locator('body').inner_text()[:350].replace('\n', ' '), flush=True)
            (output / f'{iteration}_errors_{width}.json').write_text(json.dumps(errors, ensure_ascii=False, indent=2))
            print('ERRORS', width, errors[:5], flush=True)
            print('RESPONSES', width, responses[-12:], flush=True)
            print('API_RESPONSES', width, [item for item in responses if '/api/' in item[1]], flush=True)
            print('DOCUMENT', width, page.evaluate('({ready: document.readyState, children: document.body.children.length, text: document.body.innerText.slice(0,100)})'), flush=True)
            print('STORAGE', width, page.evaluate('Object.keys(localStorage)'), flush=True)
            print('STORAGE_SHAPE', width, page.evaluate('(() => { const x = localStorage.getItem("flutter.cnetp_session"); try { const y = JSON.parse(x); return {length:x.length, type:typeof y, keys:typeof y === "object" ? Object.keys(y) : []}; } catch(e) { return {length:x.length, error:String(e)}; } })()'), flush=True)
            if os.environ.get('POST11_PANELS') == '1':
                for panel, label in [('work', 'Dossiers à indexer'), ('library', 'Documents GED'), ('versions_todo', 'Versions à traiter'), ('history', 'Historique des versions'), ('codes', 'Codification'), ('anomalies', 'Anomalies'), ('activity', 'Mon activité')]:
                    if width == 390:
                        page.get_by_role('button', name='Ouvrir le menu').click()
                    page.get_by_role('button', name=re.compile('^' + re.escape(label))).first.click()
                    page.wait_for_timeout(1200)
                    page.screenshot(path=str(output / f'{iteration}_flutter_{panel}_{width}.png'))
                print('PANELS', width, [item for item in responses if '/api/v1/st/' in item[1]], flush=True)
            if os.environ.get('POST11_DETAIL') == '1':
                if width == 390:
                    page.get_by_role('button', name='Ouvrir le menu').click()
                page.get_by_role('button', name=re.compile('^Dossiers à indexer')).first.click()
                page.wait_for_timeout(700)
                page.screenshot(path=str(output / f'{iteration}_flutter_queue_{width}.png'))
                reference = sync_db(lambda: client.get('/api/v1/st/ged/queue/').json()['results'][0]['reference'])
                page.get_by_role('button', name=re.compile(re.escape(reference))).first.click()
                page.wait_for_timeout(700)
                page.screenshot(path=str(output / f'{iteration}_flutter_fiche_{width}.png'))
                if width == 390:
                    page.get_by_role('button', name='Retour à la file des dossiers').click()
                    page.get_by_text('Filtrer par état', exact=True).wait_for()
                    page.screenshot(path=str(output / f'{iteration}_flutter_back_{width}.png'))
                    print('MOBILE_FICHE', 'queue -> fiche -> queue', flush=True)
            if os.environ.get('POST11_INDEX') == '1':
                from apps.governance.models import CTCProcessus
                from apps.governance.st_ged_models import STGEDIndexation
                queue = sync_db(lambda: client.get('/api/v1/st/ged/queue/').json()['results'])
                ready = next(row for row in queue if row['queue_state'] == 'READY')
                before = sync_db(lambda: STGEDIndexation.objects.filter(process_id=ready['id']).count())
                if width == 390:
                    page.get_by_role('button', name='Ouvrir le menu').click()
                page.get_by_role('button', name=re.compile('^Dossiers à indexer')).first.click()
                page.get_by_role('button', name=re.compile(re.escape(ready['reference']))).first.click()
                verified = page.get_by_role('checkbox', name=re.compile('Pièces vérifiées et lisibles'))
                for _ in range(15):
                    bounds = verified.bounding_box() if verified.count() else None
                    if bounds and 0 <= bounds['y'] < height - 80:
                        break
                    page.mouse.move(width - 60, height - 100)
                    page.mouse.wheel(0, 500)
                    page.wait_for_timeout(300)
                (output / f'{iteration}_fiche_{width}.txt').write_text(page.locator('body').inner_text())
                page.screenshot(path=str(output / f'{iteration}_fiche_{width}.png'))
                verified.click()
                with page.expect_response(lambda response: '/index/' in response.url and response.request.method == 'POST') as result:
                    page.get_by_role('button', name='Confirmer l’indexation', exact=True).click()
                assert result.value.status == 201, result.value.text()
                assert sync_db(lambda: STGEDIndexation.objects.filter(process_id=ready['id']).count()) == before + 1
                assert sync_db(lambda: CTCProcessus.objects.get(pk=ready['id']).current_stage) == 'RECEPTION'
                page.wait_for_timeout(1500)
                page.screenshot(path=str(output / f'{iteration}_flutter_indexed_{width}.png'))
                print('INDEXATION', ready['reference'], '201, version persisted, stage RECEPTION', flush=True)
            (output / f'{iteration}_errors_{width}.json').write_text(json.dumps(errors, ensure_ascii=False, indent=2))
            failed_ged = [(status, url) for status, url in responses if '/api/v1/st/ged/' in url and status >= 400]
            if errors or failed_ged:
                raise RuntimeError(f'Erreurs de recette : {len(errors)} erreurs navigateur, réponses GED {failed_ged}')
            context.close()
        browser.close()


if __name__ == '__main__':
    main()
