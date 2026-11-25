from datetime import timedelta, timezone as datetime_timezone
import json

from django.conf import settings
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Case, Count, IntegerField, When, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

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


def _pv_audit_snapshot(pv):
    return json.loads(JSONRenderer().render(ProcessusVerbauxSerializer(pv).data))


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
        if not (self.request.user.is_staff or self.request.user.is_superuser or
                getattr(self.request.user, 'is_ctc_staff', False)):
            qs = qs.filter(
                Q(participants__expert__user=self.request.user) |
                Q(organisateur__user=self.request.user) |
                Q(ctm__secretary__user=self.request.user) |
                Q(ctm__rapporteur__user=self.request.user) |
                Q(wg__secretary__user=self.request.user) |
                Q(wg__rapporteur__user=self.request.user)
            ).distinct()
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
        if self.action in ('preparation', 'pv_draft') and self.request.method == 'PUT':
            return [IsAuthenticated(), IsReunionManager()]
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

    @action(detail=False, methods=['get'])
    def capabilities(self, request):
        from ..permissions import _is_staff_like, _is_reunion_officer_anywhere
        from apps.governance.models import CTM, WG
        from apps.governance.phoenix_runtime import active_st_mandate
        expert = Expert.objects.filter(user=request.user).first()
        mandate = active_st_mandate(expert) if expert else None
        transverse = _is_staff_like(request.user) or bool(mandate and mandate.poste.code == 'ST-V3-07')
        if not transverse and not _is_reunion_officer_anywhere(expert):
            return Response({'can_plan': False, 'can_plan_ctm_ids': [], 'ctms': [], 'workgroups': []})
        ctms = CTM.objects.all() if transverse else CTM.objects.filter(Q(secretary=expert) | Q(rapporteur=expert)) if expert else CTM.objects.none()
        allowed_ctm_ids = list(ctms.values_list('pk', flat=True))
        groups = WG.objects.all() if transverse else WG.objects.filter(Q(secretary=expert) | Q(rapporteur=expert) | Q(ctm_id__in=allowed_ctm_ids)) if expert else WG.objects.none()
        parent_ids = set(allowed_ctm_ids) | set(groups.values_list('ctm_id', flat=True))
        return Response({
            'can_plan': bool(allowed_ctm_ids or groups.exists() or transverse),
            'can_plan_ctm_ids': allowed_ctm_ids,
            'ctms': list(CTM.objects.filter(pk__in=parent_ids).values('id', 'name')),
            'workgroups': list(groups.values('id', 'name', 'ctm_id')),
        })

    def perform_create(self, serializer):
        """Créer la réunion, sa salle et les invitations attendues."""
        expert = Expert.objects.filter(user=self.request.user).first()
        from ..permissions import _is_reunion_officer, _is_staff_like
        from types import SimpleNamespace
        wg = serializer.validated_data.get('wg')
        ctm = serializer.validated_data.get('ctm') or (wg.ctm if wg else None)
        if wg and ctm and wg.ctm_id != ctm.pk:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Le groupe doit appartenir à la sous-commission choisie.')
        target = SimpleNamespace(
            ctm_id=getattr(ctm, 'pk', None), ctm=ctm,
            wg_id=getattr(wg, 'pk', None), wg=wg,
        )
        from apps.governance.phoenix_runtime import active_st_mandate
        mandate = active_st_mandate(expert) if expert else None
        st_manager = mandate and mandate.poste.code == 'ST-V3-07'
        if not (_is_staff_like(self.request.user) or st_manager or _is_reunion_officer(expert, target)):
            raise PermissionDenied('Vous ne pouvez pas planifier une réunion pour ce groupe.')
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
        if (
            serializer.validated_data.get('status') in ('IN_PROGRESS', 'PLANNED')
            and reunion.cloture_salle
        ):
            reunion.cloture_salle = None
            reunion.save(update_fields=['cloture_salle', 'updated_at'])
        return Response(ReunionDetailSerializer(reunion).data)

    @action(detail=True, methods=['get'])
    def calendrier(self, request, pk=None):
        """Exporter une invitation privée, sans lien public de téléchargement."""
        reunion = self.get_object()
        def escape(value):
            return str(value or '').replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,').replace('\r', '')
        lines = [
            'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//CNE-ITP//Expert//FR',
            'BEGIN:VEVENT', f'UID:reunion-{reunion.pk}@cne-itp',
            'DTSTAMP:' + timezone.now().strftime('%Y%m%dT%H%M%SZ'),
            'DTSTART:' + reunion.date.astimezone(datetime_timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
            'SUMMARY:' + escape(reunion.titre),
            'DESCRIPTION:' + escape((reunion.ordre_jour or '') + '\n' + (reunion.lien_reunion_virtuelle or '')),
            'LOCATION:' + escape(reunion.lieu or reunion.lien_reunion_virtuelle),
            'STATUS:' + ('CANCELLED' if reunion.status == 'CANCELLED' else 'CONFIRMED'),
            'BEGIN:VALARM', 'TRIGGER:-P1D', 'ACTION:DISPLAY',
            'DESCRIPTION:Rappel de réunion CNE-ITP', 'END:VALARM',
            'BEGIN:VALARM', 'TRIGGER:-PT1H', 'ACTION:DISPLAY',
            'DESCRIPTION:Rappel de réunion CNE-ITP', 'END:VALARM',
            'END:VEVENT', 'END:VCALENDAR', '',
        ]
        # RFC 5545 : lignes pliées à 75 octets, y compris les accents UTF-8.
        folded = []
        for line in lines:
            part = ''
            for char in line:
                if len((part + char).encode('utf-8')) > 75:
                    folded.append(part)
                    part = ' '
                part += char
            folded.append(part)
        response = HttpResponse('\r\n'.join(folded), content_type='text/calendar; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="reunion-{reunion.pk}.ics"'
        response['Cache-Control'] = 'private, no-store'
        return response

    @action(detail=True, methods=['post'])
    def excuser(self, request, pk=None):
        reunion = self.get_object()
        participant = reunion.participants.filter(expert__user=request.user).first()
        if not participant:
            raise PermissionDenied("Action réservée aux invités.")
        if reunion.status not in ('PLANNED', 'IN_PROGRESS'):
            return Response({'detail': 'La réunion est close.'}, status=400)
        presence, _ = Presence.objects.update_or_create(
            reunion=reunion, expert=participant.expert,
            defaults={'status': 'EXCUSED', 'marked_by': participant.expert},
        )
        return Response(PresenceSerializer(presence).data)

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Retourner réunion + présences + votes + PV."""
        return Response(ReunionDetailSerializer(self.get_object(), context=self.get_serializer_context()).data)

    @action(detail=True, methods=['put'])
    def preparation(self, request, pk=None):
        from .workflow_serializers import MeetingPreparationSerializer
        from apps.core.models import AuditLog
        meeting = self.get_object()
        data = MeetingPreparationSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        with transaction.atomic():
            meeting = Reunion.objects.select_for_update().get(pk=meeting.pk)
            if meeting.status in ('COMPLETED', 'CANCELLED'):
                return Response({'detail': 'La préparation de cette réunion est close.'}, status=409)
            if meeting.preparation_revision != values['revision']:
                return Response({'detail': 'Préparation modifiée. Rechargez la réunion.'}, status=409)
            if meeting.votes.exists() and values['question_vote'] != meeting.question_vote:
                return Response({'detail': 'La question ne peut plus changer après un vote.'}, status=409)
            before = {'documents': meeting.document_links, 'question_vote': meeting.question_vote, 'meet_link': meeting.lien_reunion_virtuelle, 'ordre_jour': meeting.ordre_jour}
            meeting.document_links = values['documents']
            meeting.question_vote = values['question_vote']
            meeting.ordre_jour = values['ordre_jour']
            meeting.lien_reunion_virtuelle = values['meet_link']
            meeting.mode = 'EXTERNE' if values['meet_link'] else 'PRESENTIEL'
            meeting.preparation_revision += 1
            meeting.save()
            AuditLog.objects.create(user=request.user, action='UPDATE', content_type='MeetingPreparation', object_id=meeting.pk, object_repr=meeting.titre[:200], changes={'before': before, 'after': values})
        return Response(ReunionDetailSerializer(meeting, context=self.get_serializer_context()).data)

    @action(detail=True, methods=['put'])
    def pv_draft(self, request, pk=None):
        from .workflow_serializers import MeetingPVDraftSerializer
        from apps.core.models import AuditLog
        meeting = self.get_object()
        data = MeetingPVDraftSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            # Même verrou que la validation : une signature concurrente ne peut pas être écrasée.
            pv = ProcessusVerbaux.objects.select_for_update().filter(reunion=meeting).first()
            if not pv:
                return Response({'detail': 'Clôturez la réunion pour préparer son PV.'}, status=400)
            if pv.signature_date or pv.redaction == 'VALIDE' or pv.administrative_versions.exists():
                return Response({'detail': 'Ce PV est validé ou relève du circuit administratif.'}, status=409)
            values = data.validated_data
            if pv.revision != values.pop('revision'):
                return Response({'detail': 'Le PV a changé. Rechargez sa dernière version.'}, status=409)
            before = _pv_audit_snapshot(pv)
            for key, value in values.items():
                setattr(pv, key, value)
            pv.revision += 1
            pv.save()
            AuditLog.objects.create(user=request.user, action='UPDATE', content_type='MeetingPV', object_id=pv.pk, object_repr=pv.titre[:200], changes={'before': before, 'after': _pv_audit_snapshot(pv)})
        return Response(ProcessusVerbauxSerializer(pv).data)

    @action(detail=True, methods=['post'])
    def checkin_presence(self, request, pk=None):
        """Enregistrer la présence"""
        reunion = self.get_object()
        if not reunion.participants.filter(expert__user=request.user).exists():
            raise PermissionDenied("Émargement réservé aux invités.")
        if timezone.now() < reunion.date - timedelta(minutes=15):
            return Response({'detail': "L'émargement ouvre 15 minutes avant la réunion."}, status=400)

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
        if not reunion.participants.filter(expert__user=request.user).exists():
            raise PermissionDenied("Vote réservé aux invités.")
        if reunion.status not in ('PLANNED', 'IN_PROGRESS'):
            return Response({'detail': 'Le scrutin est clos.'}, status=status.HTTP_400_BAD_REQUEST)
        if reunion.preparation_revision and not reunion.question_vote.strip():
            return Response({'detail': 'La question soumise au vote doit être précisée.'}, status=400)

        expert = Expert.objects.filter(user=request.user).first()
        if not expert:
            return Response({'detail': "L'utilisateur n'est pas un expert."}, status=status.HTTP_403_FORBIDDEN)

        if not reunion.presences.filter(expert=expert, status='PRESENT').exists():
            return Response({'detail': "Une présence émargée est requise pour voter."}, status=status.HTTP_400_BAD_REQUEST)

        if reunion.mode == 'SALLE' and getattr(settings, 'MEETING_VOTE_REQUIRE_SESSION', False):
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
            if reunion.mode == 'SALLE':
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
        # Une nouvelle demande renvoie le PV existant, sans effacer sa rédaction.

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
Question soumise au vote: {reunion.question_vote or '(Non renseignée dans le circuit historique)'}

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
        if reunion.cloture_salle is not None:
            reunion.cloture_salle = None
            update_fields.append('cloture_salle')
        if reunion.status in ('PLANNED', 'COMPLETED'):
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


class MeetingScopedRecords:
    def get_queryset(self):
        view = ReunionViewSet()
        view.request = self.request
        return super().get_queryset().filter(reunion__in=view.get_queryset())


class PresenceViewSet(MeetingScopedRecords, viewsets.ModelViewSet):
    """ViewSet pour les présences"""
    queryset = Presence.objects.select_related('reunion', 'expert__user')
    serializer_class = PresenceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['reunion__id', 'reunion', 'status']

    def get_permissions(self):
        """Permissions granulaires : seul l'organisateur de la réunion (ou un
        Coordinateur CTC/Admin) peut modifier l'émargement des participants."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsReunionManager()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Tracer l'expert qui a créé l'émargement."""
        reunion = serializer.validated_data['reunion']
        if not IsReunionManager().has_object_permission(self.request, self, reunion):
            raise PermissionDenied("Action réservée aux gestionnaires de la réunion.")
        expert = Expert.objects.filter(user=self.request.user).first()
        serializer.save(marked_by=expert)

    def perform_update(self, serializer):
        """Tracer l'expert qui a modifié l'émargement."""
        if 'reunion' in serializer.validated_data and serializer.validated_data['reunion'] != serializer.instance.reunion:
            raise PermissionDenied("Une présence ne peut pas changer de réunion.")
        expert = Expert.objects.filter(user=self.request.user).first()
        serializer.save(marked_by=expert)


class ReunionVoteViewSet(MeetingScopedRecords, viewsets.ReadOnlyModelViewSet):
    """Votes de réunion en lecture globale; l'écriture passe par /reunions/{id}/vote/."""
    queryset = ReunionVote.objects.select_related('reunion', 'expert__user')
    serializer_class = ReunionVoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['reunion__id', 'reunion', 'choix']


class ProcessusVerbauxViewSet(MeetingScopedRecords, viewsets.ReadOnlyModelViewSet):
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
        from .workflow_serializers import MeetingPVValidationSerializer
        validation = MeetingPVValidationSerializer(data=request.data)
        validation.is_valid(raise_exception=True)

        if pv.administrative_versions.exists():
            return Response(
                {'detail': 'Le validateur officiel de ce PV administratif doit être défini avant sa signature.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            expert = Expert.objects.get(user=request.user)
            with transaction.atomic():
                pv = ProcessusVerbaux.objects.select_for_update().get(pk=pv.pk)
                if pv.signature_date or pv.redaction == 'VALIDE':
                    return Response({'detail': 'Ce PV est déjà validé.'}, status=409)
                if validation.validated_data.get('revision', pv.revision) != pv.revision:
                    return Response({'detail': 'Le PV a changé. Rechargez-le avant validation.'}, status=409)
                if pv.reunion.status != 'COMPLETED' or not all((pv.contenu.strip(), pv.points_discutes.strip(), pv.decisions.strip())):
                    return Response({'detail': 'Réunion close, points discutés et décisions renseignés requis.'}, status=400)
                before = _pv_audit_snapshot(pv)
                pv.signed_by = expert
                pv.valide_par = expert
                pv.signature_date = timezone.now()
                pv.redaction = 'VALIDE'
                pv.revision += 1
                pv.save()
                from apps.core.models import AuditLog
                AuditLog.objects.create(user=request.user, action='APPROVE', content_type='MeetingPV', object_id=pv.pk, object_repr=pv.titre[:200], changes={'before': before, 'after': _pv_audit_snapshot(pv)})
            return Response(ProcessusVerbauxSerializer(pv).data)
        except Expert.DoesNotExist:
            return Response(
                {'detail': 'L\'utilisateur n\'est pas un expert.'},
                status=status.HTTP_403_FORBIDDEN
            )
