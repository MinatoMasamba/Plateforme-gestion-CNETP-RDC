"""Services des avis juridiques du pôle 3, distincts des validations normatives."""
from datetime import date
from uuid import uuid4
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from apps.core.models import AuditLog
from .models import CTCProcessus
from .st_legal_models import STLegalOpinion, STLegalRequest
from .st_operations import actor_mandate, writable
from .st_ged import TOMES


CO_CHIEFS = {'ST-V3-13', 'ST-V3-14'}


def actor(user):
    mandate = actor_mandate(user)
    if mandate.poste.code not in CO_CHIEFS:
        raise PermissionDenied('Les avis juridiques sont réservés aux co-chefs du pôle 3.')
    return mandate


def requests(user):
    actor(user)
    return STLegalRequest.objects.select_related(
        'process__norme', 'process__administrative_reception__sc', 'opened_by',
    ).prefetch_related(
        'opinions__author', 'opinions__decided_by',
        'process__ged_files__author',
        'process__administrative_reception__pieces',
    )


def legal_processes():
    return CTCProcessus.objects.filter(norme__circuit_version='LEGACY').select_related(
        'norme', 'administrative_reception__sc',
    ).order_by('-updated_at')


def audit(user, request, action, **values):
    AuditLog.objects.create(
        user=user, action='UPDATE', content_type='governance.STLegalRequest',
        object_id=request.pk, object_repr=request.reference[:200],
        changes={'scope': 'ctc_legal', 'action': action, 'reference': request.reference,
                 'norme_id': request.process.norme_id, 'process_id': request.process_id, **values},
    )


def dossier_audit(user, request, action, **values):
    """Trace l'avis dans le dossier normatif examiné, pour le contrôle de la coordination."""
    AuditLog.objects.create(
        user=user, action='UPDATE', content_type='governance.CTCProcessus',
        object_id=request.process_id, object_repr=request.process.norme.reference_number[:200],
        changes={'scope': 'ctc_legal', 'action': action, 'reference': request.reference,
                 'norme_id': request.process.norme_id, 'request_id': request.pk, **values},
    )


def _text(value, label, minimum=1, maximum=20000):
    value = (value or '').strip()
    if len(value) < minimum:
        raise ValidationError(f'{label} obligatoire.')
    if len(value) > maximum:
        raise ValidationError(f'{label} trop long.')
    return value


@transaction.atomic
def create_request(user, process_id, subject, question, requester_name, source_reference,
                   due_date=None, priority='NORMAL'):
    writable()
    actor(user)
    process = legal_processes().get(pk=process_id)
    subject = _text(subject, 'Objet de la demande', 5, 250)
    question = _text(question, 'Question juridique', 10)
    requester_name = _text(requester_name, 'Demandeur', 2, 200)
    source_reference = _text(source_reference, 'Référence de la demande', 2, 200)
    if priority not in STLegalRequest.Priority.values:
        raise ValidationError('Priorité inconnue.')
    if due_date and due_date < date(2000, 1, 1):
        raise ValidationError('Échéance invalide.')
    request = STLegalRequest.objects.create(
        reference=f'AJ-{timezone.localdate().year}-{uuid4().hex[:8].upper()}',
        process=process, subject=subject, question=question,
        requester_name=requester_name, source_reference=source_reference,
        due_date=due_date, priority=priority, opened_by=user, created_by=user,
    )
    audit(user, request, 'legal_request_opened', subject=subject,
          requester_name=requester_name, source_reference=source_reference)
    return request


@transaction.atomic
def save_opinion(user, request_id, analysis, recommendation, submit=False):
    writable()
    actor(user)
    request = requests(user).select_for_update().get(pk=request_id)
    if request.status in (STLegalRequest.Status.ANSWERED, STLegalRequest.Status.CLOSED):
        raise ValidationError('Cette demande est déjà répondue ou clôturée.')
    analysis = _text(analysis, 'Analyse juridique', 10)
    if recommendation not in STLegalOpinion.Recommendation.values:
        raise ValidationError('Recommandation inconnue.')
    opinion = request.opinions.filter(
        author=user, status__in=(STLegalOpinion.Status.DRAFT, STLegalOpinion.Status.RETURNED),
    ).order_by('-pk').first()
    if opinion is None:
        opinion = STLegalOpinion(request=request, author=user, analysis=analysis,
                                 recommendation=recommendation, created_by=user)
    else:
        opinion.analysis = analysis
        opinion.recommendation = recommendation
        opinion.status = STLegalOpinion.Status.DRAFT
    opinion.updated_by = user
    if submit:
        opinion.status = STLegalOpinion.Status.SUBMITTED
        opinion.submitted_at = timezone.now()
    opinion.save()
    request.status = STLegalRequest.Status.IN_PROGRESS
    request.save(update_fields=['status', 'updated_at'])
    audit(user, request, 'legal_opinion_submitted' if submit else 'legal_opinion_saved',
          opinion_id=opinion.pk, recommendation=recommendation)
    if submit:
        dossier_audit(user, request, 'legal_opinion_submitted', opinion_id=opinion.pk,
                      recommendation=recommendation)
    return opinion


