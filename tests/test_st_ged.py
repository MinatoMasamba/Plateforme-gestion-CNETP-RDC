import io
from types import SimpleNamespace
import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from apps.core.models import AuditLog
from apps.governance.models import CTCProcessus, Organe, GroupeCible, PosteOrganisation, MandatOrganisation
from apps.governance.st_matrix import prepare_matrix
from apps.governance.st_operations_models import STAccessPolicy
from apps.governance.st_admin_models import STReceptionPiece
from apps.governance.st_ged_models import STGEDFile, STGEDIndexation, STGEDCode
from apps.governance import st_admin, st_ged
from apps.norms.models import NormeVersion


def pdf(text='Document de recette GED sans valeur officielle'):
    from reportlab.pdfgen import canvas
    stream=io.BytesIO();page=canvas.Canvas(stream);page.drawString(30,750,text);page.save()
    return ContentFile(stream.getvalue(),name='document.pdf')


@pytest.fixture
def ged(expert_factory,user_factory,norme_factory,tmp_path,monkeypatch):
    version=prepare_matrix();version.status='VALIDATED';version.save()
    STAccessPolicy.objects.update_or_create(pk=1,defaults={'version':version,'enabled':True})
    def member(number):
        expert=expert_factory(user=user_factory(username=f'ged-{number}',is_staff=number==11,is_superuser=number==11))
        post=PosteOrganisation.objects.get(code=f'ST-V3-{number:02}')
        MandatOrganisation.objects.create(expert=expert,poste=post,function=post.title,status='ACTIVE',start_date=timezone.localdate(),appointment_reference='Recette GED isolée')
        return expert.user
    writer,head,secretary,coordinator,ptn=[member(n) for n in (11,10,6,1,12)]
    sc=Organe.objects.create(version=version,type='SC',code='SC-IT',name='Transport',status='VALIDATED',source_reference='Recette')
    group=GroupeCible.objects.create(sc=sc,code='SC-IT-GT1',name='Groupe sans statut',activity='PRODUCTION',source_reference='Recette')
    sender=expert_factory(user=user_factory(username='ged-sender'))
    post=PosteOrganisation.objects.create(organe=sc,code='GED-SECRETARY',category='SECRETARIAT',title='Secrétaire',status='VALIDATED',source_reference='Recette')
    MandatOrganisation.objects.create(expert=sender,poste=post,function=post.title,status='ACTIVE',start_date=timezone.localdate(),appointment_reference='Recette')
    process=CTCProcessus.objects.create(norme=norme_factory())
    monkeypatch.setattr(STReceptionPiece._meta.get_field('file'),'storage',FileSystemStorage(location=tmp_path/'reception'))
    monkeypatch.setattr(STGEDFile._meta.get_field('file'),'storage',FileSystemStorage(location=tmp_path/'ged'))
    receipt=st_admin.save_reception(secretary,{'process_id':process.pk,'sc_id':sc.pk,'group_id':group.pk,'sender_id':sender.pk,'vote_date':timezone.localdate().isoformat(),'vote_percentage':80,'verified':True})
    for kind in ['PROJECT','VOTE']:st_admin.add_piece(secretary,receipt.pk,kind,pdf())
    receipt.refresh_from_db();st_admin.register_reception(secretary,receipt.pk,receipt.revision)
    return SimpleNamespace(**locals())


def prepared(g):
    st_admin.add_piece(g.secretary,g.receipt.pk,'REPORT',pdf('Rapport de revue de SC de recette'))
    code=st_ged.approve_code(g.head,g.process.pk,'GED-RECETTE-001','Décision de recette isolée, aucun code officiel créé',g.sc.pk)
    file=st_ged.upload(g.writer,g.process.pk,pdf())
    return {'code_id':code.pk,'source_id':file.pk,'base_version_id':0,'verified':True,'observation':'Pièces vérifiées'}


