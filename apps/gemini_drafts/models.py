from django.db import models
import uuid
from django.utils import timezone


class Draft(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ctm = models.CharField(max_length=200)
    wg = models.CharField(max_length=200)
    type = models.CharField(max_length=50)
    domain = models.CharField(max_length=200, blank=True, null=True)
    input_json = models.JSONField(blank=True, null=True)
    draft_text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    classification_reason = models.TextField(blank=True, help_text="Raison du choix du WG par l'IA")

    class Meta:
        db_table = 'gemini_drafts'
        ordering = ['-created_at']

    def as_dict(self):
        return {
            'id': str(self.id),
            'ctm': self.ctm,
            'wg': self.wg,
            'type': self.type,
            'domain': self.domain,
            'input_json': self.input_json,
            'draft_text': self.draft_text,
            'classification_reason': self.classification_reason,
            'created_at': int(self.created_at.timestamp() * 1000),
        }