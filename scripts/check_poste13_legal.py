"""Recette navigateur des avis juridiques (postes 13/14) sur copie SQLite isolée."""
import io
import json
import os
import sqlite3
import sys
import threading
from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'reports/poste13_legal/recette';OUT.mkdir(parents=True,exist_ok=True)
DB='/tmp/legal_recette.sqlite3'
with sqlite3.connect(ROOT/'db.sqlite3') as source,sqlite3.connect(DB) as target:source.backup(target)
os.environ['DJANGO_SETTINGS_MODULE']='config.settings_test';os.environ['SQLITE_NAME']=DB
import django
from django.conf import settings
settings.DEBUG=True;settings.ALLOWED_HOSTS=['127.0.0.1','testserver']
settings.NOTIFICATION_SETTINGS={'EMAIL_ENABLED':False,'FCM_ENABLED':False}
django.setup()
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.test import Client
from django.utils import timezone
from apps.core.models import User
from apps.experts.models import Expert, Structure
from apps.governance import st_admin, st_ged, st_legal
from apps.governance.models import CTCProcessus, GroupeCible, MandatOrganisation, Organe, PosteOrganisation
from apps.governance.st_admin_models import STReceptionPiece
from apps.governance.st_ged_models import STGEDFile
from apps.governance.st_matrix import prepare_matrix
from apps.governance.st_operations_models import STAccessPolicy


def make_pdf(name,text):
    from reportlab.pdfgen import canvas
    stream=io.BytesIO();page=canvas.Canvas(stream);page.drawString(30,750,text);page.save()
    return ContentFile(stream.getvalue(),name=name)


call_command('migrate',verbosity=0)
post=PosteOrganisation.objects.filter(code='ST-V3-13').first()
if post is None or post.organe_id is None:
    version=prepare_matrix()
else:
    version=post.organe.version
if version.status!='VALIDATED':
    version.status='VALIDATED';version.save(update_fields=['status'])
STAccessPolicy.objects.update_or_create(pk=1,defaults={'version':version,'enabled':True})

Structure.objects.get_or_create(name='Recette juridique',defaults={'acronym':'RECJ','category':'ADMIN'})
structure=Structure.objects.get(name='Recette juridique')

def member(number,username,first,last):
    user=User.objects.filter(username=username).first()
    if user is None:
        user=User.objects.create_user(username=username,email=f'{username}@example.invalid',first_name=first,last_name=last)
    expert=Expert.objects.filter(user=user).first()
    if expert is None:
        expert=Expert.objects.create(user=user,structure=structure,status='ACTIVE')
    poste=PosteOrganisation.objects.get(code=f'ST-V3-{number:02}')
    MandatOrganisation.objects.filter(poste=poste,status='ACTIVE',capacity='ORGANISATION').update(status='ENDED',end_date=timezone.localdate())
    mandate=MandatOrganisation.objects.create(expert=expert,poste=poste,function=poste.title,status='ACTIVE',
        start_date=timezone.localdate(),appointment_reference='Recette avis juridiques isolée, sans valeur officielle')
    return mandate

chief_a=member(13,'legal.recette.13','Thyty','Mawete Recette')
chief_b=member(14,'legal.recette.14','Medi','Pindi Recette')
secretary=member(6,'legal.recette.06','Secrétaire','Recette')
ged_writer=member(11,'legal.recette.11','Agent','GED Recette')

process=CTCProcessus.objects.filter(norme__circuit_version='LEGACY',received_at__isnull=True).select_related('norme').first()
if process is None:
    process=CTCProcessus.objects.select_related('norme').first()
assert process is not None,'Aucun dossier normatif disponible pour la recette.'

if not hasattr(process,'administrative_reception'):
    sc=Organe.objects.filter(type='SC',status__in=['VALIDATED','ACTIVE']).first()
    group=GroupeCible.objects.filter(sc=sc).first() or GroupeCible.objects.create(sc=sc,code='RECETTE-GT',name='Groupe de recette',activity='PRODUCTION',source_reference='Recette')
    STReceptionPiece._meta.get_field('file').storage=FileSystemStorage(location='/tmp/legal_pieces/reception')
    STGEDFile._meta.get_field('file').storage=FileSystemStorage(location='/tmp/legal_pieces/ged')
    def pdf(name,text):
        from reportlab.pdfgen import canvas
        stream=io.BytesIO();page=canvas.Canvas(stream);page.drawString(30,750,text);page.save()
        return ContentFile(stream.getvalue(),name=name)
    sender_user=User.objects.filter(username='legal.recette.sender').first()
    if sender_user is None:
        sender_user=User.objects.create_user(username='legal.recette.sender',email='legal.sender@example.invalid',first_name='SC',last_name='Expéditrice')
    sender_expert=Expert.objects.filter(user=sender_user).first()
    if sender_expert is None:
        sender_expert=Expert.objects.create(user=sender_user,structure=structure,status='ACTIVE')
    sender_poste,_=PosteOrganisation.objects.get_or_create(organe=sc,code='LEGAL-RECETTE-SENDER',defaults={
        'category':'SECRETARIAT','title':'Secrétaire de SC de recette','status':'VALIDATED','source_reference':'Recette'})
    MandatOrganisation.objects.filter(poste=sender_poste,status='ACTIVE',capacity='ORGANISATION').update(status='ENDED',end_date=timezone.localdate())
    MandatOrganisation.objects.create(expert=sender_expert,poste=sender_poste,function=sender_poste.title,status='ACTIVE',
        start_date=timezone.localdate(),appointment_reference='Recette avis juridiques isolée, sans valeur officielle')
    receipt=st_admin.save_reception(secretary.expert.user,{'process_id':process.pk,'sc_id':sc.pk,'group_id':group.pk,
        'sender_id':sender_expert.pk,'vote_date':timezone.localdate().isoformat(),'vote_percentage':80,'verified':True})
    st_admin.add_piece(secretary.expert.user,receipt.pk,'PROJECT',make_pdf('projet.pdf','Projet de norme de recette'))
    st_admin.add_piece(secretary.expert.user,receipt.pk,'VOTE',make_pdf('vote.pdf','Preuve de vote de recette'))
    st_admin.add_piece(secretary.expert.user,receipt.pk,'REPORT',make_pdf('rapport.pdf','Rapport de revue de recette'))
    receipt.refresh_from_db();st_admin.register_reception(secretary.expert.user,receipt.pk,receipt.revision)
