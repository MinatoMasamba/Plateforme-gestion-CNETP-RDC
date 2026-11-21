from urllib.parse import urlsplit

from rest_framework import serializers


class DocumentLinkSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    url = serializers.URLField(max_length=2000)

    def validate_url(self, value):
        if urlsplit(value).scheme != 'https':
            raise serializers.ValidationError('Un lien HTTPS est requis.')
        return value


class MeetingPreparationSerializer(serializers.Serializer):
    revision = serializers.IntegerField(min_value=0)
    meet_link = serializers.URLField(allow_blank=True, max_length=2000)
    ordre_jour = serializers.CharField(allow_blank=True, max_length=20000)
    question_vote = serializers.CharField(allow_blank=True, max_length=5000)
    documents = DocumentLinkSerializer(many=True)

    def validate_meet_link(self, value):
        if value:
            parts = urlsplit(value)
            if parts.scheme != 'https' or parts.hostname != 'meet.google.com' or parts.username or parts.port not in (None, 443) or not parts.path.strip('/'):
                raise serializers.ValidationError('Utilisez un lien https://meet.google.com/... valide.')
        return value

    def validate_documents(self, value):
        if len(value) > 50:
            raise serializers.ValidationError('Maximum 50 documents par réunion.')
        return value


class MeetingPVDraftSerializer(serializers.Serializer):
    revision = serializers.IntegerField(min_value=0)
    contenu = serializers.CharField(max_length=100000)
    points_discutes = serializers.CharField(max_length=30000)
    decisions = serializers.CharField(max_length=30000)
    actions = serializers.ListField(child=serializers.DictField(), max_length=100)

    def validate_actions(self, values):
        for value in values:
            if set(value) - {'text', 'responsible', 'due_date'} or not str(value.get('text', '')).strip():
                raise serializers.ValidationError('Chaque action exige un texte ; responsable et échéance sont facultatifs.')
            if value.get('due_date'):
                serializers.DateField().run_validation(value['due_date'])
        return values


class MeetingPVValidationSerializer(serializers.Serializer):
    revision = serializers.IntegerField(min_value=0, required=False)
