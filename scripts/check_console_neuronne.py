"""Recette navigateur du bouton Neuronne dans la console d'administration."""
import json
import os
import sqlite3
import sys
import threading
from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'reports/console_neuronne';OUT.mkdir(parents=True,exist_ok=True)
DB='/tmp/console_neuronne.sqlite3'
with sqlite3.connect(ROOT/'db.sqlite3') as source,sqlite3.connect(DB) as target:source.backup(target)
os.environ['DJANGO_SETTINGS_MODULE']='config.settings_test';os.environ['SQLITE_NAME']=DB
import django
from django.conf import settings
settings.DEBUG=True;settings.ALLOWED_HOSTS=['127.0.0.1','testserver']
django.setup()
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.test import Client
from apps.core.models import User

call_command('migrate',verbosity=0)
admin=User.objects.filter(username='neuronne.console.recette').first()
if admin is None:
    admin=User.objects.create_superuser(username='neuronne.console.recette',email='neuronne.console@example.invalid',password='Recette2026!',first_name='Neuronne',last_name='Console')
admin.is_staff=True;admin.is_superuser=True;admin.is_active=True;admin.save(update_fields=['is_staff','is_superuser','is_active'])
client=Client();client.force_login(admin);session=client.cookies['sessionid'].value
home=client.get('/dashboard/administration/')
assert home.status_code==200,'Console inaccessible pour le compte de recette.'
created=client.post('/api/v1/ia-agent/sessions/',{'scope':'admin'},content_type='application/json')
assert created.status_code==201,f'Session admin refusée : {created.status_code}'
session_id=created.json()['id']


class Server(ThreadingMixIn,WSGIServer):
    daemon_threads=True


class Quiet(WSGIRequestHandler):
    def log_message(self,*args):
        pass


server=make_server('127.0.0.1',0,StaticFilesHandler(get_wsgi_application()),server_class=Server,handler_class=Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}'

from playwright.sync_api import sync_playwright

results={'api_session':{'status':created.status_code,'scope':created.json()['scope'],'id':session_id}}
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='chrome',headless=True)
    for width,height,name in [(1440,900,'desktop'),(1024,900,'tablette'),(390,844,'mobile')]:
        context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
        context.route('https://**/*',lambda route:route.abort())
        context.add_cookies([{'name':'sessionid','value':session,'url':base}])
        page=context.new_page();errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(base+'/dashboard/administration/',wait_until='domcontentloaded',timeout=120000)
        page.wait_for_selector('#ia-agent-toggle-btn')
        button=page.locator('button[title="Assistant Neuronne — administration"]')
        button.wait_for(state='visible')
        assert button.is_visible()
        page.screenshot(path=str(OUT/f'console_{name}.png'),full_page=False,animations='disabled')
        button.click()
        page.wait_for_selector('#ia-agent-panel:not(.hidden)')
        assert page.locator('#ia-agent-panel').get_attribute('data-scope')=='admin'
        page.wait_for_function("()=>{const k=Object.keys(localStorage).find(x=>x.startsWith('ia_agent_session_admin'));return !!k}",timeout=30000)
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT/f'neuronne_{name}.png'),full_page=False,animations='disabled')
        panel=page.locator('#ia-agent-panel').bounding_box()
        results[name]={
            'button_visible':button.is_visible(),
            'panel_scope':'admin',
            'panel_within_viewport':bool(panel and panel['x']>=0 and panel['y']>=0 and panel['x']+panel['width']<=width+1 and panel['y']+panel['height']<=height+1),
            'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth+2'),
            'session_created':page.evaluate("()=>Object.keys(localStorage).some(x=>x.startsWith('ia_agent_session_admin'))"),
            'errors':list(errors),
        }
        context.close()
    browser.close()

server.shutdown()
(OUT/'recette.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False,indent=2),flush=True)
