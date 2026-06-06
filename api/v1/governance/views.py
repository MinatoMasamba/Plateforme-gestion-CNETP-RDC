from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.governance.models import CTM, WG, Affectation, ComitePilotage, PilotageMembreship
from .serializers import (
    CTMBasicSerializer, CTMDetailSerializer, CTMCreateUpdateSerializer,
    WGBasicSerializer, WGDetailSerializer, WGCreateUpdateSerializer,
    AffectationSerializer, AffectationCreateSerializer, AffectationBulkSerializer,
    ComitePilotageSerializer, RoleCTMSerializer
)
from ..permissions import IsCTCCoordinator, IsExpertOfCTM
from ..filters import CTMFilter, WGFilter


class CTMViewSet(viewsets.ModelViewSet):
    """ViewSet pour les Comités Techniques (CTM)"""
    queryset = CTM.objects.prefetch_related(
        'working_groups', 'affectations__expert'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CTMFilter
    search_fields = ['name', 'description', 'iso_reference']
    ordering_fields = ['number', 'name']
    ordering = ['number']

    def get_serializer_class(self):
        """Retourner le serializer approprié"""
        if self.action == 'retrieve':
            return CTMDetailSerializer
        elif self.action == 'list':
            return CTMBasicSerializer
        else:
            return CTMCreateUpdateSerializer

    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['get'])
    def experts(self, request, pk=None):
        """Récupérer tous les experts du CTM"""
        from ..experts.serializers import ExpertDetailSerializer
        ctm = self.get_object()
        experts = set(
            affectation.expert for affectation in ctm.affectations.all()
        )
        serializer = ExpertDetailSerializer(experts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def working_groups(self, request, pk=None):
        """Récupérer les groupes de travail du CTM"""
        ctm = self.get_object()
        wgs = ctm.working_groups.all()
        serializer = WGBasicSerializer(wgs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def roles(self, request, pk=None):
        """Récupérer les rôles du CTM"""
        ctm = self.get_object()
        roles = ctm.roles.all()
        serializer = RoleCTMSerializer(roles, many=True)
        return Response(serializer.data)


class WGViewSet(viewsets.ModelViewSet):
    """ViewSet pour les Groupes de Travail (WG)"""
    queryset = WG.objects.select_related('ctm').prefetch_related('affectations__expert')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = WGFilter
    search_fields = ['name', 'description', 'scope']
    ordering_fields = ['ctm__number', 'number', 'name']
    ordering = ['ctm__number', 'number']

    def get_serializer_class(self):
        """Retourner le serializer approprié"""
        if self.action == 'retrieve':
            return WGDetailSerializer
        elif self.action == 'list':
            return WGDetailSerializer
        else:
            return WGCreateUpdateSerializer

    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['get'])
    def experts(self, request, pk=None):
        """Récupérer tous les experts du WG"""
        from ..experts.serializers import ExpertDetailSerializer
        wg = self.get_object()
        experts = set(
            affectation.expert for affectation in wg.affectations.all()
        )
        serializer = ExpertDetailSerializer(experts, many=True)
        return Response(serializer.data)


class AffectationViewSet(viewsets.ModelViewSet):
    """ViewSet pour les affectations (Expert → CTM/WG)"""
    queryset = Affectation.objects.select_related(
        'expert__user', 'expert__structure', 'ctm', 'wg'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['expert', 'expert__user__username', 'ctm', 'ctm__number', 'wg', 'wg__number']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Retourner le serializer approprié"""
        if self.action == 'create' or self.action == 'update':
            return AffectationCreateSerializer
        elif self.action == 'bulk_create':
            return AffectationBulkSerializer
        return AffectationSerializer

    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_create']:
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], permission_classes=[IsCTCCoordinator])
    def bulk_create(self, request):
        """Créer plusieurs affectations en une seule requête"""
        serializer = AffectationBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        affectations = serializer.save()

        output_serializer = AffectationSerializer(affectations, many=True)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def by_expert(self, request):
        """Récupérer les affectations d'un expert"""
        expert_id = request.query_params.get('expert_id')
        if not expert_id:
            return Response(
                {'detail': 'expert_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        affectations = self.get_queryset().filter(expert_id=expert_id)
        serializer = AffectationSerializer(affectations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_ctm(self, request):
        """Récupérer les affectations d'un CTM"""
        ctm_id = request.query_params.get('ctm_id')
        if not ctm_id:
            return Response(
                {'detail': 'ctm_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        affectations = self.get_queryset().filter(ctm_id=ctm_id)
        serializer = AffectationSerializer(affectations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_wg(self, request):
        """Récupérer les affectations d'un WG"""
        wg_id = request.query_params.get('wg_id')
        if not wg_id:
            return Response(
                {'detail': 'wg_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        affectations = self.get_queryset().filter(wg_id=wg_id)
        serializer = AffectationSerializer(affectations, many=True)
        return Response(serializer.data)



class RoleCTMViewSet(viewsets.ModelViewSet):
    """ViewSet pour les rôles dans les CTM (PilotageMembreship)"""
    queryset = PilotageMembreship.objects.select_related('comite', 'expert__user')
    permission_classes = [IsAuthenticated]
    serializer_class = RoleCTMSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['comite', 'role', 'expert']
    ordering_fields = ['created_at', 'role']
    ordering = ['-created_at']

    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]


class ComitePilotageViewSet(viewsets.ModelViewSet):
    """ViewSet pour le comité de pilotage"""
    queryset = PilotageMembreship.objects.select_related(
        'expert__user', 'expert__structure', 'comite'
    )
    permission_classes = [IsAuthenticated]
    serializer_class = ComitePilotageSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['comite__id', 'role', 'expert']
    ordering_fields = ['created_at', 'role']
    ordering = ['-created_at']

    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def active_members(self, request):
        """Récupérer les membres actifs du comité"""
        comite = ComitePilotage.objects.first()
        if not comite:
            return Response([], status=status.HTTP_200_OK)
        members = self.get_queryset().filter(comite=comite)
        serializer = ComitePilotageSerializer(members, many=True)
        return Response(serializer.data)
