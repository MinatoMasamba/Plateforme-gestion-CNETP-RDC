from django.contrib import admin

from .models import CommuniqueEnvoi


@admin.register(CommuniqueEnvoi)
class CommuniqueEnvoiAdmin(admin.ModelAdmin):
    list_display = ('communique_key', 'email', 'recipient', 'status', 'sent_at', 'created_at')
    list_filter = ('status', 'communique_key', 'created_at')
    search_fields = ('email', 'recipient__username', 'recipient__first_name', 'recipient__last_name', 'subject')
    readonly_fields = ('communique_key', 'subject', 'recipient', 'email', 'status', 'error', 'sent_at', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False
