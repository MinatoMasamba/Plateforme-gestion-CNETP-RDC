from rest_framework import serializers
from apps.messaging.models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'reunion',
            'sender',
            'sender_name',
            'recipient',
            'recipient_name',
            'content',
            'timestamp',
            'parent',
            'is_read',
            'is_clause_share',
            'clause_code',
            'clause_excerpt',
        ]
        read_only_fields = ['sender', 'timestamp']
