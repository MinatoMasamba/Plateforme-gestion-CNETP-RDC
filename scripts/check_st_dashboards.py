"""Rendu des 19 postes sur copie préparée ; aucune recette métier déduite des captures."""
import json
import os
from pathlib import Path
import sys
import threading
from socketserver import ThreadingMixIn
from wsgiref.simple_server import make_server,WSGIServer,WSGIRequestHandler

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['DJANGO_SETTINGS_MODULE']='config.settings_test';os.environ['SQLITE_NAME']='/tmp/st_ui_post11.sqlite3'
import django
from django.conf import settings
settings.DEBUG=True;settings.ALLOWED_HOSTS=['127.0.0.1','testserver'];django.setup()
from django.test import Client
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from apps.core.models import User
from apps.governance.phoenix_runtime import active_st_mandate
from apps.governance.st_spaces import allowed_views_for_post
OUT=ROOT/'reports/poste11_ged/19_postes';OUT.mkdir(exist_ok=True)
manifest=json.loads((ROOT/'reports/poste11_ged/19_postes_roles.json').read_text());profiles=[]
for code,info in manifest.items():
    user=User.objects.get(email=info['email']);client=Client();client.force_login(user)
    profiles.append((code,info,client.cookies['sessionid'].value,allowed_views_for_post(active_st_mandate(user.expert_profile).poste)))
class Server(ThreadingMixIn,WSGIServer):daemon_threads=True
class Quiet(WSGIRequestHandler):
    def log_message(self,*args):pass
server=make_server('127.0.0.1',0,StaticFilesHandler(get_wsgi_application()),server_class=Server,handler_class=Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}'
from playwright.sync_api import sync_playwright
results=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='chrome',headless=True)
    for code,info,session,allowed in profiles:
        folder=OUT/code;folder.mkdir(exist_ok=True)
        context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');context.route('https://**/*',lambda r:r.abort());context.add_init_script("localStorage.setItem('theme-preference','light')");context.add_cookies([{'name':'sessionid','value':session,'url':base}])
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        response=page.goto(base+'/ctc/',wait_until='domcontentloaded',timeout=120000)
        page.locator('.view-container:not(.hidden)').first.wait_for(state='visible')
        if code=='ST-V3-11':page.wait_for_function('()=>document.querySelector("[data-ged-workspace]").getAttribute("aria-busy")==="false"')
        forbidden=next((v for v in ['admin_system','financial','indexation','ptn','exams'] if v not in allowed),None)
        refusal=context.request.get(base+f'/ctc/espace/{forbidden}/').status if forbidden else None
        for label,width,height in [('desktop',1440,1000),('tablet',820,1180),('mobile',390,844)]:
            page.set_viewport_size({'width':width,'height':height})
            page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
            page.screenshot(path=str(folder/f'tableau_bord_{label}.png'),animations='disabled')
            actual=page.evaluate('window.CTC_CTX.st_post_code');assert actual==code,(actual,code)
            metrics=page.evaluate('''()=>{const v=document.querySelector('.view-container:not(.hidden)');return {overflow:document.documentElement.scrollWidth>innerWidth+2,view:v.id,headings:[...v.querySelectorAll('h2,h3')].slice(0,7).map(e=>e.innerText),menu:[...document.querySelectorAll('#sidebar-nav-principal button')].map(e=>e.innerText)}}''')
            record={'post':code,'pole':info['pole'],'title':info['title'],'viewport':label,'http':response.status,**metrics,'javascript_errors':errors,'forbidden_view':forbidden,'forbidden_http':refusal,'classification':'UI_ONLY','business_pass':False}
            results.append(record);(OUT/'resultats.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
        context.close()
        print(code,'capturé desktop/tablette/mobile',flush=True)
    browser.close()
server.shutdown()
summary={'screens':len(results),'profiles':len(profiles),'http_errors':sum(r['http']!=200 for r in results),'overflow':sum(r['overflow'] for r in results),'javascript_errors':sum(bool(r['javascript_errors']) for r in results),'permissions_failed':sum(r['forbidden_http']!=403 for r in results if r['forbidden_view']),'classification':'Rendu et refus de navigation uniquement ; aucun PASS métier global.'}
(OUT/'synthese.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(summary,flush=True)
