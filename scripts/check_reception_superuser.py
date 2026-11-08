"""Attribution vérifiée et recette du seul travail réception, avec le compte demandé.

--live : lecture/captures uniquement sur la base locale.
Sans option : copie isolée, dossiers synthétiques et clics de réception PC/mobile.
"""
import json
import os
from pathlib import Path
import sqlite3
import sys
import threading
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LIVE = '--live' in sys.argv
OUT = ROOT/'reports/reception_superuser'
DB = ROOT/'db.sqlite3' if LIVE else Path('/tmp/reception_superuser.sqlite3')
if not LIVE:
    with sqlite3.connect(ROOT/'db.sqlite3') as source, sqlite3.connect(DB) as dest:
        source.backup(dest)
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
from apps.core.models import User, AuditLog
from apps.experts.models import Expert
from apps.governance.models import CTCProcessus, WG, PlatformFreeze
from apps.governance.phoenix_runtime import active_st_mandate
from apps.norms.models import Norme
from web.ctc_views import get_ctc_context
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
user = User.objects.get(username='superuser', email__iexact='sourceacademique@gmail.com')
expert = Expert.objects.get(user=user)
assert active_st_mandate(expert).poste.code == 'ST-V3-06'
context = get_ctc_context(expert)
assert not context['can_fast_entry'] and not context['can_route_documents']
client = Client()
client.force_login(user, backend='django.contrib.auth.backends.ModelBackend')
session = client.cookies[settings.SESSION_COOKIE_NAME].value
cases = []
for label, width, height in [('desktop', 1440, 900), ('mobile', 390, 844)]:
    process = None
    if not LIVE:
        freeze = PlatformFreeze.get_solo()
        freeze.is_locked = False
        freeze.save()
        group = WG.objects.select_related('ctm').first()
        norm = Norme.objects.create(reference_number=f'RECETTE-RECEPTION-{label}',
            title=f'Dossier de contrôle de réception — {label}', description='Recette isolée, sans valeur officielle',
            ctm=group.ctm, wg=group, circuit_version='LEGACY')
        process = CTCProcessus.objects.create(norme=norm)
    cases.append((label,width,height,process.pk if process else None))
class Server(ThreadingMixIn, WSGIServer):
    daemon_threads = True
class Quiet(WSGIRequestHandler):
    def log_message(self, *args):
        pass
server=make_server('127.0.0.1',0,StaticFilesHandler(get_wsgi_application()),server_class=Server,handler_class=Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
base='http://127.0.0.1:8001' if '--served' in sys.argv else f'http://127.0.0.1:{server.server_port}'
proof={'server_url':base,'live_read_only':LIVE,'username':user.username,'user_id':user.pk,'role':context['ctc_sub_role'],
       'post':context['st_post_code'],'is_superuser':user.is_superuser,'cases':[]}
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='chrome',headless=True)
    for label,width,height,pid in cases:
        ctx=browser.new_context(viewport={'width':width,'height':height},reduced_motion='no-preference')
        ctx.route('https://**/*',lambda route:route.abort())
        ctx.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':session,'url':base}])
        page=ctx.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'/ctc/#assistant_executif',wait_until='domcontentloaded',timeout=120000)
        page.locator('[data-reception-workspace]').wait_for(state='visible')
        prefix='serveur_8001' if '--served' in sys.argv else ('style_live' if LIVE else 'style_recette')
        page.screenshot(path=str(OUT/f'{prefix}_{label}_avant.png'),animations='disabled')
        record={'format':label,'process_id':pid,'errors':errors}
        record['css_loaded']=page.evaluate("getComputedStyle(document.querySelector('.rx-hero')).borderRadius")
        root=page.locator('[data-reception-workspace]')
        root.locator('[data-rx-search]').fill('introuvable-zzzz')
        assert root.locator('[data-rx-no-result]').is_visible()
        root.locator('[data-rx-search]').fill('')
        root.locator('[data-rx-filter=done]').click()
        assert root.locator('[data-rx-filter=done]').get_attribute('aria-pressed')=='true'
        root.locator('[data-rx-filter=all]').click()
        record['interactive_filters']='PASS'
        root.locator('[data-rx-scroll]').click()
        page.wait_for_timeout(600)
        record['scroll_to_registry']=page.evaluate("document.querySelector('#ctc-main').scrollTop > 0")
        page.screenshot(path=str(OUT/f'{prefix}_{label}_file.png'),animations='disabled')
        record['reduced_motion_respected']=False
        page.emulate_media(reduced_motion='reduce')
        record['reduced_motion_respected']=page.evaluate("getComputedStyle(document.querySelector('.rx-hero')).animationName === 'none'")
        page.emulate_media(reduced_motion='no-preference')
        if pid:
            card=page.locator(f'[data-reception-id="{pid}"]')
            card.get_by_role('button',name='Enregistrer la réception').scroll_into_view_if_needed()
            with page.expect_response(lambda r:f'/ctc/dossiers/{pid}/reception/' in r.url and r.request.method=='POST') as response:
                card.get_by_role('button',name='Enregistrer la réception').click()
            record['receive_http']=response.value.status
            assert record['receive_http']==200,response.value.text()
            card.locator('[data-reception-receipt]').wait_for(state='visible',timeout=60000)
            card.scroll_into_view_if_needed()
            record['receipt_text']=card.locator('[data-reception-receipt]').inner_text()
            assert card.get_by_role('button',name='Enregistrer la réception').count()==0
            page.screenshot(path=str(OUT/f'{prefix}_{label}_apres.png'),animations='disabled')
            csrf=next(c['value'] for c in ctx.cookies() if c['name']=='csrftoken')
            record['duplicate_http']=page.request.post(base+f'/ctc/dossiers/{pid}/reception/',form={'action':'receive'},headers={'X-CSRFToken':csrf,'Referer':base+'/ctc/'}).status
            assert record['duplicate_http']==400
        record['overflow']=page.evaluate('document.documentElement.scrollWidth>innerWidth+2')
        proof['cases'].append(record)
        print(prefix,label,'OK',flush=True)
        ctx.close()
    browser.close()
server.shutdown()
if not LIVE:
    for record in proof['cases']:
        p=CTCProcessus.objects.get(pk=record['process_id'])
        record['received_by_id']=p.received_by_id
        record['received_at']=p.received_at.isoformat()
        record['unchanged_stage']=p.current_stage
        record['audit_count']=AuditLog.objects.filter(user=user,object_id=p.pk,content_type='governance.CTCProcessus').count()
        assert p.received_by_id==expert.pk and p.current_stage=='RECEPTION' and record['audit_count']>=1
        # Vérifier les refus métier même avec le drapeau superutilisateur.
        p.sc_report_received_at=timezone.now()
        p.sc_report_reference='Rapport synthétique pour test des permissions'
        p.save(update_fields=['sc_report_received_at','sc_report_reference'])
        for action in ('index','validate_intake'):
            denied=client.post(f'/ctc/dossiers/{p.pk}/reception/',{'action':action})
            record[action+'_http']=denied.status_code
            assert denied.status_code==403
(OUT/('style_visualisation_live.json' if LIVE else 'style_verification_reception.json')).write_text(json.dumps(proof,ensure_ascii=False,indent=2))
