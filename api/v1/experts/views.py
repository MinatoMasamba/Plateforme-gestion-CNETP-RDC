from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from django.utils import timezone

from apps.experts.models import Expert, Structure
from .serializers import (
    ExpertDetailSerializer, ExpertBasicSerializer, ExpertCreateUpdateSerializer,
    ExpertInscriptionSerializer, StructureSerializer
)
from ..permissions import IsExpert, IsCTCCoordinator
from ..filters import ExpertFilter, StructureFilter


class StructureViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les structures (lecture seule)"""
    queryset = Structure.objects.all()
    serializer_class = StructureSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = StructureFilter
    search_fields = ['name', 'acronym', 'category']
    ordering_fields = ['name', 'category']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def experts(self, request, pk=None):
        """Récupérer les experts d'une structure"""
        structure = self.get_object()
        experts = structure.experts.all()
        serializer = ExpertBasicSerializer(experts, many=True)
        return Response(serializer.data)


class ExpertViewSet(viewsets.ModelViewSet):
    """ViewSet complet pour les experts"""
    queryset = Expert.objects.select_related('user', 'structure').prefetch_related('governance_affectations')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExpertFilter
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['inscription_date', 'status', 'user__last_name']
    ordering = ['-inscription_date']

    def _user_has_ctm_role(self, user, ctm_id):
        """Vérifie si l'utilisateur est Président, Rapporteur ou Secrétaire du CTM."""
        if user.is_superuser or getattr(user, 'is_ctc_staff', False):
            return True
        try:
            requester = Expert.objects.get(user=user)
        except Expert.DoesNotExist:
            return False
        from apps.governance.models import CTM
        return CTM.objects.filter(
            id=ctm_id
        ).filter(
            models.Q(scientific_president=requester) |
            models.Q(rapporteur=requester) |
            models.Q(secretary=requester)
        ).exists()

    def _target_ctm_id(self, expert):
        affectation = expert.governance_affectations.order_by('-is_primary_ctm', '-is_primary_wg').first()
        if affectation:
            return affectation.ctm_id
        return expert.ctm_id

    def get_serializer_class(self):
        """Retourner le serializer approprié selon l'action"""
        if self.action == 'retrieve':
            return ExpertDetailSerializer
        elif self.action == 'list':
            return ExpertDetailSerializer
        elif self.action == 'create':
            return ExpertCreateUpdateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ExpertCreateUpdateSerializer
        elif self.action == 'inscription':
            return ExpertInscriptionSerializer
        return ExpertDetailSerializer

    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['create', 'inscription']:
            # N'importe qui peut s'inscrire
            return []
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Seul l'expert lui-même ou CTC peut modifier
            return [IsAuthenticated()]
        elif self.action == 'activate':
            # Seul CTC peut activer
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]

    def partial_update(self, request, *args, **kwargs):
        expert = self.get_object()
        requested_status = request.data.get('status')
        if requested_status == 'ACTIVE':
            ctm_id = request.data.get('ctm_id') or self._target_ctm_id(expert)
            if not ctm_id or not self._user_has_ctm_role(request.user, ctm_id):
                raise PermissionDenied("Un rôle CTM est requis pour accepter l'adhésion de cet expert.")
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['post'], permission_classes=[])
    def inscription(self, request):
        """Endpoint public pour l'inscription d'un nouvel expert"""
        serializer = ExpertInscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expert = serializer.save()

        # Retourner les détails de l'expert créé
        output_serializer = ExpertDetailSerializer(expert)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])
    def activate(self, request, pk=None):
        """Activer un expert (seul CTC)"""
        expert = self.get_object()
        if expert.status == 'ACTIVE':
            return Response(
                {'detail': 'Cet expert est déjà actif.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        expert.status = 'ACTIVE'
        expert.save()

        serializer = ExpertDetailSerializer(expert)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='admit-to-ctm')
    def admit_to_ctm(self, request, pk=None):
        """Accepter l'adhésion CTM, affecter au WG, créer le token d'activation et envoyer l'email."""
        from apps.governance.models import Affectation

        expert = self.get_object()
        ctm_id = request.data.get('ctm_id') or self._target_ctm_id(expert)
        wg_id  = request.data.get('wg_id')

        if not ctm_id:
            return Response({'detail': 'ctm_id est requis.'}, status=status.HTTP_400_BAD_REQUEST)
        if not self._user_has_ctm_role(request.user, ctm_id):
            raise PermissionDenied("Un rôle CTM est requis pour accepter l'adhésion de cet expert.")

        expert.ctm_id          = ctm_id
        expert.status          = 'ACTIVE'
        expert.activation_date = timezone.now()

        try:
            reviewer = Expert.objects.get(user=request.user)
            expert.accepted_by = reviewer
            expert.accepted_at = timezone.now()
        except Expert.DoesNotExist:
            pass

        expert.save(update_fields=['ctm', 'status', 'activation_date', 'accepted_by', 'accepted_at'])

        if wg_id:
            Affectation.objects.update_or_create(
                expert=expert,
                ctm_id=ctm_id,
                wg_id=wg_id,
                defaults={'is_primary_ctm': True, 'is_primary_wg': True},
            )

        # Crée le token d'activation → le signal envoie l'email automatiquement
        from apps.mobileapp.models import ActivationToken
        ActivationToken.create_for_expert(expert)

        return Response(ExpertDetailSerializer(expert).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='reject')
    def reject(self, request, pk=None):
        """Rejeter la demande d'adhésion avec un motif."""
        expert = self.get_object()
        if expert.status != 'PENDING':
            return Response(
                {'detail': 'Seuls les experts en attente peuvent être rejetés.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ctm_id = self._target_ctm_id(expert)
        if not self._user_has_ctm_role(request.user, ctm_id):
            raise PermissionDenied("Un rôle CTM est requis pour rejeter cette demande.")

        reason = request.data.get('reason', '')
        try:
            reviewer = Expert.objects.get(user=request.user)
            expert.rejected_by = reviewer
        except Expert.DoesNotExist:
            pass

        expert.status          = 'REJECTED'
        expert.rejected_at     = timezone.now()
        expert.rejection_reason = reason
        expert.save(update_fields=['status', 'rejected_by', 'rejected_at', 'rejection_reason'])

        try:
            from apps.mobileapp.signals import create_notification_for_user
            create_notification_for_user(
                user=expert.user,
                title="Votre demande d'adhésion CNETP",
                body=f"Votre demande au CTM a été refusée. Motif : {reason or 'Non précisé'}",
                notification_type='SYSTEM',
                priority='HIGH',
                data={'expert_id': expert.id, 'reason': reason},
            )
        except Exception:
            pass

        return Response(ExpertDetailSerializer(expert).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='pending-for-my-ctm')
    def pending_for_my_ctm(self, request):
        """Liste des experts PENDING pour les CTM que l'utilisateur connecté dirige."""
        try:
            me = Expert.objects.get(user=request.user)
        except Expert.DoesNotExist:
            return Response([])

        from apps.governance.models import CTM
        my_ctms = CTM.objects.filter(
            models.Q(scientific_president=me) |
            models.Q(rapporteur=me) |
            models.Q(secretary=me)
        )
        pending = Expert.objects.filter(
            ctm__in=my_ctms, status='PENDING'
        ).select_related('user', 'structure', 'ctm')
        return Response(ExpertDetailSerializer(pending, many=True).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='pending-count-for-my-ctm')
    def pending_count_for_my_ctm(self, request):
        """Compteur de demandes en attente — utilisé par le badge du widget web."""
        try:
            me = Expert.objects.get(user=request.user)
        except Expert.DoesNotExist:
            return Response({'count': 0, 'is_ctm_leader': False})

        from apps.governance.models import CTM
        my_ctms = CTM.objects.filter(
            models.Q(scientific_president=me) |
            models.Q(rapporteur=me) |
            models.Q(secretary=me)
        )
        count = Expert.objects.filter(ctm__in=my_ctms, status='PENDING').count()
        return Response({'count': count, 'is_ctm_leader': my_ctms.exists()})

    @action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])
    def deactivate(self, request, pk=None):
        """Désactiver un expert (seul CTC)"""
        expert = self.get_object()
        if expert.status == 'INACTIVE':
            return Response(
                {'detail': 'Cet expert est déjà inactif.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        expert.status = 'INACTIVE'
        expert.save()

        serializer = ExpertDetailSerializer(expert)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Récupérer le profil de l'utilisateur connecté."""
        return self.my_profile(request)

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Récupérer le profil de l'utilisateur connecté"""
        try:
            expert = Expert.objects.get(user=request.user)
            serializer = ExpertDetailSerializer(expert)
            return Response(serializer.data)
        except Expert.DoesNotExist:
            return Response(
                {'detail': 'Cet utilisateur n\'est pas un expert.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def affectations(self, request, pk=None):
        """Récupérer les affectations d'un expert"""
        from ..governance.serializers import AffectationSerializer
        expert = self.get_object()
        affectations = expert.governance_affectations.all()
        serializer = AffectationSerializer(affectations, many=True)
        return Response(serializer.data)
