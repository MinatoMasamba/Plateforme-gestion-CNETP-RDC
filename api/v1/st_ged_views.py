"""API session GED : aucune validation normative attribuée au poste 11."""
import difflib
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from apps.core.models import AuditLog, User
from apps.governance import st_ged as service
from apps.governance.models import MandatOrganisation, Organe
from apps.governance.phoenix_models import GroupeCible
from apps.governance.st_ged_models import STGEDAnomaly, STGEDCode, STGEDFile, STGEDIndexation
from apps.norms.diff_utils import build_inline_diff_segments
from apps.norms.models import NormeVersion
from .norms.serializers import NormeVersionSerializer
from .st_admin_views import AdminBase

TOMES=service.TOMES


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError('Période invalide.') from exc


class IndexInput(serializers.Serializer):
    code_id=serializers.IntegerField(min_value=1)
    source_id=serializers.IntegerField(min_value=1)
    base_version_id=serializers.IntegerField(min_value=0)
    verified=serializers.BooleanField()
    observation=serializers.CharField(max_length=10000,allow_blank=True,required=False,default='')
    restore_id=serializers.IntegerField(min_value=1,required=False,allow_null=True)
    metadata=serializers.DictField(required=False,child=serializers.CharField(allow_blank=True,trim_whitespace=True,max_length=1000))


class CodeInput(serializers.Serializer):
    process_id=serializers.IntegerField(min_value=1)
    sc_id=serializers.IntegerField(min_value=1)
    code=serializers.CharField(max_length=80)
    source_reference=serializers.CharField(max_length=500)


class AnomalyInput(serializers.Serializer):
    comment=serializers.CharField(max_length=10000)
    resolve_id=serializers.IntegerField(min_value=1,required=False,allow_null=True)
    kind=serializers.ChoiceField(choices=[choice[0] for choice in STGEDAnomaly.KIND_CHOICES],required=False,default='INCONSISTENT')
    recipient_id=serializers.IntegerField(min_value=1,required=False,allow_null=True)


class ConfirmationInput(serializers.Serializer):
    indexation_id=serializers.IntegerField(min_value=1)
    decision=serializers.ChoiceField(choices=['CONFIRMED','RETURNED'])
    comment=serializers.CharField(max_length=10000)


def data_for(serializer_class, request):
    serializer=serializer_class(data=request.data);serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _row_date(row):
    value = row.get('received_at')
    if not value:
        return None
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return value.date() if hasattr(value, 'date') else value


def _queue_state(row):
    latest = row.get('latest')
    confirmation = latest.get('confirmation') if latest else None
    if confirmation:
        return 'CONFIRMED' if confirmation['decision'] == 'CONFIRMED' else 'CORRECTION'
    if latest:
        return 'INDEXED'
    if row.get('received_at') and not row.get('report_at'):
        return 'REPORT'
    if row.get('state') == 'BLOCKED':
        return 'BLOCKED'
    return 'READY'


def file_data(file):
    return {'id':file.pk,'name':file.name,'size':file.size,'sha256':file.sha256,
        'author':file.author.get_full_name() or file.author.username,
        'created_at':file.created_at.isoformat(),
        'url':f'/api/v1/st/ged/{file.process_id}/files/{file.pk}/'}


def index_data(entry):
    confirmation=getattr(entry,'confirmation',None)
    return {'id':entry.pk,'number':entry.version.version_number,'code':entry.code.code,'code_id':entry.code_id,
        'version_id':entry.version_id,'process_id':entry.process_id,'sc':entry.sc.code,'tome':TOMES.get(entry.sc.code),
        'group':entry.group.code,'source':file_data(entry.source),'report_id':entry.report_id,
        'author':entry.author.get_full_name() or entry.author.username,'created_at':entry.created_at.isoformat(),
        'observation':entry.observation,'metadata':entry.metadata,'restored_from':entry.restored_from_id,
        'confirmation':{'decision':confirmation.decision,'comment':confirmation.comment,
            'author':confirmation.author.get_full_name() or confirmation.author.username,'date':confirmation.created_at.isoformat()} if confirmation else None}


