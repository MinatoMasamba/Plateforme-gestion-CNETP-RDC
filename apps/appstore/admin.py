from django.contrib import admin
from django import forms
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from .services import compute_sha256, sanitize_upload_name

from .models import (
    AppAnnouncement,
    AppCategory,
    AppDownloadEvent,
    AppReleaseFile,
    AppScreenshot,
    AppVersion,
    SoftwareApp,
)


class ReleaseAdminForm(forms.ModelForm):
    class Meta:
        model = AppReleaseFile
        fields = '__all__'

    def clean_file(self):
        upload = self.cleaned_data.get('file')
        if upload and 'file' in self.changed_data:
            upload.name = sanitize_upload_name(upload.name)
            digest, size = compute_sha256(upload)
            self.instance.sha256 = digest
            self.instance.size_bytes = size
            self.instance.original_name = upload.name
        return upload


class AppScreenshotInline(admin.TabularInline):
    model = AppScreenshot
    extra = 0


class DownloadCountersMixin:
    """Statistiques historiques des transferts démarrés, pas des installations."""

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _download_count=Count('download_events', distinct=True),
            _downloader_count=Count('download_events__user', distinct=True),
        )

    @admin.display(description='Téléchargements démarrés', ordering='_download_count')
    def download_count(self, obj):
        if not obj.pk:
            return 0
        count = getattr(obj, '_download_count', None)
        return count if count is not None else obj.download_events.count()

    @admin.display(description='Comptes distincts', ordering='_downloader_count')
    def downloader_count(self, obj):
        if not obj.pk:
            return 0
        count = getattr(obj, '_downloader_count', None)
        return count if count is not None else obj.download_events.exclude(user=None).values('user').distinct().count()


class AppReleaseFileInline(DownloadCountersMixin, admin.TabularInline):
    model = AppReleaseFile
    form = ReleaseAdminForm
    extra = 0
    readonly_fields = ('size_bytes', 'sha256', 'original_name', 'download_count', 'downloader_count')


class AppVersionInline(admin.TabularInline):
    model = AppVersion
    extra = 0
    fields = ('version_number', 'channel', 'status', 'published_at')
    show_change_link = True


@admin.register(AppCategory)
class AppCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')


@admin.register(SoftwareApp)
class SoftwareAppAdmin(DownloadCountersMixin, admin.ModelAdmin):
    list_display = ('name', 'category', 'is_featured', 'is_published', 'publisher', 'download_count', 'downloader_count')
    readonly_fields = ('download_count', 'downloader_count')
    list_filter = ('is_published', 'is_featured', 'category')
    search_fields = ('name', 'slug', 'publisher')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [AppScreenshotInline, AppVersionInline]
    raw_id_fields = ('recommended_version',)


@admin.register(AppVersion)
class AppVersionAdmin(DownloadCountersMixin, admin.ModelAdmin):
    list_display = ('application', 'version_number', 'channel', 'status', 'published_at', 'download_count', 'downloader_count')
    readonly_fields = ('download_count', 'downloader_count')
    list_filter = ('channel', 'status')
    search_fields = ('version_number', 'application__name')
    inlines = [AppReleaseFileInline]
    filter_horizontal = ('beta_testers',)


@admin.register(AppReleaseFile)
class AppReleaseFileAdmin(DownloadCountersMixin, admin.ModelAdmin):
    form = ReleaseAdminForm
    list_display = (
        'version', 'platform', 'architecture', 'quarantine_status',
        'size_bytes', 'sha256', 'download_link', 'download_count', 'downloader_count',
    )
    list_filter = ('platform', 'quarantine_status')
    readonly_fields = ('size_bytes', 'sha256', 'original_name', 'download_link', 'download_count', 'downloader_count')

    @admin.display(description='Lien direct à envoyer')
    def download_link(self, obj):
        if not obj.pk or not obj.has_downloadable_blob:
            return 'Disponible après ajout du fichier.'
        url = reverse('web:appstore_download', args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, url)


@admin.register(AppAnnouncement)
class AppAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'status', 'is_pinned', 'published_at')
    list_filter = ('kind', 'status', 'is_pinned')
    search_fields = ('title', 'body')


@admin.register(AppDownloadEvent)
class AppDownloadEventAdmin(admin.ModelAdmin):
    list_display = ('application', 'version', 'user', 'completed_at')
    list_filter = ('application',)
    readonly_fields = (
        'user', 'application', 'version', 'release_file',
        'ip_address', 'user_agent', 'completed_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
