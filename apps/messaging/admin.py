from django.contrib import admin

from .models import CommuniqueEnvoi, CommuniqueOfficiel, CommuniqueSequence


@admin.register(CommuniqueOfficiel)
class CommuniqueOfficielAdmin(admin.ModelAdmin):
    list_display = ('numero_label', 'date_communique', 'objet', 'statut', 'created_at')
    list_filter = ('statut', 'date_communique')
    search_fields = ('objet', 'notes')
    readonly_fields = ('numero', 'numero_label', 'created_at', 'updated_at')
    fieldsets = (
        ("Communiqué", {
            'fields': ('numero', 'numero_label', 'date_communique', 'objet', 'fichier_pdf', 'statut'),
        }),
        ("Notes", {'fields': ('notes',)}),
        ("Traçabilité", {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(CommuniqueEnvoi)
class CommuniqueEnvoiAdmin(admin.ModelAdmin):
    list_display = ('communique_key', 'email', 'recipient', 'status', 'sent_at', 'created_at')
    list_filter = ('status', 'communique_key', 'created_at')
    search_fields = ('email', 'recipient__username', 'recipient__first_name', 'recipient__last_name', 'subject')
    readonly_fields = ('communique_key', 'subject', 'recipient', 'email', 'status', 'error', 'sent_at', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False


@admin.register(CommuniqueSequence)
class CommuniqueSequenceAdmin(admin.ModelAdmin):
    list_display = ('last_number',)


from django.urls import reverse  # noqa: E402
from django.utils.html import format_html  # noqa: E402
from .dispatch_models import InstitutionalDispatch, DispatchRecipient, DispatchEmailAttempt  # noqa: E402


class DispatchReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InstitutionalDispatch)
class InstitutionalDispatchAdmin(DispatchReadOnlyAdmin):
    list_display = ('created_at', 'subject', 'sender_name', 'target_code')
    list_filter = ('created_at', 'target_sc', 'target_gt')
    search_fields = ('subject', 'body', 'sender_name', 'target_code')
    exclude = ('attachment',)
    readonly_fields = tuple(f.name for f in InstitutionalDispatch._meta.fields if f.name != 'attachment') + ('document_download',)

    @admin.display(description='Document archivé')
    def document_download(self, obj):
        if not obj.attachment:
            return 'Aucun document'
        return format_html('<a href="{}">{}</a>', reverse('institutional-dispatch-attachment', args=[obj.pk]), obj.original_filename)


@admin.register(DispatchRecipient)
class DispatchRecipientAdmin(DispatchReadOnlyAdmin):
    list_display = ('dispatch', 'recipient_name', 'received_at', 'read_at', 'email_status', 'email_attempts')
    readonly_fields = tuple(f.name for f in DispatchRecipient._meta.fields)


@admin.register(DispatchEmailAttempt)
class DispatchEmailAttemptAdmin(DispatchReadOnlyAdmin):
    list_display = ('recipient', 'number', 'started_at', 'outcome', 'finished_at')
    readonly_fields = tuple(f.name for f in DispatchEmailAttempt._meta.fields)
