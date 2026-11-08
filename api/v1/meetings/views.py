from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Case, Count, IntegerField, When
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.meetings.models import (
    Reunion, Presence, ProcessusVerbaux, ReunionVote,
    ReunionParticipant, PresenceSession,
)
from apps.experts.models import Expert
from apps.meetings.services.livekit import (
    LiveKitNotConfigured, ensure_room_name, generate_join_token,
)
from apps.meetings.services.participants import (
    add_participant, sync_participants_from_affectations,
)
from apps.meetings.services.presence import (
    apply_presence_at_close, presence_seconds_for_expert, real_duration_seconds,
)
from ..permissions import (
    IsExpert, IsCTCCoordinator, IsMeetingOrganizerOrCTC,
    IsReunionManager, IsInvitedToReunion, IsReunionParticipantOrManager,
)
from ..throttles import MeetingJoinThrottle
from .serializers import (
    ReunionBasicSerializer, ReunionDetailSerializer,
    ReunionCreateUpdateSerializer, ReunionStatusUpdateSerializer,
    PresenceSerializer, PresenceCheckInSerializer,
    ProcessusVerbauxSerializer, ReunionSummarySerializer,
    ReunionStatsSerializer, ReunionVoteSerializer,
    ReunionParticipantSerializer, ReunionParticipantWriteSerializer,
    PresenceSessionSerializer,
)


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

    def get_queryset(self):
        qs = super().get_queryset()
        expert = Expert.objects.filter(user=self.request.user).first()
        if expert:
            from apps.governance.phoenix_runtime import active_st_mandate
            mandate = active_st_mandate(expert)
            if mandate:
                from apps.governance.st_permissions import visible_meetings
                from apps.governance.st_matrix import mandate_capabilities
                context = {**mandate_capabilities(mandate), 'poste': mandate.poste,
                           'ctc_pole': mandate.poste.organe.code}
                qs = qs.filter(pk__in=visible_meetings(expert, context).values('pk'))
        return qs

    def get_serializer_class(self):
        """Retourner le serializer approprié"""
        if self.action == 'retrieve':
            return ReunionDetailSerializer
        elif self.action == 'list':
            return ReunionBasicSerializer
        elif self.action == 'update_status':
            return ReunionStatusUpdateSerializer
        elif self.action in ('create', 'update', 'partial_update'):
            return ReunionCreateUpdateSerializer
        return ReunionDetailSerializer

    def get_permissions(self):
        """Permissions granulaires de la réunion."""
        if self.action in (
            'create', 'update', 'partial_update', 'destroy', 'update_status',
            'generate_pv', 'close', 'ouvrir_salle', 'cloturer_salle',
        ):
            return [IsAuthenticated(), IsReunionManager()]
        if self.action == 'participants':
            if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
                return [IsAuthenticated(), IsReunionParticipantOrManager()]
            return [IsAuthenticated(), IsReunionManager()]
        if self.action == 'rejoindre':
            return [IsAuthenticated(), IsInvitedToReunion()]
        if self.action == 'en_ligne':
            return [IsAuthenticated(), IsReunionParticipantOrManager()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """Créer la réunion et répondre avec l'objet complet (id, salle)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            ReunionDetailSerializer(
                serializer.instance, context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_create(self, serializer):
        """Créer la réunion, sa salle et les invitations attendues."""
        expert = Expert.objects.filter(user=self.request.user).first()
        reunion = serializer.save(organisateur=expert)
        if reunion.mode == 'SALLE':
            ensure_room_name(reunion)
        sync_participants_from_affectations(reunion)

    def _sync_expected_presences(self, reunion):
        sync_participants_from_affectations(reunion)

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

        # ``marked_at`` est auto_now_add : la mise à jour explicite est requise.
        now = timezone.now()
        presence, created = Presence.objects.get_or_create(
            reunion=reunion,
            expert=expert,
            defaults={'status': 'PRESENT', 'marked_at': now, 'marked_by': expert},
        )
        if not created:
            presence.status = 'PRESENT'
            presence.marked_at = now
            presence.marked_by = expert
            presence.save(update_fields=['status', 'marked_at', 'marked_by', 'updated_at'])

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

        if getattr(settings, 'MEETING_VOTE_REQUIRE_SESSION', False):
            if not reunion.sessions.filter(expert=expert, left_at__isnull=True).exists():
                return Response(
                    {'detail': "Une session ouverte dans la salle est requise pour voter."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
        """Clore la salle, calculer la présence puis générer le PV."""
        reunion = self.get_object()
        with transaction.atomic():
            if not reunion.cloture_salle:
                reunion.cloture_salle = timezone.now()
            if reunion.status != 'COMPLETED':
                reunion.status = 'COMPLETED'
            reunion.save(update_fields=['cloture_salle', 'status', 'updated_at'])
            apply_presence_at_close(reunion)
        return self.generate_pv(request, pk=pk)

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

        if ProcessusVerbaux.objects.filter(
            reunion=reunion, administrative_versions__isnull=False,
        ).exists():
            return Response(
                {'detail': 'Ce PV est versionné dans le secrétariat administratif. Utilisez son éditeur pour conserver les versions.'},
                status=status.HTTP_409_CONFLICT,
            )

        # Calculer les statistiques : les excusés ne comptent pas dans le quorum.
        presences = reunion.presences.all()
        presents = presences.filter(status='PRESENT').count()
        absents = presences.filter(status='ABSENT').count()
        excuses = presences.filter(status='EXCUSED').count()
        total = presences.count()
        attendus = max(total - excuses, 0)
        votes = reunion.votes.all()
        pour = votes.filter(choix='POUR').count()
        contre = votes.filter(choix='CONTRE').count()
        abstention = votes.filter(choix='ABSTENTION').count()

        quorum_atteint = (presents / attendus * 100) >= 50 if attendus > 0 else False

        # Générer le contenu du PV
        contenu = self._generate_pv_content(
            reunion, presents, absents, total, quorum_atteint,
            pour, contre, abstention, excuses,
        )

        # Créer ou mettre à jour le PV sans écraser une rédaction/validation.
        pv, created = ProcessusVerbaux.objects.get_or_create(
            reunion=reunion,
            defaults={
                'titre': f"Procès-Verbal - {reunion.titre}",
                'contenu': contenu,
                'nombre_presents': presents,
                'nombre_absents': absents,
                'quorum_atteint': quorum_atteint,
            },
        )
        if not created:
            pv.titre = f"Procès-Verbal - {reunion.titre}"
            pv.contenu = contenu
            pv.nombre_presents = presents
            pv.nombre_absents = absents
            pv.quorum_atteint = quorum_atteint
            pv.save(update_fields=[
                'titre', 'contenu', 'nombre_presents', 'nombre_absents',
                'quorum_atteint', 'updated_at',
            ])

        return Response(
            ProcessusVerbauxSerializer(pv).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    def _generate_pv_content(
        self, reunion, presents, absents, total, quorum,
        pour=0, contre=0, abstention=0, excuses=0,
    ):
        """Générer le contenu du PV"""
        ordre_jour = reunion.ordre_jour or '(Non renseigné)'
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
Excusés: {excuses}
Quorum atteint: {'OUI' if quorum else 'NON'}

SCRUTIN
----------------
Pour: {pour}
Contre: {contre}
Abstentions: {abstention}

ORDRE DU JOUR
----------------
{ordre_jour}

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

    @action(detail=True, methods=['get', 'post', 'delete'])
    def participants(self, request, pk=None):
        """Lister, inviter ou retirer les participants d'une réunion."""
        reunion = self.get_object()

        if request.method == 'GET':
            participants = reunion.participants.select_related('expert__user')
            return Response(ReunionParticipantSerializer(participants, many=True).data)

        if request.method == 'POST':
            serializer = ReunionParticipantWriteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            participant = add_participant(reunion, **serializer.validated_data)
            return Response(
                ReunionParticipantSerializer(participant).data,
                status=status.HTTP_201_CREATED,
            )

        expert_id = request.data.get('expert') or request.query_params.get('expert')
        if not expert_id:
            return Response({'expert': 'Requis.'}, status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = ReunionParticipant.objects.filter(
            reunion=reunion, expert_id=expert_id,
        ).delete()
        if not deleted:
            return Response({'detail': 'Participant introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], throttle_classes=[MeetingJoinThrottle])
    def rejoindre(self, request, pk=None):
        """Délivrer un jeton LiveKit à un invité autorisé."""
        reunion = self.get_object()
        expert = Expert.objects.filter(user=request.user).first()
        if expert is None:
            return Response(
                {'detail': "L'utilisateur n'est pas un expert."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if reunion.mode != 'SALLE':
            return Response(
                {'detail': 'Cette réunion ne dispose pas de salle sur la plateforme.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if reunion.status in ('CANCELLED', 'COMPLETED'):
            return Response(
                {'detail': 'La salle est fermée.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        participant = ReunionParticipant.objects.filter(reunion=reunion, expert=expert).first()
        if participant is None:
            return Response(
                {'detail': "Vous n'êtes pas invité à cette réunion."},
                status=status.HTTP_403_FORBIDDEN,
            )

        now = timezone.now()
        if participant.exclu_jusqua and participant.exclu_jusqua > now:
            return Response(
                {'detail': 'Vous êtes temporairement exclu de la salle.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        window = timedelta(minutes=int(getattr(settings, 'REUNION_JOIN_WINDOW_MINUTES', 15)))
        if now < reunion.date - window:
            return Response(
                {'detail': "La salle n'est pas encore ouverte."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if reunion.cloture_salle and now > reunion.cloture_salle:
            return Response(
                {'detail': 'La salle est fermée.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = generate_join_token(reunion, participant)
        except LiveKitNotConfigured:
            return Response(
                {'detail': "Le service de visioconférence n'est pas configuré."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(payload)

    @action(detail=True, methods=['get'])
    def en_ligne(self, request, pk=None):
        """Participants actuellement connectés à la salle."""
        reunion = self.get_object()
        sessions = reunion.sessions.filter(left_at__isnull=True).select_related('expert__user')
        return Response({
            'invites': reunion.participants.count(),
            'en_ligne': sessions.count(),
            'participants': PresenceSessionSerializer(sessions, many=True).data,
        })

    @action(detail=True, methods=['get'])
    def presences_detail(self, request, pk=None):
        """Temps de présence calculé par participant et sessions détaillées."""
        reunion = self.get_object()
        expert = Expert.objects.filter(user=request.user).first()
        is_manager = IsReunionManager().has_object_permission(request, self, reunion)
        is_participant = bool(
            expert and reunion.participants.filter(expert=expert).exists()
        )
        if not (is_manager or is_participant):
            raise PermissionDenied("Accès réservé aux participants et gestionnaires.")

        sessions = reunion.sessions.select_related('expert__user')
        participants = []
        for participant in reunion.participants.select_related('expert__user'):
            participants.append({
                'expert': participant.expert_id,
                'expert_name': participant.expert.user.get_full_name(),
                'role': participant.role,
                'presence_secondes': presence_seconds_for_expert(reunion, participant.expert),
            })

        return Response({
            'duree_salle': real_duration_seconds(reunion),
            'participants': participants,
            'sessions': PresenceSessionSerializer(sessions, many=True).data,
        })

    @action(detail=True, methods=['post'])
    def ouvrir_salle(self, request, pk=None):
        """Ouvrir la salle : la salle LiveKit est créée au premier join."""
        reunion = self.get_object()
        if reunion.mode != 'SALLE':
            return Response(
                {'detail': 'Cette réunion ne dispose pas de salle sur la plateforme.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ensure_room_name(reunion)
        update_fields = ['room_name', 'updated_at']
        if reunion.ouverture_salle is None:
            reunion.ouverture_salle = timezone.now()
            update_fields.append('ouverture_salle')
        if reunion.status == 'PLANNED':
            reunion.status = 'IN_PROGRESS'
            update_fields.append('status')
        reunion.save(update_fields=update_fields)
        return Response(ReunionDetailSerializer(reunion).data)

    @action(detail=True, methods=['post'])
    def cloturer_salle(self, request, pk=None):
        """Clôturer la salle et appliquer les règles de présence."""
        reunion = self.get_object()
        with transaction.atomic():
            update_fields = ['updated_at']
            if reunion.cloture_salle is None:
                reunion.cloture_salle = timezone.now()
                update_fields.append('cloture_salle')
            if reunion.status != 'COMPLETED':
                reunion.status = 'COMPLETED'
                update_fields.append('status')
            reunion.save(update_fields=update_fields)
            apply_presence_at_close(reunion)
        return Response(ReunionDetailSerializer(reunion).data)

    @action(detail=True, methods=['get'])
    def transcription(self, request, pk=None):
        """Consulter la transcription et ses segments horodatés."""
        reunion = self.get_object()
        expert = Expert.objects.filter(user=request.user).first()
        is_manager = IsReunionManager().has_object_permission(request, self, reunion)
        is_participant = bool(
            expert and reunion.participants.filter(expert=expert).exists()
        )
        if not (is_manager or is_participant):
            raise PermissionDenied("Accès réservé aux participants et gestionnaires.")

        transcription = getattr(reunion, 'transcription', None)
        if transcription is None:
            return Response(
                {'detail': 'Aucune transcription pour cette réunion.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        segments = transcription.segments.select_related('expert__user')
        return Response({
            'id': transcription.id,
            'statut': transcription.statut,
            'langue': transcription.langue,
            'modele': transcription.modele,
            'termine_le': transcription.termine_le,
            'segments': [
                {
                    'id': segment.id,
                    'expert': segment.expert_id,
                    'expert_name': (
                        segment.expert.user.get_full_name() if segment.expert else ''
                    ),
                    'debut_s': segment.debut_s,
                    'fin_s': segment.fin_s,
                    'texte': segment.texte,
                    'confiance': segment.confiance,
                }
                for segment in segments
            ],
        })

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
            return [IsAuthenticated(), IsReunionManager()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Tracer l'expert qui a créé l'émargement."""
        expert = Expert.objects.filter(user=self.request.user).first()
        serializer.save(marked_by=expert)

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

        if pv.administrative_versions.exists():
            return Response(
                {'detail': 'Le validateur officiel de ce PV administratif doit être défini avant sa signature.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
