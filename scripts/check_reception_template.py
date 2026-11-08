"""Recette du registre de réception ST et du menu ST-V3-06, sur copie SQLite isolée."""
import json
import os
import sqlite3
import sys
import threading
from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'reports/reception_template'
OUT.mkdir(parents=True, exist_ok=True)
DB = Path('/tmp/reception_template.sqlite3')
with sqlite3.connect(ROOT / 'db.sqlite3') as source, sqlite3.connect(DB) as target:
    source.backup(target)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_test'
os.environ['SQLITE_NAME'] = str(DB)
import django
from django.conf import settings
settings.DEBUG = True
settings.ALLOWED_HOSTS = ['testserver', '127.0.0.1']
settings.NOTIFICATION_SETTINGS = {'EMAIL_ENABLED': False, 'FCM_ENABLED': False}
django.setup()

from django.test import Client
from django.utils import timezone
from apps.core.models import User
from apps.experts.models import Expert
from apps.governance.models import (
    CTCProcessus, GroupeCible, MandatOrganisation, Organe, PlatformFreeze, PosteOrganisation, WG,
)
from apps.governance.phoenix_runtime import active_st_mandate
from apps.governance.st_admin_models import STReception
from apps.governance.st_spaces import menu_for_post
from apps.norms.models import Norme
from web.ctc_views import get_ctc_context

user = User.objects.get(username='superuser', email__iexact='sourceacademique@gmail.com')
expert = Expert.objects.get(user=user)
post = PosteOrganisation.objects.get(code='ST-V3-06')
MandatOrganisation.objects.filter(expert=expert, poste=post, status='ACTIVE').delete()
MandatOrganisation.objects.create(
    expert=expert, poste=post, capacity='ORGANISATION', status='ACTIVE',
    start_date=timezone.localdate(), function=post.title,
    appointment_reference='RECETTE-TEMPLATE-RECEPTION',
)
freeze = PlatformFreeze.get_solo()
freeze.is_locked = False
freeze.save()
assert active_st_mandate(expert).poste.code == 'ST-V3-06'
context = get_ctc_context(expert)
assert context['st_post_code'] == 'ST-V3-06'

menu_labels = [item['label'] for item in menu_for_post(post)]
required_menu = ['Réception norme', 'Mes travaux', 'Demande et traitement', 'Circuit des normes', 'Rapport']
assert all(label in menu_labels for label in required_menu), menu_labels

group_it = GroupeCible.objects.filter(sc__code='SC-IT', sc__type='SC').select_related('sc').first()
sc_it = group_it.sc
group_gf = GroupeCible.objects.filter(sc__code='SC-GF', sc__type='SC').select_related('sc').first()
sc_gf = group_gf.sc
wg = WG.objects.select_related('ctm').first()
sender = Expert.objects.filter(status='ACTIVE').exclude(pk=expert.pk).first() or expert

def make_process(label, state):
    norm = Norme.objects.create(
        reference_number=f'RECETTE-RX-{label}', title=f'Dossier de réception — {label}',
        description='Recette isolée du registre de réception, sans valeur officielle.',
        circuit_version='LEGACY', ctm=wg.ctm, wg=wg,
    )
    process = CTCProcessus.objects.create(norme=norm, current_stage='RECEPTION')
    sc, group = (sc_it, group_it) if label in ('pending', 'draft') else (sc_gf, group_gf)
    if state:
        reception = STReception.objects.create(
            process=process, sc=sc, group=group, sender=sender, created_by=user,
            state=state, revision=0,
        )
        if state == 'ENREGISTREE':
            process.received_at = timezone.now()
            process.received_by = expert
            process.save(update_fields=['received_at', 'received_by', 'updated_at'])
            reception.received_at = process.received_at
            reception.received_by = user
            reception.verified = True
            reception.save(update_fields=['received_at', 'received_by', 'verified'])
    return process

cases = [
    ('desktop', 1440, 1000, make_process('pending', None)),
    ('tablet', 1024, 1100, make_process('draft', 'BROUILLON')),
    ('mobile', 390, 844, make_process('done', 'ENREGISTREE')),
]

pending_pk = cases[0][3].pk

class Server(ThreadingMixIn, WSGIServer):
    daemon_threads = True

class Quiet(WSGIRequestHandler):
    def log_message(self, *args):
        pass

