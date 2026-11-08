"""Recette métier réelle du poste 6, exclusivement sur copie SQLite isolée."""
import io,json,os,sqlite3,sys,threading
from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import make_server,WSGIServer,WSGIRequestHandler
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=Path(os.environ.get('POST6_REPORT_DIR', ROOT/'reports/poste6_administration'));OUT.mkdir(parents=True,exist_ok=True)
DB='/tmp/post6_admin_recette.sqlite3'
with sqlite3.connect(ROOT/'db.sqlite3') as source,sqlite3.connect(DB) as target:source.backup(target)
os.environ['DJANGO_SETTINGS_MODULE']='config.settings_test';os.environ['SQLITE_NAME']=DB
import django
from django.conf import settings
settings.DEBUG=True;settings.ALLOWED_HOSTS=['127.0.0.1','testserver'];settings.NOTIFICATION_SETTINGS={'EMAIL_ENABLED':False,'FCM_ENABLED':False}
django.setup()
from django.test import Client
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from apps.core.models import User,AuditLog
from apps.experts.models import Expert
from apps.governance.models import Organe,GroupeCible,PosteOrganisation,MandatOrganisation,CTCProcessus,WG
from apps.governance.st_admin_models import STReception,STReceptionPiece,STPVVersion
from apps.meetings.models import Reunion
from apps.norms.models import Norme
from apps.mobileapp.models import Notification
call_command('migrate',verbosity=0)
STReceptionPiece._meta.get_field('file').storage=FileSystemStorage(location='/tmp/post6_admin_recette_pieces')
receiver=User.objects.get(username='superuser',email__iexact='sourceacademique@gmail.com')
sc=Organe.objects.filter(type='SC',status__in=['VALIDATED','ACTIVE']).first()
group=GroupeCible.objects.create(sc=sc,code='GT-RECETTE-ADMIN',name='Groupe de recette isolée',activity='PRODUCTION',source_reference='Test isolé, sans modification du référentiel réel')
source_user=User.objects.create_user(username='sender.admin.recette',email='sender@example.invalid')
sender=Expert.objects.create(user=source_user,structure=receiver.expert_profile.structure,status='ACTIVE')
post=PosteOrganisation.objects.create(organe=sc,code='SECRETARIAT-RECETTE-ADMIN',title='Secrétaire de recette',category='SECRETARIAT',status='VALIDATED',source_reference='Test isolé')
MandatOrganisation.objects.create(expert=sender,poste=post,function=post.title,status='ACTIVE',start_date=timezone.localdate(),appointment_reference='Test isolé')
meeting=Reunion.objects.create(type='CTC',titre='Séance de recette administrative',date=timezone.now(),organisateur=receiver.expert_profile,lieu='Environnement isolé',ordre_jour='Rapports de revue des SC')
wg=WG.objects.select_related('ctm').first();cases=[]
for label,width,height in [('desktop',1440,1000),('tablet',820,1180),('mobile',390,844)]:
    norm=Norme.objects.create(reference_number=f'RECETTE-ADMIN-{label}',title=f'Projet de norme — contrôle {label}',description='Sans valeur officielle',circuit_version='LEGACY',ctm=wg.ctm,wg=wg)
    p=CTCProcessus.objects.create(norme=norm);cases.append((label,width,height,p.pk))
client=Client();client.force_login(receiver);session=client.cookies['sessionid'].value
from reportlab.pdfgen import canvas
stream=io.BytesIO();pdf=canvas.Canvas(stream);pdf.drawString(40,750,'Justificatif de recette, sans valeur officielle');pdf.save();payload=stream.getvalue()
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
class S(ThreadingMixIn,WSGIServer):daemon_threads=True
class Q(WSGIRequestHandler):
    def log_message(self,*args):pass
