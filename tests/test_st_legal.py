import io
import pytest
from types import SimpleNamespace
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from apps.core.models import AuditLog
from apps.governance import st_admin, st_ged, st_legal
from apps.governance.models import CTCProcessus, GroupeCible, MandatOrganisation, Organe, PosteOrganisation
from apps.governance.st_admin_models import STReceptionPiece
from apps.governance.st_ged_models import STGEDFile
from apps.governance.st_matrix import prepare_matrix
from apps.governance.st_operations_models import STAccessPolicy
from apps.governance.st_legal_models import STLegalOpinion, STLegalRequest


def pdf(name='avis.pdf', text='Pièce de recette sans valeur officielle'):
    from reportlab.pdfgen import canvas
    stream=io.BytesIO();page=canvas.Canvas(stream);page.drawString(30,750,text);page.save()
    return ContentFile(stream.getvalue(),name=name)


@pytest.fixture
def legal(expert_factory,user_factory,norme_factory,tmp_path,monkeypatch):
    version=prepare_matrix();version.status='VALIDATED';version.save()
    STAccessPolicy.objects.update_or_create(pk=1,defaults={'version':version,'enabled':True})
    def member(number,username=None):
        expert=expert_factory(user=user_factory(username=username or f'legal-{number}'))
        post=PosteOrganisation.objects.get(code=f'ST-V3-{number:02}')
        MandatOrganisation.objects.create(expert=expert,poste=post,function=post.title,status='ACTIVE',
            start_date=timezone.localdate(),appointment_reference='Recette avis juridiques isolée')
        return expert.user
    chief_a,chief_b,secretary,outsider,ged_writer=[member(n) for n in (13,14,6,15,11)]
    coordinator=member(1)
    sc=Organe.objects.create(version=version,type='SC',code='SC-IT',name='Transport',status='VALIDATED',source_reference='Recette')
    group=GroupeCible.objects.create(sc=sc,code='SC-IT-GT1',name='Groupe de recette',activity='PRODUCTION',source_reference='Recette')
    sender=expert_factory(user=user_factory(username='legal-sender'))
    post=PosteOrganisation.objects.create(organe=sc,code='LEGAL-SECRETARY',category='SECRETARIAT',title='Secrétaire',
        status='VALIDATED',source_reference='Recette')
    MandatOrganisation.objects.create(expert=sender,poste=post,function=post.title,status='ACTIVE',
        start_date=timezone.localdate(),appointment_reference='Recette')
    process=CTCProcessus.objects.create(norme=norme_factory())
    monkeypatch.setattr(STReceptionPiece._meta.get_field('file'),'storage',FileSystemStorage(location=tmp_path/'reception'))
    monkeypatch.setattr(STGEDFile._meta.get_field('file'),'storage',FileSystemStorage(location=tmp_path/'ged'))
    receipt=st_admin.save_reception(secretary,{'process_id':process.pk,'sc_id':sc.pk,'group_id':group.pk,
        'sender_id':sender.pk,'vote_date':timezone.localdate().isoformat(),'vote_percentage':80,'verified':True})
    st_admin.add_piece(secretary,receipt.pk,'PROJECT',pdf('projet.pdf','Projet de norme'))
    st_admin.add_piece(secretary,receipt.pk,'VOTE',pdf('vote.pdf','Preuve du vote'))
    st_admin.add_piece(secretary,receipt.pk,'REPORT',pdf('rapport.pdf','Rapport de revue SC'))
    receipt.refresh_from_db();st_admin.register_reception(secretary,receipt.pk,receipt.revision)
    ged_file=st_ged.upload(ged_writer,process.pk,pdf('ged.pdf','Document GED de recette'))
    return SimpleNamespace(**locals())


def opened(g, user=None):
    return st_legal.create_request(user or g.chief_a,g.process.pk,'Conformité du projet de norme',
        'Le projet respecte-t-il les règles de compétence et de forme ?','Sous-commission SC-IT','COURRIEL-2026-001')


@pytest.mark.django_db
def test_request_records_provenance_and_denies_other_posts(legal):
    g=legal
    entry=opened(g)
    assert entry.reference.startswith('AJ-') and entry.status==STLegalRequest.Status.OPEN
    log=AuditLog.objects.get(content_type='governance.STLegalRequest',changes__action='legal_request_opened')
    assert log.changes['reference']==entry.reference and log.user==g.chief_a
    with pytest.raises(PermissionDenied):
        st_legal.create_request(g.outsider,g.process.pk,'Sujet valide','Question suffisamment longue','Demandeur','Référence')
    with pytest.raises(ValidationError,match='Demandeur'):
        st_legal.create_request(g.chief_a,g.process.pk,'Sujet valide','Question suffisamment longue',' ','Référence')