@pytest.mark.django_db
def test_actual_report_required_even_with_legacy_reference(ged):
    g=ged
    g.process.refresh_from_db()
    g.process.sc_report_received_at=timezone.now();g.process.sc_report_reference='Référence seule';g.process.save()
    code=st_ged.approve_code(g.head,g.process.pk,'REC-REF','Référence autorisant le code de recette',g.sc.pk)
    file=st_ged.upload(g.writer,g.process.pk,pdf())
    with pytest.raises(ValidationError,match='pièce réelle'):
        st_ged.index(g.writer,g.process.pk,code.pk,file.pk,0,True)
    assert not STGEDIndexation.objects.exists()


@pytest.mark.django_db
def test_no_invented_code_or_authorization_by_post11(ged,client):
    g=ged
    st_admin.add_piece(g.secretary,g.receipt.pk,'REPORT',pdf())
    file=st_ged.upload(g.writer,g.process.pk,pdf())
    with pytest.raises(ValidationError,match='Code documentaire'):
        st_ged.index(g.writer,g.process.pk,123456,file.pk,0,True)
    client.force_login(g.writer)
    response=client.post('/api/v1/st/ged/codes/',{'process_id':g.process.pk,'sc_id':g.sc.pk,'code':'NCD-EXEMPLE','source_reference':'Exemple interdit'},content_type='application/json')
    assert response.status_code==403 and not STGEDCode.objects.exists()


@pytest.mark.django_db
def test_indexation_records_real_metadata_without_norm_validation(ged,client,django_capture_on_commit_callbacks):
    g=ged;values=prepared(g);status=g.process.norme.status
    with django_capture_on_commit_callbacks(execute=True):entry=st_ged.index(g.writer,g.process.pk,**values)
    g.process.refresh_from_db();g.process.norme.refresh_from_db()
    assert g.process.indexed_at and not g.process.intake_validated_at and g.process.current_stage=='RECEPTION'
    assert g.process.norme.status==status and entry.version.version_number==1
    assert entry.report.kind=='REPORT' and entry.sc==g.sc and entry.group==g.group and entry.author==g.writer
    assert entry.version.version_author==g.writer and not entry.version.document
    log=AuditLog.objects.get(content_type='CTCProcessus',changes__subsystem='GED',changes__action='ged_indexed')
    assert log.object_id==g.process.pk
    assert log.changes['report_verified_by']==g.writer.pk and log.changes['source_id']==entry.source_id
    from apps.mobileapp.models import Notification
    assert Notification.objects.filter(user=g.head,data__ged_process_id=g.process.pk).exists()
    client.force_login(g.writer)
    response=client.get('/api/v1/st/ged/').json();assert response['kpis']['ready']==0 and response['kpis']['blocked']==0 and response['kpis']['indexed']==1 and response['kpis']['pending']==1
    assert response['kpis']['waiting_report']==0 and response['kpis']['anomalies']==0 and response['kpis']['versions_todo']==1
    assert response['kpis']['confirmed_period']==0 and response['kpis']['median_delay_days'] is None
    assert response['statistics']['indexations']==1 and response['statistics']['tomes'][0]['delay_samples']==1
    assert response['statistics']['tomes'][0]['tome']=='Tome 1'
    download=client.get(f'/api/v1/st/ged/{g.process.pk}/files/{entry.source_id}/')
    assert download.status_code==200 and download['Cache-Control']=='private, no-store'
    dossier=client.get(f'/ctc/norme/{g.process.norme_id}/lecture/')
    assert dossier.status_code==200 and f'/api/v1/st/ged-documents/{entry.pk}/' in dossier.content.decode()
    assert entry.source.name in dossier.content.decode()
    assert client.get(f'/api/v1/st/ged-documents/{entry.pk}/').status_code==200
    assert client.delete(f'/api/v1/st/ged-documents/{entry.pk}/').status_code==405
    assert client.delete(f'/api/v1/st/ged/{g.process.pk}/').status_code==405
    assert STGEDIndexation.objects.filter(pk=entry.pk).exists()


