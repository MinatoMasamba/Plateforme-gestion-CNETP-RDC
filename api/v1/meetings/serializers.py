from rest_framework import serializers
from apps.meetings.models import Reunion, Presence, ProcessusVerbaux, ReunionVote
from ..experts.serializers import ExpertBasicSerializer


class PresenceSerializer(serializers.ModelSerializer):
    """Serializer pour les présences"""
    expert_name = serializers.CharField(source='expert.user.get_full_name', read_only=True)
    expert_structure = serializers.CharField(source='expert.structure.name', read_only=True)

    class Meta:
        model = Presence
        fields = [
            'id', 'reunion', 'expert', 'expert_name', 'expert_structure', 'status',
            'marked_at', 'marked_by'
        ]
        read_only_fields = ['id', 'expert_name', 'expert_structure', 'marked_at']


class ReunionVoteSerializer(serializers.ModelSerializer):
    """Serializer pour les votes électroniques de réunion."""
    expert_name = serializers.CharField(source='expert.user.get_full_name', read_only=True)

    class Meta:
        model = ReunionVote
        fields = ['id', 'reunion', 'expert', 'expert_name', 'choix', 'justification', 'voted_at']
        read_only_fields = ['id', 'expert', 'expert_name', 'voted_at']


class ProcessusVerbauxSerializer(serializers.ModelSerializer):
    """Serializer pour les procès-verbaux"""
    reunion_info = serializers.SerializerMethodField()

    class Meta:
        model = ProcessusVerbaux
        fields = [
            'id', 'reunion', 'reunion_info', 'titre', 'contenu',
            'nombre_presents', 'nombre_absents', 'quorum_atteint',
            'generated_at', 'signed_by', 'signature_date'
        ]
        read_only_fields = ['id', 'generated_at']

    def get_reunion_info(self, obj):
        """Récupérer les infos de réunion"""
        return {
            'id': obj.reunion.id,
            'type': obj.reunion.type,
            'date': obj.reunion.date,
            'titre': obj.reunion.titre
        }


class ReunionBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour les réunions"""
    presences_count = serializers.SerializerMethodField()
    ctm_name = serializers.CharField(source='ctm.name', read_only=True)
    wg_name = serializers.CharField(source='wg.name', read_only=True)

    class Meta:
        model = Reunion
        fields = [
            'id', 'type', 'titre', 'description', 'ctm', 'ctm_name', 'wg', 'wg_name',
            'document_reglementaire', 'date', 'lieu', 'lien_reunion_virtuelle',
            'ordre_jour', 'status', 'presences_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_presences_count(self, obj):
        return obj.presences.count()


class ReunionDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les réunions"""
    presences = PresenceSerializer(many=True, read_only=True)
    votes = ReunionVoteSerializer(many=True, read_only=True)
    pv = ProcessusVerbauxSerializer(read_only=True)
    ctm_name = serializers.CharField(source='ctm.name', read_only=True)
    wg_name = serializers.CharField(source='wg.name', read_only=True)
    organisateur_name = serializers.CharField(
        source='organisateur.user.get_full_name',
        read_only=True
    )

    class Meta:
        model = Reunion
        fields = [
            'id', 'type', 'titre', 'description', 'ctm', 'ctm_name', 'wg', 'wg_name',
            'document_reglementaire', 'date', 'lieu',
            'lien_reunion_virtuelle', 'ordre_jour', 'status',
            'organisateur', 'organisateur_name', 'presences',
            'votes', 'pv', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'organisateur_name', 'presences', 'votes', 'pv',
            'created_at', 'updated_at'
        ]


class ReunionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/mettre à jour une réunion"""
    class Meta:
        model = Reunion
        fields = [
            'type', 'titre', 'description', 'ctm', 'wg', 'document_reglementaire', 'date', 'lieu',
            'lien_reunion_virtuelle', 'ordre_jour'
        ]

    def validate_date(self, value):
        """Vérifier que la date n'est pas dans le passé"""
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError(
                "La date de la réunion ne peut pas être dans le passé."
            )
        return value


class ReunionStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour le statut d'une réunion"""
    class Meta:
        model = Reunion
        fields = ['status']

    def validate_status(self, value):
        """Vérifier les transitions de statut valides"""
        instance = self.instance
        if instance:
            valid_transitions = {
                'PLANNED': ['IN_PROGRESS', 'CANCELLED'],
                'IN_PROGRESS': ['COMPLETED', 'CANCELLED'],
                'COMPLETED': [],
                'CANCELLED': [],
            }

            allowed_statuses = valid_transitions.get(instance.status, [])
            if value not in allowed_statuses:
                raise serializers.ValidationError(
                    f"Transition invalide de {instance.status} à {value}."
                )
        return value


class PresenceCheckInSerializer(serializers.ModelSerializer):
    """Serializer pour enregistrer la présence"""
    class Meta:
        model = Presence
        fields = ['status']


class ReunionSummarySerializer(serializers.Serializer):
    """Résumé d'une réunion"""
    reunion_id = serializers.IntegerField()
    titre = serializers.CharField()
    date = serializers.DateTimeField()
    total_experts = serializers.IntegerField()
    presents = serializers.IntegerField()
    absents = serializers.IntegerField()
    quorum_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class ReunionStatsSerializer(serializers.Serializer):
    """Statistiques sur les réunions"""
    total_reunions = serializers.IntegerField()
    by_type = serializers.DictField(child=serializers.IntegerField())
    average_attendance = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_pv_generated = serializers.IntegerField()
