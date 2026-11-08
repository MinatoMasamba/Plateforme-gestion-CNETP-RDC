"""API backend ST ; aucun contenu de démonstration."""
from decimal import Decimal
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Sum
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.governance.st_operations import (
    visible_records, write_record, confirm_record, nominate_batch, require_admin, actor_mandate,
)
from apps.governance.st_operations_models import STRecordRevision
from apps.governance.phoenix_runtime import st_posts
from apps.payments.models import Cotisation, Paiement, JetonPresence


class RevisionInput(serializers.Serializer):
    kind = serializers.ChoiceField(choices=['PTN', 'FINANCE', 'WORK'], required=False)
    reference = serializers.CharField(max_length=100, required=False)
    revision = serializers.IntegerField(min_value=0, required=False)
    title = serializers.CharField(max_length=250)
    content = serializers.CharField(required=False, allow_blank=True, max_length=100000)
    source_reference = serializers.CharField(max_length=500)
    amount = serializers.DecimalField(max_digits=16, decimal_places=2, min_value=Decimal('0.01'), required=False)
    currency = serializers.ChoiceField(choices=['CDF', 'USD', 'EUR'], required=False)
    movement = serializers.ChoiceField(choices=['ENGAGEMENT', 'DEPENSE'], required=False)
    operation_date = serializers.DateField(required=False)


def serialize_record(record):
    versions = []
    for revision in record.versions.select_related('confirmation', 'author').order_by('-number'):
        decision = getattr(revision, 'confirmation', None)
        versions.append({'number': revision.number, 'title': revision.title, 'content': revision.content,
            'source_reference': revision.source_reference, 'author_id': revision.author_id,
            'amount': str(revision.amount) if revision.amount is not None else None,
            'currency': revision.currency, 'movement': revision.movement,
            'operation_date': revision.operation_date.isoformat() if revision.operation_date else None,
            'confirmation': {'decision': decision.decision, 'comment': decision.comment,
                'author_id': decision.author_id, 'date': decision.created_at.isoformat()} if decision else None})
    return {'id': record.pk, 'reference': record.reference, 'kind': record.kind,
        'pole': record.pole, 'revision': record.revision, 'versions': versions}


class STBackendViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response({'detail': exc.messages}, status=409 if getattr(exc, 'code', None) == 'conflict' else 400)
        return super().handle_exception(exc)

    def list(self, request):
        qs = visible_records(request.user).order_by('-updated_at', '-pk')
        if request.query_params.get('kind'):
            qs = qs.filter(kind=request.query_params['kind'])
        return Response({'count': qs.count(), 'results': [serialize_record(r) for r in qs[:100]]})

    def retrieve(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        return Response(serialize_record(get_object_or_404(visible_records(request.user), pk=pk)))

    def create(self, request):
        serializer = RevisionInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data.get('operation_date'):
            data['operation_date'] = data['operation_date'].isoformat()
        record = write_record(request.user, data)
        return Response(serialize_record(record), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def revise(self, request, pk=None):
        serializer = RevisionInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data.get('operation_date'):
            data['operation_date'] = data['operation_date'].isoformat()
        return Response(serialize_record(write_record(request.user, data, record_id=pk)))

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        class Input(serializers.Serializer):
            revision = serializers.IntegerField(min_value=1)
            decision = serializers.ChoiceField(choices=['CONFIRMED', 'REJECTED'])
            comment = serializers.CharField(max_length=10000)
        serializer = Input(data=request.data)
        serializer.is_valid(raise_exception=True)
        confirm_record(request.user, pk, **serializer.validated_data)
        return self.retrieve(request, pk=pk)

    @action(detail=False, methods=['get'])
    def posts(self, request):
        require_admin(request.user)
        return Response({'results': [{'code': p.code, 'title': p.title, 'nominated_name': p.nominated_name,
            'pole': p.organe.code, 'occupied': p.mandates.filter(status='ACTIVE').exists()} for p in st_posts()]})

    @action(detail=False, methods=['post'])
    def nominations(self, request):
        apply = request.data.get('apply', False)
        if not isinstance(apply, bool):
            raise ValidationError('Le champ apply doit être un booléen.')
        return Response({'results': nominate_batch(request.user, request.data.get('assignments'), apply=apply)})

    @action(detail=False, methods=['get'])
    def audit(self, request):
        mandate = actor_mandate(request.user)
        if mandate.poste.organe.code != 'ST-P3' or mandate.poste.category != 'POLE_HEAD':
            raise PermissionDenied('Audit ST réservé aux co-chefs du pôle 3.')
        from apps.governance.st_permissions import visible_st_journal
        journal = visible_st_journal(mandate).filter(
            operation__in=['ST_NOMINATION', 'ST_PREPARE', 'ST_CONFIRM', 'RETIRE_LEGACY_CTC']).exclude(actor=request.user)
        return Response({'count': journal.count(), 'results': [{'id': row.pk, 'date': row.created_at.isoformat(),
            'actor': row.actor_name, 'operation': row.operation, 'target': row.target, 'after': row.after}
            for row in journal.order_by('-created_at', '-pk')[:100]]})

    @action(detail=False, methods=['get'], url_path='ptn-register')
    def ptn_register(self, request):
        mandate = actor_mandate(request.user)
        revisions = STRecordRevision.objects.filter(record__version=mandate.organisation_version,
            record__kind='PTN', confirmation__decision='CONFIRMED').order_by('record_id', '-number')
        results, seen = [], set()
        for revision in revisions:
            if revision.record_id in seen:
                continue
            seen.add(revision.record_id)
            results.append({'reference': revision.record.reference, 'version': revision.number,
                'title': revision.title, 'content': revision.content, 'source_reference': revision.source_reference})
        return Response({'confirmed_count': len(results), 'has_confirmed_register': bool(results), 'results': results})

    @action(detail=False, methods=['get'], url_path='finance-summary')
    def finance_summary(self, request):
        mandate = actor_mandate(request.user)
        if mandate.poste.organe.code != 'ST-P3':
            raise PermissionDenied('Lecture financière réservée au pôle 3.')
        # Seule la dernière version confirmée de chaque écriture contribue aux totaux.
        revisions = STRecordRevision.objects.filter(record__version=mandate.organisation_version,
            record__kind='FINANCE', confirmation__decision='CONFIRMED').order_by('record_id', '-number')
        totals, seen = {}, set()
        for rev in revisions:
            if rev.record_id in seen:
                continue
            seen.add(rev.record_id)
            key = (rev.currency, rev.movement)
            totals[key] = totals.get(key, Decimal('0')) + rev.amount
        return Response({'ledger': [{'currency': c, 'movement': m, 'amount': str(amount)} for (c, m), amount in totals.items()],
            'legacy': {'currency': None, 'verified_for_st_v3': False, 'currency_note': 'Devise non renseignée dans les modèles historiques ; totaux séparés.',
                'cotisations_expected': str(Cotisation.objects.aggregate(total=Sum('montant'))['total'] or Decimal('0')),
                'cotisations_confirmed': str(Paiement.objects.filter(status='CONFIRMED').aggregate(total=Sum('montant'))['total'] or Decimal('0')),
                'jetons_pending': str(JetonPresence.objects.filter(status='PENDING').aggregate(total=Sum('montant'))['total'] or Decimal('0')),
                'jetons_paid': str(JetonPresence.objects.filter(status='PAID').aggregate(total=Sum('montant'))['total'] or Decimal('0'))}})
