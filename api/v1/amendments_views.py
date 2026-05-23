from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Avg, Case, When, IntegerField

from apps.amendments.models import Amendement, Vote, ResultatVote
from apps.experts.models import Expert
from .amendments_serializers import (
    AmendementBasicSerializer, AmendementDetailSerializer,
    AmendementCreateUpdateSerializer, AmendementStatusUpdateSerializer,
    VoteSerializer, VoteCreateSerializer, ResultatVoteSerializer,
    AmendementSummarySerializer, AmendementStatsSerializer
)
from .permissions import IsExpert, IsCTCCoordinator


class AmendementViewSet(viewsets.ModelViewSet):
    """ViewSet pour les amendements"""
    queryset = Amendement.objects.select_related(
        'norme', 'version', 'proposed_by__user'
    ).prefetch_related('votes', 'resultat_vote')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['norme__id', 'status', 'version__id']
    search_fields = ['title', 'description', 'justification']
    ordering_fields = ['proposal_date', 'status']
    ordering = ['-proposal_date']
    
    def get_serializer_class(self):
        """Retourner le serializer approprié"""
        if self.action == 'retrieve':
            return AmendementDetailSerializer
        elif self.action == 'list':
            return AmendementBasicSerializer
        elif self.action == 'update_status':
            return AmendementStatusUpdateSerializer
        elif self.action == 'create' or self.action == 'update':
            return AmendementCreateUpdateSerializer
        return AmendementDetailSerializer
    
    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['create']:
            # Seul un expert peut proposer un amendement
            return [IsExpert()]
        elif self.action in ['update_status', 'update', 'partial_update', 'destroy']:
            # Seul CTC peut mettre à jour le statut
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Ajouter l'expert qui propose l'amendement"""
        # Récupérer l'expert associé à l'utilisateur
        try:
            expert = Expert.objects.get(user=self.request.user)
            serializer.save(proposed_by=expert)
        except Expert.DoesNotExist:
            return Response(
                {'detail': 'L\'utilisateur doit être un expert pour proposer un amendement.'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])
    def update_status(self, request, pk=None):
        """Mettre à jour le statut d'un amendement"""
        amendement = self.get_object()
        serializer = AmendementStatusUpdateSerializer(
            amendement,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AmendementDetailSerializer(amendement).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsExpert])
    def vote(self, request, pk=None):
        """Voter sur un amendement"""
        amendement = self.get_object()
        
        # Vérifier que l'utilisateur est un expert
        try:
            voter = Expert.objects.get(user=request.user)
        except Expert.DoesNotExist:
            return Response(
                {'detail': 'Seul un expert peut voter.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que l'amendement est en révision
        if amendement.status not in ['UNDER_REVIEW', 'PROPOSED']:
            return Response(
                {'detail': 'Le vote n\'est pas possible pour cet amendement.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer le vote
        serializer = VoteCreateSerializer(
            data=request.data,
            context={'amendement': amendement, 'voter': voter}
        )
        serializer.is_valid(raise_exception=True)
        vote = serializer.save()
        
        return Response(
            VoteSerializer(vote).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def votes(self, request, pk=None):
        """Récupérer les votes d'un amendement"""
        amendement = self.get_object()
        votes = amendement.votes.all()
        
        # Filtrer optionnellement par type de vote
        vote_type = request.query_params.get('vote')
        if vote_type:
            votes = votes.filter(vote=vote_type)
        
        serializer = VoteSerializer(votes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Récupérer les résultats de vote"""
        amendement = self.get_object()
        
        if hasattr(amendement, 'resultat_vote'):
            serializer = ResultatVoteSerializer(amendement.resultat_vote)
            return Response(serializer.data)
        
        return Response(
            {'detail': 'Aucun résultat de vote disponible.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['get'])
    def by_norme(self, request):
        """Récupérer les amendements d'une norme"""
        norme_id = request.query_params.get('norme_id')
        if not norme_id:
            return Response(
                {'detail': 'norme_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        amendements = self.get_queryset().filter(norme_id=norme_id)
        serializer = AmendementBasicSerializer(amendements, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Récupérer les amendements en attente de révision"""
        amendements = self.get_queryset().filter(
            status__in=['PROPOSED', 'UNDER_REVIEW']
        )
        serializer = AmendementBasicSerializer(amendements, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques sur les amendements"""
        total = self.get_queryset().count()
        
        # Par statut
        by_status = {}
        for status_choice in Amendement.STATUS_CHOICES:
            status_key = status_choice[0]
            count = self.get_queryset().filter(status=status_key).count()
            by_status[status_key] = count
        
        # Par norme
        by_norme = {}
        normes = self.get_queryset().values('norme__reference_number').annotate(
            count=Count('id')
        )
        for item in normes:
            by_norme[item['norme__reference_number']] = item['count']
        
        # Taux d'approbation moyen
        resultats = ResultatVote.objects.aggregate(
            avg_approval=Avg('approval_percentage')
        )
        avg_approval = resultats['avg_approval'] or 0.0
        
        response_data = {
            'total_amendments': total,
            'by_status': by_status,
            'by_norme': by_norme,
            'average_approval_rate': avg_approval
        }
        
        return Response(response_data)


class VoteViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les votes (lecture seule)"""
    queryset = Vote.objects.select_related(
        'amendement__norme', 'voter__user'
    )
    serializer_class = VoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['amendement__id', 'vote']
    ordering_fields = ['vote_date']
    ordering = ['-vote_date']
    
    @action(detail=False, methods=['get'])
    def my_votes(self, request):
        """Récupérer les votes de l'utilisateur"""
        try:
            expert = Expert.objects.get(user=request.user)
            votes = self.get_queryset().filter(voter=expert)
            serializer = VoteSerializer(votes, many=True)
            return Response(serializer.data)
        except Expert.DoesNotExist:
            return Response(
                {'detail': 'Cet utilisateur n\'est pas un expert.'},
                status=status.HTTP_404_NOT_FOUND
            )


class ResultatVoteViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les résultats de vote"""
    queryset = ResultatVote.objects.select_related('amendement__norme')
    serializer_class = ResultatVoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['amendement__norme__id', 'quorum_reached']
    
    @action(detail=False, methods=['post'])
    def recalculate_all(self, request):
        """Recalculer tous les résultats de vote (Admin)"""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Seul un admin peut recalculer les résultats.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        resultats = self.get_queryset()
        for resultat in resultats:
            resultat.calculate_results()
        
        return Response({
            'message': f'{resultats.count()} résultats recalculés'
        })
