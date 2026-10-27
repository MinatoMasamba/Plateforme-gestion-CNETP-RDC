"""Registre des modèles et des écrans de la console."""
from functools import lru_cache

from django.apps import apps
from django.contrib import admin
from django.db import models
from django.urls import reverse

from apps.governance.phoenix_admin import PhoenixReadOnlyAdmin

from .console_permissions import local_app_labels

READ_ONLY_MODELS = {
    'core.auditlog',
    'core.audittextchange',
    'core.passwordresetcode',
    'mobileapp.activationtoken',
    'mobileapp.emailconfirmationcode',
    'mobileapp.mobilesession',
    'mobileapp.pushtoken',
    'governance.activityaccesslog',
    'governance.activityaggregate',
}


def is_local_model(model):
    return model._meta.app_label in local_app_labels()


def local_app_configs():
    return sorted(
        (app for app in apps.get_app_configs() if app.name.startswith('apps.')),
        key=lambda app: app.verbose_name.lower(),
    )


def local_models():
    for app_config in local_app_configs():
        for model in app_config.get_models():
            if is_local_model(model):
                yield app_config, model


def model_label(model):
    return model._meta.label_lower


def is_read_only_model(model):
    return model_label(model) in READ_ONLY_MODELS


def get_local_model(app_label, model_name):
    model = apps.get_model(app_label, model_name)
    if model is None or not is_local_model(model):
        raise LookupError('Modèle local introuvable.')
    return model


def model_permissions(user, model):
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    return {
        'view': user.has_perm(f'{app_label}.view_{model_name}'),
        'add': user.has_perm(f'{app_label}.add_{model_name}'),
        'change': user.has_perm(f'{app_label}.change_{model_name}'),
        'delete': user.has_perm(f'{app_label}.delete_{model_name}'),
    }


def console_url(action, model=None, pk=None):
    if model is None:
        return reverse(f'console:{action}')
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    if action == 'model_list':
        return reverse('console:model_list', args=[app_label, model_name])
    if action == 'model_create':
        return reverse('console:model_create', args=[app_label, model_name])
    return reverse(f'console:{action}', args=[app_label, model_name, pk])


def admin_url(model, pk):
    return reverse(
        f'admin:{model._meta.app_label}_{model._meta.model_name}_change',
        args=[pk],
    )


class ConsoleModelAdminMixin:
    """Conserve les restrictions métier des admins existants."""

    def _has(self, request, action, obj=None):
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        if not request.user.has_perm(f'{app_label}.{action}_{model_name}'):
            return False
        if action == 'add':
            return super().has_add_permission(request)
        if action == 'change':
            return super().has_change_permission(request, obj)
        if action == 'delete':
            return super().has_delete_permission(request, obj)
        return super().has_view_permission(request, obj)

    def has_view_permission(self, request, obj=None):
        return self._has(request, 'view', obj)

    def has_add_permission(self, request):
        return self._has(request, 'add')

    def has_change_permission(self, request, obj=None):
        return self._has(request, 'change', obj)

    def has_delete_permission(self, request, obj=None):
        return self._has(request, 'delete', obj)


class ConsoleReadOnlyAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ConsoleGenericAdmin(ConsoleModelAdminMixin, admin.ModelAdmin):
    list_per_page = 25
    show_full_result_count = True

    def get_list_display(self, request):
        fields = []
        for field in self.model._meta.fields:
            if not field.editable or field.name == 'id' or isinstance(field, models.TextField):
                continue
            fields.append(field.name)
            if len(fields) == 6:
                break
        return tuple(fields) or ('__str__',)

    def get_search_fields(self, request):
        return tuple(
            field.name for field in self.model._meta.fields
            if isinstance(field, (models.CharField, models.TextField))
        )

    def get_list_filter(self, request):
        return tuple(
            field.name for field in self.model._meta.fields
            if field.choices or isinstance(
                field,
                (
                    models.BooleanField,
                    models.DateField,
                    models.DateTimeField,
                    models.ForeignKey,
                ),
            )
        )

    def get_readonly_fields(self, request, obj=None):
        return tuple(
            field.name for field in self.model._meta.fields
            if getattr(field, 'auto_now', False) or getattr(field, 'auto_now_add', False)
        )

    def get_fieldsets(self, request, obj=None):
        fields = [
            field.name for field in self.model._meta.fields
            if field.editable and field.name not in {'created_by', 'updated_by'}
        ]
        return [(None, {'fields': fields})]


