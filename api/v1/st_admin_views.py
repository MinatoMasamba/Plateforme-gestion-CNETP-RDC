"""API administrative poste 6 : réception, accusés et secrétariat de séance."""
import csv
import io
from xml.sax.saxutils import escape
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.governance import st_admin as service
from apps.governance.st_admin_models import STReceptionPiece, STPVVersion
from apps.governance.st_permissions import visible_meetings
from apps.governance.st_spaces import space_context
from apps.governance.st_matrix import mandate_capabilities
from apps.governance.models import CTCProcessus, Organe, GroupeCible
from apps.core.models import AuditLog
from apps.meetings.models import ProcessusVerbaux


def serialize_reception(r):
    return {'id':r.pk,'reference':r.reference,'state':r.state,'revision':r.revision,
        'process_id':r.process_id,'norme':r.process.norme.reference_number,'title':r.process.norme.title,
        'sc_id':r.sc_id,'group_id':r.group_id,'sender_id':r.sender_id,'vote_date':str(r.vote_date) if r.vote_date else '',
        'vote_percentage':str(r.vote_percentage) if r.vote_percentage is not None else '',
        'observations':r.observations,'verified':r.verified,'received_at':r.received_at,
        'report_received':bool(r.process.sc_report_received_at),
        'pieces':[{'id':p.pk,'kind':p.kind,'name':p.original_name,'sha256':p.sha256} for p in r.pieces.all()]}


class AdminBase(viewsets.ViewSet):
    permission_classes=[IsAuthenticated]

    def handle_exception(self, exc):
        if isinstance(exc,ValidationError):
            return Response({'detail':exc.messages},status=409 if getattr(exc,'code',None)=='conflict' else 400)
        if isinstance(exc,ObjectDoesNotExist):
            return Response({'detail':'Objet absent du périmètre autorisé.'},status=404)
        return super().handle_exception(exc)


class ReceptionInput(serializers.Serializer):
    process_id=serializers.IntegerField(min_value=1,required=False)
    revision=serializers.IntegerField(min_value=0,required=False)
    sc_id=serializers.IntegerField(min_value=1,required=False)
    group_id=serializers.IntegerField(min_value=1,required=False)
    sender_id=serializers.IntegerField(min_value=1,required=False)
    vote_date=serializers.DateField(required=False)
    vote_percentage=serializers.DecimalField(max_digits=5,decimal_places=2,min_value=0,max_value=100,required=False)
    observations=serializers.CharField(max_length=10000,allow_blank=True,required=False)
    verified=serializers.BooleanField(required=False)
    anomaly=serializers.BooleanField(required=False)


