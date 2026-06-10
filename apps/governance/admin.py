from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import CTM, WG, Affectation, ComitePilotage, PilotageMembreship, PosteNominatif, TechnicalCell, CTCMembership, PosteNominatifCTC, OriginStructure, ExecutiveLevel, CTCProcessus, NormeCadrage

# Ensure ComitePilotage objects expose a 'role' attribute to avoid errors
# when other admin modules assume a membership-like object is returned.
# This provides a safe default display.
if not hasattr(ComitePilotage, 'role'):
    setattr(ComitePilotage, 'role', property(lambda self: '—'))


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
    
    def get_member_count(self, obj):
        """Nombre de membres (override pour éviter d'appeler la méthode modèle incorrecte)"""
        return obj.affectations.filter(is_primary_ctm=True).values('expert').distinct().count()
    get_member_count.short_description = "Nombre de membres"
    
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


class PosteNominatifInline(admin.TabularInline):
    model = PosteNominatif
    extra = 0
    fields = ('order', 'role', 'title', 'required_structure', 'quota_line', 'holder')
    autocomplete_fields = ('required_structure', 'holder')
    show_change_link = True


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

    inlines = [PosteNominatifInline, PilotageMembreshipInline]
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


@admin.register(PosteNominatif)
class PosteNominatifAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_role_display', 'required_structure', 'quota_line', 'holder', 'get_statut')
    list_filter = ('role', 'comite', 'required_structure')
    search_fields = ('title', 'required_structure__name', 'holder__full_name')
    autocomplete_fields = ('comite', 'required_structure', 'holder')
    ordering = ('comite', 'order')

    def get_statut(self, obj):
        if obj.holder:
            return format_html('<span style="color: green;">✓ Pourvu</span>')
        return format_html('<span style="color: orange;">⏳ Vacant</span>')
    get_statut.short_description = "Statut"


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


class PosteNominatifCTCInline(admin.TabularInline):
    model = PosteNominatifCTC
    extra = 0
    fields = ('order', 'role', 'title', 'required_structure', 'quota_line', 'holder')
    autocomplete_fields = ('required_structure', 'holder')
    show_change_link = True


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
    
    inlines = [PosteNominatifCTCInline, CTCMembershipInline]
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


@admin.register(PosteNominatifCTC)
class PosteNominatifCTCAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_role_display', 'required_structure', 'quota_line', 'holder', 'get_statut')
    list_filter = ('role', 'ctc', 'required_structure')
    search_fields = ('title', 'required_structure__name', 'holder__full_name')
    autocomplete_fields = ('ctc', 'required_structure', 'holder')
    ordering = ('ctc', 'order')

    def get_statut(self, obj):
        if obj.holder:
            return format_html('<span style="color: green;">✓ Pourvu</span>')
        return format_html('<span style="color: orange;">⏳ Vacant</span>')
    get_statut.short_description = "Statut"


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


@admin.register(CTCProcessus)
class CTCProcessusAdmin(admin.ModelAdmin):
    list_display = ('norme', 'current_stage', 'received_by', 'received_at', 'all_reviews_completed', 'signed_out_at', 'pilotage_reception_complete')
    list_filter = ('current_stage', 'requires_sig', 'all_reviews_completed')
    search_fields = ('norme__reference_number', 'norme__title')
    raw_id_fields = ('received_by', 'intake_validated_by', 'sig_completed_by', 'signed_out_by', 'received_by_president', 'received_by_rapporteur')
    readonly_fields = ('all_reviews_completed', 'all_reviews_completed_at', 'transmitted_to_pilotage_at', 'pilotage_reception_complete')
    fieldsets = (
        ('Document', {'fields': ('norme', 'current_stage')}),
        ('Étape 1 — Réception', {'fields': ('received_by', 'received_at', 'indexed_at', 'intake_validated_by', 'intake_validated_at')}),
        ('Étape 2 — SIG', {'fields': ('requires_sig', 'sig_completed_by', 'sig_completed_at', 'it_stored_at')}),
        ('Étape 3 — Multi-Review', {'fields': ('multi_review_started_at', 'all_reviews_completed', 'all_reviews_completed_at')}),
        ('Étape 4 — FEC', {'fields': ('industrial_completed_at',)}),
        ('Étape 5 — Transmission CTC', {'fields': ('signed_out_by', 'signed_out_at', 'transmitted_to_pilotage_at')}),
        ('Étape 5 — Réception Comité de Pilotage', {'fields': (
            'received_by_president', 'received_by_president_at',
            'received_by_rapporteur', 'received_by_rapporteur_at',
            'pilotage_reception_complete',
        )}),
    )

    def pilotage_reception_complete(self, obj):
        return obj.pilotage_reception_complete
    pilotage_reception_complete.boolean = True
    pilotage_reception_complete.short_description = "Réception Pilotage complète"


