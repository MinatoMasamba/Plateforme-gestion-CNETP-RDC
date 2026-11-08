"""Recette navigateur du poste 11 ; opérations métier sur copie SQLite exclusivement."""
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import threading
from socketserver import ThreadingMixIn
from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'reports/poste11_ged/recette';OUT.mkdir(parents=True,exist_ok=True)
DB='/tmp/post11_ged_recette.sqlite3'
with sqlite3.connect(ROOT/'db.sqlite3') as source,sqlite3.connect(DB) as target:source.backup(target)
os.environ['DJANGO_SETTINGS_MODULE']='config.settings_test';os.environ['SQLITE_NAME']=DB
import django
from django.conf import settings
settings.DEBUG=True;settings.ALLOWED_HOSTS=['127.0.0.1','testserver'];settings.NOTIFICATION_SETTINGS={'EMAIL_ENABLED':False,'FCM_ENABLED':False}
django.setup()
from django.core.management import call_command
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.test import Client
from django.utils import timezone
from apps.core.models import User, AuditLog
from apps.experts.models import Expert
from apps.governance.models import Organe, GroupeCible, PosteOrganisation, MandatOrganisation, CTCProcessus, WG
from apps.governance.st_admin_models import STReceptionPiece
from apps.governance.st_ged_models import STGEDFile, STGEDIndexation
from apps.governance import st_admin, st_ged
from apps.norms.models import Norme
from apps.mobileapp.models import Notification
call_command('migrate',verbosity=0)
STReceptionPiece._meta.get_field('file').storage=FileSystemStorage(location='/tmp/post11_ged_pieces/reception')
STGEDFile._meta.get_field('file').storage=FileSystemStorage(location='/tmp/post11_ged_pieces/ged')
writer=User.objects.get(username='superuser',email__iexact='sourceacademique@gmail.com')
assert MandatOrganisation.objects.filter(expert__user=writer,poste__code='ST-V3-11',status='ACTIVE').exists()


def role(number):
    post=PosteOrganisation.objects.get(code=f'ST-V3-{number:02}')
    existing=MandatOrganisation.objects.filter(poste=post,status='ACTIVE',capacity='ORGANISATION').first()
    if existing:return existing.expert.user
    user=User.objects.create_user(username=f'ged.recette.{number}',email=f'ged{number}@example.invalid',first_name='Agent',last_name=f'Recette {number}')
    expert=Expert.objects.create(user=user,structure=writer.expert_profile.structure,status='ACTIVE')
    MandatOrganisation.objects.create(expert=expert,poste=post,function=post.title,status='ACTIVE',start_date=timezone.localdate(),appointment_reference='Recette isolée sans valeur officielle')
    return user


head,secretary,coordinator=[role(n) for n in (10,6,1)]
sc=Organe.objects.get(type='SC',code='SC-IT',status='VALIDATED');group=GroupeCible.objects.get(sc=sc,code='SC-IT-GT1')
sender_user=User.objects.create_user(username='ged.recette.sender',email='ged-sender@example.invalid',first_name='Expéditeur',last_name='Recette')
sender=Expert.objects.create(user=sender_user,structure=writer.expert_profile.structure,status='ACTIVE')
post=PosteOrganisation.objects.create(organe=sc,code='GED-RECETTE-SECRETARY',title='Secrétaire de recette',category='SECRETARIAT',status='VALIDATED',source_reference='Recette isolée')
MandatOrganisation.objects.create(expert=sender,poste=post,function=post.title,status='ACTIVE',start_date=timezone.localdate(),appointment_reference='Recette isolée')
wg=WG.objects.filter(ctm__number__in=[2,4,5]).select_related('ctm').first() or WG.objects.select_related('ctm').first()


def pdf(text):
    from reportlab.pdfgen import canvas
    stream=io.BytesIO();page=canvas.Canvas(stream);page.drawString(35,750,text);page.save()
    return stream.getvalue()