def process_data(process,user,readable_ids=None):
    receipt=getattr(process,'administrative_reception',None);report=service.report_for(process)
    last=process.norme.versions.order_by('-version_number').first()
    entries=process.ged_indexations.select_related('version','code','sc','group','source__author','author','confirmation__author').order_by('-version__version_number')
    latest=entries.first()
    reasons=service.blockers(process)
    admissibility=process.sc_report_received_at or process.received_at
    age_days=(timezone.now()-admissibility).total_seconds()/86400 if admissibility else None
    return {'id':process.pk,'norme_id':process.norme_id,'reference':process.norme.reference_number,
        'title':process.norme.title,'received_at':process.received_at,'report_at':process.sc_report_received_at,
        'admissibility':admissibility,'age_days':round(age_days,1) if age_days is not None else None,
        'dossier_readable':process.pk in readable_ids if readable_ids is not None else service.dossier_readable(user,process),
        'sc_id':receipt.sc_id if receipt else None,'sc':receipt.sc.code if receipt and receipt.sc_id else '',
        'tome':TOMES.get(receipt.sc.code) if receipt and receipt.sc_id else None,
        'group':receipt.group.code if receipt and receipt.group_id else '',
        'sender':receipt.sender.full_name if receipt and receipt.sender_id else '',
        'vote_date':receipt.vote_date if receipt else None,
        'report':{'id':report.pk,'name':report.original_name,'size':report.file.size if report.file else 0,
            'url':f'/api/v1/st/receptions/{receipt.pk}/piece/{report.pk}/'} if report else None,
        'report_present':bool(report),
        'pv_present':bool(receipt and receipt.pieces.filter(kind='VOTE').exists()),
        'indexed_at':process.indexed_at,'intake_validated_at':process.intake_validated_at,'stage':process.current_stage,'base_version_id':last.pk if last else 0,
        'next_version':last.version_number+1 if last else 1,
        'version_count':process.norme.versions.count(),
        'blockers':reasons,'state':'BLOCKED' if reasons else ('CORRECTION' if latest and getattr(latest,'confirmation',None) and latest.confirmation.decision=='RETURNED' else ('INDEXED' if latest else 'READY')),
        'latest':index_data(latest) if latest else None,
        'files':[file_data(f) for f in process.ged_files.select_related('author').order_by('-pk')],
        'versions':[index_data(e) for e in entries],
        'visibility':bool(process.received_at),
        'eligible':not reasons,
        'indexed':bool(latest),
        'report_status':('available' if report else ('awaited' if process.received_at else '')),
        'anomalies':[{'id':a.pk,'comment':a.comment,'author':a.author.get_full_name() or a.author.username,
            'kind':a.kind,'kind_label':a.get_kind_display(),'status':a.status,'status_label':a.status_label,
            'recipient':(a.recipient.get_full_name() or a.recipient.username) if a.recipient_id else '',
            'date':a.created_at,'age_days':round((timezone.now()-a.created_at).total_seconds()/86400,1),
            'resolved_at':a.resolved_at,'resolution':a.resolution}
            for a in process.ged_anomalies.select_related('author','recipient').order_by('-pk')]}