else:
    receipt=process.administrative_reception
    STReceptionPiece._meta.get_field('file').storage=FileSystemStorage(location='/tmp/legal_pieces/reception')
    STGEDFile._meta.get_field('file').storage=FileSystemStorage(location='/tmp/legal_pieces/ged')

ged_file=st_ged.upload(ged_writer.expert.user,process.pk,make_pdf('dossier-ged.pdf','Document GED de recette'))
entry=st_legal.create_request(chief_a.expert.user,process.pk,'Conformité juridique du projet de norme',
    'Le projet respecte-t-il les règles de compétence, de forme et de publication applicables ?',
    'Sous-commission de recette','COURRIEL-RECETTE-001',priority='HIGH')

client_a=Client();client_a.force_login(chief_a.expert.user);session_a=client_a.cookies['sessionid'].value
client_b=Client();client_b.force_login(chief_b.expert.user);session_b=client_b.cookies['sessionid'].value


class Server(ThreadingMixIn,WSGIServer):
    daemon_threads=True


class Quiet(WSGIRequestHandler):
    def log_message(self,*args):
        pass


server=make_server('127.0.0.1',0,StaticFilesHandler(get_wsgi_application()),server_class=Server,handler_class=Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}'

from playwright.sync_api import sync_playwright

results={}
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='chrome',headless=True)
    def context_for(session,width,height):
        context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
        context.route('https://**/*',lambda route:route.abort())
        context.add_cookies([{'name':'sessionid','value':session,'url':base}])
        return context

    # Desktop : rédaction et transmission par le co-chef 13.
    context=context_for(session_a,1440,900);page=context.new_page()
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(base+'/ctc/#legal',wait_until='domcontentloaded',timeout=120000)
    page.wait_for_selector('[data-legal-workspace]')
    page.wait_for_function("document.querySelectorAll('[data-legal-queue] .ged-queue-row').length>0")
    page.screenshot(path=str(OUT/'demandes_desktop.png'),full_page=False,animations='disabled')
    page.locator('[data-legal-queue] .ged-queue-row').first.click()
    page.wait_for_selector('[data-legal-opinion-form]:not([hidden])')
    page.locator('[data-legal-opinion-form] textarea[name=analysis]').fill('Le dossier est conforme aux règles de compétence et de forme ; réserve sur la pièce de vote à archiver.')
    page.locator('[data-legal-opinion-form] select[name=recommendation]').select_option('RESERVE')
    page.locator('[data-legal-submit]').click()
    page.locator('[data-legal-message]').filter(has_text='Avis transmis').wait_for(timeout=20000)
    page.wait_for_function("document.querySelector('[data-legal-own-state]').textContent.includes('attend la confirmation')")
    page.evaluate("document.getElementById('ctc-main').scrollTo(0,0)")
    page.screenshot(path=str(OUT/'avis_transmis_desktop.png'),full_page=False,animations='disabled')
    results['desktop_transmit']={'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth+2'),'errors':list(errors)}

    # Création d'une demande depuis l'interface.
    page.locator('[data-legal-new]').click()
    form=page.locator('[data-legal-request-form]')
    form.locator('select[name=process_id]').select_option(str(process.pk))
    form.locator('input[name=requester_name]').fill('Coordination de recette')
    form.locator('input[name=source_reference]').fill('NOTE-INTERNE-002')
    form.locator('input[name=subject]').fill('Demande complémentaire de recette')
    form.locator('textarea[name=question]').fill('Quelles pièces doivent être conservées pour la traçabilité de la décision ?')
    form.locator('[type=submit]').click()
    page.locator('[data-legal-message]').filter(has_text='enregistrée').wait_for(timeout=20000)
    results['desktop_create_reference']=page.locator('[data-legal-reference]').text_content()

    page.locator('[data-legal-mode=stats]').click();page.wait_for_timeout(600)
    page.screenshot(path=str(OUT/'statistiques_desktop.png'),full_page=False,animations='disabled')
    page.locator('[data-legal-mode=journal]').click();page.wait_for_timeout(800)
    page.screenshot(path=str(OUT/'journal_desktop.png'),full_page=False,animations='disabled')
    piece_url=page.evaluate("""()=>{const a=document.querySelector('[data-legal-pieces] a');return a?a.href:null}""")
    ged_url=page.evaluate("""()=>{const links=[...document.querySelectorAll('[data-legal-pieces] a')];const a=links.find(x=>x.textContent.includes('dossier-ged'));return a?a.href:null}""")
    results['piece_download']=context.request.get(piece_url).status if piece_url else None
    results['ged_download']=context.request.get(ged_url).status if ged_url else None
    results['desktop_errors']=list(errors)
    context.close()

    # Desktop : confirmation indépendante par le co-chef 14.
    context=context_for(session_b,1440,900);page=context.new_page()
    errors_b=[];page.on('pageerror',lambda error:errors_b.append(str(error)))
    page.goto(base+'/ctc/#legal',wait_until='domcontentloaded',timeout=120000)
    page.wait_for_selector('[data-legal-workspace]')
    page.locator('[data-legal-mode=confirm]').click()
    page.wait_for_selector('[data-legal-confirm-list] .legal-confirm-card')
    page.screenshot(path=str(OUT/'avis_a_confirmer_desktop.png'),full_page=False,animations='disabled')
    page.locator('[data-legal-confirm-list] .legal-confirm-card').first.get_by_role('button',name='Ouvrir la demande').click()
    page.wait_for_selector('.legal-decide textarea')
    page.locator('.legal-decide textarea').first.fill('Contrôle indépendant effectué ; avis et pièces concordants.')
    page.get_by_role('button',name='Confirmer l’avis').first.click()
    page.locator('[data-legal-message]').filter(has_text='Avis confirmé').wait_for(timeout=20000)
    page.wait_for_function("document.querySelector('[data-legal-state]').textContent.includes('Répondue')")
    page.evaluate("document.getElementById('ctc-main').scrollTo(0,0)")
    page.screenshot(path=str(OUT/'avis_confirme_desktop.png'),full_page=False,animations='disabled')
    results['desktop_confirm']={'status':page.locator('[data-legal-state]').text_content(),'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth+2'),'errors':list(errors_b)}
    context.close()

    # Desktop : le co-chef 13 constate la confirmation, puis clôture.
    context=context_for(session_a,1440,900);page=context.new_page()
    errors_c=[];page.on('pageerror',lambda error:errors_c.append(str(error)))
    page.goto(base+'/ctc/#legal',wait_until='domcontentloaded',timeout=120000)
    page.wait_for_selector('[data-legal-workspace]')
    page.wait_for_function("()=>[...document.querySelectorAll('[data-legal-queue] .ged-queue-row')].some(b=>b.textContent.includes('Répondue'))")
    page.locator('[data-legal-queue] .ged-queue-row').filter(has_text='Répondue').first.click()
    page.wait_for_function("document.querySelector('[data-legal-opinions]').textContent.includes('Confirmé')")
    page.evaluate("document.getElementById('ctc-main').scrollTo(0,0)")
    page.screenshot(path=str(OUT/'confirmation_constatee_desktop.png'),full_page=False,animations='disabled')
    page.locator('[data-legal-close]').click()
    page.locator('[data-legal-message]').filter(has_text='clôturée').wait_for(timeout=20000)
    page.wait_for_function("document.querySelector('[data-legal-state]').textContent.includes('Clôturée')")
    results['desktop_close']={'status':page.locator('[data-legal-state]').text_content(),'errors':list(errors_c)}
    context.close()

    # Tablette et mobile : même registre, sans débordement.
    for width,height,name in [(1024,900,'tablette'),(390,844,'mobile')]:
        context=context_for(session_a,width,height);page=context.new_page()
        errors_m=[];page.on('pageerror',lambda error:errors_m.append(str(error)))
        page.goto(base+'/ctc/#legal',wait_until='domcontentloaded',timeout=120000)
        page.wait_for_selector('[data-legal-workspace]')
        page.wait_for_function("document.querySelectorAll('[data-legal-queue] .ged-queue-row').length>0")
        page.locator('[data-legal-queue] .ged-queue-row').first.click()
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT/f'demandes_{name}.png'),full_page=False,animations='disabled')
        page.locator('[data-legal-mode=stats]').click();page.wait_for_timeout(600)
        page.screenshot(path=str(OUT/f'statistiques_{name}.png'),full_page=False,animations='disabled')
        results[name]={'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth+2'),'errors':list(errors_m)}
        context.close()
    browser.close()

server.shutdown()
results['database']={'request_reference':entry.reference,'process':process.pk,'ged_file':ged_file.pk,'reception':receipt.pk,
    'chief_a':chief_a.expert.user.username,'chief_b':chief_b.expert.user.username}
(OUT/'recette.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False,indent=2),flush=True)