@transaction.atomic
def decide_opinion(user, opinion_id, decision, comment):
    writable()
    actor(user)
    opinion = STLegalOpinion.objects.select_for_update().select_related(
        'request__process__norme', 'author',
    ).get(pk=opinion_id)
    if opinion.author_id == user.pk:
        raise ValidationError('La confirmation doit être faite par l’autre co-chef du pôle 3.')
    if opinion.status != STLegalOpinion.Status.SUBMITTED:
        raise ValidationError('Seul un avis transmis peut être confirmé ou retourné.')
    if decision not in (STLegalOpinion.Status.CONFIRMED, STLegalOpinion.Status.RETURNED):
        raise ValidationError('Décision inconnue.')
    comment = _text(comment, 'Commentaire de décision', 3, 5000)
    opinion.status = decision
    opinion.decided_at = timezone.now()
    opinion.decided_by = user
    opinion.decision_comment = comment
    opinion.updated_by = user
    opinion.save(update_fields=['status', 'decided_at', 'decided_by', 'decision_comment', 'updated_by', 'updated_at'])
    request = opinion.request
    request.status = (STLegalRequest.Status.ANSWERED
                      if decision == STLegalOpinion.Status.CONFIRMED
                      else STLegalRequest.Status.IN_PROGRESS)
    request.save(update_fields=['status', 'updated_at'])
    action = ('legal_opinion_confirmed' if decision == STLegalOpinion.Status.CONFIRMED
              else 'legal_opinion_returned')
    audit(user, request, action, opinion_id=opinion.pk, comment=comment,
          decided_by=user.pk, author_id=opinion.author_id)
    dossier_audit(user, request, action, opinion_id=opinion.pk, comment=comment,
                  decided_by=user.pk, author_id=opinion.author_id)
    return opinion


@transaction.atomic
def close_request(user, request_id):
    writable()
    actor(user)
    request = requests(user).select_for_update().get(pk=request_id)
    if request.status != STLegalRequest.Status.ANSWERED:
        raise ValidationError('Seule une demande répondue peut être clôturée.')
    request.status = STLegalRequest.Status.CLOSED
    request.closed_at = timezone.now()
    request.closed_by = user
    request.updated_by = user
    request.save(update_fields=['status', 'closed_at', 'closed_by', 'updated_by', 'updated_at'])
    audit(user, request, 'legal_request_closed')
    return request


def ged_file(user, request_id, file_id):
    request = requests(user).get(pk=request_id)
    return request.process.ged_files.get(pk=file_id)


def reception_piece(user, request_id, piece_id):
    request = requests(user).get(pk=request_id)
    reception = getattr(request.process, 'administrative_reception', None)
    if reception is None:
        from .st_admin_models import STReceptionPiece
        raise STReceptionPiece.DoesNotExist
    return reception.pieces.get(pk=piece_id)


def statistics(user):
    qs = requests(user)
    today = timezone.localdate()
    rows = list(qs)
    opinions = list(STLegalOpinion.objects.filter(request__in=rows).select_related('request', 'author', 'decided_by'))
    counts = {key: sum(row.status == key for row in rows) for key in STLegalRequest.Status.values}
    overdue = [row for row in rows if row.due_date and row.due_date < today
               and row.status not in (STLegalRequest.Status.ANSWERED, STLegalRequest.Status.CLOSED)]
    submitted = [op for op in opinions if op.status == STLegalOpinion.Status.SUBMITTED]
    confirmed = [op for op in opinions if op.status == STLegalOpinion.Status.CONFIRMED]
    returned = [op for op in opinions if op.status == STLegalOpinion.Status.RETURNED]
    delays = [(op.submitted_at - op.request.created_at).total_seconds() / 86400
              for op in opinions if op.submitted_at]
    tomas = {}
    scs = {}
    for row in rows:
        receipt = getattr(row.process, 'administrative_reception', None)
        code = receipt.sc.code if receipt and receipt.sc_id else 'Sans SC'
        scs[code] = scs.get(code, 0) + 1
        number = TOMES.get(code)
        tome = f'Tome {number}' if number is not None else code
        tomas[tome] = tomas.get(tome, 0) + 1
    recommendations = {key: sum(op.recommendation == key for op in opinions)
                       for key in STLegalOpinion.Recommendation.values}
    return {
        'total': len(rows), 'open': counts.get('OPEN', 0), 'in_progress': counts.get('IN_PROGRESS', 0),
        'answered': counts.get('ANSWERED', 0), 'closed': counts.get('CLOSED', 0),
        'overdue': len(overdue), 'pending_confirmation': len(submitted),
        'confirmed': len(confirmed), 'returned': len(returned),
        'opinions': len(opinions),
        'average_days': round(sum(delays) / len(delays), 1) if delays else None,
        'recommendations': recommendations,
        'tomes': [{'tome': key, 'count': value} for key, value in sorted(tomas.items())],
        'scs': [{'code': key, 'count': value} for key, value in sorted(scs.items())],
    }
