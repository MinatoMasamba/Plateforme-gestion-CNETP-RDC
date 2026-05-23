from rest_framework import serializers
from apps.validation.models import LegisticReview
from apps.norms.models import Norme
from apps.experts.models import Expert


class LegisticReviewBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour LegisticReview"""
    norme_reference = serializers.CharField(source='norme.reference_number', read_only=True)
    legist_name = serializers.CharField(source='legist.user.get_full_name', read_only=True)
    
    class Meta:
        model = LegisticReview
        fields = [
            'id', 'norme', 'norme_reference', 'status', 
            'legist', 'legist_name', 'comments',
            'review_start_date', 'review_end_date', 'approval_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'norme_reference', 'legist_name', 'created_at', 'updated_at']


class LegisticReviewDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour LegisticReview"""
    norme_reference = serializers.CharField(source='norme.reference_number', read_only=True)
    norme_title = serializers.CharField(source='norme.title', read_only=True)
    norme_status = serializers.CharField(source='norme.status', read_only=True)
    legist_name = serializers.CharField(source='legist.user.get_full_name', read_only=True)
    legist_email = serializers.CharField(source='legist.user.email', read_only=True)
    
    class Meta:
        model = LegisticReview
        fields = [
            'id', 'norme', 'norme_reference', 'norme_title', 'norme_status',
            'status', 'legist', 'legist_name', 'legist_email',
            'comments', 'review_start_date', 'review_end_date', 'approval_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'norme', 'norme_reference', 'norme_title', 'norme_status',
            'legist_name', 'legist_email', 'created_at', 'updated_at'
        ]


class LegisticReviewStartSerializer(serializers.ModelSerializer):
    """Serializer pour commencer un toilettage (assigner légiste)"""
    class Meta:
        model = LegisticReview
        fields = ['legist', 'comments']
    
    def validate_legist(self, value):
        """Vérifier que le légiste est bien un expert"""
        if not value.is_active:
            raise serializers.ValidationError("Le légiste doit être actif")
        return value


class LegisticReviewCompleteSerializer(serializers.ModelSerializer):
    """Serializer pour compléter un toilettage"""
    class Meta:
        model = LegisticReview
        fields = ['comments', 'approval_date']
    
    def validate_approval_date(self, value):
        """Vérifier que la date n'est pas dans le futur"""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("La date d'approbation ne peut pas être dans le futur")
        return value


class LegisticReviewRejectSerializer(serializers.ModelSerializer):
    """Serializer pour rejeter un toilettage"""
    class Meta:
        model = LegisticReview
        fields = ['comments']
