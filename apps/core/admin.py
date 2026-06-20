from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import User, AuditLog
from apps.experts.models import Expert
from apps.governance.models import PilotageMembreship, CTCMembership


class ExpertInline(admin.StackedInline):
    model = Expert
    can_delete = False
    verbose_name_plural = 'Profil Expert'
    fk_name = 'user'
    fieldsets = (
        (None, {
            'fields': (
                'structure',
                'status',
                'appointment_decree_number',
                'appointment_date',
                'specialties',
                'cv',
                'ctm',
                'get_committee_info',
            )
        }),
        ('Informations bancaires', {
            'fields': (
                'bank_account',
                'bank_name',
                'mobile_money_number',
            ),
            'classes': ('collapse',)
        }),
        ('Activité', {
            'fields': (
                'daily_rate',
                'monthly_research_allowance',
                'presence_count',
            ),
            'classes': ('collapse',)
        }),
    )
    autocomplete_fields = ('structure', 'ctm')
    readonly_fields = ('get_committee_info',)
    
    def get_committee_info(self, obj):
        """Afficher les informations des comités"""
        if not obj.pk:
            return "L'expert doit être sauvegardé d'abord"
        
        committees = []
        
        # CTM
        if obj.ctm:
            committees.append(f"<strong>CTM:</strong> CTM {obj.ctm.number} - {obj.ctm.name}")
        
        # Comité de Pilotage
        pilotages = PilotageMembreship.objects.filter(expert=obj)
        for pilotage in pilotages:
            committees.append(f"<strong>Comité de Pilotage:</strong> {pilotage.get_role_display()}")
        
        # Cellule Technique
        ctcs = CTCMembership.objects.filter(expert=obj)
        for ctc in ctcs:
            committees.append(f"<strong>Cellule Technique:</strong> {ctc.get_role_display()}")
        
        if not committees:
            return mark_safe("<em>Aucun comité assigné</em>")
        
        return mark_safe("<br/>".join(committees))
    get_committee_info.short_description = "Affectations aux comités"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations CNETP', {'fields': ('phone', 'province', 'bio', 'profile_picture')}),
        ('Permissions CNETP', {'fields': ('is_expert', 'is_ctc_staff', 'is_minister')}),
    )
    list_display = ('username', 'get_full_name', 'email', 'phone', 'province', 'is_expert', 'is_ctc_staff', 'is_minister', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_expert', 'is_ctc_staff', 'is_minister', 'created_at')
    inlines = [ExpertInline]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'content_type', 'user', 'ip_address')
    list_filter = ('action', 'content_type', 'timestamp')
    search_fields = ('user__username', 'object_repr', 'ip_address')
    readonly_fields = ('timestamp', 'user', 'changes', 'ip_address', 'user_agent')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
