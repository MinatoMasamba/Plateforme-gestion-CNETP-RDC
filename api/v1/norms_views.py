from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.norms.models import Norme, NormeVersion, ChangementVersion, NormeVote
from apps.experts.models import Expert
from .norms_serializers import (
    NormeBasicSerializer, NormeDetailSerializer, NormeCreateUpdateSerializer,
    NormeStatusUpdateSerializer, NormeVersionSerializer, NormeVersionCreateSerializer,
    NormeFullHistorySerializer, ChangementVersionSerializer, NormeVoteSerializer
)
from .permissions import IsCTCCoordinator, IsExpert, IsExpertOrCTC


class NormeViewSet(viewsets.ModelViewSet):
    """ViewSet complet pour les normes"""
    queryset = Norme.objects.select_related(
        'ctm', 'wg', 'created_by', 'updated_by'
    ).prefetch_related('versions')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'ctm__id', 'wg__id', 'is_public']
    search_fields = ['title', 'reference_number', 'description', 'tags']
    ordering_fields = ['created_at', 'publication_date', 'reference_number']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Associer l'utilisateur actuel à la création"""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        """Associer l'utilisateur actuel à la modification"""
        serializer.save(updated_by=self.request.user)

    def get_serializer_class(self):
        """Retourner le serializer approprié selon l'action"""
        if self.action == 'retrieve':
            return NormeDetailSerializer
        elif self.action == 'list':
            return NormeBasicSerializer
        elif self.action == 'create' or self.action == 'update':
            return NormeCreateUpdateSerializer
        elif self.action == 'update_status':
            return NormeStatusUpdateSerializer
        elif self.action == 'history':
            return NormeFullHistorySerializer
        return NormeDetailSerializer
    
    def get_permissions(self):
        """Permissions granulaires"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsExpertOrCTC()]
        elif self.action in ['update_status']:
            return [IsCTCCoordinator()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'], permission_classes=[IsCTCCoordinator])
    def update_status(self, request, pk=None):
        """Mettre à jour le statut d'une norme (CTC uniquement)"""
        norme = self.get_object()
        serializer = NormeStatusUpdateSerializer(norme, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsExpertOrCTC])
    def create_version(self, request, pk=None):
        """Créer une nouvelle version d'une norme"""
        norme = self.get_object()
        
        # Vérifier les permissions
        if norme.status == 'PUBLISHED' or norme.status == 'ARCHIVED':
            return Response(
                {'detail': 'Impossible de créer une version pour une norme publiée ou archivée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = NormeVersionCreateSerializer(
            data=request.data,
            context={'norme': norme, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        version = serializer.save()
        
        return Response(
            NormeVersionSerializer(version).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Récupérer l'historique complet d'une norme"""
        norme = self.get_object()
        serializer = NormeFullHistorySerializer(norme)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def votes(self, request, pk=None):
        """Récupérer les votes de la norme ouverte."""
        votes = self.get_object().votes.select_related('voter__user', 'voter__structure')
        return Response(NormeVoteSerializer(votes, many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsExpert])
    def vote(self, request, pk=None):
        """Créer ou modifier le vote de l'expert connecté sur cette norme."""
        norme = self.get_object()
        if norme.status in ['PUBLISHED', 'ARCHIVED']:
            return Response({'detail': 'Le vote est clos pour cette norme.'}, status=status.HTTP_400_BAD_REQUEST)

        expert = Expert.objects.filter(user=request.user).first()
        if not expert:
            return Response({'detail': 'Seul un expert peut voter.'}, status=status.HTTP_403_FORBIDDEN)

        choice = request.data.get('vote')
        if choice not in dict(NormeVote.VOTE_CHOICES):
            return Response({'vote': 'Choix invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        vote, created = NormeVote.objects.update_or_create(
            norme=norme,
            voter=expert,
            defaults={
                'vote': choice,
                'justification': request.data.get('justification', ''),
            }
        )
        return Response(NormeVoteSerializer(vote).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Lister les versions d'une norme"""
        norme = self.get_object()
        versions = norme.versions.all()
        
        # Pagination optionnelle
        page = request.query_params.get('page', 1)
        per_page = request.query_params.get('per_page', 10)
        
        try:
            start = (int(page) - 1) * int(per_page)
            end = start + int(per_page)
            versions = versions[start:end]
        except (ValueError, TypeError):
            pass
        
        serializer = NormeVersionSerializer(versions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='versions/(?P<version_number>[0-9]+)')
    def get_version(self, request, pk=None, version_number=None):
        """Récupérer une version spécifique"""
        norme = self.get_object()
        try:
            version = norme.versions.get(version_number=int(version_number))
            serializer = NormeVersionSerializer(version)
            return Response(serializer.data)
        except NormeVersion.DoesNotExist:
            return Response(
                {'detail': 'Version non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'], url_path='diff')
    def diff_versions(self, request, pk=None):
        """Comparer deux versions"""
        norme = self.get_object()
        v1 = request.query_params.get('v1')
        v2 = request.query_params.get('v2')
        
        if not v1 or not v2:
            return Response(
                {'detail': 'Paramètres v1 et v2 requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            version1 = norme.versions.get(version_number=int(v1))
            version2 = norme.versions.get(version_number=int(v2))
        except NormeVersion.DoesNotExist:
            return Response(
                {'detail': 'Une ou plusieurs versions non trouvées'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Simple différence de contenu (peut être améliorée avec difflib)
        changes = version2.changes.filter(
            previous_version=version1
        )
        
        return Response({
            'v1': NormeVersionSerializer(version1).data,
            'v2': NormeVersionSerializer(version2).data,
            'changes': ChangementVersionSerializer(changes, many=True).data
        })
    
    @action(detail=True, methods=['post'], url_path='rollback-version')
    def rollback_version(self, request, pk=None):
        """Restaure une version précédente en créant une nouvelle version."""
        norme = self.get_object()
        version_number_to_restore = request.data.get('version_number')

        if not version_number_to_restore:
            return Response({'detail': 'Le numéro de version est requis.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            version_to_restore = norme.versions.get(version_number=int(version_number_to_restore))
        except NormeVersion.DoesNotExist:
            return Response({'detail': 'Version non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        # Créer une nouvelle version basée sur l'ancienne
        new_version_comment = f"Restauration du contenu de la version v{version_to_restore.version_number}"
        
        create_serializer = NormeVersionCreateSerializer(
            data={
                'content': version_to_restore.content,
                'comment': new_version_comment,
                'title': f"Rollback to v{version_to_restore.version_number}"
            },
            context={'norme': norme, 'request': request}
        )
        create_serializer.is_valid(raise_exception=True)
        new_version = create_serializer.save()

        return Response(
            NormeVersionSerializer(new_version).data,
            status=status.HTTP_201_CREATED
        )
        
    @action(detail=True, methods=['get'])
    def by_ctm(self, request, pk=None):
        """Récupérer les normes d'un CTM"""
        ctm_id = request.query_params.get('ctm_id')
        if not ctm_id:
            return Response(
                {'detail': 'ctm_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        normes = self.get_queryset().filter(ctm_id=ctm_id)
        serializer = NormeBasicSerializer(normes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def by_status(self, request, pk=None):
        """Récupérer les normes par statut"""
        status_filter = request.query_params.get('status')
        if not status_filter:
            return Response(
                {'detail': 'status est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        normes = self.get_queryset().filter(status=status_filter)
        serializer = NormeBasicSerializer(normes, many=True)
        return Response(serializer.data)

    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def publish_to_jo(self, request, pk=None):
        """Publier une norme au Journal Officiel"""
        norme = self.get_object()
        
        # Vérifier que l'utilisateur est ministre ou CTC
        if not (request.user.is_minister or request.user.is_ctc_staff):
            return Response(
                {'error': 'Seul un ministre ou coordonnateur CTC peut publier'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier le statut actuel
        if norme.status != 'ADOPTED':
            return Response(
                {'error': f'La norme doit être en statut ADOPTED, actuellement: {norme.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer les données de la requête
        jo_reference = request.data.get('jo_reference')
        jo_file = request.FILES.get('jo_file')
        publication_date = request.data.get('publication_date')
        
        if not jo_reference:
            return Response(
                {'error': 'jo_reference est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour la norme
        norme.jo_reference = jo_reference
        if jo_file:
            norme.jo_file = jo_file
        if publication_date:
            norme.publication_date = publication_date
        norme.status = 'PUBLISHED'
        norme.save()
        
        return Response(
            NormeDetailSerializer(norme).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def publication_status(self, request, pk=None):
        """Récupérer le statut de publication au JO"""
        norme = self.get_object()
        
        data = {
            'id': norme.id,
            'title': norme.title,
            'reference_number': norme.reference_number,
            'status': norme.status,
            'is_published': norme.status == 'PUBLISHED',
            'jo_reference': norme.jo_reference,
            'jo_file': norme.jo_file.url if norme.jo_file else None,
            'publication_date': norme.publication_date,
        }
        
        return Response(data)


class NormeVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de lecture pour les versions de normes"""
    queryset = NormeVersion.objects.select_related('norme', 'version_author')
    serializer_class = NormeVersionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['norme__id', 'is_draft']
    ordering_fields = ['version_number', 'created_at']
    ordering = ['-version_number']
    
    @action(detail=True, methods=['get'])
    def changes(self, request, pk=None):
        """Récupérer les changements d'une version"""
        version = self.get_object()
        changes = version.changes.all()
        serializer = ChangementVersionSerializer(changes, many=True)
        return Response(serializer.data)


class ChangementVersionViewSet(viewsets.ReadOnlyModelViewSet):
    print(f'[ChangementVersionViewSet] lancement du ViewSet')  # Debug log
    """ViewSet de lecture pour les changements de version"""
    queryset = ChangementVersion.objects.select_related(
        'version__norme', 'previous_version__norme'
    )
    serializer_class = ChangementVersionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['version__norme__id', 'change_type']
    search_fields = ['section', 'new_text', 'change_reason']
    ordering_fields = ['section', 'created_at']
    ordering = ['section']
