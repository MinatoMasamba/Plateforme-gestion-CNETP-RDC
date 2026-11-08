"""Indicateurs personnels du poste 6, sans données de démonstration."""
from datetime import timedelta
from django.utils import timezone
from .st_admin_models import STReception, STPVVersion
from .models import CTCOperationalRequest
from .st_permissions import visible_meetings


def dashboard(expert, context):
    today=timezone.localdate();start=today-timedelta(days=today.weekday())
    receipts=STReception.objects.filter(received_by=expert.user,state='ENREGISTREE')
    decisions=CTCOperationalRequest.objects.filter(reviewed_by=expert)
    meetings=visible_meetings(expert,context).filter(date__lte=timezone.now())
    pv_count=meetings.exclude(pv__redaction='VALIDE').exclude(pv__administrative_versions__state='A_VALIDER').distinct().count()
    versions=STPVVersion.objects.filter(author=expert.user,created_at__date__gte=start)
    daily=[]
    for i in range(7):
        day=start+timedelta(days=i)
        daily.append({'label':['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][i],
            'receipts':receipts.filter(received_at__date=day).count(),
            'decisions':decisions.filter(reviewed_at__date=day).count()})
    maximum=max([1]+[max(row['receipts'],row['decisions']) for row in daily])
    for row in daily:
        row['receipt_height']=round(80*row['receipts']/maximum)
        row['decision_height']=round(80*row['decisions']/maximum)
    return {'pending_requests':CTCOperationalRequest.objects.filter(status='PENDING').count(),
        'pv_to_prepare':pv_count,'weekly_operations':receipts.filter(received_at__date__gte=start).count()+decisions.filter(reviewed_at__date__gte=start).count()+versions.count(),
        'receipts_registered':receipts.count(),'reports_expected':receipts.filter(process__sc_report_received_at__isnull=True).count(),
        'daily':daily,'week_start':start}
