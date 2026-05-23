from rest_framework import serializers
from apps.documents.models import DocumentFile
from apps.experts.models import Expert
from apps.core.models import User


class DocumentFileSerializer(serializers.ModelSerializer):
    """Serializer pour les documents déposés par les experts"""
    expert_name = serializers.CharField(source='expert.user.get_full_name', read_only=True)
    
    class Meta:
        model = DocumentFile
        fields = [
            'id', 'expert', 'expert_name', 'file', 'filename', 
            'file_type', 'category', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'expert_name', 'created_at']

    def create(self, validated_data):
        # Extract the file to get the filename
        file_obj = validated_data.get('file')
        if file_obj:
            validated_data['filename'] = file_obj.name
        return super().create(validated_data)
