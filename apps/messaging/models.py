from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class Message(BaseModel):
    """Modèle pour les messages de chat (général ou lié aux réunions)"""
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_messages') # For direct messages
    reunion = models.ForeignKey('meetings.Reunion', on_delete=models.SET_NULL, null=True, blank=True, related_name='messages') # Optional, for contextual messages in a meeting
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    is_read = models.BooleanField(default=False)
    is_clause_share = models.BooleanField(default=False)
    clause_code = models.CharField(max_length=255, blank=True, null=True)
    clause_excerpt = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'messaging_message'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['sender', 'timestamp']),
            models.Index(fields=['recipient', 'timestamp']),
            models.Index(fields=['reunion', 'timestamp']),
        ]

    def __str__(self):
        if self.reunion:
            return f"Message from {self.sender.get_full_name()} in {self.reunion.titre} at {self.timestamp.strftime('%H:%M')}"
        elif self.recipient:
            return f"Message from {self.sender.get_full_name()} to {self.recipient.get_full_name()} at {self.timestamp.strftime('%H:%M')}"
        return f"Message from {self.sender.get_full_name()} at {self.timestamp.strftime('%H:%M')}"
