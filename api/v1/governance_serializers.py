from rest_framework import serializers
from apps.governance.models import CTM, WG, Affectation, ComitePilotage, PilotageMembreship
from .experts_serializers import ExpertBasicSerializer


class CTMBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour CTM"""
    class Meta:
        model = CTM
        fields = ['id', 'number', 'name', 'description']
        read_only_fields = ['id']


class WGBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour WG"""
    ctm_name = serializers.CharField(source='ctm.name', read_only=True)
    
    class Meta:
        model = WG
        fields = ['id', 'number', 'name', 'description', 'ctm_name', 'ctm']
        read_only_fields = ['id', 'ctm_name']


class AffectationSerializer(serializers.ModelSerializer):
    """Serializer pour les affectations d'experts"""
    expert_name = serializers.CharField(source='expert.user.get_full_name', read_only=True)
    ctm_name = serializers.CharField(source='ctm.name', read_only=True)
    wg_name = serializers.CharField(source='wg.name', read_only=True)
    ctm_role = serializers.CharField(read_only=True)
    wg_role = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    
    class Meta:
        model = Affectation
        fields = [
            'id', 'expert', 'expert_name', 'ctm', 'ctm_name',
            'wg', 'wg_name', 'ctm_role', 'wg_role', 'role',
            'is_primary_ctm', 'is_primary_wg', 'created_at'
        ]
        read_only_fields = [
            'id', 'expert_name', 'ctm_name', 'wg_name',
            'ctm_role', 'wg_role', 'role', 'created_at'
        ]


class AffectationCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/mettre à jour une affectation"""
    class Meta:
        model = Affectation
        fields = ['expert', 'ctm', 'wg']
    
    def validate(self, data):
        """Vérifier la cohérence CTM/WG"""
        wg = data.get('wg')
        ctm = data.get('ctm')
        
        if wg and wg.ctm != ctm:
            raise serializers.ValidationError(
                "Le groupe de travail doit appartenir au comité technique sélectionné."
            )
        return data


class RoleCTMSerializer(serializers.ModelSerializer):
    """Serializer pour les rôles CTM (PilotageMembreship)"""
    expert_name = serializers.CharField(source='expert.user.get_full_name', read_only=True)
    comite_name = serializers.CharField(source='comite.name', read_only=True)
    
    class Meta:
        model = PilotageMembreship
        fields = [
            'id', 'comite', 'comite_name', 'expert', 'expert_name',
            'role', 'created_at'
        ]
        read_only_fields = ['id', 'expert_name', 'comite_name', 'created_at']


class CTMDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour CTM"""
    wg_list = WGBasicSerializer(source='working_groups', many=True, read_only=True)
    expert_count = serializers.SerializerMethodField()
    leadership = serializers.SerializerMethodField()
    latest_norms = serializers.SerializerMethodField()
    
    class Meta:
        model = CTM
        fields = [
            'id', 'number', 'name', 'description', 'iso_reference',
            'created_at', 'updated_at', 'wg_list', 'expert_count', 'leadership',
            'latest_norms'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_expert_count(self, obj):
        """Compter les experts du CTM"""
        return obj.affectations.values('expert').distinct().count()
    
    def get_leadership(self, obj):
        """Retourner les leaders du CTM"""
        from .experts_serializers import ExpertBasicSerializer
        leaders = {
            'president': None,
            'rapporteur': None,
            'secretary': None,
        }
        if obj.scientific_president:
            leaders['president'] = ExpertBasicSerializer(obj.scientific_president).data
        if obj.rapporteur:
            leaders['rapporteur'] = ExpertBasicSerializer(obj.rapporteur).data
        if obj.secretary:
            leaders['secretary'] = ExpertBasicSerializer(obj.secretary).data
        return leaders
    
    def get_latest_norms(self, obj):
        """Retourner les 3 dernières normes du CTM"""
        from apps.norms.models import Norme
        from .norms_serializers import NormeBasicSerializer
        norms = Norme.objects.filter(ctm=obj).order_by('-created_at')[:3]
        return NormeBasicSerializer(norms, many=True).data


class WGDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour WG"""
    ctm = CTMBasicSerializer(read_only=True)
    expert_list = serializers.SerializerMethodField()
    expert_count = serializers.SerializerMethodField()
    latest_norms = serializers.SerializerMethodField()
    leadership = serializers.SerializerMethodField()
    
    class Meta:
        model = WG
        fields = [
            'id', 'number', 'name', 'description', 'ctm',
            'president', 'rapporteur', 'secretary',
            'created_at', 'updated_at', 'expert_list', 'expert_count',
            'latest_norms', 'leadership'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_expert_list(self, obj):
        """Lister les experts du WG"""
        affectations = obj.affectations.all()
        return AffectationSerializer(affectations, many=True).data
    
    def get_expert_count(self, obj):
        """Compter les experts du WG"""
        return obj.affectations.values('expert').distinct().count()
    
    def get_latest_norms(self, obj):
        """Retourner les 3 dernières normes du WG"""
        from apps.norms.models import Norme
        from .norms_serializers import NormeBasicSerializer
        norms = Norme.objects.filter(wg=obj).order_by('-created_at')[:3]
        return NormeBasicSerializer(norms, many=True).data
    
    def get_leadership(self, obj):
        """Retourner les leaders du WG"""
        from .experts_serializers import ExpertBasicSerializer
        leaders = {
            'president': None,
            'rapporteur': None,
            'secretary': None,
        }
        if obj.president:
            leaders['president'] = ExpertBasicSerializer(obj.president).data
        if obj.rapporteur:
            leaders['rapporteur'] = ExpertBasicSerializer(obj.rapporteur).data
        if obj.secretary:
            leaders['secretary'] = ExpertBasicSerializer(obj.secretary).data
        return leaders


class ComitePilotageSerializer(serializers.ModelSerializer):
    """Serializer pour le comité de pilotage"""
    expert_name = serializers.CharField(source='expert.user.get_full_name', read_only=True)
    comite_name = serializers.CharField(source='comite.name', read_only=True)
    
    class Meta:
        model = PilotageMembreship
        fields = [
            'id', 'comite', 'comite_name', 'expert', 'expert_name',
            'role', 'created_at'
        ]
        read_only_fields = ['id', 'expert_name', 'comite_name', 'created_at']


class CTMCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/mettre à jour un CTM"""
    class Meta:
        model = CTM
        fields = ['number', 'name', 'description', 'iso_reference']
    
    def validate_number(self, value):
        """Vérifier l'unicité du numéro"""
        instance = self.instance
        if CTM.objects.filter(number=value).exclude(id=instance.id if instance else None).exists():
            raise serializers.ValidationError("Ce numéro de CTM existe déjà.")
        return value


class WGCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/mettre à jour un WG"""
    class Meta:
        model = WG
        fields = ['ctm', 'number', 'name', 'description', 'scope']
    
    def validate_number(self, value):
        """Vérifier l'unicité du numéro par CTM"""
        instance = self.instance
        ctm = self.initial_data.get('ctm')
        
        if WG.objects.filter(ctm_id=ctm, number=value).exclude(
            id=instance.id if instance else None
        ).exists():
            raise serializers.ValidationError(
                "Ce numéro de groupe de travail existe déjà pour ce CTM."
            )
        return value


class AffectationBulkSerializer(serializers.Serializer):
    """Serializer pour l'affectation en masse"""
    affectations = AffectationCreateSerializer(many=True)
    
    def create(self, validated_data):
        """Créer plusieurs affectations"""
        affectations_data = validated_data.get('affectations', [])
        created = []
        for data in affectations_data:
            affectation = Affectation.objects.create(**data)
            created.append(affectation)
        return created
