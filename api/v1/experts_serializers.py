from rest_framework import serializers
from apps.experts.models import Expert, Structure
from apps.core.models import User


class StructureSerializer(serializers.ModelSerializer):
    """Serializer pour les structures"""
    expert_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Structure
        fields = ['id', 'name', 'acronym', 'category', 'description', 'email', 'phone', 'website', 'contact_person', 'expert_count']
        read_only_fields = ['id', 'expert_count']
    
    def get_expert_count(self, obj):
        return obj.experts.count()


class ExpertBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour les experts (données minimales)"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    structure_name = serializers.CharField(source='structure.name', read_only=True)
    
    class Meta:
        model = Expert
        fields = ['id', 'user_name', 'structure_name', 'status', 'specialties']
        read_only_fields = ['id']


class ExpertDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les experts"""
    user = serializers.SerializerMethodField()
    structure = StructureSerializer(read_only=True)
    affectations = serializers.SerializerMethodField()
    
    class Meta:
        model = Expert
        fields = [
            'id', 'user', 'structure', 'status', 'specialties',
            'appointment_decree_number', 'appointment_date',
            'cv', 'bank_account', 'bank_name', 'mobile_money_number',
            'inscription_date', 'activation_date', 'affectations'
        ]
        read_only_fields = ['id', 'inscription_date', 'activation_date']
    
    def get_user(self, obj):
        """Retourner les infos utilisateur"""
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'phone': obj.user.phone,
            'province': obj.user.province,
        }
    
    def get_affectations(self, obj):
        """Retourner les affectations du gouvernement"""
        from .governance_serializers import AffectationSerializer
        affectations = obj.governance_affectations.all()
        return AffectationSerializer(affectations, many=True).data


class ExpertCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/mettre à jour un expert"""
    user_email = serializers.EmailField(write_only=True)
    user_phone = serializers.CharField(write_only=True, required=False)
    structure_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Expert
        fields = [
            'status', 'specialties', 'appointment_decree_number',
            'appointment_date', 'user_email', 'user_phone', 'structure_id',
            'bank_account', 'bank_name', 'mobile_money_number'
        ]
    
    def create(self, validated_data):
        """Créer un expert et associer l'utilisateur"""
        # Données séparées pour User et Expert
        user_email = validated_data.pop('user_email')
        user_phone = validated_data.pop('user_phone', '')
        structure_id = validated_data.pop('structure_id')
        
        # Créer ou récupérer l'utilisateur
        user, _ = User.objects.get_or_create(
            email=user_email,
            defaults={'username': user_email.split('@')[0]}
        )
        if user_phone:
            user.phone = user_phone
            user.save()
        
        # Créer l'expert
        structure = Structure.objects.get(id=structure_id)
        expert = Expert.objects.create(
            user=user,
            structure=structure,
            **validated_data
        )
        return expert
    
    def update(self, instance, validated_data):
        """Mettre à jour un expert"""
        user_phone = validated_data.pop('user_phone', None)
        structure_id = validated_data.pop('structure_id', None)
        validated_data.pop('user_email', None)  # Email ne peut pas être changé ici
        
        # Mettre à jour le phone si fourni
        if user_phone:
            instance.user.phone = user_phone
            instance.user.save()
        
        # Mettre à jour la structure si fournie
        if structure_id:
            instance.structure_id = structure_id
        
        # Mettre à jour les champs Expert
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class ExpertInscriptionSerializer(serializers.Serializer):
    """Serializer pour l'inscription d'un nouvel expert"""
    # Infos utilisateur
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20)
    province = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    
    # Infos expert
    structure_id = serializers.IntegerField()
    specialties = serializers.CharField(max_length=500, required=False)
    cv = serializers.FileField(required=False)
    appointment_decree_number = serializers.CharField(max_length=100, required=False)
    appointment_date = serializers.DateField(required=False)
    
    def validate_passwords(self, data):
        """Vérifier que les mots de passe correspondent"""
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
    
    def validate_structure_id(self, value):
        """Vérifier que la structure existe"""
        try:
            Structure.objects.get(id=value)
        except Structure.DoesNotExist:
            raise serializers.ValidationError("Cette structure n'existe pas.")
        return value
    
    def create(self, validated_data):
        """Créer l'utilisateur et l'expert"""
        password = validated_data.pop('password')
        validated_data.pop('password2')
        structure_id = validated_data.pop('structure_id')
        
        # Infos expert optionnelles
        expert_data = {
            'specialties': validated_data.pop('specialties', ''),
            'appointment_decree_number': validated_data.pop('appointment_decree_number', ''),
            'appointment_date': validated_data.pop('appointment_date', None),
        }
        if 'cv' in validated_data:
            expert_data['cv'] = validated_data.pop('cv')
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            province=validated_data['province'],
        )
        user.is_expert = True
        user.save()
        
        # Créer l'expert
        structure = Structure.objects.get(id=structure_id)
        expert = Expert.objects.create(
            user=user,
            structure=structure,
            status='PENDING',
            **expert_data
        )
        
        return expert


class ExpertPublicRegistrationSerializer(serializers.Serializer):
    """
    Serializer pour l'inscription PUBLIQUE des experts via QR Code
    
    Endpoint: POST /api/v1/experts/public-register/
    
    C'est un endpoint COMPLÈTEMENT SÉPARÉ et plus simple que /api/v1/auth/register/
    """
    
    # Champs utilisateur
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    
    # Champs expert
    structure_id = serializers.IntegerField(required=True)
    expertise_domains = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="IDs des CTM (Comités Techniques Miroirs) auxquels l'expert appartient"
    )
    specialties = serializers.CharField(required=False, allow_blank=True)
    organization = serializers.CharField(required=False, allow_blank=True)
    
    def validate_email(self, value):
        """Vérifier que l'email n'existe pas déjà"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
    
    def validate(self, data):
        """Vérifier que les mots de passe correspondent"""
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        
        # Vérifier que la structure existe
        try:
            Structure.objects.get(id=data.get('structure_id'))
        except Structure.DoesNotExist:
            raise serializers.ValidationError({"structure_id": "Cette structure n'existe pas."})
        
        return data
    
    def create(self, validated_data):
        """Créer l'utilisateur et l'expert via l'inscription publique"""
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        structure_id = validated_data.pop('structure_id')
        expertise_domains = validated_data.pop('expertise_domains', [])
        
        # Données optionnelles
        specialties = validated_data.pop('specialties', '')
        organization = validated_data.pop('organization', '')
        phone = validated_data.pop('phone', '')
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['email'].split('@')[0],  # Utiliser la partie avant @ comme username
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=phone,
        )
        user.is_expert = True
        user.save()
        
        # Créer l'expert
        structure = Structure.objects.get(id=structure_id)
        expert = Expert.objects.create(
            user=user,
            structure=structure,
            status='PENDING_VALIDATION',  # En attente de validation
            specialties=specialties,
            additional_info={'organization': organization} if organization else {}
        )
        
        # Associer aux domaines d'expertise (CTM) si fournis
        if expertise_domains:
            from apps.governance.models import CTM
            for ctm_id in expertise_domains:
                try:
                    ctm = CTM.objects.get(id=ctm_id)
                    # On pourrait créer une relation ici si le modèle le permet
                    # Pour l'instant, on stocke juste l'info dans additional_info
                except CTM.DoesNotExist:
                    pass
        
        return expert
