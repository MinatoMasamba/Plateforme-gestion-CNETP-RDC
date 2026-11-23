from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.experts.models import Expert
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


class ConversationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    structure_name = serializers.CharField(source='structure.name', read_only=True)
    ctm_name = serializers.CharField(source='ctm.name', read_only=True, default='')
    unread_count = serializers.IntegerField(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Expert
        fields = [
            'id',
            'user_id',
            'user_name',
            'structure_name',
            'ctm_name',
            'status',
            'specialties',
            'unread_count',
            'last_message',
        ]

    def get_last_message(self, obj):
        if not getattr(obj, 'last_message_id', None):
            return None
        return {
            'id': obj.last_message_id,
            'content': obj.last_message_content,
            'sender': obj.last_message_sender_id,
            'timestamp': serializers.DateTimeField().to_representation(
                obj.last_message_timestamp
            ),
            'is_read': obj.last_message_is_read,
            'is_clause_share': obj.last_message_is_clause_share,
            'clause_code': obj.last_message_clause_code,
            'clause_excerpt': obj.last_message_clause_excerpt,
        }
