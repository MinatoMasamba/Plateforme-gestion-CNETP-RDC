"""Opérations administratives du poste 6, transactionnelles et historisées."""
import hashlib
from decimal import Decimal, InvalidOperation
from datetime import date
from pathlib import Path
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .st_operations import actor_mandate, writable
from .st_admin_models import STReception, STReceptionPiece, STPVVersion
from .models import CTCProcessus, Organe, GroupeCible, MandatOrganisation
from apps.core.models import AuditLog


def secretary(user):
    mandate = actor_mandate(user)
    if mandate.poste.code != 'ST-V3-06':
        raise PermissionDenied('Réservé au poste 6, assistant de direction et secrétaire de séance.')
    return mandate


def readable_receptions(user):
    from apps.experts.models import Expert
    expert = Expert.objects.filter(user=user).first()
    own = Q(sender=expert) if expert else Q(pk__in=[])
    try:
        mandate = actor_mandate(user)
        if mandate.poste.code in [f'ST-V3-{n:02}' for n in (1,2,3,4,5,6,8,9,10,11,13,14)]:
            return STReception.objects.all()
    except PermissionDenied:
        pass
    return STReception.objects.filter(own)


def event(user, reception, action, before=None, comment=''):
    AuditLog.objects.create(user=user, action='UPDATE', content_type='governance.STReception',
        object_id=reception.pk, object_repr=reception.reference,
        changes={'scope':'ctc','action':action,'reference':reception.reference,
                 'before':before or {},'revision':reception.revision,'comment':comment,
                 'norme_id':reception.process.norme_id,'sc_id':reception.sc_id})


def notify_after_commit(user_id, title, body, reception_id):
    from apps.core.models import User
    from apps.mobileapp.signals import create_notification_for_user
    def send():
        user = User.objects.filter(pk=user_id, is_active=True).first()
        if user:
            create_notification_for_user(user,title,body,'SYSTEM',data={'reception_id':reception_id})
    transaction.on_commit(send, robust=True)


def notify_followup(reception, title):
    today = timezone.localdate()
    mandates = MandatOrganisation.objects.filter(status='ACTIVE', capacity='ORGANISATION',
        poste__code__in=['ST-V3-08','ST-V3-09'], expert__user__is_active=True).filter(
        Q(start_date__isnull=True)|Q(start_date__lte=today)).filter(Q(end_date__isnull=True)|Q(end_date__gte=today))
    for user_id in mandates.values_list('expert__user_id', flat=True).distinct():
        notify_after_commit(user_id,title,reception.reference,reception.pk)


