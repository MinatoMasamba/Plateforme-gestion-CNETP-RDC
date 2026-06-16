from django.contrib import admin

from .models import AgentArtifact, AgentMessage, AgentPosteContext, AgentScopeConfig, AgentSession


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


@admin.register(AgentScopeConfig)
class AgentScopeConfigAdmin(admin.ModelAdmin):
    list_display = ['label', 'scope', 'role_key', 'is_active', 'has_tool_restriction', 'updated_at']
    list_filter = ['scope', 'is_active']
    search_fields = ['label', 'role_key']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        (None, {'fields': ['scope', 'role_key', 'label', 'is_active']}),
        ('Prompt supplémentaire', {
            'fields': ['system_prompt_extra'],
            'description': 'Ce texte est ajouté au prompt de base pour personnaliser le comportement de l\'IA selon le rôle.',
        }),
        ('Restriction des outils', {
            'fields': ['allowed_tools'],
            'description': (
                'Liste JSON des outils autorisés. null = tous les outils du scope. '
                'Ex : ["get_chart_data", "list_ctm_norms"]'
            ),
        }),
        ('Métadonnées', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
    ]

    @admin.display(boolean=True, description='Outils restreints')
    def has_tool_restriction(self, obj):
        return obj.allowed_tools is not None


@admin.register(AgentPosteContext)
class AgentPosteContextAdmin(admin.ModelAdmin):
    list_display = [
        'organ', 'hierarchy_level', 'sub_role',
        'position_label_short', 'is_active',
        'has_pilotage_link', 'has_ctc_link', 'updated_at',
    ]
    list_filter = ['organ', 'hierarchy_level', 'is_active']
    search_fields = ['sub_role', 'position_label', 'mission_summary']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at', 'holder_name', 'holder_structure']
    ordering = ['organ', 'hierarchy_level', 'sub_role']

    fieldsets = [
        ('Identification', {
            'fields': ['organ', 'sub_role', 'hierarchy_level', 'is_active'],
        }),
        ('Contenu du prompt IA', {
            'fields': ['position_label', 'mission_summary', 'tools_hint'],
            'description': (
                'Ces champs sont injectés directement dans le prompt système de l\'IA '
                'lorsqu\'un utilisateur ayant ce sous-rôle ouvre une session.'
            ),
        }),
        ('Liens relationnels (optionnels)', {
            'fields': ['poste_pilotage', 'poste_ctc', 'holder_name', 'holder_structure'],
            'description': (
                'Lier au PosteNominatif correspondant pour enrichir le contexte '
                'avec les données du titulaire (nom, structure, quota line).'
            ),
            'classes': ['collapse'],
        }),
        ('Métadonnées', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]

    @admin.display(description='Intitulé (aperçu)')
    def position_label_short(self, obj):
        return obj.position_label[:70] + '…' if len(obj.position_label) > 70 else obj.position_label

    @admin.display(boolean=True, description='Lien Pilotage')
    def has_pilotage_link(self, obj):
        return obj.poste_pilotage_id is not None

    @admin.display(boolean=True, description='Lien CTC')
    def has_ctc_link(self, obj):
        return obj.poste_ctc_id is not None