class STReceptionViewSet(AdminBase):
    def list(self,request):
        qs=service.readable_receptions(request.user).select_related('process__norme').prefetch_related('pieces')
        return Response({'results':[serialize_reception(r) for r in qs.order_by('-updated_at')[:100]]})

    def retrieve(self,request,pk=None):
        return Response(serialize_reception(get_object_or_404(service.readable_receptions(request.user),pk=pk)))

    def create(self,request):
        serializer=ReceptionInput(data=request.data);serializer.is_valid(raise_exception=True)
        values=dict(serializer.validated_data)
        if values.get('vote_date'):values['vote_date']=values['vote_date'].isoformat()
        r=service.save_reception(request.user,values)
        return Response(serialize_reception(r),status=201)

    @action(detail=True,methods=['post'])
    def revise(self,request,pk=None):
        serializer=ReceptionInput(data=request.data);serializer.is_valid(raise_exception=True)
        values=dict(serializer.validated_data)
        if values.get('vote_date'):values['vote_date']=values['vote_date'].isoformat()
        return Response(serialize_reception(service.save_reception(request.user,values,pk)))

    @action(detail=True,methods=['post'])
    def register(self,request,pk=None):
        revision=serializers.IntegerField(min_value=0).run_validation(request.data.get('revision'))
        return Response(serialize_reception(service.register_reception(request.user,pk,revision)))

    @action(detail=True,methods=['post'])
    def pieces(self,request,pk=None):
        service.add_piece(request.user,pk,request.data.get('kind'),request.FILES.get('file'))
        return self.retrieve(request,pk)

    @action(detail=True,methods=['get'],url_path='piece/(?P<piece_id>[^/.]+)')
    def download_piece(self,request,pk=None,piece_id=None):
        r=get_object_or_404(service.readable_receptions(request.user),pk=pk)
        p=get_object_or_404(STReceptionPiece,reception=r,pk=piece_id)
        inline=str(request.query_params.get('inline','')).lower() in ('1','true','yes')
        response=FileResponse(p.file.open('rb'),as_attachment=not inline,filename=p.original_name)
        response['Cache-Control']='private, no-store'
        if inline:
            response['X-Frame-Options']='SAMEORIGIN'
        return response

    @action(detail=True,methods=['get'])
    def acknowledgement(self,request,pk=None):
        r=get_object_or_404(service.readable_receptions(request.user),pk=pk,state='ENREGISTREE')
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        output=io.BytesIO();styles=getSampleStyleSheet();s=r.snapshot
        texts=['RÉPUBLIQUE DÉMOCRATIQUE DU CONGO','CNE-ITP — Secrétariat technique','ACCUSÉ DE RÉCEPTION ADMINISTRATIVE',s['reference'],s['norme']+' — '+s['title'],
               'Origine : '+s['sc']+' / '+s['group'],'Vote du '+s['vote_date']+' : '+s['vote_percentage']+' %',
               'Réception : '+s['received_at'],'Agent : '+s['agent'],'Expéditeur : '+s['sender'],
               'Cet accusé constate une réception administrative. Il ne vaut ni indexation, ni approbation technique, ni validation de la norme.']
        texts+=['Pièce : '+p['original_name']+' — SHA256 '+p['sha256'] for p in s['pieces']]
        story=[]
        for i,t in enumerate(texts):story.extend([Paragraph(escape(t),styles['Heading1'] if i==2 else styles['Normal']),Spacer(1,12)])
        SimpleDocTemplate(output,title=s['reference']).build(story)
        response=HttpResponse(output.getvalue(),content_type='application/pdf');response['Content-Disposition']=f'inline; filename="{r.reference}.pdf"';response['Cache-Control']='private, no-store'
        return response

    @action(detail=True,methods=['get'])
    def history(self,request,pk=None):
        r=get_object_or_404(service.readable_receptions(request.user),pk=pk)
        return Response({'results':list(AuditLog.objects.filter(content_type='governance.STReception',object_id=r.pk).values('timestamp','action','changes'))})

    @action(detail=True,methods=['post'])
    def rectify(self,request,pk=None):
        service.secretary(request.user);service.writable()
        r=get_object_or_404(service.readable_receptions(request.user),pk=pk,state='ENREGISTREE')
        comment=serializers.CharField(max_length=10000).run_validation(request.data.get('comment'))
        service.event(request.user,r,'rectification',comment=comment)
        return Response({'detail':'Rectification ajoutée à l’historique ; accusé original conservé.'})

    @action(detail=False,methods=['get'])
    def catalogue(self,request):
        service.secretary(request.user)
        from apps.governance.models import MandatOrganisation
        from django.utils import timezone
        from django.db.models import Q
        today=timezone.localdate()
        senders=MandatOrganisation.objects.filter(status='ACTIVE',capacity='ORGANISATION',poste__organe__type='SC',expert__status='ACTIVE',expert__user__is_active=True).filter(Q(start_date__isnull=True)|Q(start_date__lte=today)).filter(Q(end_date__isnull=True)|Q(end_date__gte=today))
        return Response({'today':today.isoformat(),'processes':list(CTCProcessus.objects.filter(current_stage='RECEPTION',norme__circuit_version='LEGACY',received_at__isnull=True).values('id','norme__title','norme__reference_number')),
            'scs':list(Organe.objects.filter(type='SC',status__in=['VALIDATED','ACTIVE']).values('id','code','name','version_id')),
            'groups':list(GroupeCible.objects.filter(sc__status__in=['VALIDATED','ACTIVE']).values('id','sc_id','name','code')),
            'senders':[{'id':m.expert_id,'name':m.expert.full_name,'sc_id':m.poste.organe_id} for m in senders.select_related('expert__user','poste__organe')]})

    @action(detail=False,methods=['get'])
    def export(self,request):
        output=io.StringIO();writer=csv.writer(output,delimiter=';');writer.writerow(['Référence','Norme','État','Réception','Rapport reçu'])
        def cell(value):
            text=str(value or '');return "'"+text if text.startswith(('=','+','-','@','\t','\r')) else text
        for r in service.readable_receptions(request.user).select_related('process__norme').iterator():
            writer.writerow([cell(x) for x in [r.reference,r.process.norme.reference_number,r.state,r.received_at,bool(r.process.sc_report_received_at)]])
        response=HttpResponse('\ufeff'+output.getvalue(),content_type='text/csv; charset=utf-8');response['Content-Disposition']='attachment; filename="registre-receptions.csv"'
        return response

    @action(detail=False,methods=['get'])
    def decisions(self,request):
        service.secretary(request.user)
        from apps.governance.models import CTCOperationalRequest
        results=[]
        for row in CTCOperationalRequest.objects.exclude(status='PENDING').select_related('reviewed_by__user').order_by('-reviewed_at')[:100]:
            results.append({'reference':f'DEM-{row.pk}','source':'Demande opérationnelle','text':row.review_comment,
                'state':row.status,'author':row.reviewed_by.full_name if row.reviewed_by else 'Auteur non renseigné','date':row.reviewed_at})
        # Événements d'origine : aucune copie éditable des décisions normatives.
        for log in AuditLog.objects.filter(content_type='CTCProcessus',changes__action__in=['validate','return']).select_related('user').order_by('-timestamp')[:100]:
            results.append({'reference':f'JRN-{log.pk}','source':'Décision de la coordination','text':(log.changes or {}).get('comment',''),
                'state':(log.changes or {}).get('action',''),'author':log.user.get_full_name() or log.user.username if log.user else 'Auteur non renseigné','date':log.timestamp})
        return Response({'results':sorted(results,key=lambda row:row['date'].isoformat() if row['date'] else '',reverse=True),
                         'note':'Lecture seule depuis les modules d’origine ; aucune décision n’est modifiable ici.'})


