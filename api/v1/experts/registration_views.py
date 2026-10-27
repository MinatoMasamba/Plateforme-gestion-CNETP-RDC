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
from ..auth.serializers import UserDetailSerializer
from .serializers import ExpertPublicRegistrationSerializer


class ExpertPublicRegistrationViewSet(viewsets.ViewSet):
    """
    ViewSet pour l'inscription PUBLIQUE des experts (via QR Code)

    Endpoint: POST /api/v1/experts/public-register/

    C'est un endpoint COMPLÈTEMENT SÉPARÉ de /api/v1/auth/register/
    Réservé uniquement aux experts qui scannent le QR code
    """

    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], authentication_classes=[],
            url_path='candidature')
    def candidature(self, request):
        """Parcours du portail actuel : dossier en attente, sans mandat ni CTM."""
        from django.db import IntegrityError, transaction
        from web.forms import ExpertRegistrationForm
        from ..throttles import MobileAuthThrottle

        throttle = MobileAuthThrottle()
        if not throttle.allow_request(request, self):
            self.throttled(request, throttle.wait())
        fields = ('first_name', 'last_name', 'email', 'password',
                  'password_confirm', 'whatsapp_number', 'structure', 'specialties')
        data = {key: request.data.get(key, '') for key in fields}
        data['email'] = str(data['email']).strip().lower()
        if User.objects.filter(email__iexact=data['email']).exists():
            return Response({'email': ['Cet email est déjà utilisé.']}, status=400)
        cv = request.FILES.get('cv')
        if cv and not cv.name.lower().endswith(('.pdf', '.doc', '.docx')):
            return Response({'cv': ['Formats acceptés : PDF, DOC, DOCX.']}, status=400)
        form = ExpertRegistrationForm(data, request.FILES)
        if not form.is_valid():
            return Response(dict(form.errors), status=400)
        try:
            with transaction.atomic():
                expert = form.save()
        except IntegrityError:
            return Response({'email': ['Cet email est déjà utilisé.']}, status=400)
        return Response({
            'message': "Votre candidature est enregistrée et sera examinée par l'administration.",
            'id': expert.pk,
            'status': expert.status,
        }, status=status.HTTP_201_CREATED)

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
            "ctm_ids": [1, 2, 3],
            "phone": "+243812345678",
            "specialties": "Géotechnique, Fondations",
            "cv": <file>
        }

        Response (201):
        {
            "message": "Expert inscrit avec succès. Un email de confirmation sera envoyé.",
            "expert": {
                "id": 1,
                "email": "expert@example.com",
                "first_name": "Jean",
                "last_name": "Dupont",
                "status": "pending",
                "inscription_date": "2024-05-25T11:15:00Z",
                "ctm_ids": [1, 2, 3]
            }
        }
        """
        serializer = ExpertPublicRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            # Créer l'expert
            expert = serializer.save()

            # Récupérer les CTM pour la réponse
            ctm_ids = [expert.ctm.id] if expert.ctm else []

            return Response(
                {
                    'message': 'Expert inscrit avec succès. Un email de confirmation sera envoyé.',
                    'expert': {
                        'id': expert.id,
                        'email': expert.user.email,
                        'first_name': expert.user.first_name,
                        'last_name': expert.user.last_name,
                        'status': expert.status,
                        'inscription_date': expert.inscription_date.isoformat(),
                        'ctm_ids': ctm_ids
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
        structures = Structure.objects.all()
        from .serializers import StructureSerializer
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