server=make_server('127.0.0.1',0,StaticFilesHandler(get_wsgi_application()),server_class=S,handler_class=Q)
threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}'
records=[]
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='chrome',headless=True)
    for label,width,height,pid in cases:
        ctx=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce');ctx.route('https://**/*',lambda route:route.abort());ctx.add_cookies([{'name':'sessionid','value':session,'url':base}])
        page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'/ctc/',wait_until='domcontentloaded',timeout=120000)
        root=page.locator('[data-post6-admin]');root.wait_for(state='visible');root.locator('[data-admin-tab=reception]').click()
        f=root.locator('[data-admin-reception-form]');f.locator(f'select[name=process_id] option[value="{pid}"]').wait_for(state='attached')
        f.locator('[name=process_id]').select_option(str(pid));f.locator('[name=sc_id]').select_option(str(sc.pk));f.locator('[name=group_id]').select_option(str(group.pk));f.locator('[name=sender_id]').select_option(str(sender.pk))
        f.locator('[name=vote_date]').fill(timezone.localdate().isoformat());f.locator('[name=vote_percentage]').fill('80');f.locator('[name=verified]').check()
        with page.expect_response(lambda r:'/api/v1/st/receptions/' in r.url and r.request.method=='POST') as saved:f.locator('[data-save-reception]').click()
        assert saved.value.status==201,saved.value.text();receipt=saved.value.json();rid=receipt['id'];ref=receipt['reference']
        f.locator('[name=id]').wait_for(state='attached');page.wait_for_function('(id)=>document.querySelector("[data-admin-reception-form] [name=id]").value===String(id)',arg=rid)
        for kind in ('PROJECT','VOTE'):
            f.locator('[name=piece_kind]').select_option(kind);f.locator('[name=piece_file]').set_input_files({'name':kind+'.pdf','mimeType':'application/pdf','buffer':payload})
            with page.expect_response(lambda r:r.url.endswith(f'/receptions/{rid}/pieces/')) as attached:f.locator('[data-upload-piece]').click()
            assert attached.value.status==200,attached.value.text()
        page.screenshot(path=str(OUT/f'formulaire_{label}.png'),animations='disabled')
        with page.expect_response(lambda r:r.url.endswith(f'/receptions/{rid}/register/')) as registered:f.locator('[data-register-reception]').click()
        assert registered.value.status==200,registered.value.text()
        card=root.locator('[data-admin-registry] article').filter(has_text=ref);card.get_by_role('link',name='Accusé',exact=True).wait_for(state='visible');card.scroll_into_view_if_needed();page.screenshot(path=str(OUT/f'resultat_{label}.png'),animations='disabled')
        response=ctx.request.get(base+f'/api/v1/st/receptions/{rid}/acknowledgement/');assert response.status==200 and response.body().startswith(b'%PDF')
        (OUT/f'accuse_{label}.pdf').write_bytes(response.body())
        root.locator('[data-admin-tab=activity]').click();page.screenshot(path=str(OUT/f'activite_{label}.png'),animations='disabled')
        record={'format':label,'reception_id':rid,'reference':ref,'registered_http':registered.value.status,'pdf_http':response.status,'errors':errors,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth+2')}
        if label=='desktop':
            root.locator('[data-admin-tab=pv]').click();pv=root.locator('[data-admin-pv-form]');pv.locator(f'[name=meeting_id] option[value="{meeting.pk}"]').wait_for(state='attached');pv.locator('[name=meeting_id]').select_option(str(meeting.pk));pv.locator('[name=content]').fill('Synthèse réelle de la séance de recette.');pv.locator('[name=decisions_text]').fill('Demander les rapports de revue — pôle 1 — échéance à fixer.')
            with page.expect_response(lambda r:r.url.endswith('/api/v1/st/pv/') and r.request.method=='POST') as draft:pv.locator('[data-save-pv]').click()
            assert draft.value.status==201;page.wait_for_function('()=>document.querySelector("[data-admin-pv-form] [name=revision]").value==="1"')
            with page.expect_response(lambda r:r.url.endswith('/api/v1/st/pv/') and r.request.method=='POST') as submitted:pv.locator('[data-submit-pv]').click()
            assert submitted.value.status==201;record['pv_state']=submitted.value.json()['state'];page.wait_for_timeout(400);page.screenshot(path=str(OUT/'pv_soumis_desktop.png'),animations='disabled')
        records.append(record);(OUT/'parcours_navigateur.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print(label,'PASS réception + accusé + registre',flush=True);ctx.close()
    browser.close()
server.shutdown()
for r in records:
    reception=STReception.objects.get(pk=r['reception_id']);r['audit_events']=AuditLog.objects.filter(content_type='governance.STReception',object_id=reception.pk).count();r['report_absent']=reception.process.sc_report_received_at is None
    r['notification_sender']=Notification.objects.filter(user=source_user,data__reception_id=reception.pk).exists()
(OUT/'parcours_navigateur.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print('PV versions',STPVVersion.objects.filter(pv__reunion=meeting).count())
