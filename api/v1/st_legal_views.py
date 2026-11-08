"""API des avis juridiques du pôle 3 : aucun effet sur la validation des normes."""
from django.core.exceptions import ValidationError
from django.http import FileResponse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.models import AuditLog
from apps.governance import st_legal as service
from apps.governance.st_ged import TOMES
from apps.governance.st_legal_models import STLegalOpinion, STLegalRequest
from .st_admin_views import AdminBase


class RequestInput(serializers.Serializer):
    process_id=serializers.IntegerField(min_value=1)
    subject=serializers.CharField(max_length=250)
    question=serializers.CharField(max_length=20000)
    requester_name=serializers.CharField(max_length=200)
    source_reference=serializers.CharField(max_length=200)
    due_date=serializers.DateField(required=False,allow_null=True)
    priority=serializers.ChoiceField(choices=STLegalRequest.Priority.choices,required=False,default='NORMAL')


class OpinionInput(serializers.Serializer):
    analysis=serializers.CharField(max_length=20000)
    recommendation=serializers.ChoiceField(choices=STLegalOpinion.Recommendation.choices)
    submit=serializers.BooleanField(required=False,default=False)


class DecisionInput(serializers.Serializer):
    decision=serializers.ChoiceField(choices=['CONFIRMED','RETURNED'])
    comment=serializers.CharField(max_length=5000)


def data_for(serializer_class, request):
    serializer=serializer_class(data=request.data);serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def user_name(user):
    return user.get_full_name() or user.username if user else 'Compte archivé'


def opinion_data(opinion, user):
    return {
        'id':opinion.pk,'author':user_name(opinion.author),'author_id':opinion.author_id,
        'analysis':opinion.analysis,'recommendation':opinion.recommendation,
        'recommendation_label':opinion.get_recommendation_display(),'status':opinion.status,
        'status_label':opinion.get_status_display(),'created_at':opinion.created_at.isoformat(),
        'submitted_at':opinion.submitted_at.isoformat() if opinion.submitted_at else None,
        'decided_at':opinion.decided_at.isoformat() if opinion.decided_at else None,
        'decided_by':user_name(opinion.decided_by),'decision_comment':opinion.decision_comment,
        'can_edit':opinion.author_id==user.pk and opinion.status in ('DRAFT','RETURNED'),
        'can_decide':opinion.status=='SUBMITTED' and opinion.author_id!=user.pk,
    }


def request_data(entry, user):
    receipt=getattr(entry.process,'administrative_reception',None)
    code=receipt.sc.code if receipt and receipt.sc_id else ''
    opinions=entry.opinions.select_related('author','decided_by').order_by('-pk')
    own=next((o for o in opinions if o.author_id==user.pk and o.status in ('DRAFT','RETURNED')),None)
    return {
        'id':entry.pk,'reference':entry.reference,'subject':entry.subject,'question':entry.question,
        'requester_name':entry.requester_name,'source_reference':entry.source_reference,
        'due_date':entry.due_date.isoformat() if entry.due_date else None,'priority':entry.priority,
        'status':entry.status,'status_label':entry.get_status_display(),
        'created_at':entry.created_at.isoformat(),'opened_by':user_name(entry.opened_by),
        'process_id':entry.process_id,'norme_id':entry.process.norme_id,
        'norme_reference':entry.process.norme.reference_number,'norme_title':entry.process.norme.title,
        'sc':code,'tome':TOMES.get(code),'dossier_url':f'/ctc/norme/{entry.process.norme_id}/lecture/',
        'files':[{'id':f.pk,'name':f.name,'size':f.size,'sha256':f.sha256,
            'author':user_name(f.author),'created_at':f.created_at.isoformat(),
            'url':f'/api/v1/st/legal/{entry.pk}/ged-files/{f.pk}/'}
            for f in entry.process.ged_files.select_related('author').order_by('-pk')],
        'pieces':[{'id':p.pk,'kind':p.kind,'name':p.original_name,'sha256':p.sha256,
            'url':f'/api/v1/st/legal/{entry.pk}/pieces/{p.pk}/'}
            for p in (receipt.pieces.order_by('pk') if receipt else [])],
        'opinions':[opinion_data(o,user) for o in opinions],
        'my_opinion_id':own.pk if own else None,
        'can_write':entry.status not in ('ANSWERED','CLOSED'),
        'can_close':entry.status=='ANSWERED',
        'overdue':bool(entry.due_date and entry.due_date<timezone.localdate()
                       and entry.status not in ('ANSWERED','CLOSED')),
    }