def receipt(label,report=True):
    norm=Norme.objects.create(reference_number='GED-RECETTE-'+label.upper(),title='Dossier documentaire de recette — '+label,description='Environnement isolé, sans valeur officielle',ctm=wg.ctm,wg=wg,circuit_version='LEGACY')
    process=CTCProcessus.objects.create(norme=norm)
    r=st_admin.save_reception(secretary,{'process_id':process.pk,'sc_id':sc.pk,'group_id':group.pk,'sender_id':sender.pk,'vote_date':timezone.localdate().isoformat(),'vote_percentage':80,'verified':True})
    for kind in ['PROJECT','VOTE']+(['REPORT'] if report else []):st_admin.add_piece(secretary,r.pk,kind,ContentFile(pdf('Pièce de recette '+kind),name=kind+'.pdf'))
    r.refresh_from_db();st_admin.register_reception(secretary,r.pk,r.revision)
    return process


cases=[(name,w,h,receipt(name)) for name,w,h in [('desktop',1440,1000),('tablet',820,1180),('mobile',390,844)]]
blocked=receipt('rapport-attendu',False)
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
class Server(ThreadingMixIn,WSGIServer):daemon_threads=True
class Quiet(WSGIRequestHandler):
    def log_message(self,*args):pass
server=make_server('127.0.0.1',0,StaticFilesHandler(get_wsgi_application()),server_class=Server,handler_class=Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}'


def session(user):
    client=Client();client.force_login(user);return client.cookies['sessionid'].value


