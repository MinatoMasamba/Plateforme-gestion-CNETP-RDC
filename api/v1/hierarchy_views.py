"""Views for CNETP hierarchy API endpoints"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.governance.models import (
    ExecutiveLevel, ComitePilotage, TechnicalCell,
    CTM, WG, OriginStructure, Affectation
)
from .hierarchy_serializers import (
    ExecutiveLevelSerializer, SteeringCommitteeSerializer,
    TechnicalCellSerializer, OriginStructureSerializer,
    HierarchyOverviewSerializer
)


class ExecutiveLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for Executive Level positions"""
    queryset = ExecutiveLevel.objects.select_related('expert__user')
    serializer_class = ExecutiveLevelSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get overview of executive level"""
        executives = ExecutiveLevel.objects.all()
        serializer = ExecutiveLevelSerializer(executives, many=True)
        return Response({
            'total_positions': executives.count(),
            'positions': serializer.data
        })


class SteeringCommitteeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for Steering Committee"""
    queryset = ComitePilotage.objects.prefetch_related(
        'pilotagemembreship_set__expert__user'
    )
    serializer_class = SteeringCommitteeSerializer
    permission_classes = [IsAuthenticated]


class TechnicalCellViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for Technical Cell"""
    queryset = TechnicalCell.objects.prefetch_related(
        'ctcmembership_set__expert__user'
    )
    serializer_class = TechnicalCellSerializer
    permission_classes = [IsAuthenticated]


class OriginStructureViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for Origin Structures (Girons)"""
    queryset = OriginStructure.objects.prefetch_related('experts__user')
    serializer_class = OriginStructureSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['giron']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'giron']
    ordering = ['giron', 'name']
    
    @action(detail=True, methods=['get'])
    def experts(self, request, pk=None):
        """Get experts from this structure"""
        from .experts_serializers import ExpertDetailSerializer
        structure = self.get_object()
        experts = structure.experts.all()
        serializer = ExpertDetailSerializer(experts, many=True)
        return Response({
            'structure': structure.name,
            'expert_count': experts.count(),
            'experts': serializer.data
        })


class HierarchyViewSet(viewsets.ViewSet):
    """Master API endpoints for CNETP hierarchy"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='overview')
    def overview(self, request):
        """Get complete hierarchy overview"""
        from apps.experts.models import Expert
        
        overview_data = {
            'total_experts': Expert.objects.count(),
            'total_ctm': CTM.objects.count(),
            'total_wg': WG.objects.count(),
            'total_structures': OriginStructure.objects.count(),
            'executive_level': ExecutiveLevel.objects.count(),
            'steering_committee': ComitePilotage.objects.count(),
            'steering_committee_members': ComitePilotage.objects.first().pilotagemembreship_set.count() if ComitePilotage.objects.exists() else 0,
            'technical_cell': TechnicalCell.objects.count(),
            'technical_cell_members': TechnicalCell.objects.first().ctcmembership_set.count() if TechnicalCell.objects.exists() else 0,
            'total_affectations': Affectation.objects.count(),
        }
        return Response(overview_data)
    
    @action(detail=False, methods=['get'], url_path='ctm')
    def ctm_list(self, request):
        """Get all CTM with summary"""
        from api.v1.governance_serializers import CTMBasicSerializer
        
        ctms = CTM.objects.prefetch_related('working_groups', 'affectations')
        data = []
        for ctm in ctms:
            wg_count = ctm.working_groups.count()
            expert_count = Affectation.objects.filter(ctm=ctm).values('expert').distinct().count()
            data.append({
                'id': ctm.id,
                'number': ctm.number,
                'name': ctm.name,
                'working_groups': wg_count,
                'experts': expert_count,
                'scientific_president': ctm.scientific_president.full_name if ctm.scientific_president else None,
            })
        return Response(data)
    
    @action(detail=False, methods=['get'], url_path='wg')
    def wg_list(self, request):
        """Get all WG with summary"""
        wgs = WG.objects.select_related('ctm').prefetch_related('affectations')
        data = []
        for wg in wgs:
            expert_count = wg.affectations.values('expert').distinct().count()
            data.append({
                'id': wg.id,
                'ctm': f"CTM {wg.ctm.number}",
                'name': wg.name,
                'experts': expert_count,
                'president': wg.president.full_name if wg.president else None,
            })
        return Response(data)
    
    @action(detail=False, methods=['get'], url_path='structures')
    def structures_list(self, request):
        """Get all structures (Girons)"""
        structures = OriginStructure.objects.prefetch_related('experts')
        serializer = OriginStructureSerializer(structures, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='')
    def root(self, request):
        """Root endpoint - returns hierarchy overview"""
        return self.overview(request)

