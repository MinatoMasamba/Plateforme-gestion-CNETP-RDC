from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class Message(BaseModel):
    """Modèle pour les messages de chat (général ou lié aux réunions)"""

    STATUS_SENT      = 'sent'
    STATUS_DELIVERED = 'delivered'
    STATUS_READ      = 'read'
    STATUS_CHOICES   = [
        (STATUS_SENT,      'Envoyé'),
        (STATUS_DELIVERED, 'Distribué'),
        (STATUS_READ,      'Lu'),
    ]

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_messages')
    reunion = models.ForeignKey('meetings.Reunion', on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    subject = models.CharField(max_length=200, blank=True, default='')
    content = models.TextField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_SENT)
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