@transaction.atomic
def save_reception(user, data, pk=None):
    writable()
    secretary(user)
    if pk:
        r = STReception.objects.select_for_update().select_related('process__norme').get(pk=pk)
        if r.state == 'ENREGISTREE':
            raise ValidationError('Réception enregistrée : utiliser une rectification tracée.')
        if int(data.get('revision', -1)) != r.revision:
            raise ValidationError('Révision obsolète.', code='conflict')
    else:
        p = CTCProcessus.objects.select_for_update().select_related('norme').get(pk=data.get('process_id'))
        existing=STReception.objects.select_for_update().filter(process=p).first()
        if existing:
            return existing
        if p.norme.circuit_version != 'LEGACY' or p.current_stage != 'RECEPTION':
            raise ValidationError('Cette réception concerne uniquement les dossiers historiques à l’étape Réception ; Phoenix conserve son circuit.')
        if p.received_at:
            raise ValidationError('Dossier déjà réceptionné dans le circuit historique.')
        r, created = STReception.objects.get_or_create(process=p, defaults={'created_by':user})
        if not created:
            return r  # Une même transmission ouvre le même brouillon.
    before={'state':r.state,'revision':r.revision,'observations':r.observations}
    if data.get('sc_id'):
        r.sc = Organe.objects.get(pk=data['sc_id'],type='SC',status__in=['VALIDATED','ACTIVE'])
    if data.get('group_id'):
        r.group = GroupeCible.objects.get(pk=data['group_id'])
    if r.group_id and (not r.sc_id or r.group.sc_id != r.sc_id):
        raise ValidationError('Le groupe doit appartenir à la sous-commission choisie.')
    if data.get('sender_id'):
        from apps.experts.models import Expert
        r.sender=Expert.objects.get(pk=data['sender_id'],status='ACTIVE',user__is_active=True)
    if data.get('vote_date'):
        r.vote_date=date.fromisoformat(data['vote_date'])
        if r.vote_date > timezone.localdate():
            raise ValidationError('La date du vote ne peut pas être future.')
    if data.get('vote_percentage') is not None:
        try:
            percent=Decimal(str(data['vote_percentage']))
        except InvalidOperation:
            raise ValidationError('Pourcentage invalide.')
        if not percent.is_finite() or not 0 <= percent <= 100:
            raise ValidationError('Pourcentage compris entre 0 et 100 attendu.')
        r.vote_percentage=percent
    r.observations=str(data.get('observations',r.observations)).strip()
    r.state='ANOMALIE' if data.get('anomaly') is True else 'BROUILLON'
    if r.state=='ANOMALIE' and not r.observations:
        raise ValidationError('Un motif est obligatoire pour signaler une anomalie.')
    r.verified=data.get('verified') is True
    r.revision+=1
    r.full_clean()
    r.save()
    event(user,r,'draft_saved',before,r.observations)
    if r.state=='ANOMALIE' and r.sender_id:
        notify_after_commit(r.sender.user_id,'Anomalie sur la transmission',r.observations,r.pk)
    return r


@transaction.atomic
def add_piece(user, pk, kind, upload):
    writable();secretary(user)
    r=STReception.objects.select_for_update().select_related('process').get(pk=pk)
    if kind not in ('PROJECT','VOTE','REPORT') or not upload or upload.size>10*1024*1024:
        raise ValidationError('Pièce PDF, PNG ou JPG de 10 Mo maximum attendue (limite technique conservatoire).')
    if r.state=='ENREGISTREE' and kind!='REPORT':
        raise ValidationError('Les pièces d’une réception enregistrée sont conservées ; demander une rectification.')
    if kind=='REPORT' and r.process.sc_report_received_at:
        raise ValidationError('Rapport déjà constaté dans le circuit ; conserver son historique.')
    if kind=='REPORT' and r.state=='ENREGISTREE' and r.process.current_stage!='RECEPTION':
        raise ValidationError('Le dossier a déjà quitté l’étape de réception.')
    content=upload.read();upload.seek(0)
    suffix=Path(upload.name).suffix.lower()
    valid=(suffix=='.pdf' and content.startswith(b'%PDF-')) or (suffix=='.png' and content.startswith(b'\x89PNG\r\n\x1a\n')) or (suffix in ('.jpg','.jpeg') and content.startswith(b'\xff\xd8\xff'))
    if not valid:
        raise ValidationError('Le contenu du fichier ne correspond pas au format PDF, PNG ou JPG annoncé.')
    try:
        import io
        if suffix=='.pdf':
            import fitz
            with fitz.open(stream=content,filetype='pdf') as reader:
                if reader.needs_pass or not reader.page_count:
                    raise ValueError('PDF chiffré ou vide')
        else:
            from PIL import Image
            with Image.open(io.BytesIO(content)) as image:
                image.verify()
    except Exception as exc:
        raise ValidationError('Fichier illisible, chiffré ou endommagé.') from exc
    piece=STReceptionPiece.objects.create(reception=r,kind=kind,file=upload,
        original_name=Path(upload.name).name[:255],sha256=hashlib.sha256(content).hexdigest(),author=user)
    r.revision+=1;r.save(update_fields=['revision','updated_at'])
    event(user,r,'piece_added',comment=f'{kind} : {piece.original_name} ; SHA256 {piece.sha256}')
    if kind=='REPORT' and r.state=='ENREGISTREE':
        p=CTCProcessus.objects.select_for_update().get(pk=r.process_id)
        if p.current_stage!='RECEPTION':
            raise ValidationError('Le dossier a déjà quitté l’étape de réception.')
        p.sc_report_received_at=timezone.now();p.sc_report_received_by=user.expert_profile
        p.sc_report_reference=f'{r.reference} / pièce {piece.pk}'
        p.save(update_fields=['sc_report_received_at','sc_report_received_by','sc_report_reference','updated_at'])
        notify_followup(r,'Rapport de revue reçu')
    return piece


