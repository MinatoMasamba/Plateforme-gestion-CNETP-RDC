from django.contrib import admin
from .models import Draft


@admin.register(Draft)
class DraftAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'ctm', 'wg', 'type', 'status', 'content_format',
        'created_label', 'published_at',
    )
    list_filter = ('status', 'type', 'ctm', 'created_at')
    search_fields = ('title', 'ctm', 'wg', 'type', 'domain', 'draft_text')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'created_label')
    fieldsets = (
        ("Identification", {
            'fields': ('title', 'ctm', 'wg', 'type', 'domain', 'status', 'published_at'),
        }),
        ("Contenu", {
            'fields': ('draft_text', 'file'),
            'description': "Renseigner le texte Markdown et/ou joindre le fichier du communiqué.",
        }),
        ("Traçabilité IA", {
            'fields': ('classification_reason', 'input_json', 'created_at', 'updated_at', 'created_label'),
        }),
    )

    @admin.display(description="Format")
    def content_format(self, obj):
        return "Fichier" if obj.is_file_based else "Markdown"
