"""Recette isolée et reproductible : actions API/DB et interfaces des 19 postes."""
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
OUT = ROOT / 'reports/audit_fonctionnel_19_postes'
OUT.mkdir(parents=True, exist_ok=True)
DB = '/tmp/ctc_functional_audit.sqlite3'
with sqlite3.connect('/tmp/recette_prompt.sqlite3') as source, sqlite3.connect(DB) as target:
    source.backup(target)
os.environ['SQLITE_NAME'] = DB
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_test'
import django
from django.conf import settings
settings.DEBUG = True
settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
settings.NOTIFICATION_SETTINGS = {'EMAIL_ENABLED': False, 'FCM_ENABLED': False}
settings.MEDIA_ROOT = '/tmp/ctc_functional_media'
django.setup()
from django.test import Client
from django.core.management import call_command
from django.utils import timezone
from apps.core.models import AuditLog
from apps.experts.models import Expert
from apps.norms.models import Norme
from apps.governance.models import CTCProcessus, JournalMigration, PlatformFreeze, WG
from apps.governance.phoenix_runtime import active_st_mandate
from apps.governance.st_spaces import menu_for_post
from apps.governance.st_operations_models import STRecord
from apps.governance.st_report_models import STReport
call_command('migrate', verbosity=0)
freeze = PlatformFreeze.get_solo()
freeze.is_locked = False
freeze.save()
roles = json.loads((ROOT/'reports/recette_prompt/roles.json').read_text())
actors, evidence = {}, {'database': DB, 'posts': {}, 'circuit': {}, 'ui': []}
for code, info in roles.items():
    expert = Expert.objects.select_related('user').get(user__email=info['email'])
    client = Client()
    client.force_login(expert.user, backend='django.contrib.auth.backends.ModelBackend')
    actors[info['number']] = (expert, client)
    item = {'name': expert.full_name, 'menu': menu_for_post(active_st_mandate(expert).poste)}
    before = JournalMigration.objects.count()
    r = client.post('/api/v1/st/records/', {'kind': 'WORK', 'reference': f'AUDIT19-{info["number"]}',
        'title': 'Travail de recette isolée', 'source_reference': 'Recette — sans valeur officielle'}, content_type='application/json')
    item['work_create_http'] = r.status_code
    item['work_db'] = STRecord.objects.filter(reference=f'AUDIT19-{info["number"]}', created_by=expert.user).exists()
    item['audit_delta'] = JournalMigration.objects.count()-before
    report = client.post('/api/v1/st/reports/', {'title': f'Rapport recette poste {info["number"]}',
        'sections': [{'title': 'Sources', 'content': 'Saisie manuelle — aucune extraction automatique vérifiée.'}]}, content_type='application/json')
    item['report_create_http'] = report.status_code
    item['report_db'] = STReport.objects.filter(owner=expert.user, versions__title=f'Rapport recette poste {info["number"]}').exists()
    if report.status_code == 201:
        rid = report.json()['id']
        export = client.get(f'/api/v1/st/reports/{rid}/export/?file_format=pdf')
        item['export_pdf_http'] = export.status_code
        item['export_pdf_magic'] = export.content.startswith(b'%PDF')
        (OUT/'preuves'/f'rapport_poste_{info["number"]}.pdf').write_bytes(export.content)
    evidence['posts'][code] = item
group = WG.objects.select_related('ctm').first()
norm = Norme.objects.create(wg=group, ctm=group.ctm, title='Norme de recette isolée', reference_number='AUDIT19-CIRCUIT', description='Sans valeur officielle', circuit_version='LEGACY')
process = CTCProcessus.objects.create(norme=norm)
for number, action, extra in [(6,'receive',{}),(11,'index',{}),(6,'record_sc_report',{'reference':'Rapport synthétique de recette'}),(11,'index',{}),(1,'validate_intake',{})]:
    r=actors[number][1].post(f'/ctc/dossiers/{process.pk}/reception/', {'action':action, **extra})
    evidence['circuit'][f'{number}-{action}-{len(evidence["circuit"])}']={'http':r.status_code,'body':r.json()}
