from django.contrib import admin
from django.core.exceptions import PermissionDenied

from apps.governance.models import JournalMigration

from .models import Report, ReportTypePermission


@admin.register(ReportTypePermission)
class ReportTypePermissionAdmin(admin.ModelAdmin):
    list_display = ('habilitation', 'report_type', 'enabled')
    list_filter = ('report_type', 'enabled')
    search_fields = ('habilitation__decision_reference', 'habilitation__mandat__expert__user__email')

    def has_module_permission(self, request):
        return request.user.is_active and request.user.has_perm('governance.manage_phoenix')

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not request.user.has_perm('governance.manage_phoenix'):
            raise PermissionDenied
        obj.full_clean()
        before = {}
        if change:
            previous = ReportTypePermission.objects.get(pk=obj.pk)
            before = {'habilitation': previous.habilitation_id, 'report_type': previous.report_type,
                      'enabled': previous.enabled}
        super().save_model(request, obj, form, change)
        JournalMigration.objects.create(
            version=obj.habilitation.perimeter.version, actor=request.user,
            actor_name=request.user.get_full_name() or request.user.username,
            operation='REPORT_TYPE_PERMISSION', target=f'report_type_permission:{obj.pk}',
            before=before, after={'habilitation': obj.habilitation_id, 'report_type': obj.report_type,
                                  'enabled': obj.enabled},
            reason='Habilitation de modèle de rapport enregistrée depuis l’administration.',
        )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reference', 'report_type', 'status', 'prepared_by', 'period_end', 'created_at')
    list_filter = ('report_type', 'status')
    search_fields = ('reference', 'title')

    def has_module_permission(self, request):
        return request.user.is_active and request.user.has_perm('governance.manage_phoenix')

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
