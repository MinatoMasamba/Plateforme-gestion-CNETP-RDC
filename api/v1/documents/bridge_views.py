"""
API Bridge Views - Mappe /api/ vers /api/v1/ pour compatibilité frontend
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.documents.models import DocumentFile
from apps.experts.models import Expert
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class DocumentsAPIView(viewsets.ModelViewSet):
    """
    API endpoint pour les documents
    GET /api/documents - Liste tous les documents
    GET /api/documents/:id - Détail du document
    """
    queryset = DocumentFile.objects.select_related('expert').all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        from .serializers import DocumentFileSerializer
        return DocumentFileSerializer

    def list(self, request, *args, **kwargs):
        """Retourne la liste des documents"""
        try:
            documents = self.queryset.values(
                'id', 'title', 'description', 'file_type', 'created_at', 'expert_id'
            )
            return Response({
                'count': len(list(documents)),
                'results': list(documents)
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CollaboratorsAPIView(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les collaborateurs/experts
    GET /api/collaborators - Liste tous les experts
    GET /api/collaborators/:id - Détail de l'expert
    """
    queryset = Expert.objects.select_related('user', 'structure').all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        from ..experts.serializers import ExpertSerializer
        return ExpertSerializer

    def list(self, request, *args, **kwargs):
        """Retourne la liste des collaborateurs"""
        try:
            experts = self.queryset.values(
                'id',
                'user__first_name',
                'user__last_name',
                'user__email',
                'status',
                'user__is_active',
                'created_at'
            )
            results = []
            for exp in experts:
                results.append({
                    'id': exp['id'],
                    'name': f"{exp['user__first_name']} {exp['user__last_name']}",
                    'email': exp['user__email'],
                    'role': exp.get('status', 'Expert'),
                    'isActive': exp['user__is_active'],
                    'createdAt': exp['created_at']
                })
            return Response({
                'count': len(results),
                'results': results
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
