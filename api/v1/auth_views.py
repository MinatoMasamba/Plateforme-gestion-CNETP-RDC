from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from apps.core.models import User
from .auth_serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
)


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet pour gérer l'authentification
    - register : Inscription (POST)
    - login : Connexion (POST)
    - logout : Déconnexion (POST)
    - me : Profil utilisateur courant (GET)
    - profile : Mettre à jour le profil (PATCH)
    - change-password : Changer le mot de passe (POST)
    """
    
    permission_classes = [AllowAny]  # Par défaut, tout le monde peut s'enregistrer/connecter
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Endpoint d'inscription : POST /api/v1/auth/register/
        
        Body :
        {
            "username": "john_doe",
            "email": "john@cnetp.cd",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePassword123!",
            "password2": "SecurePassword123!",
            "phone": "+243812345678"
        }
        """
        # Empêcher toute tentative d'inscription en tant qu'expert depuis cet endpoint
        if str(request.data.get('is_expert', '')).lower() in ['true', '1', 'yes']:
            return Response({'detail': "Inscription d'expert non autorisée sur cet endpoint."}, status=status.HTTP_403_FORBIDDEN)

        # Passer la request au serializer si besoin
        serializer = UserRegistrationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'message': 'Utilisateur créé avec succès',
                    'user': UserDetailSerializer(user).data,
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Endpoint de connexion : POST /api/v1/auth/login/
        
        Body :
        {
            "username": "john_doe",
            "password": "SecurePassword123!"
        }
        
        Response :
        {
            "message": "Connexion réussie",
            "user": {...},
            "token": "xyz123...abc"
        }
        """
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            # Pour session-based auth, Django gère la session automatiquement
            # Pour JWT, on retournerait le token ici
            return Response(
                {
                    'message': 'Connexion réussie',
                    'user': UserDetailSerializer(user).data,
                    'session_id': request.session.session_key,
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Endpoint de déconnexion : POST /api/v1/auth/logout/
        
        Nécessite l'authentification
        """
        logout(request)
        return Response(
            {'message': 'Déconnexion réussie'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Endpoint du profil utilisateur courant : GET /api/v1/auth/me/
        
        Retourne les infos de l'utilisateur authentifié
        """
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """
        Endpoint pour mettre à jour le profil : PATCH /api/v1/auth/profile/
        
        Body :
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "newemail@cnetp.cd",
            "phone": "+243812345678",
            "province": "Kinshasa",
            "bio": "Expert en géotechnique"
        }
        """
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Profil mis à jour avec succès',
                    'user': UserDetailSerializer(request.user).data,
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Endpoint pour changer le mot de passe : POST /api/v1/auth/change-password/
        
        Body :
        {
            "old_password": "OldPassword123!",
            "new_password": "NewPassword123!",
            "new_password2": "NewPassword123!"
        }
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {'message': 'Mot de passe changé avec succès'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour lister les utilisateurs (lecture seule)
    - list : GET /api/v1/users/
    - retrieve : GET /api/v1/users/{id}/
    """
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtrer la liste des utilisateurs selon les paramètres de requête
        Exemples :
        - /api/v1/users/?is_expert=true
        - /api/v1/users/?search=john
        """
        queryset = User.objects.all()
        
        # Filtre par expert
        is_expert = self.request.query_params.get('is_expert', None)
        if is_expert is not None:
            queryset = queryset.filter(is_expert=is_expert.lower() == 'true')
        
        # Filtre par staff CTC
        is_ctc_staff = self.request.query_params.get('is_ctc_staff', None)
        if is_ctc_staff is not None:
            queryset = queryset.filter(is_ctc_staff=is_ctc_staff.lower() == 'true')
        
        # Recherche par nom ou email
        search = self.request.query_params.get('search', None)
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return queryset.order_by('-date_joined')