client = Client()
client.force_login(user)
session = client.cookies[settings.SESSION_COOKIE_NAME].value
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
server = make_server('127.0.0.1', 0, StaticFilesHandler(get_wsgi_application()), server_class=Server, handler_class=Quiet)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}'

from playwright.sync_api import sync_playwright
proof = {'menu': menu_labels, 'required_menu': required_menu, 'cases': []}
with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='chrome', headless=True)
    for label, width, height, pending_process in cases:
        ctx = browser.new_context(viewport={'width': width, 'height': height}, reduced_motion='reduce')
        ctx.route('https://**/*', lambda route: route.abort())
        ctx.add_cookies([{'name': settings.SESSION_COOKIE_NAME, 'value': session, 'url': base}])
        page = ctx.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base + '/ctc/#assistant_executif', wait_until='domcontentloaded', timeout=120000)
        root = page.locator('[data-reception-workspace]')
        root.wait_for(state='visible')
        record = {'format': label, 'errors': errors}

        sidebar = page.locator('#sidebar-nav-principal')
        sidebar_labels = sidebar.locator('.sidebar-nav-btn').all_inner_texts()
        record['sidebar_labels'] = [text.strip() for text in sidebar_labels]
        assert required_menu[0] in record['sidebar_labels'], record['sidebar_labels']
        assert 'Mes travaux' in record['sidebar_labels'], record['sidebar_labels']
        assert 'Rapport' in record['sidebar_labels'], record['sidebar_labels']
        if label == 'desktop':
            for menu_label, view_id in (
                ('Mes travaux', 'assignations'), ('Demande et traitement', 'ctc_requests'),
                ('Circuit des normes', 'dossiers'), ('Rapport', 'rapports'),
            ):
                sidebar.get_by_role('button', name=menu_label, exact=True).click()
                page.locator(f'#view-{view_id}').wait_for(state='visible')
            sidebar.get_by_role('button', name='Réception norme', exact=True).click()
            root.wait_for(state='visible')
            record['sidebar_navigation'] = 'PASS'

        assert root.locator('.rx-step--current').inner_text().find('Réception ST') >= 0
        assert root.locator('.rx-step').count() == 7
        rows = root.locator('tr[data-reception-id]')
        assert rows.count() >= 3, rows.count()
        record['rows'] = rows.count()
        record['summary'] = root.locator('[data-rx-count]').inner_text()
        page.screenshot(path=str(OUT / f'registre_{label}_top.png'), animations='disabled')

        search = root.locator('[data-rx-search]')
        search.fill('introuvable-zzzz')
        assert root.locator('[data-rx-no-result]').is_visible()
        search.fill('')
        root.locator('[data-rx-reset]').click()
        assert root.locator('[data-rx-no-result]').is_hidden()

        status = root.locator('[data-rx-status]')
        status.select_option('done')
        assert root.locator('tr[data-reception-id]:visible').count() == 1
        status.select_option('draft')
        assert root.locator('tr[data-reception-id]:visible').count() == 1
        root.locator('[data-rx-reset]').click()
        assert root.locator('tr[data-reception-id]:visible').count() == record['rows']

        tome = root.locator('select[data-rx-tome]')
        tome.select_option('Tome 1')
        assert root.locator('tr[data-reception-id]:visible').count() == 1
        tome.select_option('Tome 2')
        assert root.locator('tr[data-reception-id]:visible').count() == 1
        root.locator('[data-rx-reset]').click()
        root.locator('[data-rx-registry]').screenshot(path=str(OUT / f'registre_{label}_table.png'), animations='disabled')

        root.locator(f'tr[data-reception-id="{pending_pk}"]').get_by_role('button', name='Préparer la réception').click()
        admin = page.locator('[data-post6-admin]')
        admin.wait_for(state='visible')
        assert page.evaluate("document.querySelector('[data-admin-panel=reception]').hidden === false")
        assert page.evaluate("document.querySelector('[data-admin-reception-form] [name=process_id]').value") == str(pending_pk)
        record['start_process'] = 'PASS'

        record['overflow'] = page.evaluate('document.documentElement.scrollWidth > innerWidth + 2')
        assert record['overflow'] is False
        page.screenshot(path=str(OUT / f'registre_{label}.png'), animations='disabled', full_page=True)
        page.screenshot(path=str(OUT / f'preparation_{label}.png'), animations='disabled')
        proof['cases'].append(record)
        print(label, 'PASS', record['summary'], flush=True)
        ctx.close()
    browser.close()
server.shutdown()
(OUT / 'recette.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2))
