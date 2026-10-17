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


class CommuniqueEnvoi(BaseModel):
    """Suivi nominatif des envois d'un communiqué (HTML, texte et PDF)."""

    STATUS_PENDING = 'PENDING'
    STATUS_SENT = 'SENT'
    STATUS_FAILED = 'FAILED'
    STATUS_SKIPPED = 'SKIPPED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_SENT, 'Envoyé'),
        (STATUS_FAILED, 'Échec'),
        (STATUS_SKIPPED, 'Ignoré'),
    ]

    communique_key = models.CharField(max_length=120, db_index=True)
    subject = models.CharField(max_length=300)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='communique_envois',
    )
    email = models.EmailField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'messaging_communique_envoi'
        verbose_name = "Envoi de communiqué"
        verbose_name_plural = "Envois de communiqués"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['communique_key', 'email'],
                name='unique_communique_envoi_par_email',
            ),
        ]
        indexes = [
            models.Index(fields=['communique_key', 'status']),
        ]

    def __str__(self):
        return f"{self.communique_key} — {self.email} ({self.get_status_display()})"


class CommuniqueSequence(models.Model):
    """Compteur unique du numéro des communiqués officiels."""

    last_number = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Séquence des communiqués"
        verbose_name_plural = "Séquence des communiqués"

    @classmethod
    def peek_next_number(cls):
        sequence = cls.objects.first()
        return (sequence.last_number if sequence else 1) + 1

    @classmethod
    def next_number(cls):
        from django.db import transaction

        with transaction.atomic():
            sequence, _ = cls.objects.select_for_update().get_or_create(
                pk=1, defaults={'last_number': 1},
            )
            sequence.last_number += 1
            sequence.save(update_fields=['last_number'])
            return sequence.last_number


class CommuniqueOfficiel(BaseModel):
    """Communiqué officiel : numéro auto-incrémenté, date saisissable."""

    STATUS_DRAFT = 'DRAFT'
    STATUS_SENT = 'SENT'
    STATUS_ARCHIVED = 'ARCHIVED'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Brouillon'),
        (STATUS_SENT, 'Envoyé'),
        (STATUS_ARCHIVED, 'Archivé'),
    ]

    numero = models.PositiveIntegerField(unique=True, editable=False, verbose_name="Numéro")
    date_communique = models.DateField(verbose_name="Date du communiqué")
    objet = models.CharField(max_length=300, verbose_name="Objet")
    fichier_pdf = models.FileField(
        upload_to='communiques/%Y/%m/',
        blank=True, null=True,
        verbose_name="PDF original du communiqué",
        help_text="Fichier officiel à joindre tel quel à l'email ; aucun PDF n'est régénéré.",
    )
    statut = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    notes = models.TextField(blank=True, verbose_name="Notes internes")

    class Meta:
        db_table = 'messaging_communique_officiel'
        verbose_name = "Communiqué officiel"
        verbose_name_plural = "Communiqués officiels"
        ordering = ['-numero']

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = CommuniqueSequence.next_number()
        return super().save(*args, **kwargs)

    @property
    def numero_label(self):
        return f"{self.numero:03d}"

    def __str__(self):
        return f"Communiqué N° {self.numero_label} du {self.date_communique:%d/%m/%Y}"