class STLegalViewSet(AdminBase):
    def list(self,request):
        service.actor(request.user)
        qs=service.requests(request.user).order_by('-created_at','-pk')
        rows=[request_data(entry,request.user) for entry in qs[:250]]
        stats=service.statistics(request.user)
        processes=service.legal_processes()[:300]
        return Response({
            'results':rows,'total':qs.count(),'user_id':request.user.pk,
            'can_write':True,'can_confirm':True,'limit':250,
            'kpis':{'open':stats['open']+stats['in_progress'],'pending':stats['pending_confirmation'],
                'confirmed':stats['confirmed'],'overdue':stats['overdue']},
            'statistics':stats,
            'processes':[{'id':p.pk,'reference':p.norme.reference_number,'title':p.norme.title,
                'sc':p.administrative_reception.sc.code if getattr(p,'administrative_reception',None) and p.administrative_reception.sc_id else '',
                'tome':TOMES.get(p.administrative_reception.sc.code) if getattr(p,'administrative_reception',None) and p.administrative_reception.sc_id else None}
                for p in processes],
            'processes_total':service.legal_processes().count(),
        })

    def retrieve(self,request,pk=None):
        return Response(request_data(service.requests(request.user).get(pk=pk),request.user))

    @action(detail=False,methods=['post'],url_path='requests')
    def open_request(self,request):
        entry=service.create_request(request.user,**data_for(RequestInput,request))
        return Response(request_data(service.requests(request.user).get(pk=entry.pk),request.user),status=201)

    @action(detail=True,methods=['post'])
    def opinions(self,request,pk=None):
        opinion=service.save_opinion(request.user,pk,**data_for(OpinionInput,request))
        return Response(opinion_data(opinion,request.user),status=201)

    @action(detail=False,methods=['post'],url_path=r'opinions/(?P<opinion_id>\d+)/decide')
    def decide(self,request,opinion_id=None):
        opinion=service.decide_opinion(request.user,opinion_id,**data_for(DecisionInput,request))
        return Response(opinion_data(opinion,request.user),status=200)

    @action(detail=True,methods=['post'])
    def close(self,request,pk=None):
        entry=service.close_request(request.user,pk)
        return Response({'id':entry.pk,'status':entry.status,'closed_at':entry.closed_at.isoformat()})

    @action(detail=True,methods=['get'],url_path=r'ged-files/(?P<file_id>\d+)')
    def download_ged(self,request,pk=None,file_id=None):
        file=service.ged_file(request.user,pk,file_id)
        try:response=FileResponse(file.file.open('rb'),as_attachment=True,filename=file.name)
        except OSError as exc:raise ValidationError('Fichier privé introuvable.') from exc
        response['Cache-Control']='private, no-store'
        return response

    @action(detail=True,methods=['get'],url_path=r'pieces/(?P<piece_id>\d+)')
    def download_piece(self,request,pk=None,piece_id=None):
        piece=service.reception_piece(request.user,pk,piece_id)
        try:response=FileResponse(piece.file.open('rb'),as_attachment=True,filename=piece.original_name)
        except OSError as exc:raise ValidationError('Pièce de réception introuvable.') from exc
        response['Cache-Control']='private, no-store'
        return response

    @action(detail=False,methods=['get'])
    def history(self,request):
        service.actor(request.user)
        qs=AuditLog.objects.filter(content_type='governance.STLegalRequest',
            changes__scope='ctc_legal').select_related('user').order_by('-timestamp')
        return Response({'results':[{'date':e.timestamp,'author':user_name(e.user),
            'reference':e.object_repr,'action':e.changes.get('action'),
            'comment':e.changes.get('comment',''),'recommendation':e.changes.get('recommendation',''),
            'decided_by':e.changes.get('decided_by')} for e in qs[:200]]})
