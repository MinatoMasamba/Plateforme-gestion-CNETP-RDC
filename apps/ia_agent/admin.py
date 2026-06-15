from django.contrib import admin

from .models import AgentArtifact, AgentMessage, AgentSession


class AgentMessageInline(admin.TabularInline):
    model = AgentMessage
    extra = 0
    readonly_fields = ['role', 'content', 'tool_name', 'tool_input', 'tool_output', 'created_at']
    can_delete = False


@admin.register(AgentSession)
class AgentSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'scope', 'title', 'is_active', 'created_at', 'updated_at']
    list_filter = ['scope', 'is_active']
    search_fields = ['user__username', 'user__email', 'title']
    inlines = [AgentMessageInline]


@admin.register(AgentArtifact)
class AgentArtifactAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'artifact_type', 'title', 'status', 'created_at']
    list_filter = ['artifact_type', 'status']
    search_fields = ['title']