r=actors[10][1].post(f'/ctc/dossiers/{process.pk}/consolidation/', {'comment':'Tentative avant examens'})
evidence['circuit']['consolidation_without_reviews']={'http':r.status_code,'body':r.json()}
r=actors[1][1].post(f'/ctc/dossiers/{process.pk}/validation/', {'action':'validate','comment':'Tentative de contournement'})
process.refresh_from_db()
evidence['circuit']['final_without_reviews']={'http':r.status_code,'validated_at':str(process.validated_at),'body':r.json()}
evidence['circuit']['audit_events']=list(AuditLog.objects.filter(content_type='CTCProcessus',object_id=process.pk).values('action','changes'))
(OUT/'preuves/resultats.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
class Server(ThreadingMixIn, WSGIServer):
    daemon_threads=True
class Quiet(WSGIRequestHandler):
    def log_message(self, *args):
        pass
server=make_server('127.0.0.1',0,StaticFilesHandler(get_wsgi_application()),server_class=Server,handler_class=Quiet)
threading.Thread(target=server.serve_forever, daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}'
profiles=[]
for n,(expert,client) in actors.items():
    profiles.append((n,client.cookies[settings.SESSION_COOKIE_NAME].value,evidence['posts'][f'ST-V3-{n:02}']['menu']))
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='chrome',headless=True)
    for number,session,menu in profiles:
        if '--diagnostic' in sys.argv and number != 1:
            continue
        for label,width,height in [('desktop',1440,900),('mobile',390,844)]:
            context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
            context.route('https://**/*',lambda route:route.abort())
            context.add_cookies([{'name':'sessionid','value':session,'url':base}])
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            folder=OUT/'captures'/f'{number:02}'
            folder.mkdir(parents=True,exist_ok=True)
            record={'post':number,'format':label,'modules':[]}
            try:
                page.goto(base+'/ctc/',wait_until='domcontentloaded',timeout=120000)
                page.screenshot(path=str(folder/f'chargement_{label}.png'),animations='disabled')
                record['url']=page.url
                page.wait_for_function('!!(window.CTC_CTX && window.switchView)',timeout=10000)
                page.screenshot(path=str(folder/f'accueil_{label}.png'),animations='disabled')
                for m in menu:
                    page.evaluate('(v)=>window.switchView(v)',m['view'])
                    missing=page.locator('.view-container:not(.hidden) [data-st-incomplete]').count()>0
                    record['modules'].append({'view':m['view'],'absent':missing})
                    page.screenshot(path=str(folder/f'{m["view"]}_{label}.png'),animations='disabled')
                if number == 12:
                    page.evaluate('window.switchView("ptn")')
                    form=page.locator('#ptn-create-form')
                    for name,value in {'reference':f'AUDIT-UI-{label}', 'title':'Paramètre saisi dans le navigateur', 'source_reference':'Recette isolée', 'content':'Valeur 20 MPa ; tome 0, saisie libre'}.items():
                        form.locator('[name='+name+']').fill(value)
                    with page.expect_response(lambda response: '/api/v1/st/records/' in response.url and response.request.method == 'POST') as result:
                        form.locator('button[type=submit]').click()
                    record['ptn_form_http']=result.value.status
                    page.wait_for_timeout(800)
                    page.screenshot(path=str(folder/f'ptn_resultat_{label}.png'),animations='disabled')
                record['errors']=errors
                record['overflow']=page.evaluate('document.documentElement.scrollWidth>innerWidth+2')
            except Exception as exc:
                record['error']=str(exc)
                record['errors']=errors
                record['url']=page.url
            evidence['ui'].append(record)
            (OUT/'preuves/resultats.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
            print(f'VISUALISE poste={number} {label} {record.get("error", "OK")}',flush=True)
            context.close()
    browser.close()
evidence['ptn_ui_db'] = list(STRecord.objects.filter(reference__startswith='AUDIT-UI-').values('reference','revision'))
(OUT/'preuves/resultats.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
server.shutdown()
print('Recette terminée : '+str(OUT),flush=True)
