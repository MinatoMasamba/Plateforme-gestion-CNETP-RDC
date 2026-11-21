from django.contrib import admin
from .models import ClientDiagnostic


@admin.register(ClientDiagnostic)
class ClientDiagnosticAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'category', 'app_version', 'platform', 'journal_written')
    list_filter = ('category', 'platform', 'app_version', 'journal_written')
    search_fields = ('event_id', 'message')
    readonly_fields = ('id', 'event_id', 'created_at', 'user', 'category', 'app_version', 'platform', 'message', 'details', 'journal_written')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
