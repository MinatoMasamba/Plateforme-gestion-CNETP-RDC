"""Consultation du référentiel ; les propositions passent par le service journalisé."""
from django.contrib import admin
from .models import (
    OrganisationVersion, Organe, PosteOrganisation, GroupeCible,
    CorrespondanceStructure, CorrespondanceGroupe, AffectationSousCommission, ChoixOrganisationExpert, MandatOrganisation,
    HabilitationAction, RattachementDocumentaire, JournalMigration,
    CircuitOrganisation, DossierPhoenix, PiecePhoenix, DecisionPhoenix, EnquetePhoenix,
)


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
