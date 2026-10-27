from datetime import date
from decimal import Decimal

from django.db.models import Sum, DecimalField
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.payments.models import Cotisation, Paiement, JetonPresence
from apps.experts.models import Expert, Structure
from .receipts import generate_jeton_receipt, generate_payment_receipt
from .sepa import build_pain_001, sepa_settings
from .serializers import (
    CotisationBasicSerializer, CotisationDetailSerializer,
    CotisationCreateUpdateSerializer, PaiementBasicSerializer,
    PaiementDetailSerializer, PaiementCreateSerializer,
    JetonPresenceBasicSerializer, JetonPresenceDetailSerializer,
    JetonPresenceCreateSerializer, PaymentDashboardSerializer,
    JetonSummarySerializer, PaymentStatsSerializer
)
from ..permissions import IsCTCCoordinator


class CotisationViewSet(viewsets.ModelViewSet):
    """ViewSet pour les cotisations"""
    queryset = Cotisation.objects.select_related('structure').prefetch_related('paiements')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['structure__id', 'annee', 'status']
    search_fields = ['structure__name']
    ordering_fields = ['due_date', 'annee']
    ordering = ['-annee']

    def get_serializer_class(self):
        """Retourner le serializer approprié"""
        if self.action == 'retrieve':
            return CotisationDetailSerializer
        elif self.action == 'list':
            return CotisationBasicSerializer
        elif self.action == 'create' or self.action == 'update':
            return CotisationCreateUpdateSerializer
        return CotisationDetailSerializer

    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])
    def send_reminder(self, request, pk=None):
        """Envoyer un rappel pour une cotisation non payée"""
        cotisation = self.get_object()

        if cotisation.status == 'PAID':
            return Response(
                {'detail': 'La cotisation est déjà payée.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.payments.tasks import send_payment_reminder
        send_payment_reminder.delay(cotisation.id)

        return Response({
            'message': 'Rappel envoyé à la structure.',
            'structure': cotisation.structure.name,
            'montant_en_attente': str(cotisation.montant)
        })

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Récupérer les cotisations non payées"""
        cotisations = self.get_queryset().filter(
            status__in=['PENDING', 'PARTIAL']
        ).filter(
            due_date__lt=timezone.now()
        )
        serializer = CotisationBasicSerializer(cotisations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_structure(self, request):
        """Récupérer les cotisations d'une structure"""
        structure_id = request.query_params.get('structure_id')
        if not structure_id:
            return Response(
                {'detail': 'structure_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cotisations = self.get_queryset().filter(structure_id=structure_id)
        serializer = CotisationBasicSerializer(cotisations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Tableau de bord des cotisations"""
        cotisations = self.get_queryset()

        total_cotisations = cotisations.aggregate(
            total=Sum('montant', output_field=DecimalField())
        )['total'] or Decimal('0')

        total_paye = Paiement.objects.filter(
            status='CONFIRMED'
        ).aggregate(
            total=Sum('montant', output_field=DecimalField())
        )['total'] or Decimal('0')

        total_en_attente = total_cotisations - total_paye

        percentage = (total_paye / total_cotisations * 100) if total_cotisations > 0 else Decimal('0')

        return Response({
            'total_cotisations': str(total_cotisations),
            'total_paye': str(total_paye),
            'total_en_attente': str(total_en_attente),
            'percentage_paye': str(round(percentage, 2)),
            'nombre_structures': Structure.objects.count(),
            'structures_payees': cotisations.filter(status='PAID').count(),
            'structures_en_retard': cotisations.filter(status__in=['PENDING', 'PARTIAL']).count()
        })


class PaiementViewSet(viewsets.ModelViewSet):
    """ViewSet pour les paiements"""
    queryset = Paiement.objects.select_related('cotisation__structure')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['cotisation__id', 'status', 'methode_paiement']
    search_fields = ['numero_transaction', 'numero_recu']
    ordering_fields = ['payment_date', 'created_at']
    ordering = ['-payment_date']

    def get_serializer_class(self):
        """Retourner le serializer approprié"""
        if self.action == 'retrieve':
            return PaiementDetailSerializer
        elif self.action == 'list':
            return PaiementBasicSerializer
        elif self.action == 'create' or self.action == 'update':
            return PaiementCreateSerializer
        return PaiementDetailSerializer

    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['create']:
            return [IsAuthenticated()]
        elif self.action in ['confirm', 'reject', 'update', 'partial_update', 'destroy']:
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])
    def confirm(self, request, pk=None):
        """Confirmer un paiement"""
        paiement = self.get_object()

        if paiement.status != 'PENDING':
            return Response(
                {'detail': 'Seul un paiement en attente peut être confirmé.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        paiement.status = 'CONFIRMED'
        paiement.confirmed_at = timezone.now()
        paiement.save()

        self._update_cotisation_status(paiement.cotisation)

        return Response(PaiementDetailSerializer(paiement).data)

    @action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])
    def reject(self, request, pk=None):
        """Rejeter un paiement"""
        paiement = self.get_object()

        paiement.status = 'REJECTED'
        paiement.save()

        return Response(PaiementDetailSerializer(paiement).data)

    def _update_cotisation_status(self, cotisation):
        """Mettre à jour le statut de la cotisation"""
        paiements = cotisation.paiements.filter(status='CONFIRMED')
        total_paye = paiements.aggregate(
            total=Sum('montant', output_field=DecimalField())
        )['total'] or Decimal('0')

        if total_paye >= cotisation.montant:
            cotisation.status = 'PAID'
        elif total_paye > 0:
            cotisation.status = 'PARTIAL'
        else:
            cotisation.status = 'PENDING'

        cotisation.save()

    @action(detail=False, methods=['get'])
    def by_cotisation(self, request):
        """Récupérer les paiements d'une cotisation"""
        cotisation_id = request.query_params.get('cotisation_id')
        if not cotisation_id:
            return Response(
                {'detail': 'cotisation_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        paiements = self.get_queryset().filter(cotisation_id=cotisation_id)
        serializer = PaiementBasicSerializer(paiements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_confirmations(self, request):
        """Récupérer les paiements en attente de confirmation"""
        paiements = self.get_queryset().filter(status='PENDING')
        serializer = PaiementBasicSerializer(paiements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        """Télécharger le reçu PDF d'un paiement."""
        paiement = self.get_object()
        user = request.user
        staff = (
            user.is_staff or user.is_superuser
            or getattr(user, 'is_ctc_staff', False)
        )
        expert = getattr(user, 'expert_profile', None)
        if not staff and (
            expert is None
            or paiement.cotisation.structure_id != expert.structure_id
        ):
            return Response(
                {'detail': "Ce reçu n'appartient pas à votre structure."},
                status=status.HTTP_403_FORBIDDEN,
            )
        response = HttpResponse(
            generate_payment_receipt(paiement),
            content_type='application/pdf',
        )
        filename = f"recu-{paiement.numero_recu or paiement.pk}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class JetonPresenceViewSet(viewsets.ModelViewSet):
    """ViewSet pour les jetons de présence"""
    queryset = JetonPresence.objects.select_related(
        'expert__user', 'reunion', 'contestation_resolved_by',
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['expert__id', 'status', 'reunion__id']
    search_fields = ['expert__user__first_name', 'expert__user__last_name']
    ordering_fields = ['payment_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Retourner le serializer approprié"""
        if self.action == 'retrieve':
            return JetonPresenceDetailSerializer
        elif self.action == 'list':
            return JetonPresenceBasicSerializer
        elif self.action == 'create' or self.action == 'update':
            return JetonPresenceCreateSerializer
        return JetonPresenceDetailSerializer

    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in [
            'create', 'update', 'partial_update', 'destroy',
            'resolve_contestation', 'sepa_export',
        ]:
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def by_expert(self, request):
        """Récupérer les jetons d'un expert"""
        expert_id = request.query_params.get('expert_id')
        if not expert_id:
            return Response(
                {'detail': 'expert_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        jetons = self.get_queryset().filter(expert_id=expert_id)

        total = jetons.count()
        montant_total = jetons.aggregate(
            total=Sum('montant', output_field=DecimalField())
        )['total'] or Decimal('0')
        montant_paye = jetons.filter(status='PAID').aggregate(
            total=Sum('montant', output_field=DecimalField())
        )['total'] or Decimal('0')
        montant_en_attente = montant_total - montant_paye

        return Response({
            'expert_id': expert_id,
            'total_jetons': total,
            'montant_total': str(montant_total),
            'montant_paye': str(montant_paye),
            'montant_en_attente': str(montant_en_attente),
            'jetons': JetonPresenceBasicSerializer(jetons, many=True).data
        })

    @action(detail=False, methods=['get'])
    def pending_payment(self, request):
        """Récupérer les jetons en attente de paiement"""
        jetons = self.get_queryset().filter(status='PENDING')
        serializer = JetonPresenceBasicSerializer(jetons, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])
    def mark_as_paid(self, request, pk=None):
        """Marquer un jeton comme payé"""
        jeton = self.get_object()
        jeton.status = 'PAID'
        jeton.payment_date = timezone.now()
        jeton.save()

        return Response(JetonPresenceDetailSerializer(jeton).data)

    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        """Télécharger le reçu PDF d'une indemnité."""
        jeton = self.get_object()
        user = request.user
        staff = (
            user.is_staff or user.is_superuser
            or getattr(user, 'is_ctc_staff', False)
        )
        expert = getattr(user, 'expert_profile', None)
        if not staff and (expert is None or expert.pk != jeton.expert_id):
            return Response(
                {'detail': "Ce reçu ne concerne pas votre indemnité."},
                status=status.HTTP_403_FORBIDDEN,
            )
        response = HttpResponse(
            generate_jeton_receipt(jeton),
            content_type='application/pdf',
        )
        response['Content-Disposition'] = (
            f'attachment; filename="indemnite-{jeton.pk}.pdf"'
        )
        return response

    @action(detail=True, methods=['post'])
    def contest(self, request, pk=None):
        """Contester une indemnité dont l'utilisateur est le bénéficiaire."""
        jeton = self.get_object()
        expert = getattr(request.user, 'expert_profile', None)
        if expert is None or jeton.expert_id != expert.pk:
            return Response(
                {'detail': "Seul le bénéficiaire peut contester cette indemnité."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if jeton.contestation_status == 'PENDING':
            return Response(
                {'detail': "Une contestation est déjà en cours d'instruction."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        motif = str(request.data.get('motif') or '').strip()
        if len(motif) < 10:
            return Response(
                {'detail': 'Le motif doit contenir au moins 10 caractères.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        jeton.contestation_status = 'PENDING'
        jeton.contestation_motif = motif
        jeton.contestation_created_at = timezone.now()
        jeton.contestation_resolution = ''
        jeton.contestation_resolved_at = None
        jeton.contestation_resolved_by = None
        jeton.save(update_fields=[
            'contestation_status', 'contestation_motif',
            'contestation_created_at', 'contestation_resolution',
            'contestation_resolved_at', 'contestation_resolved_by',
            'updated_at',
        ])
        return Response(JetonPresenceDetailSerializer(jeton).data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsCTCCoordinator],
    )
    def resolve_contestation(self, request, pk=None):
        """Accepter ou rejeter une contestation d'indemnité."""
        jeton = self.get_object()
        if jeton.contestation_status != 'PENDING':
            return Response(
                {'detail': "Cette contestation n'est pas en attente d'instruction."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        decision = str(request.data.get('decision') or '').upper()
        if decision not in {'ACCEPTED', 'REJECTED'}:
            return Response(
                {'detail': 'La décision doit être ACCEPTED ou REJECTED.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        resolution = str(request.data.get('resolution') or '').strip()
        if not resolution:
            return Response(
                {'detail': "La note d'instruction est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        jeton.contestation_status = decision
        jeton.contestation_resolution = resolution
        jeton.contestation_resolved_at = timezone.now()
        jeton.contestation_resolved_by = request.user
        jeton.save(update_fields=[
            'contestation_status', 'contestation_resolution',
            'contestation_resolved_at', 'contestation_resolved_by',
            'updated_at',
        ])
        return Response(JetonPresenceDetailSerializer(jeton).data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsCTCCoordinator],
    )
    def sepa_export(self, request):
        """Exporter les indemnités en attente au format pain.001."""
        config = sepa_settings()
        if config['missing']:
            return Response(
                {
                    'detail': (
                        'Coordonnées bancaires de la CNETP non configurées : '
                        + ', '.join(config['missing'])
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        jetons = self.get_queryset().filter(status='PENDING')
        raw_ids = (request.query_params.get('ids') or '').strip()
        if raw_ids:
            try:
                ids = {int(value) for value in raw_ids.split(',') if value.strip()}
            except ValueError:
                return Response(
                    {'detail': 'ids doit être une liste d’identifiants.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            jetons = jetons.filter(pk__in=ids)
            if jetons.count() != len(ids):
                return Response(
                    {'detail': 'Certains jetons ne sont plus en attente de paiement.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        jetons = list(jetons)
        if not jetons:
            return Response(
                {'detail': 'Aucune indemnité en attente à exporter.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        missing = []
        for jeton in jetons:
            expert = jeton.expert
            name = expert.user.get_full_name() or expert.user.username
            if not expert.bank_account or not expert.bank_name:
                missing.append(name)
        if missing:
            return Response(
                {
                    'detail': (
                        'Coordonnées bancaires manquantes pour : '
                        + ', '.join(sorted(missing))
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_date = (request.query_params.get('execution_date') or '').strip()
        try:
            execution_date = date.fromisoformat(raw_date) if raw_date else date.today()
        except ValueError:
            return Response(
                {'detail': 'execution_date doit être une date AAAA-MM-JJ.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        xml = build_pain_001(
            jetons,
            debtor_name=config['debtor_name'],
            debtor_iban=config['debtor_iban'],
            debtor_bic=config['debtor_bic'],
            currency=config['currency'],
            execution_date=execution_date,
        )
        response = HttpResponse(
            xml,
            content_type='application/xml; charset=utf-8',
        )
        response['Content-Disposition'] = (
            f'attachment; filename="pain001-{execution_date.isoformat()}.xml"'
        )
        return response

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques sur les jetons"""
        total_distribues = self.get_queryset().aggregate(
            total=Sum('montant', output_field=DecimalField())
        )['total'] or Decimal('0')

        total_payes = self.get_queryset().filter(status='PAID').aggregate(
            total=Sum('montant', output_field=DecimalField())
        )['total'] or Decimal('0')

        return Response({
            'total_jetons_distribues': str(total_distribues),
            'total_jetons_payes': str(total_payes),
            'nombre_experts': Expert.objects.filter(
                jetons__isnull=False
            ).distinct().count(),
            'jetons_en_attente': self.get_queryset().filter(status='PENDING').count()
        })
