"""API d’envoi et d’historique SC/GT ; fichiers privés et périmètres contrôlés."""
import uuid
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.governance.models import Organe, GroupeCible
from apps.governance.phoenix_runtime import current_organisation_version
from apps.messaging.dispatch_models import DispatchRecipient
from apps.messaging.dispatch_services import send_dispatch, visible_dispatches, sender_mandate, target_recipients, retry_dispatch_emails
from apps.mobileapp.models import Notification


class SendDispatchSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=250)
    body = serializers.CharField(max_length=100000, required=False, allow_blank=True, default='')
    sc_id = serializers.IntegerField(min_value=1, required=False)
    gt_id = serializers.IntegerField(min_value=1, required=False)
    attachment = serializers.FileField(required=False, allow_empty_file=False)
    request_key = serializers.UUIDField(required=False, default=uuid.uuid4)

    def validate(self, attrs):
        if bool(attrs.get('sc_id')) == bool(attrs.get('gt_id')):
            raise serializers.ValidationError('Choisir une SC ou un seul GT, exclusivement.')
        if not attrs.get('body') and not attrs.get('attachment'):
            raise serializers.ValidationError('Un texte ou un document est obligatoire.')
        return attrs


def representation(dispatch, user):
    deliveries = list(dispatch.recipients.prefetch_related('email_history'))
    privileged = dispatch.sender_id == user.pk or (user.is_staff and user.has_perm('messaging.view_institutionaldispatch'))
    return {'id': dispatch.pk, 'subject': dispatch.subject, 'body': dispatch.body,
        'sender_id': dispatch.sender_id, 'sender_name': dispatch.sender_name,
        'created_at': dispatch.created_at.isoformat(),
        'target': {'type': 'ALL_USERS' if dispatch.target_all_users else ('ALL_SC' if dispatch.target_all_sc else ('GT' if dispatch.target_gt_id else 'SC')), 'id': dispatch.target_gt_id or dispatch.target_sc_id, 'code': dispatch.target_code, 'label': dispatch.target_label},
        'recipient_count': len(deliveries), 'read_count': sum(d.read_at is not None for d in deliveries) if privileged else None,
        'channels': ['INTERNAL', 'EMAIL'],
        'recipients': [{'user_id': d.user_id, 'name': d.recipient_name, 'read_at': d.read_at.isoformat() if d.read_at else None,
            'email_status': d.email_status, 'email_error': d.email_error, 'email_sent_at': d.email_sent_at.isoformat() if d.email_sent_at else None,
            'email_history': [{'number': attempt.number, 'outcome': attempt.outcome, 'error': attempt.error, 'finished_at': attempt.finished_at.isoformat() if attempt.finished_at else None} for attempt in d.email_history.all()]}  for d in deliveries if privileged or d.user_id == user.pk],
        'attachment': {'name': dispatch.original_filename, 'size': dispatch.attachment_size, 'sha256': dispatch.attachment_sha256,
            'download_url': f'/api/v1/communications/{dispatch.pk}/attachment/'} if dispatch.attachment else None}


class InstitutionalDispatchViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response({'detail': exc.messages}, status=409 if getattr(exc, 'code', None) == 'conflict' else 400)
        return super().handle_exception(exc)

    def list(self, request):
        qs = visible_dispatches(request.user)
        direction = request.query_params.get('direction')
        if direction == 'sent':
            qs = qs.filter(sender=request.user)
        elif direction == 'received':
            qs = qs.filter(recipients__user=request.user)
        elif direction not in (None, 'all'):
            raise ValidationError('Direction attendue : sent, received ou all.')
        for parameter in ('sc_id', 'gt_id'):
            value = request.query_params.get(parameter)
            if value:
                try:
                    value = int(value)
                except ValueError:
                    raise ValidationError('Identifiant de cible invalide.')
                qs = qs.filter(**{f'target_{parameter}': value})
        if request.query_params.get('search'):
            term = request.query_params['search'][:250]
            qs = qs.filter(Q(subject__icontains=term) | Q(body__icontains=term))
        paginator = LimitOffsetPagination()
        paginator.default_limit, paginator.max_limit = 25, 100
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response([representation(row, request.user) for row in page])

    def retrieve(self, request, pk=None):
        return Response(representation(get_object_or_404(visible_dispatches(request.user), pk=pk), request.user))

    def create(self, request):
        serializer = SendDispatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data.copy()
        data['upload'] = data.pop('attachment', None)
        dispatch, created = send_dispatch(request.user, **data)
        return Response(representation(dispatch, request.user), status=201 if created else 200)

    @action(detail=False, methods=['get'])
    def targets(self, request):
        sender_mandate(request.user)
        version = current_organisation_version()
        results = []
        for sc in Organe.objects.filter(version=version, type='SC').order_by('code'):
            valid = sc.status in ('VALIDATED', 'ACTIVE')
            count = target_recipients(sc).count() if valid else 0
            results.append({'type': 'SC', 'id': sc.pk, 'code': sc.code, 'label': sc.name, 'status': sc.status, 'recipient_count': count, 'sendable': valid and count > 0})
        for gt in GroupeCible.objects.filter(sc__version=version).select_related('sc').order_by('sc__code', 'code'):
            valid = gt.sc.status in ('VALIDATED', 'ACTIVE')
            count = target_recipients(gt.sc, gt).count() if valid else 0
            results.append({'type': 'GT', 'id': gt.pk, 'sc_id': gt.sc_id, 'code': gt.code, 'label': gt.name, 'recipient_count': count, 'sendable': valid and count > 0})
        return Response({'organisation_version': version.code if version else None, 'results': results})

    @action(detail=True, methods=['get'])
    def attachment(self, request, pk=None):
        dispatch = get_object_or_404(visible_dispatches(request.user), pk=pk)
        if not dispatch.attachment:
            raise NotFound('Aucune pièce jointe pour cet envoi.')
        try:
            stream = dispatch.attachment.open('rb')
        except FileNotFoundError:
            raise NotFound('Le fichier archivé est introuvable.')
        response = FileResponse(stream, as_attachment=True, filename=dispatch.original_filename, content_type=dispatch.attachment_mime)
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        return response

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        dispatch = get_object_or_404(visible_dispatches(request.user), pk=pk)
        delivery = DispatchRecipient.objects.filter(dispatch=dispatch, user=request.user).first()
        if not delivery:
            raise PermissionDenied('Seul un destinataire peut accuser lecture pour lui-même.')
        with transaction.atomic():
            now = timezone.now()
            DispatchRecipient.objects.filter(pk=delivery.pk, read_at__isnull=True).update(read_at=now)
            if delivery.notification_id:
                Notification.objects.filter(pk=delivery.notification_id, user=request.user, is_read=False).update(is_read=True, read_at=now)
        delivery.refresh_from_db()
        return Response({'id': dispatch.pk, 'read_at': delivery.read_at.isoformat()})


    @action(detail=True, methods=['post'], url_path='retry-email')
    def retry_email(self, request, pk=None):
        count = retry_dispatch_emails(request.user, pk)
        return Response({'id': int(pk), 'recipients_requeued': count})
