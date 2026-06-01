from django.contrib import admin
from .models import CTM, WG, Affectation, ComitePilotage, PilotageMembreship, TechnicalCell, CTCMembership, OriginStructure, ExecutiveLevel

@admin.register(CTM)
class CTMAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'scientific_president', 'rapporteur')
    search_fields = ('name', 'iso_reference', 'number')
    ordering = ('number',)

@admin.register(WG)
class WGAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'ctm', 'president')
    search_fields = ('name', 'ctm__name', 'number')
    list_filter = ('ctm',)

@admin.register(Affectation)
class AffectationAdmin(admin.ModelAdmin):
    list_display = ('expert', 'ctm', 'wg')
    search_fields = ('expert__full_name', 'ctm__name', 'wg__name')
    list_filter = ('ctm', 'wg')

@admin.register(ComitePilotage)
class ComitePilotageAdmin(admin.ModelAdmin):
    list_display = ('name', 'president', 'vice_president', 'secretary')

@admin.register(PilotageMembreship)
class PilotageMembershipsAdmin(admin.ModelAdmin):
    list_display = ('expert', 'role')
    search_fields = ('expert__full_name',)
    list_filter = ('role',)

@admin.register(TechnicalCell)
class TechnicalCellAdmin(admin.ModelAdmin):
    list_display = ('name', 'coordinator', 'vice_coordinator')

@admin.register(CTCMembership)
class CTCMembershipAdmin(admin.ModelAdmin):
    list_display = ('expert', 'role')
    search_fields = ('expert__full_name',)
    list_filter = ('role',)

@admin.register(OriginStructure)
class OriginStructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'giron', 'expected_expert_count', 'get_expert_count')
    search_fields = ('name', 'code')
    list_filter = ('giron',)
    readonly_fields = ('get_expert_count',)

@admin.register(ExecutiveLevel)
class ExecutiveLevelAdmin(admin.ModelAdmin):
    list_display = ('get_position_display', 'expert')
    search_fields = ('expert__full_name',)
    list_filter = ('position',)
