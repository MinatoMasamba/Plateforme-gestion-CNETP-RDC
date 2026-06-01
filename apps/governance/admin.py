from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import CTM, WG, Affectation, ComitePilotage, PilotageMembreship, TechnicalCell, CTCMembership, OriginStructure, ExecutiveLevel


class WGInline(admin.TabularInline):
    model = WG
    extra = 0
    fields = ('name', 'number', 'president', 'rapporteur', 'secretary')


@admin.register(CTM)
class CTMAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'scientific_president', 'rapporteur', 'get_member_count')
    search_fields = ('name', 'iso_reference', 'number')
    ordering = ('number',)
    readonly_fields = ('get_member_count', 'get_members_list')
    
    fieldsets = (
        ('Informations générales', {
            'fields': (
                'number',
                'name',
                'description',
                'iso_reference',
                'arso_reference',
            )
        }),
        ('Leadership', {
            'fields': (
                'scientific_president',
                'rapporteur',
                'secretary',
            )
        }),
        ('Statistiques', {
            'fields': (
                'get_member_count',
                'get_members_list',
            )
        }),
    )
    
    inlines = [WGInline]
    
    def get_members_list(self, obj):
        """Afficher la liste des experts"""
        affectations = Affectation.objects.filter(ctm=obj, is_primary_ctm=True).select_related('expert')
        if not affectations:
            return format_html("<em>Aucun expert assigné</em>")
        
        members = []
        for aff in affectations[:10]:  # Limiter à 10 pour l'affichage
            members.append(f"• {aff.expert.full_name}")
        
        if affectations.count() > 10:
            members.append(f"... et {affectations.count() - 10} autres")
        
        return mark_safe("<br/>".join(members))
    get_members_list.short_description = "Experts (aperçu)"


@admin.register(WG)
class WGAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'ctm', 'president', 'rapporteur')
    search_fields = ('name', 'ctm__name', 'number')
    list_filter = ('ctm',)
    autocomplete_fields = ('ctm', 'president', 'rapporteur', 'secretary')


@admin.register(Affectation)
class AffectationAdmin(admin.ModelAdmin):
    list_display = ('expert', 'ctm', 'wg', 'is_primary_ctm', 'is_primary_wg')
    search_fields = ('expert__full_name', 'ctm__name', 'wg__name')
    list_filter = ('ctm', 'wg', 'is_primary_ctm')
    autocomplete_fields = ('expert', 'ctm', 'wg')


class PilotageMembreshipInline(admin.TabularInline):
    model = PilotageMembreship
    extra = 0
    autocomplete_fields = ('expert',)


@admin.register(ComitePilotage)
class ComitePilotageAdmin(admin.ModelAdmin):
    list_display = ('name', 'president', 'vice_president', 'secretary', 'get_member_count')
    search_fields = ('name',)
    readonly_fields = ('get_member_count', 'get_members_list', 'get_role_distribution')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name',)
        }),
        ('Leadership', {
            'fields': (
                'president',
                'vice_president',
                'secretary',
                'rapporteur',
            )
        }),
        ('Statistiques', {
            'fields': (
                'get_member_count',
                'get_role_distribution',
                'get_members_list',
            )
        }),
    )
    
    inlines = [PilotageMembreshipInline]
    autocomplete_fields = ('president', 'vice_president', 'secretary', 'rapporteur')
    
    def get_member_count(self, obj):
        return obj.members.count()
    get_member_count.short_description = "Nombre de membres"
    
    def get_role_distribution(self, obj):
        """Distribution des rôles"""
        roles = PilotageMembreship.objects.filter(comite=obj).values('role').annotate(
            count=Count('id')
        )
        
        distribution = []
        for role_dict in roles:
            role = role_dict['role']
            count = role_dict['count']
            role_display = dict(PilotageMembreship._meta.get_field('role').choices).get(role, role)
            distribution.append(f"• {role_display}: {count}")
        
        if not distribution:
            return "—"
        return mark_safe("<br/>".join(distribution))
    get_role_distribution.short_description = "Distribution des rôles"
    
    def get_members_list(self, obj):
        """Afficher la liste des membres"""
        memberships = PilotageMembreship.objects.filter(comite=obj).select_related('expert')
        if not memberships:
            return format_html("<em>Aucun membre</em>")
        
        members = []
        for membership in memberships[:15]:  # Limiter à 15
            role_display = dict(PilotageMembreship._meta.get_field('role').choices).get(membership.role, membership.role)
            members.append(f"• {membership.expert.full_name} ({role_display})")
        
        if memberships.count() > 15:
            members.append(f"... et {memberships.count() - 15} autres")
        
        return mark_safe("<br/>".join(members))
    get_members_list.short_description = "Membres (aperçu)"