@pytest.mark.django_db
def test_documentary_metadata_is_saved_per_version_and_preserves_originals(ged, client):
    g = ged
    values = prepared(g)
    original_title = g.process.norme.title
    original_reference = g.process.norme.reference_number
    original_vote = g.receipt.vote_date
    metadata = {'reference': 'DOC-CORRIGE', 'title': 'Titre documentaire corrigé',
                'tome': 'Tome 2', 'sc': 'SC corrigée sur la pièce', 'group': '',
                'sender': 'Émetteur corrigé', 'vote_date': '2026-01-15', 'version': 'V03 papier'}
    client.force_login(g.writer)
    response = client.post(f'/api/v1/st/ged/{g.process.pk}/index/',
                           {**values, 'metadata': metadata}, content_type='application/json')
    assert response.status_code == 201, response.content
    first = STGEDIndexation.objects.get(pk=response.json()['id'])
    assert first.metadata['title'] == metadata['title']
    assert first.metadata['group'] == ''
    assert first.version.title == metadata['title']
    assert first.sc_id == g.sc.pk and first.group_id == g.group.pk
    g.process.norme.refresh_from_db()
    g.receipt.refresh_from_db()
    assert g.process.norme.title == original_title
    assert g.process.norme.reference_number == original_reference
    assert g.receipt.vote_date == original_vote
    second = st_ged.index(g.writer, g.process.pk, **{**values, 'base_version_id': first.version_id,
                          'metadata': {**metadata, 'title': 'Autre titre'}})
    first.refresh_from_db()
    assert first.metadata['title'] == metadata['title']
    assert second.metadata['title'] == 'Autre titre'
    assert client.get(f'/api/v1/st/ged/{g.process.pk}/').json()['latest']['metadata'] == second.metadata
    log = AuditLog.objects.get(changes__indexation_id=second.pk, changes__action='ged_indexed')
    assert log.changes['metadata'] == second.metadata
    rejected = client.post(f'/api/v1/st/ged/{g.process.pk}/index/',
                           {**values, 'metadata': metadata}, content_type='application/json')
    assert rejected.status_code == 409
    assert STGEDIndexation.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize('metadata', [{'title': ''}, {'sc_id': '123'}, {'vote_date': '2026-99-99'}])
def test_invalid_documentary_metadata_creates_no_version(ged, metadata):
    g = ged
    values = prepared(g)
    with pytest.raises(ValidationError):
        st_ged.index(g.writer, g.process.pk, **values, metadata=metadata)
    assert not STGEDIndexation.objects.exists()
    assert not NormeVersion.all_objects.filter(norme=g.process.norme).exists()


@pytest.mark.django_db
def test_report_preview_is_inline_and_download_stays_explicit(ged, client):
    g = ged
    prepared(g)
    report = g.receipt.pieces.get(kind='REPORT')
    url = f'/api/v1/st/receptions/{g.receipt.pk}/piece/{report.pk}/'
    client.force_login(g.writer)
    preview = client.get(url, {'inline': 1})
    assert preview.status_code == 200
    assert preview['Content-Disposition'].startswith('inline;')
    assert preview['Content-Type'] == 'application/pdf'
    assert preview['Cache-Control'] == 'private, no-store'
    assert client.get(url)['Content-Disposition'].startswith('attachment;')
    client.logout()
    assert client.get(url, {'inline': 1}).status_code in (401, 403)


