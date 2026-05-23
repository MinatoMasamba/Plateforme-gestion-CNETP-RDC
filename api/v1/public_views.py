from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.public.models import PublicAmendement
from apps.norms.models import Norme
from api.v1.public_serializers import (
    PublicAmendementSerializer,
    PublicAmendementDetailSerializer,
    PublicAmendementReviewSerializer
)
from api.v1.permissions import IsCTCCoordinator


class PublicAmendementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les amendements publics.
    - Les utilisateurs publics peuvent créer/lister (readonly pour les leurs)
    - Le CTC peut réviser et approuver/rejeter
    """
    queryset = PublicAmendement.objects.all()
    serializer_class = PublicAmendementSerializer

    def get_permissions(self):
        """
        Permissions granulaires:
        - create: AllowAny (public peut soumettre)
        - list: AllowAny (lecture publique)
        - retrieve: AllowAny
        - update/destroy: Réservé à CTC
        - review: IsCTCCoordinator uniquement
        """
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy', 'review']:
            return [IsAuthenticated(), IsCTCCoordinator()]
        return [AllowAny()]

    def get_serializer_class(self):
        """Utiliser le serializer approprié selon l'action"""
        if self.action == 'retrieve':
            return PublicAmendementDetailSerializer
        elif self.action == 'review':
            return PublicAmendementReviewSerializer
        return PublicAmendementSerializer

    def get_queryset(self):
        """Filtrer les amendements publics"""
        queryset = PublicAmendement.objects.all()

        # Filter par norme si spécifié
        norme_id = self.request.query_params.get('norme_id')
        if norme_id:
            queryset = queryset.filter(norme_id=norme_id)

        # Filter par statut si spécifié
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-created_at')

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def submit_for_norm(self, request):
        """
        Soumettre un amendement public pour une norme spécifique (phase d'enquête)
        POST /public-amendments/submit_for_norm/
        """
        norme_id = request.data.get('norme_id')
        
        # Vérifier que la norme existe et est en enquête publique
        norme = get_object_or_404(Norme, id=norme_id)
        
        if norme.status != 'PUBLIC_INQUIRY':
            return Response(
                {'error': 'Cette norme n\'est pas en phase d\'enquête publique'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Créer l'amendement
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(norme=norme)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def review(self, request, pk=None):
        """
        Réviser un amendement public (CTC only)
        POST /public-amendments/{id}/review/
        """
        amendment = self.get_object()
        serializer = PublicAmendementReviewSerializer(amendment, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def by_norm(self, request):
        """
        Lister les amendements publics d'une norme
        GET /public-amendments/by_norm/?norme_id=1
        """
        norme_id = request.query_params.get('norme_id')
        
        if not norme_id:
            return Response(
                {'error': 'norme_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        amendments = PublicAmendement.objects.filter(norme_id=norme_id).order_by('-created_at')
        serializer = self.get_serializer(amendments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending_review(self, request):
        """
        Lister les amendements en attente de révision (CTC only)
        GET /public-amendments/pending_review/
        """
        amendments = PublicAmendement.objects.filter(
            status__in=['PENDING', 'UNDER_REVIEW']
        ).order_by('created_at')
        serializer = self.get_serializer(amendments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def statistics(self, request):
        """
        Statistiques sur les amendements publics
        GET /public-amendments/statistics/
        """
        norme_id = request.query_params.get('norme_id')
        
        if norme_id:
            amendments = PublicAmendement.objects.filter(norme_id=norme_id)
        else:
            amendments = PublicAmendement.objects.all()

        stats = {
            'total': amendments.count(),
            'pending': amendments.filter(status='PENDING').count(),
            'under_review': amendments.filter(status='UNDER_REVIEW').count(),
            'accepted': amendments.filter(status='ACCEPTED').count(),
            'rejected': amendments.filter(status='REJECTED').count(),
            'archived': amendments.filter(status='ARCHIVED').count(),
        }

        return Response(stats)
