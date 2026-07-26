from django.contrib import admin

from .models import PublicAmendement

# Register your models here.


@admin.register(PublicAmendement)
class PublicAmendementAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'norme', 'status', 'proposed_by_name', 'proposed_by_province', 'created_at')
    list_filter = ('status', 'norme')
    search_fields = ('title', 'description', 'proposed_by_name', 'proposed_by_email', 'proposed_by_province')
    readonly_fields = ('created_at', 'updated_at')
