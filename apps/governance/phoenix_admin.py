"""Consultation du référentiel ; les propositions passent par le service journalisé."""
from django.contrib import admin

from apps.experts.models import Expert

from .models import (
    OrganisationVersion, Organe, PosteOrganisation, GroupeCible,
    CorrespondanceStructure, CorrespondanceGroupe, AffectationSousCommission, ChoixOrganisationExpert, MandatOrganisation,
    HabilitationAction, RattachementDocumentaire, JournalMigration, NominationCTC,
    CircuitOrganisation, DossierPhoenix, PiecePhoenix, DecisionPhoenix, EnquetePhoenix,
)
from .phoenix_runtime import ST_ORGANE_TYPES, st_posts


class PhoenixReadOnlyAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrganisationVersion)
class OrganisationVersionAdmin(PhoenixReadOnlyAdmin):
    list_display = ('code', 'name', 'status', 'source_document')
    search_fields = ('code', 'name')


@admin.register(Organe)
class OrganeAdmin(PhoenixReadOnlyAdmin):
    list_display = ('code', 'name', 'type', 'version', 'status')
    list_filter = ('version', 'type', 'status')


@admin.register(PosteOrganisation)
class PosteOrganisationAdmin(PhoenixReadOnlyAdmin):
    list_display = ('code', 'title', 'organe', 'category', 'origin_label')
    list_filter = ('organe__version', 'category', 'organe__type')
    search_fields = ('code', 'title', 'origin_label')


@admin.register(NominationCTC)
class NominationCTCAdmin(admin.ModelAdmin):
    list_display = ('poste', 'expert', 'function', 'capacity', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'capacity', 'poste__organe')
    search_fields = ('poste__code', 'poste__title', 'expert__user__first_name', 'expert__user__last_name')
    fields = ('expert', 'poste', 'function', 'capacity', 'appointment_reference', 'start_date', 'end_date', 'status')
    ordering = ('poste__organe__code', 'poste__code')

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .filter(poste__organe__type__in=ST_ORGANE_TYPES)
            .select_related('expert__user', 'poste__organe')
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'poste':
            kwargs['queryset'] = st_posts()
        elif db_field.name == 'expert':
            kwargs['queryset'] = Expert.objects.filter(
                status='ACTIVE', user__is_active=True,
            ).select_related('user')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.function and obj.poste_id:
            obj.function = obj.poste.title or obj.poste.code
        super().save_model(request, obj, form, change)
        JournalMigration.objects.create(
            version=obj.organisation_version,
            actor=request.user,
            actor_name=request.user.get_full_name() or request.user.username,
            operation='ADMIN_NOMINATION',
            target=f'mandat:{obj.pk}',
            after={'poste': obj.poste_id, 'expert': obj.expert_id, 'status': obj.status},
            reason='Nomination CTC enregistrée depuis l’administration.',
        )


@admin.register(JournalMigration)
class JournalMigrationAdmin(PhoenixReadOnlyAdmin):
    list_display = ('created_at', 'version', 'actor_name', 'operation', 'target')
    list_filter = ('version', 'operation')


@admin.register(ChoixOrganisationExpert)
class ChoixOrganisationExpertAdmin(PhoenixReadOnlyAdmin):
    list_display = ('created_at', 'expert', 'sc', 'source_wg', 'status')
    list_filter = ('version', 'sc', 'status')
    search_fields = ('expert__user__first_name', 'expert__user__last_name', 'source_wg__name')


for model in (GroupeCible, CorrespondanceStructure, CorrespondanceGroupe,
              AffectationSousCommission, MandatOrganisation, HabilitationAction, RattachementDocumentaire,
              CircuitOrganisation, DossierPhoenix, PiecePhoenix, DecisionPhoenix, EnquetePhoenix):
    admin.site.register(model, PhoenixReadOnlyAdmin)