from playwright.sync_api import sync_playwright
results=[]
writer_session,head_session=session(writer),session(head)
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='chrome',headless=True)
    code_ctx=browser.new_context(viewport={'width':1440,'height':1000});code_ctx.route('https://**/*',lambda r:r.abort());code_ctx.add_cookies([{'name':'sessionid','value':head_session,'url':base}]);code_page=code_ctx.new_page();code_page.goto(base+'/ctc/#ged',wait_until='domcontentloaded',timeout=120000)
    code_page.wait_for_function('()=>document.querySelector("[data-ged-workspace]").getAttribute("aria-busy")==="false"')
    code_root=code_page.locator('[data-ged-workspace]');code_root.locator('[data-ged-mode=codification]').click();code_form=code_root.locator('[data-ged-code-form]')
    for label,_,_,process in cases:
        code_form.locator('[name=process_id]').select_option(str(process.pk));code_form.locator('[name=sc_id]').select_option(str(sc.pk));code_form.locator('[name=code]').fill('DOC-RECETTE-'+label.upper());code_form.locator('[name=source_reference]').fill('Autorisation de recette isolée, sans code officiel')
        with code_page.expect_response(lambda r:r.url.endswith('/st/ged/codes/')) as authorization:code_root.locator('[data-ged-authorize-code]').click()
        assert authorization.value.status==201,authorization.value.text()
        code_page.wait_for_function('()=>!document.querySelector("[data-ged-authorize-code]").hasAttribute("aria-busy")')
        code_root.locator('[data-ged-message]').filter(has_text='Code documentaire autorisé').wait_for(state='visible')
    code_page.screenshot(path=str(OUT/'autorisation_codes_chef_p2.png'),animations='disabled');code_ctx.close()
    for label,width,height,process in cases:
        ctx=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce');ctx.route('https://**/*',lambda r:r.abort());ctx.add_cookies([{'name':'sessionid','value':writer_session,'url':base}])
        page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'/ctc/',wait_until='domcontentloaded',timeout=120000)
        root=page.locator('[data-ged-workspace]');root.wait_for(state='visible');page.wait_for_function('()=>document.querySelector("[data-ged-workspace]").getAttribute("aria-busy")==="false"')
        page.screenshot(path=str(OUT/f'tableau_bord_{label}.png'),animations='disabled')
        if label=='mobile':
            trigger=page.get_by_role('button',name='Ouvrir le menu',exact=True)
            if trigger.count():
                trigger.click();page.screenshot(path=str(OUT/'menu_mobile.png'),animations='disabled');page.evaluate('toggleDock(false)')
        root.locator(f'[data-ged-process="{process.pk}"]').click()
        form=root.locator('[data-ged-index-form]');form.locator('[name=observation]').fill('Contrôle documentaire effectué en recette isolée.')
        form.locator('[name=upload]').set_input_files({'name':'projet-documentaire.pdf','mimeType':'application/pdf','buffer':pdf('Première version documentaire '+label)})
        with page.expect_response(lambda r:r.url.endswith(f'/st/ged/{process.pk}/files/') and r.request.method=='POST') as uploaded:root.locator('[data-ged-upload]').click()
        assert uploaded.value.status==201,uploaded.value.text()
        root.locator('[data-ged-message]').filter(has_text='Fichier contrôlé').wait_for(state='visible')
        form.locator('[name=verified]').check();root.locator('[data-ged-index]').scroll_into_view_if_needed();page.screenshot(path=str(OUT/f'fiche_indexation_{label}.png'),animations='disabled')
        with page.expect_response(lambda r:r.url.endswith(f'/st/ged/{process.pk}/index/')) as indexed:root.locator('[data-ged-index]').click()
        assert indexed.value.status==201,indexed.value.text();first=indexed.value.json()
        root.locator('[data-ged-message]').filter(has_text='Indexation enregistrée').wait_for(state='visible')
        page.screenshot(path=str(OUT/f'indexation_enregistree_{label}.png'),animations='disabled')
        root.locator('[data-ged-mode=ged]').click();root.locator('[data-ged-panel=library]').wait_for(state='visible');page.screenshot(path=str(OUT/f'bibliotheque_{label}.png'),animations='disabled')
        root.locator('[data-ged-mode=codification]').click();root.locator('[data-ged-panel=codes]').wait_for(state='visible');assert root.locator('[data-ged-code-form]').count()==0;page.screenshot(path=str(OUT/f'codification_{label}.png'),animations='disabled')
        download=ctx.request.get(base+first['source']['url']);assert download.status==200 and download.body().startswith(b'%PDF')
        reader=ctx.new_page();dossier_response=reader.goto(base+f'/ctc/norme/{process.norme_id}/lecture/',wait_until='domcontentloaded',timeout=120000);assert dossier_response.status==200
        reader.get_by_role('link',name='Télécharger projet-documentaire.pdf',exact=True).wait_for(state='visible');reader.screenshot(path=str(OUT/f'dossier_ouvert_{label}.png'),animations='disabled')
        indexed_document=ctx.request.get(base+f'/api/v1/st/ged-documents/{first["id"]}/');assert indexed_document.status==200
        reader.close()
        row={'format':label,'process_id':process.pk,'index_http':indexed.value.status,'file_http':download.status,'first_version':first['number']}
        row['dossier_http']=dossier_response.status;row['indexed_document_http']=indexed_document.status
        if label=='desktop':
            root.locator('[data-ged-mode=indexation]').click();page.evaluate('(id)=>window.stGEDSelect(id)',process.pk)
            form.locator('[name=upload]').set_input_files({'name':'projet-revise.pdf','mimeType':'application/pdf','buffer':pdf('Deuxième version révisée documentaire')})
            with page.expect_response(lambda r:r.url.endswith(f'/st/ged/{process.pk}/files/')) as second_file:root.locator('[data-ged-upload]').click()
            assert second_file.value.status==201
            root.locator('[data-ged-message]').filter(has_text='Fichier contrôlé').wait_for(state='visible')
            form.locator('[name=verified]').check()
            with page.expect_response(lambda r:r.url.endswith(f'/st/ged/{process.pk}/index/')) as second_index:root.locator('[data-ged-index]').click()
            assert second_index.value.status==201
            root.locator('[data-ged-message]').filter(has_text='Indexation enregistrée').wait_for(state='visible')
            root.locator('[data-ged-mode=versions]').click()
            with page.expect_response(lambda r:'/compare/' in r.url) as comparison:root.locator('[data-ged-compare]').click()
            assert comparison.value.status==200 and comparison.value.json()['file_changed']
            root.locator('[data-ged-diff]').filter(has_text='Fichiers différents').wait_for(state='visible');page.screenshot(path=str(OUT/'comparaison_versions_desktop.png'),animations='disabled')
            def dialog(d):d.accept('Restauration de recette vérifiée') if d.type=='prompt' else d.accept()
            page.on('dialog',dialog)
            with page.expect_response(lambda r:r.url.endswith(f'/st/ged/{process.pk}/index/')) as restoration:root.locator('[data-ged-versions] article').filter(has_text='v1 ·').get_by_role('button',name='Restaurer en nouvelle version').click()
            assert restoration.value.status==201 and restoration.value.json()['number']==3
            page.remove_listener('dialog',dialog);row['restored_version']=3
            root.locator('[data-ged-mode=ged_anomalies]').click();anomaly=root.locator('[data-ged-anomaly-form]');anomaly.locator('[name=process_id]').select_option(str(process.pk));anomaly.locator('[name=comment]').fill('Annexe de recette à vérifier')
            with page.expect_response(lambda r:r.url.endswith(f'/st/ged/{process.pk}/anomalies/')) as issue:root.locator('[data-ged-anomaly-submit]').click()
            assert issue.value.status==201
            root.locator('[data-ged-message]').filter(has_text='Anomalie enregistrée').wait_for(state='visible');page.screenshot(path=str(OUT/'anomalie_desktop.png'),animations='disabled')
            page.once('dialog',lambda d:d.accept('Annexe corrigée et contrôlée'))
            with page.expect_response(lambda r:r.url.endswith(f'/st/ged/{process.pk}/anomalies/')) as resolved:root.locator('[data-ged-anomalies] article').filter(has_text=process.norme.reference_number).get_by_role('button',name='Enregistrer la résolution').click()
            assert resolved.value.status==200;row['anomaly_resolved']=True
        root.locator('[data-ged-mode=ged_activity]').click();root.locator('[data-ged-panel=activity]').wait_for(state='visible');page.screenshot(path=str(OUT/f'activite_graphiques_{label}.png'),animations='disabled')
        charts=root.locator('[data-ged-charts]');charts.scroll_into_view_if_needed();page.screenshot(path=str(OUT/f'statistiques_{label}.png'),animations='disabled')
        if label=='mobile':
            for i,title in enumerate(['volume','tomes','delais']):
                charts.locator('article').nth(i).scroll_into_view_if_needed();page.screenshot(path=str(OUT/f'graphique_{title}_mobile.png'),animations='disabled')
        row['overflow']=page.evaluate('document.documentElement.scrollWidth>innerWidth+2');row['javascript_errors']=errors
        detail=ctx.request.get(base+f'/api/v1/st/ged/{process.pk}/').json();row['stage_after_index']=detail['stage'];row['intake_not_validated']=detail['intake_validated_at'] is None
        assert row['intake_not_validated'] and not row['overflow'] and not errors
        results.append(row);(OUT/'parcours.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(label,'PASS indexation + fichier privé + historique + statistiques',flush=True);ctx.close()
    desktop=cases[0][3]
    ctx=browser.new_context(viewport={'width':1440,'height':1000});ctx.route('https://**/*',lambda r:r.abort());ctx.add_cookies([{'name':'sessionid','value':head_session,'url':base}]);page=ctx.new_page();page.goto(base+'/ctc/#ged',wait_until='domcontentloaded',timeout=120000)
    page.wait_for_function('()=>document.querySelector("[data-ged-workspace]").getAttribute("aria-busy")==="false"');page.evaluate('(id)=>{window.switchView("ged");window.stGEDSelect(id)}',desktop.pk)
    page.locator('[data-ged-confirm-comment]').fill('Versions, rapport et codification contrôlés en recette isolée.')
    with page.expect_response(lambda r:r.url.endswith('/st/ged/confirm/')) as confirmation:page.locator('[data-ged-confirm=CONFIRMED]').click()
    assert confirmation.value.status==201,confirmation.value.text();page.locator('[data-ged-message]').filter(has_text='Décision documentaire enregistrée').wait_for(state='visible');page.screenshot(path=str(OUT/'confirmation_chef_p2.png'),animations='disabled')
    results[0]['head_confirm_http']=confirmation.value.status
    browser.close()
desktop.refresh_from_db();assert desktop.intake_validated_at is None
client=Client();client.force_login(coordinator);response=client.post(f'/ctc/dossiers/{desktop.pk}/reception/',{'action':'validate_intake'})
assert response.status_code==200,response.content
desktop.refresh_from_db();results[0]['coordination_intake_http']=response.status_code;results[0]['stage_after_coordination']=desktop.current_stage
results[0]['versions_preserved']=STGEDIndexation.objects.filter(process=desktop).count()
for row in results:
    row['audit_events']=AuditLog.objects.filter(content_type='CTCProcessus',changes__subsystem='GED',object_id=row['process_id'],changes__action__in=['ged_indexed','ged_restored']).count()
    row['head_notification']=Notification.objects.filter(user=head,data__ged_process_id=row['process_id']).exists()
(OUT/'parcours.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
server.shutdown();print('PASS confirmation documentaire chef P2 distincte de la validation d’entrée par la coordination.',flush=True)
