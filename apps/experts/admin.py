from django.contrib import admin
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
    readonly_fields = ('inscription_date', 'activation_date')

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
