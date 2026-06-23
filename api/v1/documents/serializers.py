from rest_framework import serializers
from apps.documents.models import DocumentFile


class DocumentFileSerializer(serializers.ModelSerializer):
    """Serializer pour les documents déposés par les experts"""
    expert_name = serializers.CharField(source='expert.user.get_full_name', read_only=True)

    class Meta:
        model = DocumentFile
        fields = [
            'id', 'expert', 'expert_name', 'file', 'title',
            'file_type', 'category', 'description', 'norme', 'is_public',
            'file_size', 'created_at',
        ]
        read_only_fields = ['id', 'expert_name', 'file_size', 'created_at']

    def create(self, validated_data):
        file_obj = validated_data.get('file')
        if file_obj:
            validated_data['file_size'] = file_obj.size
            validated_data['mime_type'] = getattr(file_obj, 'content_type', '') or ''
        return super().create(validated_data)
