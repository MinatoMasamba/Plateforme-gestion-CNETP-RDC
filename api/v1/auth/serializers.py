from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.core.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription d'un nouvel utilisateur"""
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2', 'phone']
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
        }

    def validate(self, data):
        """Valider que les deux mots de passe correspondent"""
        if data.get('password') != data.get('password2'):
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return data

    def validate_username(self, value):
        """Vérifier l'unicité du nom d'utilisateur"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur existe déjà.")
        return value

    def validate_email(self, value):
        """Vérifier l'unicité de l'email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def create(self, validated_data):
        """Créer l'utilisateur avec le mot de passe hashé"""
        validated_data.pop('password2')  # Supprimer le champ password2
        # Forcer le rôle 'simple user' lors de l'inscription publique
        validated_data.pop('is_expert', None)
        user = User.objects.create_user(is_expert=False, **validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer pour la connexion utilisateur"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Vérifier les credentials"""
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Identifiants invalides.")
            data['user'] = user
        else:
            raise serializers.ValidationError("Veuillez fournir le nom d'utilisateur et le mot de passe.")
        return data


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer pour afficher les détails d'un utilisateur"""
    is_expert = serializers.SerializerMethodField()
    is_ctc_staff = serializers.SerializerMethodField()
    structure = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'province', 'is_expert', 'is_ctc_staff',
            'is_minister', 'structure', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']

    def get_is_expert(self, obj):
        """Vérifier si l'utilisateur est un expert"""
        return obj.is_expert

    def get_is_ctc_staff(self, obj):
        """Vérifier si l'utilisateur est du staff CTC"""
        return obj.is_ctc_staff

    def get_structure(self, obj):
        """Retourner la structure de l'expert s'il en a une"""
        if hasattr(obj, 'expert_profile'):
            return {
                'id': obj.expert_profile.structure.id,
                'name': obj.expert_profile.structure.name,
                'acronym': obj.expert_profile.structure.acronym,
            }
        return None


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour le profil utilisateur"""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'province', 'bio']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour changer le mot de passe"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        """Valider que les nouveaux mots de passe correspondent"""
        if data.get('new_password') != data.get('new_password2'):
            raise serializers.ValidationError({"new_password": "Les mots de passe ne correspondent pas."})
        return data

    def validate_old_password(self, value):
        """Vérifier que l'ancien mot de passe est correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("L'ancien mot de passe est incorrect.")
        return value