class STPVViewSet(AdminBase):
    def accessible(self,user):
        mandate=service.secretary(user)
        ctx={**mandate_capabilities(mandate),**space_context(mandate.poste),'poste':mandate.poste,'ctc_pole':mandate.poste.organe.code}
        return visible_meetings(mandate.expert,ctx)

    def list(self,request):
        meetings=self.accessible(request.user).select_related('pv').prefetch_related('participants__expert__user','presences__expert__user')
        results=[]
        for meeting in meetings[:100]:
            pv=getattr(meeting,'pv',None);v=pv.administrative_versions.first() if pv else None
            results.append({'meeting_id':meeting.pk,'title':meeting.titre,'date':meeting.date,'place':meeting.lieu,'agenda':meeting.ordre_jour,
                'participants':[{'name':p.expert.full_name,'role':p.get_role_display()} for p in meeting.participants.all()],
                'presences':[{'name':p.expert.full_name,'status':p.status} for p in meeting.presences.all()],
                'pv_id':pv.pk if pv else None,'revision':v.number if v else 0,'state':v.state if v else 'BROUILLON',
                'content':v.content if v else (pv.contenu if pv else ''),'decisions':v.decisions if v else []})
        return Response({'results':results,'validation_note':'Le validateur officiel doit être défini par type de séance. Aucune approbation automatique.'})

    def retrieve(self,request,pk=None):
        pv=get_object_or_404(ProcessusVerbaux,reunion__in=self.accessible(request.user),pk=pk)
        return Response({'pv_id':pv.pk,'versions':[{'number':v.number,'state':v.state,'content':v.content,
            'decisions':v.decisions,'meeting':v.meeting_snapshot,'author_id':v.author_id,'created_at':v.created_at}
            for v in pv.administrative_versions.all()]})

    @action(detail=True,methods=['get'])
    def export(self,request,pk=None):
        pv=get_object_or_404(ProcessusVerbaux,reunion__in=self.accessible(request.user),pk=pk)
        version=serializers.IntegerField(min_value=1).run_validation(request.query_params.get('revision'))
        v=get_object_or_404(STPVVersion,pv=pv,number=version)
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        output=io.BytesIO();styles=getSampleStyleSheet();snapshot=v.meeting_snapshot
        texts=['CNE-ITP — Secrétariat technique','PROCÈS-VERBAL — VERSION DE TRAVAIL',
            f'{v.title} — version {v.number} — {v.state}',
            'Document non approuvé officiellement. Autorité de validation à définir selon le type de séance.',
            'Date : '+str(snapshot.get('date','')),'Lieu : '+str(snapshot.get('place','')),
            'Ordre du jour : '+str(snapshot.get('agenda','')),
            'Invitations : '+str(snapshot.get('participants',[])),
            'Présences constatées : '+str(snapshot.get('presences',[])),v.content]
        texts+=['Décision préparée : '+str(d) for d in v.decisions]
        story=[]
        for text in texts:story.extend([Paragraph(escape(text).replace('\n','<br/>'),styles['Normal']),Spacer(1,12)])
        SimpleDocTemplate(output,title=f'PV-{pv.pk}-v{v.number}').build(story)
        response=HttpResponse(output.getvalue(),content_type='application/pdf');response['Content-Disposition']=f'inline; filename="PV-{pv.pk}-v{v.number}-travail.pdf"';response['Cache-Control']='private, no-store'
        return response

    @transaction.atomic
    def create(self,request):
        service.writable()
        class Input(serializers.Serializer):
            meeting_id=serializers.IntegerField(min_value=1)
            revision=serializers.IntegerField(min_value=0)
            content=serializers.CharField(max_length=100000)
            decisions=serializers.ListField(child=serializers.DictField(),max_length=50,default=list)
            submit=serializers.BooleanField(default=False)
        serializer=Input(data=request.data);serializer.is_valid(raise_exception=True);d=serializer.validated_data
        meeting=get_object_or_404(self.accessible(request.user).select_for_update(),pk=d['meeting_id'])
        pv,_=ProcessusVerbaux.objects.get_or_create(reunion=meeting,defaults={'titre':'PV — '+meeting.titre,'contenu':''})
        pv=ProcessusVerbaux.objects.select_for_update().get(pk=pv.pk)
        if pv.redaction=='VALIDE' or pv.signature_date:
            raise ValidationError('PV officiel existant : rectification soumise au circuit compétent.')
        last=pv.administrative_versions.first()
        if (last.number if last else 0)!=d['revision']:raise ValidationError('Version obsolète.',code='conflict')
        if last and last.state=='A_VALIDER':raise ValidationError('Version soumise figée ; circuit de correction officiel à définir.')
        for decision in d['decisions']:
            if not set(decision)<= {'text','responsible','due_date','norme_id'} or not str(decision.get('text','')).strip():
                raise ValidationError('Décision : texte obligatoire ; responsable, échéance et norme facultatifs à préciser.')
        snapshot={'date':meeting.date.isoformat(),'place':meeting.lieu,'agenda':meeting.ordre_jour,
            'participants':[{'expert_id':p.expert_id,'name':p.expert.full_name,'role':p.role} for p in meeting.participants.select_related('expert__user')],
            'presences':[{'expert_id':p.expert_id,'status':p.status,'marked_at':p.marked_at.isoformat() if p.marked_at else None} for p in meeting.presences.all()]}
        v=STPVVersion.objects.create(pv=pv,number=d['revision']+1,state='A_VALIDER' if d['submit'] else 'BROUILLON',title=pv.titre,content=d['content'],decisions=d['decisions'],meeting_snapshot=snapshot,author=request.user)
        pv.contenu=v.content;pv.decisions='\n'.join(str(x['text']) for x in v.decisions);pv.save(update_fields=['contenu','decisions'])
        AuditLog.objects.create(user=request.user,action='CREATE',content_type='governance.STPVVersion',object_id=v.pk,object_repr=pv.titre,changes={'scope':'ctc','pv_id':pv.pk,'revision':v.number,'state':v.state})
        return Response({'pv_id':pv.pk,'revision':v.number,'state':v.state,'detail':'Version figée ; validateur officiel à désigner.' if d['submit'] else 'Brouillon versionné enregistré.'},status=201)