@transaction.atomic
def register_reception(user,pk,revision):
    writable();secretary(user)
    r=STReception.objects.select_for_update().select_related('process__norme','sc','group','sender__user').get(pk=pk)
    if r.state=='ENREGISTREE':
        return r  # Réponse idempotente : même numéro et même accusé.
    if r.revision!=revision:
        raise ValidationError('Révision obsolète.',code='conflict')
    p=CTCProcessus.objects.select_for_update().get(pk=r.process_id)
    if p.received_at or p.current_stage!='RECEPTION' or p.norme.circuit_version!='LEGACY':
        raise ValidationError('Réception historique déjà enregistrée ou étape différente.')
    if not all((r.sc_id,r.group_id,r.sender_id,r.vote_date,r.verified)) or r.state=='ANOMALIE':
        raise ValidationError('Identification, vote, vérification administrative et correction des anomalies obligatoires.')
    if r.vote_percentage is None or r.vote_percentage<=75:
        raise ValidationError('Le vote favorable doit être strictement supérieur à 75 %.')
    today=timezone.localdate()
    if r.group.sc_id!=r.sc_id or r.vote_date>today:
        raise ValidationError('Origine incohérente ou date de vote future.')
    if r.sc.status not in ('VALIDATED','ACTIVE'):
        raise ValidationError('La SC doit être confirmée dans le référentiel avant l’enregistrement officiel. Le brouillon est conservé.')
    if not MandatOrganisation.objects.filter(expert=r.sender,expert__status='ACTIVE',expert__user__is_active=True,
        poste__organe=r.sc,poste__status__in=['VALIDATED','ACTIVE'],status='ACTIVE',capacity='ORGANISATION').filter(
        Q(start_date__isnull=True)|Q(start_date__lte=today)).filter(Q(end_date__isnull=True)|Q(end_date__gte=today)).exists():
        raise ValidationError('L’expéditeur doit disposer d’un mandat officiel en cours dans la SC d’origine ; une simple adhésion ne suffit pas.')
    kinds=set(r.pieces.values_list('kind',flat=True))
    if not {'PROJECT','VOTE'}<=kinds:
        raise ValidationError('Projet de norme et preuve du vote obligatoires.')
    r.state='ENREGISTREE';r.received_at=timezone.now();r.received_by=user;r.revision+=1
    r.snapshot={'reference':r.reference,'norme':r.process.norme.reference_number,'title':r.process.norme.title,
        'sc':r.sc.name,'group':r.group.name,'vote_date':str(r.vote_date),'vote_percentage':str(r.vote_percentage),
        'received_at':r.received_at.isoformat(),'agent':user.get_full_name() or user.username,
        'sender':r.sender.full_name,'observations':r.observations,
        'pieces':list(r.pieces.values('id','kind','original_name','sha256'))}
    r.save();p.mark_received(user.expert_profile)
    if 'REPORT' in kinds:
        piece=r.pieces.filter(kind='REPORT').latest('pk')
        p.sc_report_received_at=timezone.now();p.sc_report_received_by=user.expert_profile;p.sc_report_reference=f'{r.reference} / pièce {piece.pk}'
        p.save(update_fields=['sc_report_received_at','sc_report_received_by','sc_report_reference','updated_at'])
    event(user,r,'registered',comment=r.observations)
    notify_after_commit(r.sender.user_id,'Accusé de réception disponible',r.reference,r.pk)
    notify_followup(r,'Réception enregistrée : suivi du rapport de revue')
    return r
