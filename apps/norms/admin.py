from django.contrib import admin
from django.apps import apps
from django.db import models as django_models

from .models import Norme, NormeVersion, ChangementVersion


class NormsModelAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    list_per_page = 50
    ordering = ("-pk",)
    show_full_result_count = True

    def get_list_display(self, request):
        fields = [
            field.name
            for field in self.model._meta.fields
            if field.editable and not isinstance(field, django_models.ManyToManyField)
        ]
        return fields or ("__str__",)

    def get_search_fields(self, request):
        return [
            field.name
            for field in self.model._meta.fields
            if isinstance(field, (django_models.CharField, django_models.TextField))
        ]

    def get_list_filter(self, request):
        return [
            field.name
            for field in self.model._meta.fields
            if field.choices
            or isinstance(
                field,
                (
                    django_models.BooleanField,
                    django_models.DateField,
                    django_models.DateTimeField,
                    django_models.ForeignKey,
                ),
            )
        ]

    def get_readonly_fields(self, request, obj=None):
        return [
            field.name
            for field in self.model._meta.fields
            if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False)
        ]

    def get_fieldsets(self, request, obj=None):
        fields = [field.name for field in self.model._meta.fields if field.editable]
        return [(None, {"fields": fields})]

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def has_view_permission(self, request, obj=None):
        return True


class NormeVersionInline(admin.TabularInline):
    model = NormeVersion
    extra = 0
    fields = ("version_number", "title", "version_author", "is_draft", "created_at")
    readonly_fields = ("created_at",)


class ChangementVersionInline(admin.TabularInline):
    model = ChangementVersion
    fk_name = "version"
    extra = 0
    fields = (
        "section",
        "change_type",
        "previous_version",
        "old_text",
        "new_text",
        "change_reason",
    )


class NormeAdmin(NormsModelAdmin):
    list_display = (
        "reference_number",
        "title",
        "standard_family",
        "norm_type",
        "target_count",
        "status",
        "ctm",
        "wg",
        "is_public",
        "publication_date",
        "locked_by",
    )
    search_fields = (
        "reference_number",
        "title",
        "standard_family",
        "iso_reference",
        "arso_reference",
        "jo_reference",
        "tags",
    )
    list_filter = ("standard_family", "norm_type", "status", "ctm", "wg", "is_public", "publication_date")
    inlines = (NormeVersionInline,)


class NormeVersionAdmin(NormsModelAdmin):
    list_display = ("norme", "version_number", "is_draft", "version_author", "created_at")
    search_fields = ("norme__reference_number", "title", "summary")
    list_filter = ("is_draft", "version_author", "created_at")
    inlines = (ChangementVersionInline,)


class ChangementVersionAdmin(NormsModelAdmin):
    list_display = ("version", "section", "change_type", "previous_version")
    search_fields = (
        "version__norme__reference_number",
        "section",
        "old_text",
        "new_text",
        "change_reason",
    )
    list_filter = ("change_type",)


admin.site.register(Norme, NormeAdmin)
admin.site.register(NormeVersion, NormeVersionAdmin)
admin.site.register(ChangementVersion, ChangementVersionAdmin)

from django.apps import apps as django_apps

app_config = django_apps.get_app_config("norms")
for model in app_config.get_models():
    try:
        if model in {Norme, NormeVersion, ChangementVersion}:
            continue
        admin.site.register(model, NormsModelAdmin)
    except admin.sites.AlreadyRegistered:
        pass
