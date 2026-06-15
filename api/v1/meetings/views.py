from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Avg, Case, When, IntegerField, F
from django.utils import timezone

from apps.meetings.models import Reunion, Presence, ProcessusVerbaux, ReunionVote
from apps.experts.models import Expert
from .serializers import (
    ReunionBasicSerializer, ReunionDetailSerializer,
    ReunionCreateUpdateSerializer, ReunionStatusUpdateSerializer,
    PresenceSerializer, PresenceCheckInSerializer,
    ProcessusVerbauxSerializer, ReunionSummarySerializer,
    ReunionStatsSerializer, ReunionVoteSerializer
)
from ..permissions import IsExpert, IsCTCCoordinator, IsMeetingOrganizerOrCTC


class ReunionViewSet(viewsets.ModelViewSet):
    """ViewSet pour les réunions"""
    queryset = Reunion.objects.select_related(
        'organisateur__user', 'pv__signed_by', 'ctm', 'wg'
    ).prefetch_related('presences__expert__user', 'votes__expert__user')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'status', 'organisateur__ctm__id']
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
        if self.action in ['checkin_presence', 'generate_pv', 'vote', 'close']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Ajouter le CTC qui organise la réunion"""
        expert = Expert.objects.filter(user=self.request.user).first()
        reunion = serializer.save(organisateur=expert)
        self._sync_expected_presences(reunion)

    def _sync_expected_presences(self, reunion):
        affectations = None
        if reunion.wg_id:
            affectations = reunion.wg.affectations.select_related('expert')
        elif reunion.ctm_id:
            affectations = reunion.ctm.affectations.select_related('expert')

        if not affectations:
            return

        for affectation in affectations:
            Presence.objects.get_or_create(
                reunion=reunion,
                expert=affectation.expert,
                defaults={'status': 'ABSENT'}
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

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Retourner réunion + présences + votes + PV."""
        return Response(ReunionDetailSerializer(self.get_object()).data)

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

    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """Créer ou modifier le vote de l'expert connecté."""
        reunion = self.get_object()
        if reunion.status == 'COMPLETED':
            return Response({'detail': 'Le scrutin est clos.'}, status=status.HTTP_400_BAD_REQUEST)

        expert = Expert.objects.filter(user=request.user).first()
        if not expert:
            return Response({'detail': "L'utilisateur n'est pas un expert."}, status=status.HTTP_403_FORBIDDEN)

        if not reunion.presences.filter(expert=expert, status='PRESENT').exists():
            return Response({'detail': "Une présence émargée est requise pour voter."}, status=status.HTTP_400_BAD_REQUEST)

        choix = request.data.get('choix')
        if choix not in dict(ReunionVote.CHOIX_CHOICES):
            return Response({'choix': 'Choix invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        vote, created = ReunionVote.objects.update_or_create(
            reunion=reunion,
            expert=expert,
            defaults={
                'choix': choix,
                'justification': request.data.get('justification', ''),
            }
        )
        return Response(ReunionVoteSerializer(vote).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Clore la réunion puis générer/retourner le PV."""
        reunion = self.get_object()
        if reunion.status != 'COMPLETED':
            reunion.status = 'COMPLETED'
            reunion.save(update_fields=['status'])
        pv_response = self.generate_pv(request, pk=pk)
        return pv_response

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
        votes = reunion.votes.all()
        pour = votes.filter(choix='POUR').count()
        contre = votes.filter(choix='CONTRE').count()
        abstention = votes.filter(choix='ABSTENTION').count()

        quorum_atteint = (presents / total * 100) >= 50 if total > 0 else False

        # Générer le contenu du PV
        contenu = self._generate_pv_content(reunion, presents, absents, total, quorum_atteint, pour, contre, abstention)

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

    def _generate_pv_content(self, reunion, presents, absents, total, quorum, pour=0, contre=0, abstention=0):
        """Générer le contenu du PV"""
        content = f"""
PROCÈS-VERBAL DE RÉUNION
----------------

Titre: {reunion.titre}
Date: {reunion.date.strftime('%Y-%m-%d %H:%M')}
Lieu: {reunion.lieu if reunion.lieu else 'Virtuel'}
Type: {reunion.get_type_display()}
CTM: {reunion.ctm.name if reunion.ctm else 'N/A'}
WG: {reunion.wg.name if reunion.wg else 'N/A'}
Document réglementaire: {reunion.document_reglementaire or 'N/A'}

PARTICIPATION
----------------
Total experts attendus: {total}
Présents: {presents}
Absents: {absents}
Quorum atteint: {'OUI' if quorum else 'NON'}

SCRUTIN
----------------
Pour: {pour}
Contre: {contre}
Abstentions: {abstention}

ORDRE DU JOUR
----------------
{reunion.ordre_jour}

POINTS DISCUTÉS
----------------
(À compléter)

DÉCISIONS PRISES
----------------
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
    filterset_fields = ['reunion__id', 'reunion', 'status']

    def get_permissions(self):
        """Permissions granulaires : seul l'organisateur de la réunion (ou un
        Coordinateur CTC/Admin) peut modifier l'émargement des participants."""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsMeetingOrganizerOrCTC()]
        return [IsAuthenticated()]

    def perform_update(self, serializer):
        """Tracer l'expert qui a modifié l'émargement."""
        expert = Expert.objects.filter(user=self.request.user).first()
        serializer.save(marked_by=expert)


class ReunionVoteViewSet(viewsets.ReadOnlyModelViewSet):
    """Votes de réunion en lecture globale; l'écriture passe par /reunions/{id}/vote/."""
    queryset = ReunionVote.objects.select_related('reunion', 'expert__user')
    serializer_class = ReunionVoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['reunion__id', 'reunion', 'choix']


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
