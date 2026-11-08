from django.contrib import admin

from .models import (
    Enregistrement, LiveKitWebhookEvent, Presence, PresenceSession,
    ProcessusVerbaux, ReglePresence, Reunion, ReunionParticipant, ReunionVote,
    TranscriptSegment, Transcription,
)


@admin.register(Reunion)
class ReunionAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type', 'mode', 'date', 'status', 'organisateur')
    list_filter = ('type', 'mode', 'status')
    search_fields = ('titre', 'description', 'room_name')


@admin.register(ReunionParticipant)
class ReunionParticipantAdmin(admin.ModelAdmin):
    list_display = ('reunion', 'expert', 'role', 'peut_parler', 'exclu_jusqua')
    list_filter = ('role',)
    search_fields = ('expert__user__first_name', 'expert__user__last_name', 'reunion__titre')


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ('reunion', 'expert', 'status', 'marked_at', 'marked_by')
    list_filter = ('status',)
    search_fields = ('expert__user__first_name', 'expert__user__last_name', 'reunion__titre')


@admin.register(PresenceSession)
class PresenceSessionAdmin(admin.ModelAdmin):
    list_display = ('reunion', 'expert', 'joined_at', 'left_at', 'left_reason')
    list_filter = ('left_reason',)
    search_fields = ('expert__user__first_name', 'expert__user__last_name', 'reunion__titre')


@admin.register(ProcessusVerbaux)
class ProcessusVerbauxAdmin(admin.ModelAdmin):
    list_display = ('reunion', 'titre', 'redaction', 'quorum_atteint', 'generated_at')
    list_filter = ('redaction', 'quorum_atteint')
    search_fields = ('titre', 'contenu', 'reunion__titre')


@admin.register(ReglePresence)
class ReglePresenceAdmin(admin.ModelAdmin):
    list_display = ('type_reunion', 'seuil_presence_pct', 'tolerance_coupure_s', 'montant_jeton')


@admin.register(Enregistrement)
class EnregistrementAdmin(admin.ModelAdmin):
    list_display = ('reunion', 'expert', 'egress_id', 'statut', 'debut', 'duree_secondes')
    list_filter = ('statut',)


@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ('reunion', 'statut', 'langue', 'modele', 'termine_le')
    list_filter = ('statut', 'langue')


@admin.register(TranscriptSegment)
class TranscriptSegmentAdmin(admin.ModelAdmin):
    list_display = ('transcription', 'expert', 'debut_s', 'fin_s', 'texte')
    search_fields = ('texte',)


@admin.register(LiveKitWebhookEvent)
class LiveKitWebhookEventAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'event_type', 'room_name', 'traite_le')
    list_filter = ('event_type',)
    search_fields = ('event_id', 'room_name')
