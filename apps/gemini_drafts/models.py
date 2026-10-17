from django.db import models
import uuid
from django.utils import timezone


MONTHS_FR = (
    'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
)


class Draft(models.Model):
    """Communiqué généré par l'IA, conservé dans l'historique avec sa date.

    Le contenu peut être fourni soit sous forme de texte Markdown
    (``draft_text``), soit sous forme de fichier joint (``file``).
    Chaque enregistrement est immuable côté historique : les éditions
    ultérieures créent un nouveau brouillon et l'ancien reste consultable.
    """

    STATUS_DRAFT = 'DRAFT'
    STATUS_PUBLISHED = 'PUBLISHED'
    STATUS_ARCHIVED = 'ARCHIVED'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Brouillon'),
        (STATUS_PUBLISHED, 'Publié'),
        (STATUS_ARCHIVED, 'Archivé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300, blank=True, verbose_name="Titre")
    ctm = models.CharField(max_length=200)
    wg = models.CharField(max_length=200)
    type = models.CharField(max_length=50)
    domain = models.CharField(max_length=200, blank=True, null=True)
    input_json = models.JSONField(blank=True, null=True)
    draft_text = models.TextField(
        blank=True,
        help_text="Contenu du communiqué au format Markdown (facultatif si un fichier est joint)",
    )
    file = models.FileField(
        upload_to='communiques/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Fichier du communiqué",
        help_text="Fichier joint (PDF, DOCX...) si le contenu n'est pas fourni en Markdown",
    )
    classification_reason = models.TextField(blank=True, help_text="Raison du choix du WG par l'IA")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name="Statut",
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Publié le",
        help_text="Date de publication officielle du communiqué",
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        db_table = 'gemini_drafts'
        ordering = ['-created_at']
        verbose_name = "Communiqué"
        verbose_name_plural = "Communiqués"
        indexes = [
            models.Index(fields=['ctm', 'wg']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return self.title or f"{self.type} — {self.ctm} / {self.wg} ({self.created_date})"

    @property
    def reference_date(self):
        """Date de référence : publication si disponible, sinon création."""
        return self.published_at or self.created_at

    @property
    def created_date(self):
        return timezone.localtime(self.created_at).date()

    @property
    def created_day(self):
        return self.created_date.day

    @property
    def created_month(self):
        return self.created_date.month

    @property
    def created_year(self):
        return self.created_date.year

    @property
    def created_month_label(self):
        return MONTHS_FR[self.created_month - 1]

    @property
    def created_label(self):
        """Date lisible en français, ex. « 17 octobre 2026 »."""
        return f"{self.created_day} {self.created_month_label} {self.created_year}"

    @property
    def is_file_based(self):
        return bool(self.file)

    def as_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'ctm': self.ctm,
            'wg': self.wg,
            'type': self.type,
            'domain': self.domain,
            'input_json': self.input_json,
            'draft_text': self.draft_text,
            'file_url': self.file.url if self.file else None,
            'content_format': 'file' if self.is_file_based else 'markdown',
            'status': self.status,
            'status_display': self.get_status_display(),
            'classification_reason': self.classification_reason,
            'published_at': int(self.published_at.timestamp() * 1000) if self.published_at else None,
            'created_at': int(self.created_at.timestamp() * 1000),
            'updated_at': int(self.updated_at.timestamp() * 1000) if self.updated_at else None,
            'created_date': self.created_date.isoformat(),
            'created_day': self.created_day,
            'created_month': self.created_month,
            'created_month_label': self.created_month_label,
            'created_year': self.created_year,
            'created_label': self.created_label,
        }
