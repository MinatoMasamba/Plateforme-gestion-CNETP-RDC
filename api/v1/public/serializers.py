from rest_framework import serializers
from apps.public.models import PublicAmendement


class PublicAmendementSerializer(serializers.ModelSerializer):
    """Serializer pour PublicAmendement (créer/lister)"""
    status_display = serializers.CharField(source='get_status_display_fr', read_only=True)

    class Meta:
        model = PublicAmendement
        fields = [
            'id', 'norme', 'proposed_by_name', 'proposed_by_email',
            'proposed_by_organization', 'proposed_by_province', 'title', 'description',
            'justification', 'status', 'status_display',
            'review_notes', 'reviewed_by', 'reviewed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'review_notes', 'reviewed_by',
            'reviewed_at', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        """Créer un nouvel amendement public"""
        amendment = PublicAmendement.objects.create(**validated_data)
        return amendment


class PublicAmendementDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour PublicAmendement"""
    status_display = serializers.CharField(source='get_status_display_fr', read_only=True)
    norme_title = serializers.CharField(source='norme.title', read_only=True)
    norme_reference = serializers.CharField(source='norme.reference_number', read_only=True)

    class Meta:
        model = PublicAmendement
        fields = [
            'id', 'norme', 'norme_title', 'norme_reference',
            'proposed_by_name', 'proposed_by_email', 'proposed_by_organization',
            'proposed_by_province',
            'title', 'description', 'justification',
            'status', 'status_display', 'review_notes', 'reviewed_by', 'reviewed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'review_notes', 'reviewed_by',
            'reviewed_at', 'created_at', 'updated_at', 'norme_title', 'norme_reference'
        ]


class PublicAmendementReviewSerializer(serializers.ModelSerializer):
    """Serializer pour révision par CTC"""
    class Meta:
        model = PublicAmendement
        fields = ['status', 'review_notes', 'reviewed_by']

    def update(self, instance, validated_data):
        """Mettre à jour le statut de révision"""
        instance.mark_as_reviewed(
            reviewer_name=validated_data.get('reviewed_by', instance.reviewed_by),
            notes=validated_data.get('review_notes', instance.review_notes),
            status=validated_data.get('status', instance.status)
        )
        return instance
