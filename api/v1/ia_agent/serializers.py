from rest_framework import serializers

from apps.ia_agent.models import AgentArtifact, AgentMessage, AgentSession


class AgentSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentSession
        fields = ['id', 'scope', 'title', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AgentMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentMessage
        fields = ['id', 'role', 'content', 'tool_name', 'tool_input', 'tool_output', 'created_at']


class AgentArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentArtifact
        fields = [
            'id', 'session', 'message', 'artifact_type', 'title', 'payload', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields
