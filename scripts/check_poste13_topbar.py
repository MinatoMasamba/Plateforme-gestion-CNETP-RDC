"""Vérification visuelle de la barre supérieure avec un libellé de pôle long (poste 13)."""
import json
import os
import sqlite3
import sys
import threading
from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'reports/poste13_topbar'
OUT.mkdir(parents=True, exist_ok=True)
DB = '/tmp/topbar_layout.sqlite3'
with sqlite3.connect(ROOT / 'db.sqlite3') as source, sqlite3.connect(DB) as target:
    source.backup(target)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_test'
os.environ['SQLITE_NAME'] = DB
import django
from django.conf import settings
settings.DEBUG = True
settings.ALLOWED_HOSTS = ['127.0.0.1', 'testserver']
settings.NOTIFICATION_SETTINGS = {'EMAIL_ENABLED': False, 'FCM_ENABLED': False}
django.setup()
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.test import Client
from django.utils import timezone
from apps.core.models import User
from apps.experts.models import Expert
from apps.governance.models import MandatOrganisation, PosteOrganisation
from apps.governance.st_operations_models import STAccessPolicy
from apps.governance.st_matrix import prepare_matrix

call_command('migrate', verbosity=0)
post = PosteOrganisation.objects.filter(code='ST-V3-13').first()
if post is None:
    version = prepare_matrix()
    if version.status != 'VALIDATED':
        version.status = 'VALIDATED'
        version.save(update_fields=['status'])
    STAccessPolicy.objects.update_or_create(pk=1, defaults={'version': version, 'enabled': True})
    post = PosteOrganisation.objects.get(code='ST-V3-13')
else:
    version = post.organe.version if post.organe_id else None
    if version and version.status != 'VALIDATED':
        version.status = 'VALIDATED'
        version.save(update_fields=['status'])
    if version:
        STAccessPolicy.objects.update_or_create(pk=1, defaults={'version': version, 'enabled': True})

mandate = MandatOrganisation.objects.filter(poste=post, status='ACTIVE', capacity='ORGANISATION').select_related('expert__user').first()
if mandate is None:
    user = User.objects.filter(username='topbar.recette.13').first()
    if user is None:
        user = User.objects.create_user(username='topbar.recette.13', email='topbar13@example.invalid', first_name='Thyty', last_name='Mawete Recette')
    expert = Expert.objects.filter(user=user).first()
    if expert is None:
        structure = Expert.objects.exclude(structure=None).values_list('structure_id', flat=True).first()
        expert = Expert.objects.create(user=user, structure_id=structure, status='ACTIVE')
    mandate = MandatOrganisation.objects.create(expert=expert, poste=post, function=post.title, status='ACTIVE', start_date=timezone.localdate(), appointment_reference='Recette topbar isolée, sans valeur officielle')
user = mandate.expert.user

client = Client()
client.force_login(user)
session = client.cookies['sessionid'].value


class Server(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class Quiet(WSGIRequestHandler):
    def log_message(self, *args):
        pass


server = make_server('127.0.0.1', 0, StaticFilesHandler(get_wsgi_application()), server_class=Server, handler_class=Quiet)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}'

from playwright.sync_api import sync_playwright

results = []
with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='chrome', headless=True)
    for width, height in [(1600, 900), (1440, 900), (1280, 900), (1024, 900), (768, 900), (390, 844)]:
        context = browser.new_context(viewport={'width': width, 'height': height}, reduced_motion='reduce')
        context.route('https://**/*', lambda route: route.abort())
        context.add_cookies([{'name': 'sessionid', 'value': session, 'url': base}])
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base + '/ctc/', wait_until='domcontentloaded', timeout=120000)
        page.wait_for_selector('header h1')
        page.screenshot(path=str(OUT / f'topbar_{width}.png'), clip={'x': 0, 'y': 0, 'width': width, 'height': 120}, animations='disabled')
        if width in (1440, 390):
            page.wait_for_timeout(1500)
            suffix = 'desktop' if width == 1440 else 'mobile'
            page.screenshot(path=str(ROOT / f'reports/audit_fonctionnel_19_postes/captures/13/espace_p3_{suffix}_corrige.png'), full_page=True, animations='disabled')
        metrics = page.evaluate("""() => {
          const h1 = document.querySelector('header h1');
          const spans = [...document.querySelectorAll('header button span')];
          return {
            h1_height: h1.getBoundingClientRect().height,
            nav_heights: spans.map(s => s.getBoundingClientRect().height),
            overflow: document.documentElement.scrollWidth > innerWidth + 2,
            scroll_width: document.documentElement.scrollWidth,
            inner_width: innerWidth,
          };
        }""")
        metrics.update({'width': width, 'javascript_errors': errors})
        results.append(metrics)
        context.close()
    browser.close()

(OUT / 'layout.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
server.shutdown()
for row in results:
    print(row['width'], 'h1=', round(row['h1_height'], 1), 'nav=', [round(h, 1) for h in row['nav_heights']], 'overflow=', row['overflow'], 'errors=', row['javascript_errors'])
