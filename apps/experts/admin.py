from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Expert, Structure
from apps.governance.models import Affectation, PilotageMembreship, CTCMembership, ExecutiveLevel


class AffectationInline(admin.TabularInline):
    model = Affectation
    extra = 1
    autocomplete_fields = ('ctm', 'wg')


class PilotageMembreshipInline(admin.TabularInline):
    model = PilotageMembreship
    extra = 0


class CTCMembershipInline(admin.TabularInline):
    model = CTCMembership
    extra = 0


class ExecutiveLevelInline(admin.TabularInline):
    model = ExecutiveLevel
    extra = 0
    max_num = 1


@admin.register(Structure)
class StructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'acronym', 'category', 'email', 'phone', 'get_expert_count')
    search_fields = ('name', 'acronym', 'description', 'contact_person', 'email')
    list_filter = ('category',)
    ordering = ('category', 'name')
    readonly_fields = ('get_expert_count',)

    def get_expert_count(self, obj):
        return obj.get_expert_count()
    get_expert_count.short_description = 'Nombre d’experts'


@admin.register(Expert)
class ExpertAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'user',
        'structure',
        'status',
        'get_committees',
        'appointment_date',
        'presence_count',
    )
    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__email',
        'structure__name',
        'structure__acronym',
        'specialties',
        'appointment_decree_number',
    )
    list_filter = ('status', 'structure', 'appointment_date')
    autocomplete_fields = ('user', 'structure', 'ctm')
    ordering = ('user__last_name', 'user__first_name')
    readonly_fields = ('inscription_date', 'activation_date', 'get_committees_detail')

    fieldsets = (
        ('Informations générales', {
            'fields': (
                'user',
                'structure',
                'ctm',
                'status',
                'appointment_decree_number',
                'appointment_date',
            )
        }),
        ('Compétences et documents', {
            'fields': (
                'specialties',
                'cv',
            )
        }),
        ('Affectations aux comités', {
            'fields': (
                'get_committees_detail',
            ),
            'classes': ('collapse',)
        }),
        ('Informations bancaires', {
            'fields': (
                'bank_account',
                'bank_name',
                'mobile_money_number',
            )
        }),
        ('Activité et suivi', {
            'fields': (
                'daily_rate',
                'monthly_research_allowance',
                'presence_count',
                'inscription_date',
                'activation_date',
            )
        }),
    )

    inlines = [
        AffectationInline,
        PilotageMembreshipInline,
        CTCMembershipInline,
        ExecutiveLevelInline,
    ]

    actions = ('make_active', 'make_inactive',)

    def make_active(self, request, queryset):
        queryset.update(status='ACTIVE')
    make_active.short_description = 'Marquer les experts sélectionnés comme actifs'

    def make_inactive(self, request, queryset):
        queryset.update(status='INACTIVE')
    make_inactive.short_description = 'Marquer les experts sélectionnés comme inactifs'
    
    def get_committees(self, obj):
        """Afficher les comités dans la liste"""
        committees = []
        
        if obj.ctm:
            committees.append(f"CTM {obj.ctm.number}")
        
        pilotage_m = PilotageMembreship.objects.filter(expert=obj).first()
        if pilotage_m:
            committees.append(f"Pilotage ({pilotage_m.role})")
        
        ctc_membership = CTCMembership.objects.filter(expert=obj).first()
        if ctc_membership:
            committees.append(f"CTC ({ctc_membership.role})")
        
        return ", ".join(committees) if committees else "—"
    get_committees.short_description = "Comités"
    
    def get_committees_detail(self, obj):
        """Afficher les détails des comités"""
        details = []
        
        if obj.ctm:
            details.append(f"<strong>CTM Principale:</strong> CTM {obj.ctm.number} - {obj.ctm.name}")
        
        pilotage_memberships = PilotageMembreship.objects.filter(expert=obj).select_related('comite')
        for pilotage_m in pilotage_memberships:
            details.append(f"<strong>Comité de Pilotage:</strong> {pilotage_m.role}")
        
        ctc_memberships = CTCMembership.objects.filter(expert=obj).select_related('ctc')
        for ctc_m in ctc_memberships:
            details.append(f"<strong>Cellule Technique:</strong> {ctc_m.role}")
        
        if not details:
            return mark_safe("<em>Aucun comité assigné</em>")
        return mark_safe("<br/>".join(details))
    get_committees_detail.short_description = "Affectations aux comités"
