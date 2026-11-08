from django.contrib import admin

from .models import (
    AppAnnouncement,
    AppCategory,
    AppDownloadEvent,
    AppReleaseFile,
    AppScreenshot,
    AppVersion,
    SoftwareApp,
)


class AppScreenshotInline(admin.TabularInline):
    model = AppScreenshot
    extra = 0


class AppReleaseFileInline(admin.TabularInline):
    model = AppReleaseFile
    extra = 0
    readonly_fields = ('size_bytes', 'sha256', 'original_name')


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
class SoftwareAppAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_featured', 'is_published', 'publisher')
    list_filter = ('is_published', 'is_featured', 'category')
    search_fields = ('name', 'slug', 'publisher')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [AppScreenshotInline, AppVersionInline]
    raw_id_fields = ('recommended_version',)


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ('application', 'version_number', 'channel', 'status', 'published_at')
    list_filter = ('channel', 'status')
    search_fields = ('version_number', 'application__name')
    inlines = [AppReleaseFileInline]
    filter_horizontal = ('beta_testers',)


@admin.register(AppReleaseFile)
class AppReleaseFileAdmin(admin.ModelAdmin):
    list_display = (
        'version', 'platform', 'architecture', 'quarantine_status',
        'size_bytes', 'sha256',
    )
    list_filter = ('platform', 'quarantine_status')
    readonly_fields = ('size_bytes', 'sha256', 'original_name')


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