@pytest.mark.django_db
def test_full_version_history_includes_writing_and_ged_with_existing_scope(ged, client, norme_factory):
    g = ged
    draft = NormeVersion.all_objects.create(norme=g.process.norme, version_number=1,
        title='Avant-projet', content='Texte avant la revue', version_author=g.writer)
    values = {**prepared(g), 'base_version_id': draft.pk}
    indexed = st_ged.index(g.writer, g.process.pk, **values)
    client.force_login(g.writer)
    url = f'/api/v1/st/ged/{g.process.pk}/version-history/'
    response = client.get(url)
    assert response.status_code == 200, response.content
    assert [row['version_number'] for row in response.json()] == [2, 1]
    assert response.json()[0]['source_url'].endswith(f'/files/{indexed.source_id}/')
    assert response.json()[1]['content'] == draft.content
    assert response.json()[1]['status_label'] == 'Version de rédaction'
    assert client.get(f'/api/v1/st/ged/{g.process.pk}/').json()['version_count'] == 2
    compared = client.get(url + 'compare/', {'left': draft.pk, 'right': indexed.version_id})
    assert compared.status_code == 200 and compared.json()['diff_segments']
    foreign = NormeVersion.all_objects.create(norme=norme_factory(), version_number=1,
        title='Autre dossier', content='Ne pas exposer ce contenu')
    assert client.get(url + 'compare/', {'left': draft.pk, 'right': foreign.pk}).status_code == 404
    client.force_login(g.member(13))
    assert client.get(url).status_code == 403
    assert client.get(url + 'compare/', {'left': draft.pk, 'right': indexed.version_id}).status_code == 403


@pytest.mark.django_db
def test_statistics_group_indexations_by_tome_once(ged,client):
    g=ged;values=prepared(g)
    first=st_ged.index(g.writer,g.process.pk,**values)
    g.process.refresh_from_db()
    st_ged.index(g.writer,g.process.pk,**{**values,'base_version_id':first.version_id})
    stats=st_ged.statistics(g.writer)
    assert [row['tome'] for row in stats['tomes']]==['Tome 1']
    assert stats['tomes'][0]['count']==1 and stats['tomes'][0]['delay_samples']==2
    client.force_login(g.writer)
    assert client.get('/api/v1/st/ged/').json()['kpis']['pending']==1


@pytest.mark.django_db
def test_version_conflict_and_old_index_endpoint_cannot_bypass(ged,client):
    g=ged;values=prepared(g)
    st_ged.index(g.writer,g.process.pk,**values)
    client.force_login(g.writer)
    assert client.get('/api/v1/st/ged/pk-invalide/').status_code==404
    response=client.post(f'/api/v1/st/ged/{g.process.pk}/index/',values,content_type='application/json')
    assert response.status_code==409 and STGEDIndexation.objects.count()==1
    assert client.post(f'/ctc/dossiers/{g.process.pk}/reception/',{'action':'index'}).status_code==400
    assert client.post(f'/ctc/dossiers/{g.process.pk}/reception/',{'action':'validate_intake'}).status_code==403


@pytest.mark.django_db
def test_new_version_comparison_and_restore_keep_all_history(ged,client):
    g=ged;values=prepared(g)
    first=st_ged.index(g.writer,g.process.pk,**values)
    file=st_ged.upload(g.writer,g.process.pk,pdf('Deuxième contenu documentaire'))
    second=st_ged.index(g.writer,g.process.pk,**{**values,'source_id':file.pk,'base_version_id':first.version_id})
    client.force_login(g.writer)
    comparison=client.get(f'/api/v1/st/ged/{g.process.pk}/compare/',{'left':first.pk,'right':second.pk})
    assert comparison.status_code==200 and comparison.json()['file_changed'] and comparison.json()['text_diff']
    restored=st_ged.index(g.writer,g.process.pk,**{**values,'base_version_id':second.version_id,'restore_id':first.pk,'observation':'Restauration motivée du premier document'})
    assert restored.version.version_number==3 and restored.restored_from==first
    assert restored.version.content==first.version.content
    assert STGEDIndexation.objects.count()==3 and STGEDFile.objects.count()==2 and NormeVersion.all_objects.filter(norme=g.process.norme).count()==3


