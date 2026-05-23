from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Avg, Case, When, IntegerField, F
from django.utils import timezone

from apps.meetings.models import Reunion, Presence, ProcessusVerbaux
from apps.experts.models import Expert
from .meetings_serializers import (
    ReunionBasicSerializer, ReunionDetailSerializer,
    ReunionCreateUpdateSerializer, ReunionStatusUpdateSerializer,
    PresenceSerializer, PresenceCheckInSerializer,
    ProcessusVerbauxSerializer, ReunionSummarySerializer,
    ReunionStatsSerializer
)
from .permissions import IsExpert, IsCTCCoordinator


class ReunionViewSet(viewsets.ModelViewSet):
    """ViewSet pour les réunions"""
    queryset = Reunion.objects.select_related(
        'organisateur__user', 'pv__signed_by'
    ).prefetch_related('presences__expert__user')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'status']
    search_fields = ['titre', 'description', 'ordre_jour']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']
    
    def get_serializer_class(self):
        """Retourner le serializer approprié"""
        if self.action == 'retrieve':
            return ReunionDetailSerializer
        elif self.action == 'list':
            return ReunionBasicSerializer
        elif self.action == 'update_status':
            return ReunionStatusUpdateSerializer
        elif self.action == 'create' or self.action == 'update':
            return ReunionCreateUpdateSerializer
        return ReunionDetailSerializer
    
    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['create']:
            # Seul CTC peut créer une réunion
            return [IsCTCCoordinator()]
        elif self.action in ['update_status', 'update', 'partial_update', 'destroy']:
            # Seul CTC peut mettre à jour
            return [IsCTCCoordinator()]
        elif self.action in ['checkin_presence', 'generate_pv']:
            # Expert ou CTC peut participer
            return [IsExpert()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Ajouter le CTC qui organise la réunion"""
        try:
            expert = Expert.objects.get(user=self.request.user)
            serializer.save(organisateur=expert)
        except Expert.DoesNotExist:
            return Response(
                {'detail': 'L\'utilisateur doit être un expert.'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])
    def update_status(self, request, pk=None):
        """Mettre à jour le statut d'une réunion"""
        reunion = self.get_object()
        serializer = ReunionStatusUpdateSerializer(
            reunion,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReunionDetailSerializer(reunion).data)
    
    @action(detail=True, methods=['post'])
    def checkin_presence(self, request, pk=None):
        """Enregistrer la présence"""
        reunion = self.get_object()
        
        try:
            expert = Expert.objects.get(user=request.user)
        except Expert.DoesNotExist:
            return Response(
                {'detail': 'L\'utilisateur n\'est pas un expert.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que la réunion est en cours ou planifiée
        if reunion.status not in ['PLANNED', 'IN_PROGRESS']:
            return Response(
                {'detail': 'La réunion n\'est pas active.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer ou mettre à jour la présence
        presence, created = Presence.objects.update_or_create(
            reunion=reunion,
            expert=expert,
            defaults={'status': 'PRESENT', 'marked_at': timezone.now()}
        )
        
        return Response(
            PresenceSerializer(presence).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])
    def generate_pv(self, request, pk=None):
        """Générer le procès-verbal"""
        reunion = self.get_object()
        
        # Vérifier que la réunion est complétée
        if reunion.status != 'COMPLETED':
            return Response(
                {'detail': 'La réunion doit être complétée pour générer le PV.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculer les statistiques
        presences = reunion.presences.all()
        presents = presences.filter(status='PRESENT').count()
        absents = presences.filter(status='ABSENT').count()
        total = presences.count()
        
        quorum_atteint = (presents / total * 100) >= 50 if total > 0 else False
        
        # Générer le contenu du PV
        contenu = self._generate_pv_content(reunion, presents, absents, total, quorum_atteint)
        
        # Créer ou mettre à jour le PV
        pv, created = ProcessusVerbaux.objects.update_or_create(
            reunion=reunion,
            defaults={
                'titre': f"Procès-Verbal - {reunion.titre}",
                'contenu': contenu,
                'nombre_presents': presents,
                'nombre_absents': absents,
                'quorum_atteint': quorum_atteint,
                'generated_at': timezone.now()
            }
        )
        
        return Response(
            ProcessusVerbauxSerializer(pv).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    def _generate_pv_content(self, reunion, presents, absents, total, quorum):
        """Générer le contenu du PV"""
        content = f"""
PROCÈS-VERBAL DE RÉUNION
========================

Titre: {reunion.titre}
Date: {reunion.date.strftime('%Y-%m-%d %H:%M')}
Lieu: {reunion.lieu if reunion.lieu else 'Virtuel'}
Type: {reunion.get_type_display()}

PARTICIPATION
=============
Total experts attendus: {total}
Présents: {presents}
Absents: {absents}
Quorum atteint: {'OUI' if quorum else 'NON'}

ORDRE DU JOUR
=============
{reunion.ordre_jour}

POINTS DISCUTÉS
===============
(À compléter)

DÉCISIONS PRISES
================
(À compléter)

Généré le: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return content
    
    @action(detail=True, methods=['get'])
    def presences(self, request, pk=None):
        """Récupérer les présences d'une réunion"""
        reunion = self.get_object()
        presences = reunion.presences.all()
        serializer = PresenceSerializer(presences, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Récupérer les réunions à venir"""
        tomorrow = timezone.now() + timezone.timedelta(days=1)
        reunions = self.get_queryset().filter(
            date__gte=timezone.now(),
            status__in=['PLANNED']
        )
        serializer = ReunionBasicSerializer(reunions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def past(self, request):
        """Récupérer les réunions passées"""
        reunions = self.get_queryset().filter(
            date__lt=timezone.now(),
            status__in=['COMPLETED', 'CANCELLED']
        )
        serializer = ReunionBasicSerializer(reunions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques sur les réunions"""
        total = self.get_queryset().count()
        
        # Par type
        by_type = {}
        for type_choice in Reunion.TYPE_CHOICES:
            type_key = type_choice[0]
            count = self.get_queryset().filter(type=type_key).count()
            by_type[type_key] = count
        
        # Moyenne d'assiduité
        presences = Presence.objects.values('reunion').annotate(
            total=Count('id'),
            presents=Count(Case(When(status='PRESENT', then=1), output_field=IntegerField()))
        )
        
        if presences.exists():
            avg_attendance = sum(
                (p['presents'] / p['total'] * 100) if p['total'] > 0 else 0
                for p in presences
            ) / presences.count()
        else:
            avg_attendance = 0.0
        
        # Total PV générés
        total_pv = ProcessusVerbaux.objects.count()
        
        response_data = {
            'total_reunions': total,
            'by_type': by_type,
            'average_attendance': round(avg_attendance, 2),
            'total_pv_generated': total_pv
        }
        
        return Response(response_data)


class PresenceViewSet(viewsets.ModelViewSet):
    """ViewSet pour les présences"""
    queryset = Presence.objects.select_related('reunion', 'expert__user')
    serializer_class = PresenceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['reunion__id', 'status']
    
    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['create', 'update', 'partial_update']:
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]


class ProcessusVerbauxViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les procès-verbaux (lecture seule)"""
    queryset = ProcessusVerbaux.objects.select_related('reunion', 'signed_by__user')
    serializer_class = ProcessusVerbauxSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['reunion__type']
    
    @action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])
    def sign(self, request, pk=None):
        """Signer un procès-verbal"""
        pv = self.get_object()
        
        try:
            expert = Expert.objects.get(user=request.user)
            pv.signed_by = expert
            pv.signature_date = timezone.now()
            pv.save()
            
            return Response(ProcessusVerbauxSerializer(pv).data)
        except Expert.DoesNotExist:
            return Response(
                {'detail': 'L\'utilisateur n\'est pas un expert.'},
                status=status.HTTP_403_FORBIDDEN
            )
