import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer pour la messagerie directe temps réel.
    URL: ws://.../ws/chat/{other_user_id}/?token=<jwt>
    Room: chat_{min_id}_{max_id}
    """

    async def connect(self):
        # Authenticate via JWT token in query string
        user = await self._authenticate()
        if user is None:
            await self.close(code=4001)
            return

        self.user = user
        other_id = self.scope['url_route']['kwargs']['user_id']

        # Deterministic room name (same for both participants)
        ids = sorted([user.id, int(other_id)])
        self.room_name = f"chat_{ids[0]}_{ids[1]}"

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get('type', 'chat_message')

        if msg_type == 'chat_message':
            await self._handle_send(data)
        elif msg_type == 'mark_read':
            await self._handle_mark_read(data)

    async def _handle_send(self, data):
        receiver_id = data.get('receiver_id')
        content     = (data.get('content') or '').strip()
        subject     = (data.get('subject') or '').strip()

        if not content or not receiver_id:
            return

        message = await self._save_message(receiver_id, content, subject)
        if message is None:
            return

        # Broadcast to both participants
        payload = {
            'type': 'chat_message',
            'id':             message['id'],
            'subject':        message['subject'],
            'content':        message['content'],
            'sender':         message['sender_id'],
            'sender_name':    message['sender_name'],
            'sender_email':   message['sender_email'],
            'receiver':       message['receiver_id'],
            'receiver_name':  message['receiver_name'],
            'status':         'delivered',
            'is_read':        False,
            'timestamp':      message['timestamp'],
        }
        await self.channel_layer.group_send(self.room_name, payload)

    async def _handle_mark_read(self, data):
        message_id = data.get('message_id')
        if not message_id:
            return

        updated = await self._mark_message_read(message_id)
        if updated:
            # Notify sender that message was read
            await self.channel_layer.group_send(self.room_name, {
                'type':       'read_ack',
                'message_id': message_id,
                'status':     'read',
            })

    # ── Channel layer event handlers ─────────────────────────────────────────

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def read_ack(self, event):
        await self.send(text_data=json.dumps(event))

    # ── DB helpers ────────────────────────────────────────────────────────────

    @database_sync_to_async
    def _authenticate(self):
        query_string = self.scope.get('query_string', b'').decode()
        token_str = None
        for part in query_string.split('&'):
            if part.startswith('token='):
                token_str = part[6:]
                break
        if not token_str:
            return None
        try:
            access = AccessToken(token_str)
            return User.objects.get(id=access['user_id'])
        except (TokenError, InvalidToken, User.DoesNotExist, KeyError):
            return None

    @database_sync_to_async
    def _save_message(self, receiver_id, content, subject):
        from apps.messaging.models import Message
        try:
            receiver = User.objects.get(pk=receiver_id)
        except User.DoesNotExist:
            return None

        msg = Message.objects.create(
            sender=self.user,
            recipient=receiver,
            content=content,
            subject=subject,
            status=Message.STATUS_DELIVERED,
        )

        # Push notification (best-effort)
        try:
            from apps.mobileapp.models import Notification
            Notification.objects.create(
                user=receiver,
                title=f"Message de {self.user.get_full_name() or self.user.username}",
                body=content[:120],
                notification_type='MESSAGE',
                priority='NORMAL',
                data={'message_id': msg.id, 'sender_id': self.user.id},
            )
        except Exception:
            pass

        return {
            'id':            msg.id,
            'subject':       msg.subject,
            'content':       msg.content,
            'sender_id':     self.user.id,
            'sender_name':   self.user.get_full_name(),
            'sender_email':  self.user.email,
            'receiver_id':   receiver.id,
            'receiver_name': receiver.get_full_name(),
            'timestamp':     msg.timestamp.isoformat(),
        }

    @database_sync_to_async
    def _mark_message_read(self, message_id):
        from apps.messaging.models import Message
        return Message.objects.filter(
            pk=message_id,
            recipient=self.user,
        ).update(is_read=True, status=Message.STATUS_READ)
