from rest_framework import serializers
from apps.norms.models import Norme, NormeVersion, ChangementVersion
from .experts_serializers import ExpertBasicSerializer


class ChangementVersionSerializer(serializers.ModelSerializer):
    """Serializer pour les changements de version"""
    class Meta:
        model = ChangementVersion
        fields = [
            'id', 'version', 'section', 'old_text', 'new_text',
            'change_type', 'change_reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NormeVersionSerializer(serializers.ModelSerializer):
    """Serializer pour les versions de normes"""
    author_name = serializers.CharField(source='version_author.get_full_name', read_only=True)
    changes = ChangementVersionSerializer(many=True, read_only=True)
    
    class Meta:
        model = NormeVersion
        fields = [
            'id', 'norme', 'version_number', 'title', 'content',
            'document', 'summary', 'is_draft', 'version_author',
            'author_name', 'created_at', 'changes'
        ]
        read_only_fields = ['id', 'version_number', 'created_at', 'author_name']


class NormeBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour les normes"""
    ctm_name = serializers.CharField(source='ctm.name', read_only=True)
    wg_name = serializers.CharField(source='wg.name', read_only=True)
    
    class Meta:
        model = Norme
        fields = [
            'id', 'reference_number', 'title', 'status',
            'ctm', 'ctm_name', 'wg', 'wg_name', 'is_public', 'created_at'
        ]
        read_only_fields = ['id', 'ctm_name', 'wg_name', 'created_at']


class NormeDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les normes"""
    ctm_name = serializers.CharField(source='ctm.name', read_only=True)
    wg_name = serializers.CharField(source='wg.name', read_only=True)
    latest_version = serializers.SerializerMethodField()
    version_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Norme
        fields = [
            'id', 'reference_number', 'title', 'description', 'status',
            'ctm', 'ctm_name', 'wg', 'wg_name',
            'iso_reference', 'arso_reference',
            'start_date', 'ctm_submission_date', 'legistic_review_date',
            'public_inquiry_start', 'public_inquiry_end', 'pilotage_validation_date',
            'adoption_date', 'homologation_date',
            'publication_date', 'jo_reference', 'jo_file',
            'current_version', 'tags', 'is_public',
            'latest_version', 'version_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ctm_name', 'wg_name', 'created_at', 'updated_at']
    
    def get_latest_version(self, obj):
        latest = obj.get_latest_version()
        if latest:
            return NormeVersionSerializer(latest).data
        return None
    
    def get_version_count(self, obj):
        return obj.versions.count()


class NormeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/mettre à jour une norme"""
    class Meta:
        model = Norme
        fields = [
            'reference_number', 'title', 'description',
            'ctm', 'wg', 'iso_reference', 'arso_reference',
            'tags', 'is_public'
        ]
    
    def validate(self, data):
        """Vérifier que WG appartient au CTM"""
        wg = data.get('wg')
        ctm = data.get('ctm')
        
        if wg and wg.ctm != ctm:
            raise serializers.ValidationError(
                "Le groupe de travail doit appartenir au comité technique sélectionné."
            )
        return data


class NormeStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour le statut d'une norme"""
    class Meta:
        model = Norme
        fields = ['status']
    
    def validate_status(self, value):
        """Vérifier la transition de statut valide"""
        instance = self.instance
        if instance:
            # Définir les transitions valides
            valid_transitions = {
                'DRAFT': ['INTERNAL_REVIEW'],
                'INTERNAL_REVIEW': ['CTM_REVIEW', 'DRAFT'],
                'CTM_REVIEW': ['LEGISTIC_REVIEW', 'INTERNAL_REVIEW'],
                'LEGISTIC_REVIEW': ['PUBLIC_INQUIRY', 'CTM_REVIEW'],
                'PUBLIC_INQUIRY': ['PILOTAGE_REVIEW', 'CTM_REVIEW'],
                'PILOTAGE_REVIEW': ['FINAL_REVIEW', 'PUBLIC_INQUIRY'],
                'FINAL_REVIEW': ['ADOPTED', 'PUBLIC_INQUIRY'],
                'ADOPTED': ['HOMOLOGATED'],
                'HOMOLOGATED': ['PUBLISHED'],
                'PUBLISHED': ['ARCHIVED'],
                'ARCHIVED': [],
            }
            
            allowed_statuses = valid_transitions.get(instance.status, [])
            if value not in allowed_statuses:
                raise serializers.ValidationError(
                    f"Transition invalide de {instance.status} à {value}. "
                    f"Transitions valides: {', '.join(allowed_statuses)}"
                )
        return value


class NormeVersionCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une nouvelle version de norme"""
    class Meta:
        model = NormeVersion
        fields = ['title', 'content', 'document', 'summary']
    
    def create(self, validated_data):
        """Créer une nouvelle version avec numéro auto-incrémenté"""
        norme = self.context.get('norme')
        if not norme:
            raise serializers.ValidationError("Norme not provided in context")
        
        # Calculer le prochain numéro de version
        latest = norme.versions.order_by('-version_number').first()
        next_version_number = (latest.version_number + 1) if latest else 1
        
        version = NormeVersion.objects.create(
            norme=norme,
            version_number=next_version_number,
            version_author=self.context.get('request').user,
            **validated_data
        )
        return version


class NormeFullHistorySerializer(serializers.ModelSerializer):
    """Serializer avec historique complet"""
    versions = NormeVersionSerializer(many=True, read_only=True)
    ctm_name = serializers.CharField(source='ctm.name', read_only=True)
    wg_name = serializers.CharField(source='wg.name', read_only=True)
    
    class Meta:
        model = Norme
        fields = [
            'id', 'reference_number', 'title', 'description',
            'ctm', 'ctm_name', 'wg', 'wg_name', 'status',
            'iso_reference', 'arso_reference', 'tags', 'is_public',
            'versions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ctm_name', 'wg_name', 'created_at', 'updated_at']
