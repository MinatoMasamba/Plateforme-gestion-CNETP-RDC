from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import date

from apps.validation.models import LegisticReview
from apps.norms.models import Norme
from .serializers import (
    LegisticReviewBasicSerializer,
    LegisticReviewDetailSerializer,
    LegisticReviewStartSerializer,
    LegisticReviewCompleteSerializer,
    LegisticReviewRejectSerializer
)
from ..permissions import IsLegist, IsCTCCoordinator


class LegisticReviewViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion du toilettage légistique"""
    queryset = LegisticReview.objects.select_related('norme', 'legist')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'norme__status']
    search_fields = ['norme__reference_number', 'norme__title', 'legist__user__first_name']
    ordering_fields = ['created_at', 'status', 'review_start_date']
    ordering = ['-created_at']

    WORKFLOW_STEPS = [
        {'id': 1, 'status': 'DRAFT', 'title': 'Conception spécialisée WG'},
        {'id': 2, 'status': 'CTM_REVIEW', 'title': 'Validation Sectorielle CTM'},
        {'id': 3, 'status': 'LEGISTIC_REVIEW', 'title': 'Toilettage CTC'},
        {'id': 4, 'status': 'PUBLIC_INQUIRY', 'title': 'Enquête Publique Numérique'},
        {'id': 5, 'status': 'PILOTAGE_REVIEW', 'title': 'Dépôt Assemblée Plénière'},
        {'id': 6, 'status': 'HOMOLOGATED', 'title': 'Sanction Ministérielle'},
        {'id': 7, 'status': 'PUBLISHED', 'title': 'Publication JO et Portail'},
    ]

    STATUS_TO_STEP = {
        'DRAFT': 1,
        'INTERNAL_REVIEW': 1,
        'CTM_REVIEW': 2,
        'LEGISTIC_REVIEW': 3,
        'PUBLIC_INQUIRY': 4,
        'PILOTAGE_REVIEW': 5,
        'FINAL_REVIEW': 5,
        'ADOPTED': 5,
        'HOMOLOGATED': 6,
        'PUBLISHED': 7,
        'ARCHIVED': 7,
    }

    STEP_TO_STATUS = {
        1: 'DRAFT',
        2: 'CTM_REVIEW',
        3: 'LEGISTIC_REVIEW',
        4: 'PUBLIC_INQUIRY',
        5: 'PILOTAGE_REVIEW',
        6: 'HOMOLOGATED',
        7: 'PUBLISHED',
    }

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
            return [IsCTCCoordinator()]
        elif self.action in ['complete_review', 'reject_review']:
            return [IsLegist()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]

    def _is_ctc_member(self, user):
        return bool(user and user.is_authenticated and (user.is_ctc_staff or user.is_superuser))

    def _latest_content(self, norme):
        latest = getattr(norme, 'prefetched_latest_version', None) or norme.get_latest_version()
        return latest.content if latest else ''

    def _vote_summary(self, norme):
        counts = norme.votes.aggregate(
            total=Count('id'),
            for_votes=Count('id', filter=Q(vote='FOR')),
            against_votes=Count('id', filter=Q(vote='AGAINST')),
            abstain_votes=Count('id', filter=Q(vote='ABSTAIN')),
        )
        total = counts['total'] or 0
        for_votes = counts['for_votes'] or 0
        percent_for = round((for_votes / total) * 100, 2) if total else 0
        return {
            'total': total,
            'for': for_votes,
            'against': counts['against_votes'] or 0,
            'abstain': counts['abstain_votes'] or 0,
            'percent_for': percent_for,
            'passes_threshold': total > 0 and percent_for > 50,
        }

    def _norme_payload(self, norme):
        vote_summary = self._vote_summary(norme)
        step = self.STATUS_TO_STEP.get(norme.status, 1)
        return {
            'id': norme.id,
            'title': norme.title,
            'code': norme.reference_number,
            'description': norme.description,
            'ctm': getattr(norme.ctm, 'name', ''),
            'wg': getattr(norme.wg, 'name', ''),
            'status': norme.status,
            'status_label': norme.get_status_display(),
            'step': step,
            'workflow_title': self.WORKFLOW_STEPS[step - 1]['title'],
            'updated_at': norme.updated_at.date().isoformat() if norme.updated_at else None,
            'is_public': norme.is_public,
            'votes': vote_summary,
            'download_url': norme.current_version.url if norme.current_version else '',
        }

    def _review_payload(self, review):
        norme = review.norme
        return {
            **self._norme_payload(norme),
            'review_id': review.id,
            'review_status': review.status,
            'review_status_label': review.get_status_display(),
            'assigned_to': review.legist.user.get_full_name() if review.legist else '',
            'comments': review.comments or '',
            'content': self._latest_content(norme),
        }

    def _sync_vote_progression(self):
        candidates = Norme.objects.filter(status__in=['INTERNAL_REVIEW', 'CTM_REVIEW']).prefetch_related('votes')
        promoted = []
        with transaction.atomic():
            for norme in candidates:
                summary = self._vote_summary(norme)
                if not summary['passes_threshold']:
                    continue
                norme.status = 'LEGISTIC_REVIEW'
                norme.legistic_review_date = date.today()
                norme.is_public = False
                norme.save(update_fields=['status', 'legistic_review_date', 'is_public', 'updated_at'])
                LegisticReview.objects.get_or_create(norme=norme, defaults={'status': 'PENDING'})
                promoted.append(norme.id)
        return promoted

    @action(detail=False, methods=['get'], url_path='workspace')
    def workspace(self, request):
        """Données serveur pour Processus ISO + Portail Public des Normes."""
        promoted = self._sync_vote_progression()
        normes = Norme.objects.select_related('ctm', 'wg').prefetch_related('votes').all()
        return Response({
            'steps': self.WORKFLOW_STEPS,
            'promoted_norme_ids': promoted,
            'normes': [self._norme_payload(norme) for norme in normes],
        })

    @action(detail=False, methods=['get'], url_path='legistique-workspace')
    def legistique_workspace(self, request):
        """Données du bureau légistique, visibles uniquement aux membres CTC."""
        if not self._is_ctc_member(request.user):
            return Response(
                {'detail': "Vous n'êtes pas autorisé à consulter le bureau légistique."},
                status=status.HTTP_403_FORBIDDEN
            )

        self._sync_vote_progression()
        for norme in Norme.objects.filter(status='LEGISTIC_REVIEW'):
            LegisticReview.objects.get_or_create(norme=norme, defaults={'status': 'PENDING'})

        reviews = LegisticReview.objects.select_related('norme', 'norme__ctm', 'norme__wg', 'legist__user').filter(
            status__in=['PENDING', 'ASSIGNED', 'IN_REVIEW']
        )
        return Response({
            'can_access': True,
            'reviews': [self._review_payload(review) for review in reviews],
        })

    @action(detail=True, methods=['post'], url_path='assign-self')
    def assign_self(self, request, pk=None):
        """Le membre CTC prend en charge le toilettage."""
        if not self._is_ctc_member(request.user):
            return Response({'detail': 'Action réservée aux membres CTC.'}, status=status.HTTP_403_FORBIDDEN)

        review = self.get_object()
        expert = getattr(request.user, 'expert_profile', None)
        if not expert:
            return Response({'detail': 'Aucun profil expert lié à ce compte.'}, status=status.HTTP_400_BAD_REQUEST)

        review.legist = expert
        review.status = 'IN_REVIEW'
        review.review_start_date = date.today()
        review.save()
        return Response(self._review_payload(review))

    @action(detail=True, methods=['post'], url_path='validate-ctc')
    def validate_ctc(self, request, pk=None):
        """Validation CTC officielle: la norme passe à l'enquête publique, non publiée."""
        if not self._is_ctc_member(request.user):
            return Response({'detail': 'Action réservée aux membres CTC.'}, status=status.HTTP_403_FORBIDDEN)

        review = self.get_object()
        comments = request.data.get('comments', '')
        content = request.data.get('content', '')
        with transaction.atomic():
            review.status = 'REVIEW_COMPLETED'
            review.comments = comments
            review.review_end_date = date.today()
            review.approval_date = date.today()
            review.save()

            norme = review.norme
            if content:
                latest = norme.get_latest_version()
                next_number = (latest.version_number + 1) if latest else 1
                norme.versions.create(
                    version_number=next_number,
                    title=norme.title,
                    content=content,
                    summary='Validation CTC - toilettage légistique',
                    is_draft=False,
                    version_author=request.user,
                )
            norme.status = 'PUBLIC_INQUIRY'
            norme.public_inquiry_start = date.today()
            norme.is_public = True
            norme.save(update_fields=['status', 'public_inquiry_start', 'is_public', 'updated_at'])

        return Response(self._review_payload(review))

    @action(detail=False, methods=['post'], url_path='set-step')
    def set_step(self, request):
        """Met à jour une phase réglementaire depuis l'écran Processus ISO."""
        if not self._is_ctc_member(request.user):
            return Response({'detail': 'Action réservée aux membres CTC.'}, status=status.HTTP_403_FORBIDDEN)

        norme_id = request.data.get('norme_id')
        step = int(request.data.get('step', 0))
        if step not in self.STEP_TO_STATUS:
            return Response({'step': 'Phase invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        norme = Norme.objects.get(pk=norme_id)
        norme.status = self.STEP_TO_STATUS[step]
        norme.is_public = step >= 4
        if step == 3:
            norme.legistic_review_date = date.today()
            LegisticReview.objects.get_or_create(norme=norme, defaults={'status': 'PENDING'})
        elif step == 4 and not norme.public_inquiry_start:
            norme.public_inquiry_start = date.today()
        elif step == 6 and not norme.homologation_date:
            norme.homologation_date = date.today()
        elif step == 7 and not norme.publication_date:
            norme.publication_date = date.today()
        norme.save()
        return Response(self._norme_payload(norme))

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

        if review.legist != request.user.expert_profile and not request.user.is_ctc_staff:
            return Response(
                {'error': 'You are not the assigned legist'},
                status=status.HTTP_403_FORBIDDEN
            )

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

        if review.legist != request.user.expert_profile and not request.user.is_ctc_staff:
            return Response(
                {'error': 'You are not the assigned legist'},
                status=status.HTTP_403_FORBIDDEN
            )

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
