from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from apps.experts.models import Expert, Structure
from apps.experts.profile_updates import missing_requirements, transition
from .serializers import (
    ExpertDetailSerializer, ExpertBasicSerializer, ExpertCreateUpdateSerializer,
    ExpertInscriptionSerializer, ExpertListSerializer, StructureSerializer
)
from ..permissions import IsCTCCoordinator, IsOwnerOrCTC
from ..filters import ExpertFilter, StructureFilter


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
    queryset = Expert.objects.select_related(
        'user', 'structure', 'profile_update',
    ).prefetch_related('governance_affectations')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExpertFilter
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['inscription_date', 'status', 'user__last_name']
    ordering = ['-inscription_date']

    @action(detail=True, methods=['get', 'post'], url_path='profile-update')
    def profile_update(self, request, pk=None):
        """État documentaire privé ; transitions avec contrôle serveur et historique."""
        from apps.governance.models import OrganisationVersion

        expert = self.get_object()
        staff = request.user.is_superuser or request.user.is_staff or getattr(request.user, 'is_ctc_staff', False)
        if request.user.pk != expert.user_id and not staff:
            raise PermissionDenied('Accès réservé à l’expert et au secrétariat.')
        state = getattr(expert, 'profile_update', None)
        if request.method == 'POST':
            version = None
            if request.data.get('version_id'):
                version = OrganisationVersion.objects.filter(pk=request.data['version_id']).first()
                if not version:
                    raise ValidationError({'version_id': 'Version inconnue.'})
            try:
                state = transition(expert, request.data.get('status'), request.user,
                                   version=version, comment=request.data.get('comment', ''))
            except DjangoValidationError as exc:
                raise ValidationError(getattr(exc, 'message_dict', None) or exc.messages) from exc
        version = state.version if state else None
        return Response({
            'status': state.status if state else 'NOT_STARTED',
            'version_id': version.pk if version else None,
            'submitted_at': state.submitted_at if state else None,
            'completed_at': state.completed_at if state else None,
            'missing_requirements': missing_requirements(expert, version) if version else [],
            'review_comment': state.review_comment if state else '',
        })

    def _user_has_ctm_role(self, user, ctm_id):
        """Vérifie si l'utilisateur est Président, Rapporteur ou Secrétaire du CTM."""
        if user.is_superuser or getattr(user, 'is_ctc_staff', False):
            return True
        try:
            requester = Expert.objects.get(user=user)
        except Expert.DoesNotExist:
            return False
        from web.profile_update_views import ctm_bureau_ids
        try:
            return int(ctm_id) in ctm_bureau_ids(requester)
        except (ValueError, TypeError):
            return False

    def _managed_ctm_ids(self, user):
        from apps.governance.models import CTM
        from web.profile_update_views import ctm_bureau_ids
        if user.is_superuser or getattr(user, 'is_ctc_staff', False):
            return set(CTM.objects.values_list('id', flat=True))
        return ctm_bureau_ids(Expert.objects.filter(user=user).first())

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
            return ExpertListSerializer
        elif self.action == 'create':
            return ExpertCreateUpdateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ExpertCreateUpdateSerializer
        elif self.action == 'inscription':
            return ExpertInscriptionSerializer
        return ExpertDetailSerializer

    def get_permissions(self):
        """Permissions granulaires"""
        if self.action == 'inscription':
            # L'inscription publique passe par cet endpoint
            return []
        elif self.action == 'create':
            # Création directe réservée au secrétariat technique
            return [IsCTCCoordinator()]
        elif self.action in ['update', 'partial_update']:
            # Seul l'expert lui-même ou le CTC peut modifier sa fiche
            return [IsAuthenticated(), IsOwnerOrCTC()]
        elif self.action == 'destroy':
            # Suppression réservée au secrétariat technique
            return [IsCTCCoordinator()]
        elif self.action == 'activate':
            # Seul CTC peut activer
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        """Détail d'un expert.

        Les données sensibles (coordonnées bancaires) ne sont renvoyées qu'à
        l'intéressé, au secrétariat technique ou au staff. Les autres experts
        voient la fiche d'annuaire publique.
        """
        instance = self.get_object()
        privileged = (
            getattr(request.user, 'is_superuser', False)
            or getattr(request.user, 'is_staff', False)
            or getattr(request.user, 'is_ctc_staff', False)
            or instance.user_id == request.user.id
        )
        serializer = ExpertDetailSerializer(instance) if privileged else ExpertListSerializer(instance)
        return Response(serializer.data)

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
    @transaction.atomic
    def admit_to_ctm(self, request, pk=None):
        """Accepter l'adhésion CTM, affecter au WG, créer le token d'activation et envoyer l'email."""
        from apps.governance.models import Affectation

        expert = self.get_object()
        ctm_id = request.data.get('ctm_id') or self._target_ctm_id(expert)
        wg_id  = request.data.get('wg_id')

        if not ctm_id:
            return Response({'detail': 'ctm_id est requis.'}, status=status.HTTP_400_BAD_REQUEST)
        if not self._user_has_ctm_role(request.user, ctm_id):
            raise PermissionDenied("Un rôle CTM est requis pour accepter l'adhésion de cet expert.")

        if expert.status != 'PENDING':
            return Response({'detail': 'Seules les demandes en attente peuvent être admises.'}, status=400)
        if str(self._target_ctm_id(expert)) != str(ctm_id):
            return Response({'detail': 'La CTM doit correspondre à la demande d’adhésion.'}, status=400)
        from apps.governance.models import WG
        try:
            wg_id = int(wg_id)
        except (ValueError, TypeError):
            return Response({'wg_id': 'Sélectionnez un groupe de travail valide.'}, status=400)
        if not wg_id or not WG.objects.filter(pk=wg_id, ctm_id=ctm_id).exists():
            return Response({'wg_id': 'Sélectionnez un groupe de travail de cette CTM.'}, status=400)

        expert.ctm_id          = ctm_id
        expert.status          = 'ACTIVE'
        expert.activation_date = timezone.now()

        try:
            reviewer = Expert.objects.get(user=request.user)
            expert.accepted_by = reviewer
            expert.accepted_at = timezone.now()
        except Expert.DoesNotExist:
            pass

        expert.save(update_fields=['ctm', 'status', 'activation_date', 'accepted_by', 'accepted_at'])

        if wg_id:
            Affectation.objects.update_or_create(
                expert=expert,
                ctm_id=ctm_id,
                wg_id=wg_id,
                defaults={'is_primary_ctm': True, 'is_primary_wg': True},
            )

        # Crée le token d'activation → le signal envoie l'email automatiquement
        from apps.mobileapp.models import ActivationToken
        ActivationToken.create_for_expert(expert)

        return Response(ExpertDetailSerializer(expert).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='reject')
    def reject(self, request, pk=None):
        """Rejeter la demande d'adhésion avec un motif."""
        expert = self.get_object()
        if expert.status != 'PENDING':
            return Response(
                {'detail': 'Seuls les experts en attente peuvent être rejetés.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ctm_id = self._target_ctm_id(expert)
        if not self._user_has_ctm_role(request.user, ctm_id):
            raise PermissionDenied("Un rôle CTM est requis pour rejeter cette demande.")

        reason = request.data.get('reason', '')
        try:
            reviewer = Expert.objects.get(user=request.user)
            expert.rejected_by = reviewer
        except Expert.DoesNotExist:
            pass

        expert.status          = 'REJECTED'
        expert.rejected_at     = timezone.now()
        expert.rejection_reason = reason
        expert.save(update_fields=['status', 'rejected_by', 'rejected_at', 'rejection_reason'])

        try:
            from apps.mobileapp.signals import create_notification_for_user
            create_notification_for_user(
                user=expert.user,
                title="Votre demande d'adhésion CNETP",
                body=f"Votre demande au CTM a été refusée. Motif : {reason or 'Non précisé'}",
                notification_type='SYSTEM',
                priority='HIGH',
                data={'expert_id': expert.id, 'reason': reason},
            )
        except Exception:
            pass

        return Response(ExpertDetailSerializer(expert).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='pending-for-my-ctm')
    def pending_for_my_ctm(self, request):
        """Liste des experts PENDING pour les CTM que l'utilisateur connecté dirige."""
        my_ctms = self._managed_ctm_ids(request.user)
        pending = Expert.objects.filter(
            ctm__in=my_ctms, status='PENDING'
        ).select_related('user', 'structure', 'ctm')
        return Response(ExpertDetailSerializer(pending, many=True).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='pending-count-for-my-ctm')
    def pending_count_for_my_ctm(self, request):
        """Compteur de demandes en attente — utilisé par le badge du widget web."""
        my_ctms = self._managed_ctm_ids(request.user)
        count = Expert.objects.filter(ctm__in=my_ctms, status='PENDING').count()
        return Response({'count': count, 'is_ctm_leader': bool(my_ctms)})

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

    @action(detail=False, methods=['get', 'patch'], url_path='my-affiliation')
    def my_affiliation(self, request):
        """Choix autonome de la sous-commission et des WG du profil connecté."""
        from rest_framework import serializers
        from apps.governance.models import Affectation, CTM, WG
        from web.profile_update_views import ctm_bureau_ids

        expert = Expert.objects.filter(user=request.user).first()
        if expert is None:
            return Response({'detail': 'Profil expert introuvable.'}, status=404)
        bureau_ids = ctm_bureau_ids(expert)
        if request.method == 'PATCH':
            class SelectionSerializer(serializers.Serializer):
                ctm = serializers.PrimaryKeyRelatedField(queryset=CTM.objects.all())
                wgs = serializers.PrimaryKeyRelatedField(
                    queryset=WG.objects.all(), many=True, allow_empty=True,
                )

            selection = SelectionSerializer(data=request.data)
            selection.is_valid(raise_exception=True)
            ctm = selection.validated_data['ctm']
            wgs = list({wg.pk: wg for wg in selection.validated_data['wgs']}.values())
            if any(wg.ctm_id != ctm.pk for wg in wgs):
                raise ValidationError({'wgs': 'Groupe de travail invalide pour cette sous-commission.'})
            if not wgs and WG.objects.filter(ctm=ctm).exists():
                raise ValidationError({'wgs': 'Sélectionnez au moins un groupe de travail.'})
            if len(wgs) > 1 and ctm.pk not in bureau_ids:
                raise ValidationError({'wgs': 'Un seul groupe de travail est autorisé pour ce profil.'})
            with transaction.atomic():
                Affectation.objects.filter(expert=expert).delete()
                Affectation.objects.bulk_create([
                    Affectation(expert=expert, ctm=ctm, wg=wg,
                                is_primary_ctm=True, is_primary_wg=True)
                    for wg in (wgs or [None])
                ])
                expert.ctm = ctm
                expert.save(update_fields=['ctm'])
        return Response({
            'ctm': expert.ctm_id,
            'wgs': list(expert.governance_affectations.filter(
                ctm_id=expert.ctm_id, wg__isnull=False,
            ).values_list('wg_id', flat=True)),
            'bureau_ctm_ids': sorted(bureau_ids),
            'ctms': list(CTM.objects.order_by('number').values('id', 'number', 'name')),
            'workgroups': list(WG.objects.order_by('number').values('id', 'ctm_id', 'number', 'name')),
        })

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Récupérer le profil de l'utilisateur connecté"""
        try:
            expert = Expert.objects.select_related(
                'user', 'structure', 'profile_update',
            ).get(user=request.user)
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
        from ..governance.serializers import AffectationSerializer
        expert = self.get_object()
        affectations = expert.governance_affectations.all()
        serializer = AffectationSerializer(affectations, many=True)
        return Response(serializer.data)