@pytest.mark.django_db
def test_other_co_chief_confirms_and_opinion_reaches_dossier(legal):
    g=legal;entry=opened(g)
    opinion=st_legal.save_opinion(g.chief_a,entry.pk,'Le dossier est conforme sous réserve de la pièce jointe.','RESERVE',submit=True)
    assert opinion.status==STLegalOpinion.Status.SUBMITTED and opinion.submitted_at
    with pytest.raises(ValidationError,match='autre co-chef'):
        st_legal.decide_opinion(g.chief_a,opinion.pk,'CONFIRMED','Auto-confirmation interdite')
    st_legal.decide_opinion(g.chief_b,opinion.pk,'CONFIRMED','Contrôle indépendant effectué')
    opinion.refresh_from_db();entry.refresh_from_db()
    assert opinion.status==STLegalOpinion.Status.CONFIRMED and opinion.decided_by==g.chief_b
    assert entry.status==STLegalRequest.Status.ANSWERED
    assert AuditLog.objects.filter(content_type='governance.CTCProcessus',object_id=g.process.pk,
        changes__action='legal_opinion_confirmed').exists()


@pytest.mark.django_db
def test_returned_opinion_is_corrected_then_confirmed(legal):
    g=legal;entry=opened(g)
    opinion=st_legal.save_opinion(g.chief_a,entry.pk,'Première analyse à compléter.','COMPLEMENT',submit=True)
    st_legal.decide_opinion(g.chief_b,opinion.pk,'RETURNED','Joindre la motivation complète')
    opinion.refresh_from_db();assert opinion.status==STLegalOpinion.Status.RETURNED
    corrected=st_legal.save_opinion(g.chief_a,entry.pk,'Analyse complétée avec la motivation demandée.','FAVORABLE',submit=True)
    assert corrected.pk==opinion.pk and corrected.status==STLegalOpinion.Status.SUBMITTED
    st_legal.decide_opinion(g.chief_b,opinion.pk,'CONFIRMED','Version corrigée conforme')
    actions=list(AuditLog.objects.filter(content_type='governance.STLegalRequest',
        changes__action__in=['legal_opinion_returned','legal_opinion_confirmed']).values_list('changes__action',flat=True))
    assert 'legal_opinion_returned' in actions and 'legal_opinion_confirmed' in actions


@pytest.mark.django_db
def test_api_lists_dossiers_and_serves_private_pieces(legal,client):
    g=legal;entry=opened(g)
    client.force_login(g.chief_a)
    listing=client.get('/api/v1/st/legal/')
    assert listing.status_code==200
    payload=listing.json()
    assert payload['total']==1 and payload['processes'] and payload['kpis']['open']==1
    assert payload['statistics']['tomes'][0]['tome']=='Tome 1'
    piece=payload['results'][0]['pieces'][0]
    ged=payload['results'][0]['files'][0]
    assert client.get(piece['url']).status_code==200
    assert client.get(ged['url'])['Cache-Control']=='private, no-store'
    created=client.post('/api/v1/st/legal/requests/',{
        'process_id':g.process.pk,'subject':'Deuxième demande','question':'Question juridique complète',
        'requester_name':'Coordination','source_reference':'NOTE-002'},content_type='application/json')
    assert created.status_code==201 and created.json()['reference'].startswith('AJ-')
    client.force_login(g.outsider)
    assert client.get('/api/v1/st/legal/').status_code==403


@pytest.mark.django_db
def test_close_requires_answer_and_statistics_are_computed(legal,client):
    g=legal;entry=opened(g)
    with pytest.raises(ValidationError,match='répondue'):
        st_legal.close_request(g.chief_b,entry.pk)
    opinion=st_legal.save_opinion(g.chief_a,entry.pk,'Analyse juridique complète et motivée.','FAVORABLE',submit=True)
    st_legal.decide_opinion(g.chief_b,opinion.pk,'CONFIRMED','Conforme')
    closed=st_legal.close_request(g.chief_b,entry.pk)
    assert closed.status==STLegalRequest.Status.CLOSED and closed.closed_by==g.chief_b
    stats=st_legal.statistics(g.chief_a)
    assert stats['total']==1 and stats['closed']==1 and stats['confirmed']==1
    assert stats['tomes']==[{'tome':'Tome 1','count':1}]
    assert stats['average_days'] is not None
    client.force_login(g.chief_a)
    history=client.get('/api/v1/st/legal/history/').json()['results']
    assert any(row['action']=='legal_request_closed' for row in history)