@pytest.mark.django_db
def test_pole2_confirmation_distinct_from_coordination(ged,client,django_capture_on_commit_callbacks):
    g=ged;entry=st_ged.index(g.writer,g.process.pk,**prepared(g))
    with pytest.raises(PermissionDenied):st_ged.confirm(g.writer,entry.pk,'CONFIRMED','Ne doit pas décider')
    client.force_login(g.coordinator)
    assert client.post(f'/ctc/dossiers/{g.process.pk}/reception/',{'action':'validate_intake'}).status_code==400
    with django_capture_on_commit_callbacks(execute=True):st_ged.confirm(g.head,entry.pk,'CONFIRMED','Code et version contrôlés')
    g.process.refresh_from_db();assert not g.process.intake_validated_at
    response=client.post(f'/ctc/dossiers/{g.process.pk}/reception/',{'action':'validate_intake'})
    assert response.status_code==200,response.content
    g.process.refresh_from_db();assert g.process.intake_validated_at and g.process.current_stage!='RECEPTION'
    with pytest.raises(ValidationError):st_ged.upload(g.writer,g.process.pk,pdf())
    client.force_login(g.writer)
    assert not client.get(f'/api/v1/st/ged/{g.process.pk}/').json()['dossier_readable']
    assert client.get(f'/api/v1/st/ged-documents/{entry.pk}/').status_code==200
    jurist=g.member(13)
    client.force_login(jurist)
    assert client.get(f'/api/v1/st/ged-documents/{entry.pk}/').status_code==200


@pytest.mark.django_db
def test_anomaly_blocks_indexing_and_resolution_preserves_receipt(ged):
    g=ged;values=prepared(g)
    issue=st_ged.anomaly(g.writer,g.process.pk,'Annexe documentaire incohérente')
    with pytest.raises(ValidationError,match='Anomalie'):st_ged.index(g.writer,g.process.pk,**values)
    st_ged.anomaly(g.writer,g.process.pk,'Annexe corrigée et contrôlée',issue.pk)
    issue.refresh_from_db();g.receipt.refresh_from_db()
    assert issue.resolved_at and issue.comment=='Annexe documentaire incohérente' and g.receipt.state=='ENREGISTREE'
    assert st_ged.index(g.writer,g.process.pk,**values)


@pytest.mark.django_db
def test_corrupt_oversize_and_falsely_named_files_are_rejected(ged):
    for file in [ContentFile(b'%PDF-endommage',name='bad.pdf'),ContentFile(b'\x89PNG\r\n\x1a\n',name='bad.png'),ContentFile(b'MZexe',name='fake.jpg'),ContentFile(b'x'*(10*1024*1024+1),name='large.pdf')]:
        with pytest.raises(ValidationError):st_ged.upload(ged.writer,ged.process.pk,file)
    assert not STGEDFile.objects.exists()


@pytest.mark.django_db
def test_report_integrity_and_human_verification_required(ged):
    g=ged;values=prepared(g)
    with pytest.raises(ValidationError,match='Vérifiez'):st_ged.index(g.writer,g.process.pk,**{**values,'verified':False})
    piece=g.receipt.pieces.get(kind='REPORT')
    with piece.file.storage.open(piece.file.name,'wb') as stream:stream.write(pdf('Contenu altéré').read())
    with pytest.raises(ValidationError,match='empreinte'):st_ged.index(g.writer,g.process.pk,**values)
    assert not STGEDIndexation.objects.exists()


@pytest.mark.django_db
def test_post11_only_personal_history_and_documents(ged,client):
    g=ged;values=prepared(g)
    head_source=st_ged.upload(g.head,g.process.pk,pdf())
    entry=st_ged.index(g.head,g.process.pk,**{**values,'source_id':head_source.pk})
    client.force_login(g.writer)
    assert client.get(f'/api/v1/st/ged/{g.process.pk}/').status_code==404
    assert client.get(f'/api/v1/st/ged/{g.process.pk}/files/{entry.source_id}/').status_code==404
    history=client.get('/api/v1/st/ged/history/').json()['results']
    assert len(history)==1 and history[0]['action']=='ged_file_uploaded' and history[0]['author']==g.writer.username
    client.force_login(g.ptn)
    assert client.get('/api/v1/st/ged/').status_code==403
    assert client.get(f'/api/v1/st/ged-documents/{entry.pk}/').status_code==403