def _norms_admin_class(base_class):
    class ConsoleNormsAdmin(ConsoleModelAdminMixin, base_class):
        def get_queryset(self, request):
            return self.model._base_manager.all()

    ConsoleNormsAdmin.__name__ = f'Console{base_class.__name__}'
    return ConsoleNormsAdmin


def _phoenix_admin_class(base_class):
    class ConsolePhoenixAdmin(base_class):
        def get_readonly_fields(self, request, obj=None):
            return []

        def has_view_permission(self, request, obj=None):
            return request.user.has_perm(
                f'{self.model._meta.app_label}.view_{self.model._meta.model_name}'
            )

        def has_add_permission(self, request):
            return request.user.has_perm(
                f'{self.model._meta.app_label}.add_{self.model._meta.model_name}'
            )

        def has_change_permission(self, request, obj=None):
            return request.user.has_perm(
                f'{self.model._meta.app_label}.change_{self.model._meta.model_name}'
            )

        def has_delete_permission(self, request, obj=None):
            return request.user.has_perm(
                f'{self.model._meta.app_label}.delete_{self.model._meta.model_name}'
            )

    ConsolePhoenixAdmin.__name__ = f'Console{base_class.__name__}'
    return ConsolePhoenixAdmin


@lru_cache(maxsize=None)
def get_model_admin(model):
    if is_read_only_model(model):
        return ConsoleReadOnlyAdmin(model, admin.site)
    registered = admin.site._registry.get(model)
    if registered is None:
        return ConsoleGenericAdmin(model, admin.site)
    base_class = registered.__class__
    if isinstance(registered, PhoenixReadOnlyAdmin):
        return _phoenix_admin_class(base_class)(model, admin.site)
    if model._meta.app_label == 'norms':
        return _norms_admin_class(base_class)(model, admin.site)
    if issubclass(base_class, ConsoleModelAdminMixin):
        return base_class(model, admin.site)
    return type(
        f'Console{base_class.__name__}',
        (ConsoleModelAdminMixin, base_class),
        {},
    )(model, admin.site)


def model_rows_for_app(app_config):
    rows = []
    for model in app_config.get_models():
        if not is_local_model(model):
            continue
        rows.append({
            'model': model,
            'label': model._meta.verbose_name_plural,
            'count': model._base_manager.count(),
            'read_only': is_read_only_model(model),
        })
    return rows


def model_admin_fields(model_admin, request, obj=None):
    readonly = set(model_admin.get_readonly_fields(request, obj))
    exclude = set(model_admin.get_exclude(request, obj) or ())
    fields = []
    for field in model_admin.model._meta.fields:
        if (
            field.name in readonly
            or field.name in exclude
            or field.name in {'id', 'pk', 'created_by', 'updated_by'}
            or not field.editable
        ):
            continue
        fields.append(field.name)
    for field in model_admin.model._meta.many_to_many:
        if field.name in readonly or field.name in exclude:
            continue
        fields.append(field.name)
    return fields


def model_admin_fieldsets(model_admin, request, obj=None):
    fields = model_admin_fields(model_admin, request, obj)
    allowed = set(fields)
    sections = []
    try:
        fieldsets = model_admin.get_fieldsets(request, obj)
    except Exception:
        fieldsets = ()
    for name, options in fieldsets:
        section_fields = []
        for item in options.get('fields', ()):
            if isinstance(item, (list, tuple)):
                candidates = item
            else:
                candidates = (item,)
            section_fields.extend(field for field in candidates if field in allowed)
        if section_fields:
            sections.append({
                'name': name or 'Informations',
                'description': options.get('description', ''),
                'fields': section_fields,
            })
    if not sections and fields:
        sections.append({'name': 'Informations', 'description': '', 'fields': fields})
    return sections, fields
