from datetime import timedelta
from decimal import Decimal
import io
import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from apps.governance.st_matrix import prepare_matrix
from apps.governance.models import PosteOrganisation,MandatOrganisation,Organe,GroupeCible,CTCProcessus
from apps.governance.st_operations_models import STAccessPolicy
from apps.governance.st_admin_models import STReception,STReceptionPiece,STPVVersion
from apps.governance import st_admin as service
from apps.core.models import AuditLog
from apps.meetings.models import Reunion


def pdf():
    from reportlab.pdfgen import canvas
    stream=io.BytesIO();c=canvas.Canvas(stream);c.drawString(40,750,'Justificatif de recette sans valeur officielle');c.save()
    return ContentFile(stream.getvalue(),name='preuve.pdf')


@pytest.fixture
def setup(user_factory,expert_factory,norme_factory,tmp_path,monkeypatch):
    version=prepare_matrix();version.status='VALIDATED';version.save()
    STAccessPolicy.objects.update_or_create(pk=1,defaults={'version':version,'enabled':True})
    secretary=expert_factory(user=user_factory(username='secretary',is_superuser=True,is_staff=True))
    post=PosteOrganisation.objects.get(code='ST-V3-06')
    MandatOrganisation.objects.create(expert=secretary,poste=post,function=post.title,status='ACTIVE',start_date=timezone.localdate(),appointment_reference='Recette')
    sc=Organe.objects.create(version=version,code='SC-TEST',type='SC',name='SC Test',status='VALIDATED',source_reference='Recette')
    group=GroupeCible.objects.create(sc=sc,code='GT-1',name='Groupe test',activity='PRODUCTION',source_reference='Recette')
    sender=expert_factory(user=user_factory(username='sender'))
    source_post=PosteOrganisation.objects.create(organe=sc,code='SC-TEST-SECRETARY',category='SECRETARIAT',title='Secrétaire',status='VALIDATED',source_reference='Recette')
    MandatOrganisation.objects.create(expert=sender,poste=source_post,function='Secrétaire',status='ACTIVE',start_date=timezone.localdate(),appointment_reference='Recette')
    process=CTCProcessus.objects.create(norme=norme_factory())
    monkeypatch.setattr(STReceptionPiece._meta.get_field('file'),'storage',FileSystemStorage(location=tmp_path))
    values={'process_id':process.pk,'sc_id':sc.pk,'group_id':group.pk,'sender_id':sender.pk,'vote_date':timezone.localdate().isoformat(),'vote_percentage':'76','verified':True}
    return secretary,sender,process,values


def prepared(setup):
    secretary,sender,process,values=setup
    r=service.save_reception(secretary.user,values)
    service.add_piece(secretary.user,r.pk,'PROJECT',pdf());service.add_piece(secretary.user,r.pk,'VOTE',pdf())
    r.refresh_from_db()
    return secretary,sender,process,r


@pytest.mark.django_db
def test_register_without_report_idempotent_audited(setup,client,django_capture_on_commit_callbacks):
    secretary,sender,p,r=prepared(setup)
    with django_capture_on_commit_callbacks(execute=True):
        registered=service.register_reception(secretary.user,r.pk,r.revision)
    p.refresh_from_db()
    assert p.received_by==secretary and p.sc_report_received_at is None
    assert p.indexed_at is None and p.intake_validated_at is None
    assert registered.snapshot['sender']==sender.full_name
    second=service.register_reception(secretary.user,r.pk,0)
    assert second.reference==registered.reference
    assert AuditLog.objects.filter(content_type='governance.STReception',object_id=r.pk,changes__action='registered').count()==1
    from apps.mobileapp.models import Notification
    assert Notification.objects.filter(user=sender.user,data__reception_id=r.pk).exists()
    client.force_login(secretary.user)
    response=client.get(f'/api/v1/st/receptions/{r.pk}/acknowledgement/')
    assert response.status_code==200 and response.content.startswith(b'%PDF')
    assert client.post(f'/ctc/dossiers/{p.pk}/reception/',{'action':'validate_intake'}).status_code==400  # Rapport absent.


@pytest.mark.django_db
@pytest.mark.parametrize('vote',['0','75','74.99'])
def test_insufficient_vote_never_registers(setup,vote):
    secretary,_,p,r=prepared(setup)
    r.vote_percentage=Decimal(vote);r.save()
    with pytest.raises(ValidationError,match='75'):
        service.register_reception(secretary.user,r.pk,r.revision)
    p.refresh_from_db();assert p.received_at is None