@pytest.mark.django_db
def test_returned_version_can_be_corrected_without_erasing_decision(ged,client):
    g=ged;values=prepared(g);first=st_ged.index(g.writer,g.process.pk,**values)
    st_ged.confirm(g.head,first.pk,'RETURNED','Corriger la codification documentaire')
    client.force_login(g.writer)
    payload=client.get('/api/v1/st/ged/').json()
    assert payload['results'][0]['state']=='CORRECTION' and payload['kpis']['blocked']==1 and payload['kpis']['pending']==0
    second=st_ged.index(g.writer,g.process.pk,**{**values,'base_version_id':first.version_id,'observation':'Préparation corrigée'})
    assert second.version.version_number==2 and first.confirmation.decision=='RETURNED'
    assert client.get('/api/v1/st/ged/').json()['kpis']['pending']==1


@pytest.mark.django_db
@pytest.mark.parametrize('format,suffix',[('PNG','png'),('JPEG','jpg')])
def test_real_images_are_accepted_without_inventing_text(ged,format,suffix):
    from PIL import Image
    stream=io.BytesIO();Image.new('RGB',(20,20),'white').save(stream,format=format)
    file=st_ged.upload(ged.writer,ged.process.pk,ContentFile(stream.getvalue(),name='image.'+suffix))
    assert file.size>0 and file.sha256 and file.file.storage.exists(file.file.name)


@pytest.mark.django_db
def test_unindexed_version_prevents_intake_after_confirmation(ged):
    g=ged;entry=st_ged.index(g.writer,g.process.pk,**prepared(g))
    st_ged.confirm(g.head,entry.pk,'CONFIRMED','Pièces vérifiées')
    g.process.refresh_from_db()
    assert st_ged.confirmed_for_intake(g.process)
    NormeVersion.all_objects.create(norme=g.process.norme,version_number=2,title='Nouvelle version non indexée',content='Texte transmis')
    assert not st_ged.confirmed_for_intake(g.process)


@pytest.mark.django_db
def test_queue_shows_reception_before_report_and_applies_real_filters(ged,client):
    g=ged
    client.force_login(g.writer)
    response=client.get('/api/v1/st/ged/queue/')
    assert response.status_code==200
    payload=response.json()
    assert payload['total']==1 and payload['counts']['REPORT']==1 and payload['counts']['total']==1
    row=payload['results'][0]
    assert row['reference']==g.process.norme.reference_number and row['queue_state']=='REPORT'
    assert row['pv_present'] is True and row['report_present'] is False
    assert row['report_status']=='awaited' and row['received_at']
    assert payload['scs'] and payload['groups'] and payload['scs'][0]['tome_label']
    assert client.get('/api/v1/st/ged/queue/?states=READY').json()['total']==0
    assert client.get('/api/v1/st/ged/queue/?report=received').json()['total']==0
    assert client.get('/api/v1/st/ged/queue/?sc=SC-IT').json()['total']==1
    assert client.get('/api/v1/st/ged/queue/?group=SC-IT-GT1').json()['total']==1
    assert client.get('/api/v1/st/ged/queue/?q=INTROUVABLE').json()['total']==0
    assert client.get('/api/v1/st/ged/queue/?date_from=2099-01-01').json()['total']==0


@pytest.mark.django_db
def test_queue_becomes_ready_once_report_and_code_exist(ged,client):
    g=ged
    st_admin.add_piece(g.secretary,g.receipt.pk,'REPORT',pdf())
    st_ged.approve_code(g.head,g.process.pk,'GED-QUEUE-001','Décision de recette isolée pour la file',g.sc.pk)
    client.force_login(g.writer)
    payload=client.get('/api/v1/st/ged/queue/?states=READY&report=received').json()
    assert payload['total']==1
    row=payload['results'][0]
    assert row['queue_state']=='READY' and row['report_present'] is True and row['pv_present'] is True
    page=client.get('/api/v1/st/ged/queue/?page_size=1&page=2').json()
    assert page['total']==1 and page['results']==[] and page['page_size']==10
