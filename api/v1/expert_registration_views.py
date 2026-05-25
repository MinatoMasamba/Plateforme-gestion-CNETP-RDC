"""
API Views pour l'inscription publique des experts
Endpoint spécifique pour les experts via QR code (pas le même que register user simple)
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login

from apps.core.models import User
from apps.experts.models import Expert, Structure
from apps.governance.models import CTM, WG
from .auth_serializers import UserDetailSerializer
from .serializers import ExpertPublicRegistrationSerializer


class ExpertPublicRegistrationViewSet(viewsets.ViewSet):
    """
    ViewSet pour l'inscription PUBLIQUE des experts (via QR Code)
    
    Endpoint: POST /api/v1/experts/public-register/
    
    C'est un endpoint COMPLÈTEMENT SÉPARÉ de /api/v1/auth/register/
    Réservé uniquement aux experts qui scannent le QR code
    """
    
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def public_register(self, request):
        """
        Inscription publique d'un expert via QR code
        
        POST /api/v1/experts/public-register/
        
        Body:
        {
            "email": "expert@example.com",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
            "first_name": "Jean",
            "last_name": "Dupont",
            "structure_id": 1,
            "expertise_domains": [1, 2, 3],
            "phone": "+243812345678",
            "organization": "Cabinet Conseil"
        }
        
        Response (201):
        {
            "message": "Expert inscrit avec succès",
            "expert": {
                "id": 1,
                "email": "expert@example.com",
                "first_name": "Jean",
                "last_name": "Dupont",
                "status": "pending_validation",
                "inscription_date": "2024-05-25T11:15:00Z"
            }
        }
        """
        serializer = ExpertPublicRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            # Créer l'expert
            expert = serializer.save()
            
            # Log de l'inscription
            self.request.environ['REMOTE_ADDR']
            
            return Response(
                {
                    'message': 'Expert inscrit avec succès. Un email de confirmation sera envoyé.',
                    'expert': {
                        'id': expert.id,
                        'email': expert.user.email,
                        'first_name': expert.user.first_name,
                        'last_name': expert.user.last_name,
                        'status': expert.status,
                        'inscription_date': expert.inscription_date.isoformat()
                    }
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def structures(self, request):
        """
        Récupérer les structures disponibles pour l'inscription
        
        GET /api/v1/experts/public-register/structures/
        """
        structures = Structure.objects.filter(is_active=True)
        from .experts_serializers import StructureSerializer
        serializer = StructureSerializer(structures, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def ctm(self, request):
        """
        Récupérer les CTM (domaines d'expertise)
        
        GET /api/v1/experts/public-register/ctm/
        """
        ctms = CTM.objects.all().order_by('number')
        data = [
            {
                'id': ctm.id,
                'number': ctm.number,
                'name': ctm.name,
                'description': ctm.description
            }
            for ctm in ctms
        ]
        return Response(data)


class ExpertPublicRegistrationView(generics.CreateAPIView):
    """
    Vue générique pour l'inscription publique des experts
    
    Endpoint: POST /api/v1/experts/public-register-simple/
    
    Alternative plus simple aux ViewSet
    """
    permission_classes = [AllowAny]
    serializer_class = ExpertPublicRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        """Créer un nouvel expert"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response(
            {
                'message': 'Expert inscrit avec succès',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )
