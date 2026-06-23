from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.documents.models import DocumentFile
from .serializers import DocumentFileSerializer


class DocumentFileViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des documents déposés par les experts"""
    queryset = DocumentFile.objects.select_related('expert', 'uploaded_by', 'norme').all()
    serializer_class = DocumentFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['expert', 'file_type', 'category', 'is_public', 'norme']
    search_fields = ['title', 'description', 'expert__user__first_name', 'expert__user__last_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Associer l'utilisateur courant et son profil expert le cas échéant."""
        user = self.request.user
        expert = getattr(user, 'expert_profile', None)
        serializer.save(uploaded_by=user, expert=expert)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        if document.uploaded_by_id != request.user.id and not request.user.is_staff:
            return Response(
                {'detail': "Vous ne pouvez supprimer que vos propres documents."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def my_documents(self, request):
        """Lister les documents déposés par l'utilisateur connecté."""
        documents = self.get_queryset().filter(uploaded_by=request.user)
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def public_documents(self, request):
        """Lister les documents marqués publics."""
        documents = self.get_queryset().filter(is_public=True)
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)
