from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.messaging.models import Message

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    sender_name  = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_email = serializers.EmailField(source='sender.email', read_only=True)

    # Alias "receiver" / "receiver_name" pour compatibilité Flutter
    # (Django utilise en interne "recipient")
    receiver      = serializers.PrimaryKeyRelatedField(source='recipient', read_only=True)
    receiver_name = serializers.CharField(source='recipient.get_full_name', read_only=True)

    # Champ d'écriture : Flutter envoie "receiver_id"
    receiver_id = serializers.PrimaryKeyRelatedField(
        source='recipient',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Message
        fields = [
            'id',
            'reunion',
            'sender',
            'sender_name',
            'sender_email',
            'receiver',
            'receiver_name',
            'receiver_id',
            'subject',
            'content',
            'status',
            'timestamp',
            'parent',
            'is_read',
            'is_clause_share',
            'clause_code',
            'clause_excerpt',
        ]
        read_only_fields = [
            'sender', 'sender_name', 'sender_email',
            'receiver', 'receiver_name',
            'timestamp', 'status',
        ]
