from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import date

from apps.validation.models import LegisticReview
from apps.norms.models import Norme
from .validation_serializers import (
    LegisticReviewBasicSerializer,
    LegisticReviewDetailSerializer,
    LegisticReviewStartSerializer,
    LegisticReviewCompleteSerializer,
    LegisticReviewRejectSerializer
)
from .permissions import IsLegist, IsCTCCoordinator


class LegisticReviewViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion du toilettage légistique"""
    queryset = LegisticReview.objects.select_related('norme', 'legist')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'norme__status']
    search_fields = ['norme__reference_number', 'norme__title', 'legist__user__first_name']
    ordering_fields = ['created_at', 'status', 'review_start_date']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retourner le serializer approprié"""
        if self.action == 'retrieve':
            return LegisticReviewDetailSerializer
        elif self.action == 'list':
            return LegisticReviewBasicSerializer
        elif self.action == 'start_review':
            return LegisticReviewStartSerializer
        elif self.action == 'complete_review':
            return LegisticReviewCompleteSerializer
        elif self.action == 'reject_review':
            return LegisticReviewRejectSerializer
        return LegisticReviewBasicSerializer
    
    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['start_review']:
            # Coordinateur CTC assigne un légiste
            return [IsCTCCoordinator()]
        elif self.action in ['complete_review', 'reject_review']:
            # Le légiste lui-même complète le toilettage
            return [IsLegist()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Récupérer tous les toilettages en attente"""
        reviews = self.get_queryset().filter(status__in=['PENDING', 'ASSIGNED'])
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def in_review(self, request):
        """Récupérer tous les toilettages en cours"""
        reviews = self.get_queryset().filter(status='IN_REVIEW')
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start_review(self, request, pk=None):
        """Démarrer le toilettage légistique (assigner légiste)"""
        review = self.get_object()
        
        # Vérifier que le statut permet de démarrer
        if review.status not in ['PENDING']:
            return Response(
                {'error': f'Cannot start review with status {review.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            review.legist = serializer.validated_data['legist']
            review.comments = serializer.validated_data.get('comments', '')
            review.status = 'ASSIGNED'
            review.review_start_date = date.today()
            review.save()
            
            return Response(
                LegisticReviewDetailSerializer(review).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete_review(self, request, pk=None):
        """Compléter le toilettage légistique"""
        review = self.get_object()
        
        # Vérifier permissions : le légiste assigné ou CTC
        if review.legist != request.user.expert_profile and not request.user.is_ctc_staff:
            return Response(
                {'error': 'You are not the assigned legist'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que le statut permet de compléter
        if review.status not in ['ASSIGNED', 'IN_REVIEW']:
            return Response(
                {'error': f'Cannot complete review with status {review.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            review.status = 'REVIEW_COMPLETED'
            review.approval_date = serializer.validated_data.get('approval_date', date.today())
            if serializer.validated_data.get('comments'):
                review.comments = serializer.validated_data['comments']
            review.review_end_date = date.today()
            review.save()
            
            # Mettre à jour la norme
            review.norme.status = 'LEGISTIC_REVIEW'
            review.norme.legistic_review_date = date.today()
            review.norme.save()
            
            return Response(
                LegisticReviewDetailSerializer(review).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject_review(self, request, pk=None):
        """Rejeter le toilettage légistique"""
        review = self.get_object()
        
        # Vérifier permissions : le légiste ou CTC
        if review.legist != request.user.expert_profile and not request.user.is_ctc_staff:
            return Response(
                {'error': 'You are not the assigned legist'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que le statut permet de rejeter
        if review.status not in ['ASSIGNED', 'IN_REVIEW']:
            return Response(
                {'error': f'Cannot reject review with status {review.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            review.status = 'REJECTED'
            review.comments = serializer.validated_data.get('comments', '')
            review.review_end_date = date.today()
            review.save()
            
            # Revenir à INTERNAL_REVIEW pour que la norme soit révisée
            review.norme.status = 'INTERNAL_REVIEW'
            review.norme.save()
            
            return Response(
                LegisticReviewDetailSerializer(review).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Récupérer les toilettages assignés à l'utilisateur"""
        if not hasattr(request.user, 'expert_profile'):
            return Response(
                {'error': 'You are not an expert'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        expert = request.user.expert_profile
        reviews = self.get_queryset().filter(legist=expert)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