@admin.register(NormeCadrage)
class NormeCadrageAdmin(admin.ModelAdmin):
    list_display = ('norme', 'current_stage', 'opened_by', 'experts_review_complete', 'mandate_formalized_at', 'transmitted_to_ctc_at', 'conformity_quitus_complete', 'final_validated_at')
    list_filter = ('current_stage',)
    search_fields = ('norme__reference_number', 'norme__title')
    raw_id_fields = (
        'opened_by', 'onic_validated_by', 'btp_validated_by', 'mandate_formalized_by',
        'scheduled_by', 'pv_verified_by', 'onic_quitus_by', 'btp_quitus_by', 'final_validated_by',
    )
    readonly_fields = ('experts_review_complete', 'conformity_quitus_complete')
    fieldsets = (
        ('Document', {'fields': ('norme', 'current_stage')}),
        ('Phase 1.1 — Orientation stratégique (Président)', {
            'fields': ('opened_by', 'opened_at', 'strategic_orientation'),
        }),
        ('Phase 1.2 — Validation des experts WG (1er & 2nd Vice-Présidents)', {
            'fields': (
                'onic_validated_by', 'onic_validated_at', 'onic_notes',
                'btp_validated_by', 'btp_validated_at', 'btp_notes',
                'experts_review_complete',
            ),
        }),
        ('Phase 1.3 — Mandat opérationnel (Secrétaire)', {
            'fields': ('mandate_formalized_by', 'mandate_formalized_at', 'operational_mandate'),
        }),
        ('Phase 1.4 — Chronogramme & ordre de service (Rapporteur Général)', {
            'fields': (
                'scheduled_by', 'scheduled_at',
                'deadline_ctm_review', 'deadline_ctc_handoff', 'deadline_pilotage_review',
                'transmitted_to_ctc_at',
            ),
        }),
        ('Phase 2.1 — Vérification du PV de l\'Assemblée Plénière (Secrétaire)', {
            'fields': ('pv_verified_by', 'pv_verified_at', 'pv_reference'),
        }),
        ('Phase 2.2 — Quitus de conformité (1er & 2nd Vice-Présidents)', {
            'fields': (
                'onic_quitus_by', 'onic_quitus_at',
                'btp_quitus_by', 'btp_quitus_at',
                'conformity_quitus_complete',
            ),
        }),
        ('Phase 2.3 — Validation finale & signature (Président)', {
            'fields': ('final_validated_by', 'final_validated_at', 'resolution_reference', 'transmitted_to_ministry_at'),
        }),
    )

    def experts_review_complete(self, obj):
        return obj.experts_review_complete
    experts_review_complete.boolean = True
    experts_review_complete.short_description = "Experts WG validés (VP1+VP2)"

    def conformity_quitus_complete(self, obj):
        return obj.conformity_quitus_complete
    conformity_quitus_complete.boolean = True
    conformity_quitus_complete.short_description = "Quitus conformité complet"
