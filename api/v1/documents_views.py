from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser

from apps.documents.models import DocumentFile
from .documents_serializers import DocumentFileSerializer
from apps.experts.models import Expert # Import Expert model
from django.contrib.auth import get_user_model

User = get_user_model()

class DocumentFileViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des documents déposés par les experts"""
    queryset = DocumentFile.objects.select_related('expert').all()
    serializer_class = DocumentFileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['expert', 'file_type', 'category']
    search_fields = ['description', 'filename', 'expert__user__first_name', 'expert__user__last_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Assigner automatiquement l'expert à partir de l'utilisateur authentifié"""
        try:
            expert = self.request.user.expert_profile
            serializer.save(expert=expert)
        except AttributeError:
            # If the user doesn't have an expert profile, we still save the document but without linking an expert.
            # This might be desired if a non-expert can upload documents, though the prompt implies experts.
            serializer.save()