@pytest.mark.django_db
def test_missing_piece_anomaly_and_correction(setup):
    secretary,_,p,values=setup
    r=service.save_reception(secretary.user,{**values,'anomaly':True,'observations':'PV manquant'})
    with pytest.raises(ValidationError):service.register_reception(secretary.user,r.pk,r.revision)
    r=service.save_reception(secretary.user,{**values,'revision':r.revision,'observations':'Pièces reçues','anomaly':False},r.pk)
    with pytest.raises(ValidationError,match='preuve du vote'):
        service.register_reception(secretary.user,r.pk,r.revision)
    assert r.state=='BROUILLON'


@pytest.mark.django_db
def test_later_report_and_immutable_receipt(setup):
    secretary,_,p,r=prepared(setup)
    service.register_reception(secretary.user,r.pk,r.revision)
    r.refresh_from_db();snapshot=r.snapshot.copy()
    service.add_piece(secretary.user,r.pk,'REPORT',pdf())
    p.refresh_from_db();r.refresh_from_db()
    assert p.sc_report_received_at and p.sc_report_received_by==secretary
    assert r.snapshot==snapshot
    with pytest.raises(ValidationError):service.save_reception(secretary.user,{'revision':r.revision},r.pk)


@pytest.mark.django_db
def test_private_pieces_and_wrong_post_denied(setup,client,user_factory,expert_factory):
    secretary,_,p,r=prepared(setup)
    outsider=expert_factory(user=user_factory(username='outsider'))
    with pytest.raises(PermissionDenied):service.register_reception(outsider.user,r.pk,r.revision)
    client.force_login(outsider.user)
    assert client.get(f'/api/v1/st/receptions/{r.pk}/piece/{r.pieces.first().pk}/').status_code==404
    with pytest.raises(ValidationError):service.add_piece(secretary.user,r.pk,'PROJECT',ContentFile(b'%PDF-broken',name='broken.pdf'))


@pytest.mark.django_db
def test_future_vote_and_cross_sc_group_rejected(setup):
    secretary,_,_,values=setup
    with pytest.raises(ValidationError):service.save_reception(secretary.user,{**values,'vote_date':(timezone.localdate()+timedelta(days=1)).isoformat()})


@pytest.mark.django_db
def test_group_without_status_can_register_but_sc_must_be_confirmed(setup,client):
    secretary,_,_,r=prepared(setup)
    r.sc.status='PROPOSED';r.sc.save()
    with pytest.raises(ValidationError,match='référentiel'):
        service.register_reception(secretary.user,r.pk,r.revision)
    r.refresh_from_db();assert r.state=='BROUILLON'
    r.sc.status='VALIDATED';r.sc.save()
    registered=service.register_reception(secretary.user,r.pk,r.revision)
    assert registered.state=='ENREGISTREE'
    client.force_login(secretary.user)
    groups=client.get('/api/v1/st/receptions/catalogue/').json()['groups']
    assert any(g['id']==r.group_id for g in groups)
    assert all('status' not in g for g in groups)


@pytest.mark.django_db
def test_pv_versions_freeze_on_submission_no_auto_approval(setup,client,user_factory,expert_factory):
    secretary,_,_,_=setup
    meeting=Reunion.objects.create(type='CTC',titre='Séance de recette',date=timezone.now(),organisateur=secretary)
    client.force_login(secretary.user)
    url='/api/v1/st/pv/'
    data={'meeting_id':meeting.pk,'revision':0,'content':'Synthèse des échanges','decisions':[{'text':'Déposer le rapport de SC'}]}
    first=client.post(url,data,content_type='application/json');assert first.status_code==201
    second=client.post(url,{**data,'revision':1,'submit':True},content_type='application/json');assert second.status_code==201
    third=client.post(url,{**data,'revision':2},content_type='application/json');assert third.status_code==400
    assert STPVVersion.objects.filter(pv__reunion=meeting).count()==2
    meeting.refresh_from_db();assert meeting.pv.redaction!='VALIDE' and meeting.pv.signature_date is None
    assert client.post(f'/api/v1/pv/{meeting.pv.pk}/sign/').status_code==403
    coordinator=expert_factory(user=user_factory(username='coordinator'))
    post=PosteOrganisation.objects.get(code='ST-V3-01')
    MandatOrganisation.objects.create(expert=coordinator,poste=post,function=post.title,status='ACTIVE',start_date=timezone.localdate(),appointment_reference='Recette')
    client.force_login(coordinator.user)
    assert client.post(f'/api/v1/pv/{meeting.pv.pk}/sign/').status_code==400
    meeting.status='COMPLETED';meeting.save()
    client.force_login(secretary.user)
    assert client.post(f'/api/v1/reunions/{meeting.pk}/generate_pv/').status_code==409
    meeting.pv.refresh_from_db()
    assert meeting.pv.contenu=='Synthèse des échanges' and meeting.pv.signature_date is None