class STGEDViewSet(AdminBase):
    lookup_value_regex=r'\d+'

    @action(detail=False, methods=['get'], url_path='received-norms')
    def received_norms(self, request):
        qs = service.received_processes(request.user).annotate(
            versions_count=Count('norme__versions', distinct=True)).order_by('-received_at', '-pk')
        page = Paginator(qs, 100).get_page(request.query_params.get('page', 1))
        rows = []
        for process in page:
            receipt = getattr(process, 'administrative_reception', None)
            rows.append({'id': process.pk, 'reference': process.norme.reference_number,
                         'title': process.norme.title, 'received_at': process.received_at,
                         'sc': receipt.sc.code if receipt and receipt.sc_id else '',
                         'version_count': process.versions_count})
        return Response({'results': rows, 'count': page.paginator.count,
                         'next': page.next_page_number() if page.has_next() else None})
    def handle_exception(self, exc):
        if isinstance(exc, IntegrityError):
            return Response({'detail':'Cette référence ou cette version existe déjà. Actualisez avant de recommencer.'}, status=409)
        return super().handle_exception(exc)

    def list(self, request):
        mandate=service.actor(request.user)
        try:
            days=int(request.query_params.get('days','30'))
        except (TypeError, ValueError):
            days=30
        days=max(1,min(days,365))
        date_from=_parse_date(request.query_params.get('date_from'))
        date_to=_parse_date(request.query_params.get('date_to'))
        qs=service.processes(request.user).order_by('-updated_at')
        scoped=list(qs[:250])
        readable_ids=set(service.dossier_processes(request.user).filter(pk__in=[p.pk for p in scoped]).values_list('pk',flat=True))
        results=[process_data(p,request.user,readable_ids) for p in scoped]
        ids=[p['id'] for p in results]
        codes=STGEDCode.objects.filter(norme__ctc_processus__id__in=ids).select_related('approved_by')
        pending=sum(bool(p['latest'] and not p['latest']['confirmation']) for p in results)
        versions_todo=sum(bool(p['latest'] and (not p['latest']['confirmation'] or p['latest']['confirmation']['decision']=='RETURNED')) for p in results)
        statistics=service.statistics(request.user,days)
        sc_activity=service.sc_activity(request.user,days,date_from,date_to)
        pipeline_upstream=service.pipeline_upstream(request.user)
        pipeline_downstream=service.pipeline_downstream(request.user)
        codification=service.codification_analysis(request.user)
        cutoff=timezone.localdate()-timedelta(days=14)
        waiting_report=sum(bool(p['received_at'] and not p['report_at']) for p in results)
        overdue_14=sum(bool(p['received_at'] and not p['report_at'] and p['vote_date'] and p['vote_date']<cutoff) for p in results)
        oldest=sorted((p for p in results if p['state']=='READY'),
            key=lambda p:(p['report_at'] or p['received_at'] or timezone.now()))[:5]
        activity_qs=AuditLog.objects.filter(Q(content_type='CTCProcessus',changes__subsystem='GED') | Q(content_type='governance.STGEDIndexation'))
        if mandate.poste.code=='ST-V3-11':
            activity_qs=activity_qs.filter(user=request.user)
        activity=[{'date':e.timestamp,'author':e.user.get_full_name() or e.user.username if e.user else 'Compte archivé',
            'reference':e.object_repr,'action':e.changes.get('action'),'comment':e.changes.get('comment',''),
            'code':e.changes.get('code',''),'version':e.changes.get('version')} for e in activity_qs.select_related('user')[:8]]
        tome_count={};tome_missing={}
        for p in results:
            label=service.tome_label(p['sc']) if p['sc'] else 'SC à renseigner'
            tome_count[label]=tome_count.get(label,0)+1
            if p['state'] in ('READY','BLOCKED') and any('Rapport de revue' in b for b in p['blockers']):
                tome_missing[label]=tome_missing.get(label,0)+1
        tomes=[{'tome':label,'count':tome_count[label],'missing_report':tome_missing.get(label,0)} for label in sorted(tome_count)]
        versions_queue=[];anomalies=[]
        for p in results:
            latest=p['latest']
            if latest and (not latest['confirmation'] or latest['confirmation']['decision']=='RETURNED'):
                versions_queue.append({'id':latest['id'],'process_id':p['id'],'reference':p['reference'],'title':p['title'],
                    'sc':p['sc'],'tome':p['tome'],'group':p['group'],'code':latest['code'],
                    'version':latest['number'],'created_at':latest['created_at'],'author':latest['author'],
                    'state':p['state'],'age_days':p['age_days'],'confirmation':latest['confirmation'],
                    'dossier_readable':p['dossier_readable']})
            for a in p['anomalies']:
                anomalies.append({**a,'process_id':p['id'],'reference':p['reference'],'title':p['title']})
        anomalies.sort(key=lambda a:a['date'],reverse=True)
        recipients={}
        for row in MandatOrganisation.objects.filter(status='ACTIVE',expert__status='ACTIVE',
                expert__user__is_active=True).select_related('expert__user','poste').order_by('poste__code'):
            user=row.expert.user
            recipients.setdefault(user.pk,{'id':user.pk,'name':user.get_full_name() or user.username,
                'poste':row.poste.code,'title':row.poste.title})
        return Response({'results':results,'total':qs.count(),'limit':250,'head':mandate.poste.code=='ST-V3-10',
            'can_write':mandate.poste.code in ('ST-V3-10','ST-V3-11'),
            'kpis':{'ready':sum(p['state']=='READY' for p in results), 'blocked':sum(p['state'] in ('BLOCKED','CORRECTION') for p in results),
                'indexed':sum(bool(p['latest']) for p in results),'pending':pending,
                'versions_todo':versions_todo,
                'anomalies':sum(1 for a in anomalies if not a['resolved_at']),
                'waiting_report':waiting_report,'overdue_14':overdue_14,
                'confirmed_period':statistics['confirmed_period'],
                'median_delay_days':statistics['median_delay_days']},
            'oldest':[{'id':p['id'],'reference':p['reference'],'title':p['title'],'sc':p['sc'],
                'tome':p['tome'],'admissibility':p['report_at'] or p['received_at'],'age_days':p['age_days']} for p in oldest],
            'versions_todo':versions_queue,'anomalies':anomalies,
            'activity':activity,'tomes':tomes,'updated_at':timezone.now(),
            'codes':[{'id':c.pk,'code':c.code,'norme_id':c.norme_id,'sc_id':c.sc_id,
                'source_reference':c.source_reference,'author':c.approved_by.get_full_name() or c.approved_by.username} for c in codes],
            'scs':list(Organe.objects.filter(type='SC',status__in=['VALIDATED','ACTIVE']).values('id','code','name','official_name')),
            'nomenclature':[{'sc':code,'tome':number,'label':f'Tome {number}'} for code,number in TOMES.items()],
            'recipients':sorted(recipients.values(),key=lambda r:(r['poste'],r['name'])),
            'statistics':statistics,
            'sc_activity':sc_activity,
            'pipeline_upstream':pipeline_upstream,
            'pipeline_downstream':pipeline_downstream,
            'codification_analysis':codification})

    @action(detail=False, methods=['get'])
    def queue(self, request):
        """File du poste 11 : visibilité dès la réception, filtres et comptes réels."""
        user = request.user
        service.actor(user)
        scoped = list(service.processes(user).order_by('-updated_at')[:500])
        readable = set(service.dossier_processes(user).filter(
            pk__in=[p.pk for p in scoped]).values_list('pk', flat=True))
        rows = [process_data(p, user, readable) for p in scoped]
        for row in rows:
            row['queue_state'] = _queue_state(row)
        categories = ('READY', 'REPORT', 'BLOCKED', 'CORRECTION', 'INDEXED', 'CONFIRMED')
        counts = {key: sum(1 for row in rows if row['queue_state'] == key) for key in categories}
        counts['total'] = len(rows)
        counts['ANOMALY'] = sum(1 for row in rows if any(not a['resolved_at'] for a in row['anomalies']))
        states = [key for key in (request.query_params.get('states') or '').split(',') if key in categories]
        sc = (request.query_params.get('sc') or '').strip()
        group = (request.query_params.get('group') or '').strip()
        report = (request.query_params.get('report') or '').strip()
        anomaly = request.query_params.get('anomaly') in ('1', 'true', 'on')
        query = (request.query_params.get('q') or '').strip().lower()
        date_from = _parse_date(request.query_params.get('date_from'))
        date_to = _parse_date(request.query_params.get('date_to'))
        result = rows
        if states:
            result = [row for row in result if row['queue_state'] in states]
        if sc:
            result = [row for row in result if row['sc'] == sc]
        if group:
            result = [row for row in result if row['group'] == group]
        if report == 'received':
            result = [row for row in result if row['report_at']]
        elif report == 'awaited':
            result = [row for row in result if row['received_at'] and not row['report_at']]
        if anomaly:
            result = [row for row in result if any(not a['resolved_at'] for a in row['anomalies'])]
        if date_from:
            result = [row for row in result if _row_date(row) and _row_date(row) >= date_from]
        if date_to:
            result = [row for row in result if _row_date(row) and _row_date(row) <= date_to]
        if query:
            result = [row for row in result if query in ' '.join(filter(None, (
                row['reference'], row['title'], row['sc'], row['group'],
                (row['latest'] or {}).get('code', '')))).lower()]
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = min(100, max(10, int(request.query_params.get('page_size', 50))))
        except (TypeError, ValueError):
            page_size = 50
        total = len(result)
        start = (page - 1) * page_size
        scs = [{'code': organe.code, 'name': organe.official_name or organe.name,
                'tome': TOMES.get(organe.code), 'tome_label': service.tome_label(organe.code)}
               for organe in Organe.objects.filter(type='SC', status__in=['VALIDATED', 'ACTIVE']).order_by('code')]
        groups = [{'code': item.code, 'name': item.name, 'sc': item.sc.code}
                  for item in GroupeCible.objects.filter(
                      sc__type='SC', sc__status__in=['VALIDATED', 'ACTIVE']).select_related('sc').order_by('code')]
        return Response({'results': result[start:start + page_size], 'total': total,
                         'counts': counts, 'scs': scs, 'groups': groups,
                         'page': page, 'page_size': page_size, 'states': states})

    def retrieve(self, request, pk=None):
        return Response(process_data(service.processes(request.user).get(pk=pk),request.user))

    @action(detail=True,methods=['post'])
    def files(self, request, pk=None):
        result=service.upload(request.user,pk,request.FILES.get('file'))
        return Response(file_data(result),status=201)

    @action(detail=True,methods=['get'],url_path=r'files/(?P<file_id>\d+)')
    def download(self,request,pk=None,file_id=None):
        process=service.processes(request.user).get(pk=pk)
        file=STGEDFile.objects.get(pk=file_id,process=process)
        inline=str(request.query_params.get('inline','')).lower() in ('1','true','yes')
        try:
            response=FileResponse(file.file.open('rb'),as_attachment=not inline,filename=file.name)
        except OSError as exc:
            raise ValidationError('Fichier privé introuvable.') from exc
        response['Cache-Control']='private, no-store'
        if inline:
            response['Content-Disposition']=f'inline; filename="{file.name}"'
            lower=file.name.lower()
            if lower.endswith('.pdf'):
                response['Content-Type']='application/pdf'
            elif lower.endswith('.png'):
                response['Content-Type']='image/png'
            elif lower.endswith(('.jpg','.jpeg')):
                response['Content-Type']='image/jpeg'
            response['X-Frame-Options']='SAMEORIGIN'
        return response

    @action(detail=True,methods=['post'])
    def index(self,request,pk=None):
        result=service.index(request.user,pk,**data_for(IndexInput,request))
        return Response(index_data(result),status=201)

    @action(detail=True,methods=['get'],url_path='code-check')
    def code_check(self,request,pk=None):
        try:
            code_id=int(request.query_params.get('code_id',''))
        except (TypeError, ValueError) as exc:
            raise ValidationError('Code documentaire invalide.') from exc
        used=STGEDIndexation.objects.filter(code_id=code_id).exclude(process_id=pk).select_related('process__norme').first()
        return Response({'used':bool(used),'reference':used.process.norme.reference_number if used else None})

    @action(detail=False,methods=['get'],url_path='code-lookup')
    def code_lookup(self,request):
        code=(request.query_params.get('code') or '').strip()
        if not code:
            raise ValidationError('Saisissez un code documentaire à vérifier.')
        result=STGEDCode.objects.filter(code__iexact=code).select_related('norme','sc').first()
        if not result:
            return Response({'available':True,'code':code,'used':False,'author':''})
        return Response({'available':False,'code':result.code,'used':True,
            'reference':result.norme.reference_number,'norme_id':result.norme_id,
            'sc':result.sc.code,'source_reference':result.source_reference,
            'author':result.approved_by.get_full_name() or result.approved_by.username})

    @action(detail=False,methods=['post'])
    def codes(self,request):
        result=service.approve_code(request.user,**data_for(CodeInput,request))
        return Response({'id':result.pk,'code':result.code},status=201)

    @action(detail=True,methods=['post'])
    def anomalies(self,request,pk=None):
        result=service.anomaly(request.user,pk,**data_for(AnomalyInput,request))
        return Response({'id':result.pk,'resolved_at':result.resolved_at},status=200 if result.resolved_at else 201)

    @action(detail=False,methods=['post'])
    def confirm(self,request):
        result=service.confirm(request.user,**data_for(ConfirmationInput,request))
        return Response({'id':result.pk,'decision':result.decision},status=201)

    @action(detail=True,methods=['get'])
    def compare(self,request,pk=None):
        process=service.processes(request.user).get(pk=pk)
        try:
            left_id=int(request.query_params.get('left',''));right_id=int(request.query_params.get('right',''))
        except ValueError as exc:
            raise ValidationError('Sélectionnez deux versions documentaires.') from exc
        left=STGEDIndexation.objects.select_related('version','source','code').get(pk=left_id,process=process)
        right=STGEDIndexation.objects.select_related('version','source','code').get(pk=right_id,process=process)
        diff='\n'.join(difflib.unified_diff(left.version.content.splitlines(),right.version.content.splitlines(),
            fromfile=f'v{left.version.version_number}',tofile=f'v{right.version.version_number}',lineterm=''))
        segments=build_inline_diff_segments(left.version.content or '', right.version.content or '')
        if len(segments) > 4000:
            segments=segments[:4000]
        return Response({'left':{'number':left.version.version_number,'code':left.code.code,'sha256':left.source.sha256},
            'right':{'number':right.version.version_number,'code':right.code.code,'sha256':right.source.sha256},
            'file_changed':left.source.sha256!=right.source.sha256,'text_diff':diff[:100000],
            'segments':segments,
            'note':'Comparaison des métadonnées et du texte extrait des PDF ; rouge = suppression, bleu = ajout. Les scans restent à contrôler visuellement.'})

    @action(detail=True, methods=['get'], url_path='version-history')
    def version_history(self, request, pk=None):
        """Versions de rédaction et versions GED du même dossier autorisé."""
        process = get_object_or_404(service.received_processes(request.user), pk=pk)
        versions = NormeVersion.all_objects.filter(norme_id=process.norme_id).select_related(
            'version_author').order_by('-version_number')
        entries = {entry.version_id: entry for entry in process.ged_indexations.select_related(
            'source', 'confirmation')}
        rows = NormeVersionSerializer(versions, many=True).data
        for row in rows:
            entry = entries.get(row['id'])
            row['source_url'] = (file_data(entry.source)['url'] if service.document_readable(request.user, entry)
                                 else None) if entry else row.get('document')
            confirmation = getattr(entry, 'confirmation', None) if entry else None
            row['status_label'] = ('Version GED · ' + (
                confirmation.get_decision_display() if confirmation else 'Contrôle en attente')
                if entry else 'Version de rédaction')
        return Response(rows)

    @action(detail=True, methods=['get'], url_path='version-history/compare')
    def compare_history(self, request, pk=None):
        process = get_object_or_404(service.received_processes(request.user), pk=pk)
        ids = {}
        for name in ('left', 'right'):
            ids[name] = serializers.IntegerField(min_value=1).run_validation(request.query_params.get(name))
        versions = NormeVersion.all_objects.filter(norme_id=process.norme_id)
        left = get_object_or_404(versions, pk=ids['left'])
        right = get_object_or_404(versions, pk=ids['right'])
        return Response({'diff_segments': build_inline_diff_segments(left.content or '', right.content or ''),
                         'note': 'Comparaison du texte enregistré ; les documents scannés restent à contrôler visuellement.'})

    @action(detail=False,methods=['get'])
    def history(self,request):
        mandate=service.actor(request.user)
        qs=AuditLog.objects.filter(Q(content_type='CTCProcessus',changes__subsystem='GED') | Q(content_type='governance.STGEDIndexation'))
        if mandate.poste.code=='ST-V3-11':qs=qs.filter(user=request.user)
        return Response({'results':[{'date':e.timestamp,'author':e.user.get_full_name() or e.user.username if e.user else 'Compte archivé',
            'reference':e.object_repr,'action':e.changes.get('action'), 'comment':e.changes.get('comment',''),
            'code':e.changes.get('code',''),'version':e.changes.get('version')} for e in qs.select_related('user')[:150]]})


class STGEDDocumentView(APIView):
    """Pièce indexée accessible aux lecteurs déjà autorisés du dossier CTC."""
    permission_classes=[IsAuthenticated]

    def get(self,request,pk):
        entry=get_object_or_404(STGEDIndexation.objects.select_related('process__norme','source'),pk=pk)
        if not service.document_readable(request.user,entry):
            raise PermissionDenied('Ce document ne relève pas de votre périmètre de lecture.')
        try:
            response=FileResponse(entry.source.file.open('rb'),as_attachment=True,filename=entry.source.name)
        except OSError as exc:
            raise Http404('Document privé indisponible.') from exc
        response['Cache-Control']='private, no-store'
        return response
