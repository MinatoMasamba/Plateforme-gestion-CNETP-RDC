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
            'fields': ('numero', 'numero_label', 'date_communique', 'objet', 'statut'),
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
