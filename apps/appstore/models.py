from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from apps.core.models import BaseModel

from .storage import appstore_private_storage, package_upload_to


class AppCategory(BaseModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Catégorie App Store'
        verbose_name_plural = 'Catégories App Store'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:140]
        super().save(*args, **kwargs)


class SoftwareApp(BaseModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField(max_length=280)
    full_description = models.TextField(blank=True)
    features = models.TextField(
        blank=True,
        help_text='Une fonctionnalité par ligne.',
    )
    publisher = models.CharField(max_length=200, default='CNE-ITP')
    category = models.ForeignKey(
        AppCategory,
        on_delete=models.PROTECT,
        related_name='applications',
        null=True,
        blank=True,
    )
    icon = models.ImageField(upload_to='appstore/icons/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    recommended_version = models.ForeignKey(
        'AppVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:200] or 'application'
            slug = base
            counter = 2
            while SoftwareApp.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_withdrawn(self):
        return self.withdrawn_at is not None

    def feature_list(self):
        return [line.strip() for line in (self.features or '').splitlines() if line.strip()]

    def visible_platforms(self):
        platforms = (
            AppReleaseFile.objects.filter(
                version__application=self,
                version__status=AppVersion.Status.PUBLISHED,
                quarantine_status=AppReleaseFile.QuarantineStatus.APPROVED,
            )
            .exclude(file='')
            .order_by('platform')
            .values_list('platform', flat=True)
        )
        return list(dict.fromkeys(platforms))


class AppScreenshot(BaseModel):
    application = models.ForeignKey(
        SoftwareApp,
        on_delete=models.CASCADE,
        related_name='screenshots',
    )
    image = models.ImageField(upload_to='appstore/screenshots/')
    caption = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Capture d’écran'
        verbose_name_plural = 'Captures d’écran'

    def __str__(self):
        return f'{self.application.name} — capture {self.pk}'


class AppVersion(BaseModel):
    class Channel(models.TextChoices):
        STABLE = 'stable', 'Stable'
        BETA = 'beta', 'Bêta'
        OTHER = 'other', 'Autre'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Brouillon'
        QUARANTINE = 'quarantine', 'Quarantaine'
        PUBLISHED = 'published', 'Publiée'
        WITHDRAWN = 'withdrawn', 'Retirée'

    application = models.ForeignKey(
        SoftwareApp,
        on_delete=models.CASCADE,
        related_name='versions',
    )
    version_number = models.CharField(max_length=64)
    channel = models.CharField(
        max_length=16,
        choices=Channel.choices,
        default=Channel.STABLE,
    )
    release_notes = models.TextField(blank=True)
    known_issues = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    min_os_version = models.CharField(max_length=120, blank=True)
    compatibility_notes = models.TextField(blank=True)
    beta_testers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='appstore_beta_versions',
    )

    class Meta:
        ordering = ['-published_at', '-created_at']
        unique_together = [('application', 'version_number')]
        verbose_name = 'Version'
        verbose_name_plural = 'Versions'

    def __str__(self):
        return f'{self.application.name} {self.version_number}'

    def mark_published(self, when=None):
        self.status = self.Status.PUBLISHED
        self.published_at = when or timezone.now()
        self.save(update_fields=['status', 'published_at', 'updated_at'])

    def mark_withdrawn(self):
        self.status = self.Status.WITHDRAWN
        self.save(update_fields=['status', 'updated_at'])


class AppReleaseFile(BaseModel):
    class Platform(models.TextChoices):
        ANDROID = 'android', 'Android'
        WINDOWS = 'windows', 'Windows'
        LINUX = 'linux', 'Linux'
        MACOS = 'macos', 'macOS'
        WEB = 'web', 'Web'

    class Architecture(models.TextChoices):
        ANY = 'any', 'Indifférent'
        X86_64 = 'x86_64', 'x86_64'
        ARM64 = 'arm64', 'ARM64'
        ARMV7 = 'armv7', 'ARMv7'

    class QuarantineStatus(models.TextChoices):
        PENDING = 'pending', 'En quarantaine'
        APPROVED = 'approved', 'Approuvé'
        REJECTED = 'rejected', 'Rejeté'

    version = models.ForeignKey(
        AppVersion,
        on_delete=models.CASCADE,
        related_name='files',
    )
    platform = models.CharField(max_length=16, choices=Platform.choices)
    architecture = models.CharField(
        max_length=16,
        choices=Architecture.choices,
        default=Architecture.ANY,
    )
    file = models.FileField(
        storage=appstore_private_storage,
        upload_to=package_upload_to,
        blank=True,
    )
    original_name = models.CharField(max_length=255, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True)
    quarantine_status = models.CharField(
        max_length=16,
        choices=QuarantineStatus.choices,
        default=QuarantineStatus.PENDING,
    )
    install_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['platform', 'architecture', 'id']
        verbose_name = 'Fichier de distribution'
        verbose_name_plural = 'Fichiers de distribution'
        constraints = [
            models.UniqueConstraint(
                fields=['version', 'platform', 'architecture'],
                name='appstore_unique_version_platform_arch',
            ),
        ]

    def __str__(self):
        return f'{self.version} / {self.get_platform_display()} ({self.architecture})'

    @property
    def has_downloadable_blob(self):
        return bool(self.file) and bool(self.sha256) and self.size_bytes > 0

    def human_size(self):
        size = self.size_bytes or 0
        for unit in ('o', 'Ko', 'Mo', 'Go'):
            if size < 1024 or unit == 'Go':
                if unit == 'o':
                    return f'{size} {unit}'
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{self.size_bytes} o'


class AppAnnouncement(BaseModel):
    class Kind(models.TextChoices):
        NEW_APP = 'new_app', 'Nouvelle application'
        UPDATE = 'update', 'Mise à jour'
        BUGFIX = 'bugfix', 'Correction'
        MAINTENANCE = 'maintenance', 'Maintenance'
        COMPATIBILITY = 'compatibility', 'Compatibilité'
        INSTRUCTION = 'instruction', 'Instruction officielle'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Brouillon'
        PUBLISHED = 'published', 'Publiée'
        ARCHIVED = 'archived', 'Archivée'

    title = models.CharField(max_length=220)
    body = models.TextField()
    kind = models.CharField(max_length=24, choices=Kind.choices, default=Kind.UPDATE)
    image = models.ImageField(upload_to='appstore/announcements/', blank=True, null=True)
    application = models.ForeignKey(
        SoftwareApp,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='announcements',
    )
    version = models.ForeignKey(
        AppVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='announcements',
    )
    is_pinned = models.BooleanField(default=False)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-is_pinned', '-published_at', '-created_at']
        verbose_name = 'Annonce App Store'
        verbose_name_plural = 'Annonces App Store'

    def __str__(self):
        return self.title


class AppDownloadEvent(models.Model):
    """Événement créé uniquement lorsqu'un FileResponse de téléchargement démarre."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appstore_downloads',
    )
    application = models.ForeignKey(
        SoftwareApp,
        on_delete=models.CASCADE,
        related_name='download_events',
    )
    version = models.ForeignKey(
        AppVersion,
        on_delete=models.CASCADE,
        related_name='download_events',
    )
    release_file = models.ForeignKey(
        AppReleaseFile,
        on_delete=models.CASCADE,
        related_name='download_events',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']
        verbose_name = 'Téléchargement'
        verbose_name_plural = 'Téléchargements'
        indexes = [
            models.Index(fields=['completed_at']),
            models.Index(fields=['application', 'completed_at']),
        ]

    def __str__(self):
        return f'{self.application} {self.version.version_number} @ {self.completed_at}'
