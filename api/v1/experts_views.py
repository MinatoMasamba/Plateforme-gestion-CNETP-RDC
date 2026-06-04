from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models

from apps.experts.models import Expert, Structure
from .experts_serializers import (
    ExpertDetailSerializer, ExpertBasicSerializer, ExpertCreateUpdateSerializer,
    ExpertInscriptionSerializer, StructureSerializer
)
from .permissions import IsExpert, IsCTCCoordinator
from .filters import ExpertFilter, StructureFilter


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
        """Un role CTM est un poste de leadership CTM, pas une simple affectation membre."""
        if user.is_superuser or getattr(user, 'is_ctc_staff', False):
            return True

        try:
            requester = Expert.objects.get(user=user)
        except Expert.DoesNotExist:
            return False

        return requester.governance_affectations.filter(
            ctm_id=ctm_id,
        ).filter(
            models.Q(ctm__scientific_president=requester) |
            models.Q(ctm__rapporteur=requester) |
            models.Q(ctm__secretary=requester)
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
        """Accepter l'adhésion CTM et préparer l'affectation WG."""
        from apps.governance.models import Affectation

        expert = self.get_object()
        ctm_id = request.data.get('ctm_id') or self._target_ctm_id(expert)
        wg_id = request.data.get('wg_id')

        if not ctm_id:
            return Response({'detail': 'ctm_id est requis.'}, status=status.HTTP_400_BAD_REQUEST)
        if not self._user_has_ctm_role(request.user, ctm_id):
            raise PermissionDenied("Un rôle CTM est requis pour accepter l'adhésion de cet expert.")

        expert.ctm_id = ctm_id
        expert.status = 'ACTIVE'
        expert.save(update_fields=['ctm', 'status'])

        if wg_id:
            Affectation.objects.update_or_create(
                expert=expert,
                ctm_id=ctm_id,
                wg_id=wg_id,
                defaults={'is_primary_ctm': True, 'is_primary_wg': True},
            )

        serializer = ExpertDetailSerializer(expert)
        return Response(serializer.data)
    
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
        from .governance_serializers import AffectationSerializer
        expert = self.get_object()
        affectations = expert.governance_affectations.all()
        serializer = AffectationSerializer(affectations, many=True)
        return Response(serializer.data)