@admin.register(PilotageMembreship)
class PilotageMembershipsAdmin(admin.ModelAdmin):
    list_display = ('expert', 'comite', 'get_role_display', 'expert_structure')
    search_fields = ('expert__full_name', 'expert__user__email')
    list_filter = ('role', 'comite')
    autocomplete_fields = ('expert', 'comite')
    
    def expert_structure(self, obj):
        return obj.expert.structure.name if obj.expert.structure else "—"
    expert_structure.short_description = "Structure"


class CTCMembershipInline(admin.TabularInline):
    model = CTCMembership
    extra = 0
    autocomplete_fields = ('expert',)


@admin.register(TechnicalCell)
class TechnicalCellAdmin(admin.ModelAdmin):
    list_display = ('name', 'coordinator', 'vice_coordinator', 'get_member_count')
    search_fields = ('name',)
    readonly_fields = ('get_member_count', 'get_role_distribution', 'get_members_list')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name',)
        }),
        ('Leadership', {
            'fields': (
                'coordinator',
                'vice_coordinator',
            )
        }),
        ('Statistiques', {
            'fields': (
                'get_member_count',
                'get_role_distribution',
                'get_members_list',
            )
        }),
    )
    
    inlines = [CTCMembershipInline]
    autocomplete_fields = ('coordinator', 'vice_coordinator')
    
    def get_member_count(self, obj):
        return obj.members.count()
    get_member_count.short_description = "Nombre de membres"
    
    def get_role_distribution(self, obj):
        """Distribution des rôles"""
        roles = CTCMembership.objects.filter(ctc=obj).values('role').annotate(
            count=Count('id')
        )
        
        distribution = []
        for role_dict in roles:
            role = role_dict['role']
            count = role_dict['count']
            role_display = dict(CTCMembership._meta.get_field('role').choices).get(role, role)
            distribution.append(f"• {role_display}: {count}")
        
        if not distribution:
            return "—"
        return mark_safe("<br/>".join(distribution))
    get_role_distribution.short_description = "Distribution des rôles"
    
    def get_members_list(self, obj):
        """Afficher la liste des membres"""
        memberships = CTCMembership.objects.filter(ctc=obj).select_related('expert')
        if not memberships:
            return format_html("<em>Aucun membre</em>")
        
        members = []
        for membership in memberships[:15]:  # Limiter à 15
            role_display = dict(CTCMembership._meta.get_field('role').choices).get(membership.role, membership.role)
            members.append(f"• {membership.expert.full_name} ({role_display})")
        
        if memberships.count() > 15:
            members.append(f"... et {memberships.count() - 15} autres")
        
        return mark_safe("<br/>".join(members))
    get_members_list.short_description = "Membres (aperçu)"


@admin.register(CTCMembership)
class CTCMembershipAdmin(admin.ModelAdmin):
    list_display = ('expert', 'ctc', 'get_role_display', 'expert_structure')
    search_fields = ('expert__full_name', 'expert__user__email')
    list_filter = ('role', 'ctc')
    autocomplete_fields = ('expert', 'ctc')
    
    def expert_structure(self, obj):
        return obj.expert.structure.name if obj.expert.structure else "—"
    expert_structure.short_description = "Structure"


@admin.register(OriginStructure)
class OriginStructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'giron', 'expected_expert_count', 'get_expert_count')
    search_fields = ('name', 'code')
    list_filter = ('giron',)
    readonly_fields = ('get_expert_count',)


@admin.register(ExecutiveLevel)
class ExecutiveLevelAdmin(admin.ModelAdmin):
    list_display = ('get_position_display', 'expert', 'expert_structure')
    search_fields = ('expert__full_name',)
    list_filter = ('position',)
    autocomplete_fields = ('expert',)
    
    def expert_structure(self, obj):
        return obj.expert.structure.name if obj.expert and obj.expert.structure else "Vacant"
    expert_structure.short_description = "Structure"
