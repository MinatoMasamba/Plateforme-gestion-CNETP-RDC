"""Vues de la console d'administration."""
import json
from datetime import date, datetime

from django.apps import apps
from django.contrib import admin, messages
from django.contrib.admin.exceptions import DisallowedModelAdminLookup
from django.contrib.admin.models import LogEntry
from django.contrib.admin.views.main import IncorrectLookupParameters
from django.contrib.auth.forms import SetPasswordForm
from django.core.cache import cache
from django.core.exceptions import FieldError, PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.core.account_services import (
    deactivate_user,
    is_last_active_superuser,
    previous_expert_status,
    reactivate_user,
)
from apps.core.models import AuditLog, User

from .console_audit import record_admin_action, record_user_action, recent_activity, snapshot
from .console_changelist import ConsoleChangeList, filter_groups
from .console_forms import ConsoleUserCreationForm, ConsoleUserEditForm, build_model_form
from .console_permissions import console_required
from .console_registry import (
    admin_url,
    console_url,
    get_local_model,
    get_model_admin,
    is_local_model,
    local_app_configs,
    model_permissions,
)

APP_ICONS = {
    'core': 'users',
    'experts': 'user-check',
    'norms': 'book-open',
    'governance': 'landmark',
    'validation': 'badge-check',
    'payments': 'wallet',
    'meetings': 'calendar-days',
    'documents': 'files',
    'messaging': 'message-square',
    'amendments': 'file-pen-line',
    'gemini_drafts': 'sparkles',
    'ia_agent': 'bot',
    'mobileapp': 'smartphone',
    'public': 'globe',
    'dashboard': 'layout-dashboard',
}
MONTHS_FR = [
    'Janv.', 'Févr.', 'Mars', 'Avr.', 'Mai', 'Juin',
    'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.',
]
SENSITIVE_FIELDS = {'password', 'code', 'token', 'secret'}


def _get_model_or_404(app_label, model_name):
    try:
        return get_local_model(app_label, model_name)
    except LookupError as exc:
        raise Http404('Modèle introuvable.') from exc


def _get_object_or_404(model, pk):
    try:
        return model._base_manager.get(pk=pk)
    except (model.DoesNotExist, ValueError, ValidationError) as exc:
        raise Http404('Objet introuvable.') from exc


def _pagination_context(page_obj, request):
    params = request.GET.copy()
    params.pop('p', None)

    def url_for(number):
        values = params.copy()
        values['p'] = number
        return '?' + values.urlencode()

    pages = []
    for number in page_obj.paginator.get_elided_page_range(
        page_obj.number,
        on_each_side=2,
        on_ends=1,
    ):
        if number == page_obj.paginator.ELLIPSIS:
            pages.append({'ellipsis': True})
        else:
            pages.append({
                'number': number,
                'current': number == page_obj.number,
                'url': url_for(number),
            })
    return {
        'pages': pages,
        'previous_url': url_for(page_obj.previous_page_number()) if page_obj.has_previous() else None,
        'next_url': url_for(page_obj.next_page_number()) if page_obj.has_next() else None,
        'pagination_meta': (
            f'{page_obj.paginator.count} résultat'
            f'{"" if page_obj.paginator.count == 1 else "s"}'
            f' · page {page_obj.number} sur {page_obj.paginator.num_pages}'
        ),
    }


def _set_audit_fields(instance, user, creating=False):
    field_names = {field.name for field in instance._meta.fields}
    if creating and 'created_by' in field_names:
        instance.created_by = user
    if 'updated_by' in field_names:
        instance.updated_by = user


def _month_starts(count=12):
    now = timezone.localdate().replace(day=1)
    months = []
    for offset in range(count - 1, -1, -1):
        year = now.year
        month = now.month - offset
        while month <= 0:
            month += 12
            year -= 1
        months.append(date(year, month, 1))
    return months


def _activity_chart():
    months = _month_starts()
    start = timezone.make_aware(datetime.combine(months[0], datetime.min.time()))
    admin_counts = {
        row['month'].date(): row['total']
        for row in LogEntry.objects.filter(action_time__gte=start)
        .annotate(month=TruncMonth('action_time'))
        .values('month')
        .annotate(total=Count('id'))
    }
    business_counts = {
        row['month'].date(): row['total']
        for row in AuditLog.objects.filter(timestamp__gte=start)
        .annotate(month=TruncMonth('timestamp'))
        .values('month')
        .annotate(total=Count('id'))
    }
    labels = [f'{MONTHS_FR[month.month - 1]} {month.year}' for month in months]
    return {
        'labels': labels,
        'admin': [admin_counts.get(month, 0) for month in months],
        'business': [business_counts.get(month, 0) for month in months],
    }


def _app_stats():
    cached = cache.get('console_app_stats')
    if cached is not None:
        return cached
    rows = []
    for app_config in local_app_configs():
        models = [model for model in app_config.get_models() if is_local_model(model)]
        if not models:
            continue
        rows.append({
            'label': app_config.verbose_name,
            'name': app_config.label,
            'icon': APP_ICONS.get(app_config.label, 'box'),
            'model_count': len(models),
            'total': sum(model._base_manager.count() for model in models),
            'url': reverse('console:models') + f'#app-{app_config.label}',
        })
    cache.set('console_app_stats', rows, 60)
    return rows


def _norm_chart():
    Norme = apps.get_model('norms', 'Norme')
    labels = dict(Norme.STATUS_CHOICES)
    rows = (
        Norme._base_manager.values('status')
        .annotate(total=Count('pk'))
        .order_by('-total')
    )
    return {
        'labels': [labels.get(row['status'], row['status']) for row in rows],
        'values': [row['total'] for row in rows],
    }


@console_required
def home(request):
    UserModel = apps.get_model('core', 'User')
    Expert = apps.get_model('experts', 'Expert')
    Norme = apps.get_model('norms', 'Norme')
    stats = [
        {
            'label': 'Utilisateurs',
            'value': UserModel.objects.count(),
            'detail': f'{UserModel.objects.filter(is_active=True).count()} actifs',
            'icon': 'users',
            'url': reverse('console:users'),
        },
        {
            'label': 'Experts',
            'value': Expert.objects.count(),
            'detail': f'{Expert.objects.filter(status="ACTIVE").count()} actifs',
            'icon': 'user-check',
            'url': reverse('console:model_list', args=['experts', 'expert']),
        },
        {
            'label': 'Normes',
            'value': Norme._base_manager.count(),
            'detail': f'{Norme._base_manager.filter(status="PUBLISHED").count()} publiées',
            'icon': 'book-open',
            'url': reverse('console:model_list', args=['norms', 'norme']),
        },
        {
            'label': 'Journal',
            'value': LogEntry.objects.count() + AuditLog.objects.count(),
            'detail': 'actions enregistrées',
            'icon': 'history',
            'url': reverse('console:audit'),
        },
    ]
    alerts = []
    pending_experts = Expert.objects.filter(status='PENDING').count()
    if pending_experts:
        alerts.append({
            'label': 'Experts en attente',
            'count': pending_experts,
            'url': reverse('console:model_list', args=['experts', 'expert']) + '?status=PENDING',
            'icon': 'user-clock',
        })
    pending_norms = Norme._base_manager.exclude(status__in=['PUBLISHED', 'ARCHIVED']).count()
    if pending_norms:
        alerts.append({
            'label': 'Normes en circuit',
            'count': pending_norms,
            'url': reverse('console:model_list', args=['norms', 'norme']),
            'icon': 'book-open-check',
        })
    inactive_users = UserModel.objects.filter(is_active=False).count()
    if inactive_users:
        alerts.append({
            'label': 'Comptes désactivés',
            'count': inactive_users,
            'url': reverse('console:users') + '?status=inactive',
            'icon': 'user-x',
        })
    chart_data = {
        'activity': _activity_chart(),
        'apps': {
            'labels': [row['label'] for row in _app_stats()],
            'values': [row['total'] for row in _app_stats()],
        },
        'norms': _norm_chart(),
    }
    return render(request, 'dashboard/console/home.html', {
        'page_title': 'Console d’administration',
        'stats': stats,
        'alerts': alerts,
        'apps': _app_stats(),
        'recent_activity': recent_activity(8),
        'chart_data': chart_data,
        'quick_actions': [
            {'label': 'Créer un utilisateur', 'url': reverse('console:user_create'), 'icon': 'user-plus'},
            {'label': 'Créer un expert', 'url': reverse('console:model_create', args=['experts', 'expert']), 'icon': 'user-plus'},
            {'label': 'Créer une norme', 'url': reverse('console:model_create', args=['norms', 'norme']), 'icon': 'file-plus'},
            {'label': 'Consulter le journal', 'url': reverse('console:audit'), 'icon': 'history'},
        ],
    })


@console_required
def models_index(request):
    query = request.GET.get('q', '').strip().lower()
    groups = []
    for app_config in local_app_configs():
        rows = []
        for model in app_config.get_models():
            if not is_local_model(model):
                continue
            label = str(model._meta.verbose_name_plural)
            if query and query not in label.lower() and query not in model._meta.model_name:
                continue
            permissions = model_permissions(request.user, model)
            if not permissions['view']:
                continue
            rows.append({
                'model': model,
                'label': label,
                'count': model._base_manager.count(),
                'permissions': permissions,
                'url': console_url('model_list', model),
            })
        if rows:
            groups.append({
                'label': app_config.verbose_name,
                'name': app_config.label,
                'icon': APP_ICONS.get(app_config.label, 'box'),
                'rows': rows,
            })
    return render(request, 'dashboard/console/models.html', {
        'page_title': 'Modèles',
        'groups': groups,
        'query': request.GET.get('q', ''),
    })


def _related_admin(model, related_field, related_pk):
    base_admin = get_model_admin(model)
    base_class = base_admin.__class__

    class RelatedConsoleAdmin(base_class):
        def get_queryset(self, request):
            return super().get_queryset(request).filter(**{related_field: related_pk})

    RelatedConsoleAdmin.__name__ = f'Related{base_class.__name__}'
    return RelatedConsoleAdmin(model, admin.site)


@console_required
def model_list(request, app_label, model_name):
    model = _get_model_or_404(app_label, model_name)
    if model is User:
        return redirect('console:users')
    model_admin = get_model_admin(model)
    if not model_admin.has_view_permission(request):
        raise PermissionDenied

    related_field = request.GET.get('related_field')
    related_pk = request.GET.get('related_pk')
    related_label = ''
    if related_field and related_pk:
        try:
            field = model._meta.get_field(related_field)
        except Exception as exc:
            raise Http404('Filtre de relation invalide.') from exc
        if not field.is_relation:
            raise Http404('Filtre de relation invalide.')
        model_admin = _related_admin(model, related_field, related_pk)
        related_label = field.verbose_name

    list_display = model_admin.get_list_display(request)
    list_display_links = model_admin.get_list_display_links(request, list_display)
    list_filter = model_admin.get_list_filter(request)
    date_hierarchy = getattr(model_admin, 'date_hierarchy', None)
    search_fields = model_admin.get_search_fields(request)
    list_select_related = model_admin.get_list_select_related(request)
    sortable_by = model_admin.get_sortable_by(request)
    try:
        change_list = ConsoleChangeList(
            request,
            model,
            list_display,
            list_display_links,
            list_filter,
            date_hierarchy,
            search_fields,
            list_select_related,
            getattr(model_admin, 'list_per_page', 100),
            getattr(model_admin, 'list_max_show_all', 200),
            (),
            model_admin,
            sortable_by,
            getattr(model_admin, 'search_help_text', None),
        )
    except (IncorrectLookupParameters, DisallowedModelAdminLookup, FieldError, ValueError) as exc:
        raise Http404('Filtre invalide.') from exc

    pages = []
    previous_url = None
    next_url = None
    pagination_meta = ''
    if change_list.paginator:
        try:
            page_number = change_list.paginator.validate_number(change_list.page_num)
        except Exception:
            page_number = 1
        for number in change_list.paginator.get_elided_page_range(page_number, on_each_side=2, on_ends=1):
            if number == change_list.paginator.ELLIPSIS:
                pages.append({'ellipsis': True})
            else:
                pages.append({
                    'number': number,
                    'current': number == page_number,
                    'url': change_list.get_query_string({'p': number}),
                })
        if page_number > 1:
            previous_url = change_list.get_query_string({'p': page_number - 1})
        if page_number < change_list.paginator.num_pages:
            next_url = change_list.get_query_string({'p': page_number + 1})
        pagination_meta = (
            f'{change_list.paginator.count} résultat'
            f'{"" if change_list.paginator.count == 1 else "s"}'
            f' · page {page_number} sur {change_list.paginator.num_pages}'
        )

    return render(request, 'dashboard/console/model_list.html', {
        'page_title': str(model._meta.verbose_name_plural),
        'model': model,
        'opts': model._meta,
        'app_label': model._meta.app_label,
        'model_name': model._meta.model_name,
        'model_verbose_name': model._meta.verbose_name,
        'model_verbose_name_plural': model._meta.verbose_name_plural,
        'model_admin': model_admin,
        'cl': change_list,
        'filters': filter_groups(change_list),
        'pages': pages,
        'previous_url': previous_url,
        'next_url': next_url,
        'pagination_meta': pagination_meta,
        'permissions': model_permissions(request.user, model),
        'related_label': related_label,
        'related_clear_url': console_url('model_list', model),
    })


@console_required
@require_http_methods(['GET', 'POST'])
def model_create(request, app_label, model_name):
    model = _get_model_or_404(app_label, model_name)
    if model is User:
        return redirect('console:user_create')
    model_admin = get_model_admin(model)
    if not model_admin.has_add_permission(request):
        raise PermissionDenied
    FormClass = build_model_form(model_admin, request)
    form = FormClass(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        instance = form.save(commit=False)
        _set_audit_fields(instance, request.user, creating=True)
        instance.save()
        form.save_m2m()
        record_admin_action(request, 'CREATE', instance, 'Création via la console.')
        messages.success(request, f'{model._meta.verbose_name} créé(e).')
        return redirect('console:model_detail', app_label, model_name, instance.pk)
    return render(request, 'dashboard/console/model_form.html', {
        'page_title': f'Créer — {model._meta.verbose_name}',
        'model': model,
        'model_verbose_name': model._meta.verbose_name,
        'form': form,
        'is_create': True,
        'cancel_url': console_url('model_list', model),
        'submit_label': 'Créer',
    })


def _display_value(obj, field):
    if field.name in SENSITIVE_FIELDS:
        return '••••••'
    try:
        value = getattr(obj, field.name)
    except Exception:
        return '—'
    if field.choices and value is not None:
        display = getattr(obj, f'get_{field.name}_display', None)
        if display:
            value = display()
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.strftime('%d/%m/%Y %H:%M')
    if isinstance(value, date):
        return value.strftime('%d/%m/%Y')
    if isinstance(value, bool):
        return 'Oui' if value else 'Non'
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    if value is None or value == '':
        return '—'
    return value


def _detail_fields(obj):
    rows = []
    for field in obj._meta.fields:
        if field.name in {'created_by', 'updated_by'}:
            continue
        link = None
        file_url = None
        value = _display_value(obj, field)
        raw = getattr(obj, field.name, None)
        if field.is_relation and raw is not None:
            related_model = field.related_model
            if related_model is not None and is_local_model(related_model):
                link = console_url('model_detail', related_model, raw.pk)
        if raw and hasattr(raw, 'url'):
            try:
                file_url = raw.url
            except ValueError:
                file_url = None
        rows.append({
            'name': field.name,
            'label': field.verbose_name,
            'value': value,
            'link': link,
            'file_url': file_url,
            'long': isinstance(field, (models.TextField, models.JSONField)),
        })
    return rows


def _m2m_rows(obj):
    rows = []
    for field in obj._meta.many_to_many:
        related_model = field.related_model
        if not is_local_model(related_model):
            continue
        values = []
        for item in getattr(obj, field.name).all()[:25]:
            values.append({
                'label': str(item),
                'url': console_url('model_detail', related_model, item.pk),
            })
        rows.append({
            'label': field.verbose_name,
            'values': values,
            'count': getattr(obj, field.name).count(),
        })
    return rows


def _reverse_rows(obj):
    rows = []
    for relation in obj._meta.related_objects:
        related_model = relation.related_model
        if related_model is None or not is_local_model(related_model):
            continue
        accessor = relation.get_accessor_name()
        if not accessor:
            continue
        try:
            manager = getattr(obj, accessor)
        except Exception:
            continue
        if not hasattr(manager, 'count'):
            continue
        count = manager.count()
        if not count:
            continue
        field_name = relation.field.name
        rows.append({
            'label': related_model._meta.verbose_name_plural,
            'count': count,
            'url': console_url('model_list', related_model)
            + f'?related_field={field_name}&related_pk={obj.pk}',
        })
    return rows


@console_required
def model_detail(request, app_label, model_name, pk):
    model = _get_model_or_404(app_label, model_name)
    if model is User:
        return redirect('console:user_detail', pk)
    model_admin = get_model_admin(model)
    if not model_admin.has_view_permission(request):
        raise PermissionDenied
    obj = _get_object_or_404(model, pk)
    try:
        admin_link = admin_url(model, obj.pk)
    except NoReverseMatch:
        admin_link = None
    return render(request, 'dashboard/console/model_detail.html', {
        'page_title': str(obj),
        'model': model,
        'model_verbose_name': model._meta.verbose_name,
        'object': obj,
        'fields': _detail_fields(obj),
        'm2m_rows': _m2m_rows(obj),
        'reverse_rows': _reverse_rows(obj),
        'permissions': model_permissions(request.user, model),
        'admin_url': admin_link,
        'edit_url': console_url('model_edit', model, obj.pk),
        'delete_url': console_url('model_delete', model, obj.pk),
        'list_url': console_url('model_list', model),
    })


@console_required
@require_http_methods(['GET', 'POST'])
def model_edit(request, app_label, model_name, pk):
    model = _get_model_or_404(app_label, model_name)
    if model is User:
        return redirect('console:user_edit', pk)
    model_admin = get_model_admin(model)
    obj = _get_object_or_404(model, pk)
    if not model_admin.has_change_permission(request, obj):
        raise PermissionDenied
    old_snapshot = snapshot(obj)
    FormClass = build_model_form(model_admin, request, obj)
    form = FormClass(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        instance = form.save(commit=False)
        _set_audit_fields(instance, request.user)
        instance.save()
        form.save_m2m()
        record_admin_action(request, 'UPDATE', instance, 'Modification via la console.', old_snapshot)
        messages.success(request, f'{model._meta.verbose_name} mis(e) à jour.')
        return redirect('console:model_detail', app_label, model_name, instance.pk)
    return render(request, 'dashboard/console/model_form.html', {
        'page_title': f'Modifier — {model._meta.verbose_name}',
        'model': model,
        'model_verbose_name': model._meta.verbose_name,
        'object': obj,
        'form': form,
        'is_create': False,
        'cancel_url': console_url('model_detail', model, obj.pk),
        'submit_label': 'Enregistrer',
    })


@console_required
@require_http_methods(['GET', 'POST'])
def model_delete(request, app_label, model_name, pk):
    model = _get_model_or_404(app_label, model_name)
    if model is User:
        raise PermissionDenied
    model_admin = get_model_admin(model)
    obj = _get_object_or_404(model, pk)
    if not model_admin.has_delete_permission(request, obj):
        raise PermissionDenied
    if request.method == 'POST':
        old_snapshot = snapshot(obj)
        object_pk = obj.pk
        object_repr = str(obj)
        try:
            obj.delete()
        except models.ProtectedError:
            messages.error(request, 'Suppression impossible : des objets protégés y sont liés.')
            return redirect('console:model_detail', app_label, model_name, object_pk)
        except models.RestrictedError:
            messages.error(request, 'Suppression impossible : des objets restreints y sont liés.')
            return redirect('console:model_detail', app_label, model_name, object_pk)
        obj.pk = object_pk
        record_admin_action(
            request,
            'DELETE',
            obj,
            f'Suppression de {object_repr}.',
            old_snapshot,
            object_repr=object_repr,
        )
        messages.success(request, f'{object_repr} supprimé(e).')
        return redirect('console:model_list', app_label, model_name)
    return render(request, 'dashboard/console/confirm_delete.html', {
        'page_title': f'Supprimer — {model._meta.verbose_name}',
        'model': model,
        'object': obj,
        'related_rows': _reverse_rows(obj),
        'cancel_url': console_url('model_detail', model, obj.pk),
    })


@console_required
def users(request):
    queryset = User.objects.select_related('expert_profile', 'expert_profile__structure')
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    role = request.GET.get('role', '')
    expert_status = request.GET.get('expert_status', '')
    if query:
        queryset = queryset.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )
    if status == 'active':
        queryset = queryset.filter(is_active=True)
    elif status == 'inactive':
        queryset = queryset.filter(is_active=False)
    if role == 'superuser':
        queryset = queryset.filter(is_superuser=True)
    elif role == 'staff':
        queryset = queryset.filter(is_staff=True)
    elif role == 'expert':
        queryset = queryset.filter(is_expert=True)
    elif role == 'ctc':
        queryset = queryset.filter(is_ctc_staff=True)
    elif role == 'minister':
        queryset = queryset.filter(is_minister=True)
    if expert_status:
        queryset = queryset.filter(expert_profile__status=expert_status)
    paginator = Paginator(queryset.order_by('-date_joined'), 25)
    page_obj = paginator.get_page(request.GET.get('p'))
    context = {
        'page_title': 'Utilisateurs',
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'role': role,
        'expert_status': expert_status,
        'expert_statuses': apps.get_model('experts', 'Expert').STATUS_CHOICES,
        'can_create': request.user.has_perm('core.add_user'),
    }
    context.update(_pagination_context(page_obj, request))
    return render(request, 'dashboard/console/users.html', context)


@console_required
def user_detail(request, pk):
    user_obj = _get_object_or_404(User, pk)
    expert = getattr(user_obj, 'expert_profile', None)
    admin_logs = LogEntry.objects.filter(
        content_type__app_label='core',
        content_type__model='user',
        object_id=str(user_obj.pk),
    ).select_related('user').order_by('-action_time')[:20]
    business_logs = AuditLog.objects.filter(
        content_type='core.User',
        object_id=user_obj.pk,
    ).select_related('user').order_by('-timestamp')[:20]
    return render(request, 'dashboard/console/user_detail.html', {
        'page_title': str(user_obj),
        'object': user_obj,
        'expert': expert,
        'previous_expert_status': previous_expert_status(user_obj),
        'admin_logs': admin_logs,
        'business_logs': business_logs,
        'can_edit': request.user.has_perm('core.change_user')
        and (request.user.is_superuser or not user_obj.is_superuser),
        'can_deactivate': user_obj.is_active
        and user_obj != request.user
        and (request.user.is_superuser or not user_obj.is_superuser)
        and not is_last_active_superuser(user_obj),
        'can_reactivate': not user_obj.is_active
        and (request.user.is_superuser or not user_obj.is_superuser),
        'edit_url': reverse('console:user_edit', args=[user_obj.pk]),
        'password_url': reverse('console:user_password', args=[user_obj.pk]),
        'deactivate_url': reverse('console:user_deactivate', args=[user_obj.pk]),
        'reactivate_url': reverse('console:user_reactivate', args=[user_obj.pk]),
    })


@console_required
@require_http_methods(['GET', 'POST'])
def user_create(request):
    if not request.user.has_perm('core.add_user'):
        raise PermissionDenied
    form = ConsoleUserCreationForm(request.POST or None, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        user_obj = form.save()
        record_user_action(request, 'CREATE', user_obj, 'Création via la console.')
        messages.success(request, 'Utilisateur créé.')
        return redirect('console:user_detail', user_obj.pk)
    return render(request, 'dashboard/console/user_form.html', {
        'page_title': 'Créer un utilisateur',
        'form': form,
        'is_create': True,
        'cancel_url': reverse('console:users'),
        'submit_label': 'Créer',
    })


@console_required
@require_http_methods(['GET', 'POST'])
def user_edit(request, pk):
    user_obj = _get_object_or_404(User, pk)
    if not request.user.has_perm('core.change_user'):
        raise PermissionDenied
    if user_obj.is_superuser and not request.user.is_superuser:
        raise PermissionDenied
    old_snapshot = snapshot(user_obj)
    form = ConsoleUserEditForm(
        request.POST or None,
        instance=user_obj,
        actor=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        new_active = form.cleaned_data.get('is_active', user_obj.is_active)
        new_superuser = form.cleaned_data.get('is_superuser', user_obj.is_superuser)
        if user_obj == request.user and not new_active:
            form.add_error(None, 'Vous ne pouvez pas désactiver votre propre compte.')
        elif is_last_active_superuser(user_obj) and (not new_active or not new_superuser):
            form.add_error(None, 'Le dernier superutilisateur actif doit rester actif.')
        else:
            user_obj = form.save()
            record_user_action(request, 'UPDATE', user_obj, 'Modification via la console.', old_snapshot)
            messages.success(request, 'Utilisateur mis à jour.')
            return redirect('console:user_detail', user_obj.pk)
    return render(request, 'dashboard/console/user_form.html', {
        'page_title': f'Modifier — {user_obj}',
        'object': user_obj,
        'form': form,
        'is_create': False,
        'cancel_url': reverse('console:user_detail', args=[user_obj.pk]),
        'submit_label': 'Enregistrer',
    })


@console_required
@require_http_methods(['GET', 'POST'])
def user_password(request, pk):
    user_obj = _get_object_or_404(User, pk)
    if not request.user.has_perm('core.change_user'):
        raise PermissionDenied
    if user_obj.is_superuser and not request.user.is_superuser:
        raise PermissionDenied
    form = SetPasswordForm(user_obj, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        record_user_action(request, 'UPDATE', user_obj, 'Réinitialisation du mot de passe.')
        messages.success(request, 'Mot de passe réinitialisé.')
        return redirect('console:user_detail', user_obj.pk)
    return render(request, 'dashboard/console/user_form.html', {
        'page_title': f'Mot de passe — {user_obj}',
        'object': user_obj,
        'form': form,
        'is_create': False,
        'cancel_url': reverse('console:user_detail', args=[user_obj.pk]),
        'submit_label': 'Réinitialiser',
    })


@console_required
@require_http_methods(['GET', 'POST'])
def user_deactivate(request, pk):
    user_obj = _get_object_or_404(User, pk)
    if not request.user.has_perm('core.change_user'):
        raise PermissionDenied
    if user_obj.is_superuser and not request.user.is_superuser:
        raise PermissionDenied
    if user_obj == request.user:
        messages.error(request, 'Vous ne pouvez pas désactiver votre propre compte.')
        return redirect('console:user_detail', user_obj.pk)
    if is_last_active_superuser(user_obj):
        messages.error(request, 'Impossible de désactiver le dernier superutilisateur actif.')
        return redirect('console:user_detail', user_obj.pk)
    expert = getattr(user_obj, 'expert_profile', None)
    if request.method == 'POST':
        old_snapshot = snapshot(user_obj)
        old_expert_snapshot = snapshot(expert) if expert else None
        deactivate_user(user_obj)
        record_user_action(request, 'UPDATE', user_obj, 'Désactivation du compte.', old_snapshot)
        if expert:
            expert.refresh_from_db()
            if old_expert_snapshot and old_expert_snapshot.get('status') != expert.status:
                record_admin_action(
                    request, 'UPDATE', expert,
                    'Suspension suite à la désactivation du compte.',
                    old_expert_snapshot,
                )
        messages.success(request, 'Compte désactivé.')
        return redirect('console:user_detail', user_obj.pk)
    return render(request, 'dashboard/console/confirm_user.html', {
        'page_title': 'Désactiver le compte',
        'object': user_obj,
        'expert': expert,
        'action': 'deactivate',
        'cancel_url': reverse('console:user_detail', args=[user_obj.pk]),
    })


@console_required
@require_http_methods(['GET', 'POST'])
def user_reactivate(request, pk):
    user_obj = _get_object_or_404(User, pk)
    if not request.user.has_perm('core.change_user'):
        raise PermissionDenied
    if user_obj.is_superuser and not request.user.is_superuser:
        raise PermissionDenied
    expert = getattr(user_obj, 'expert_profile', None)
    if request.method == 'POST':
        restore = request.POST.get('restore_expert_status') == 'on'
        old_snapshot = snapshot(user_obj)
        old_expert_snapshot = snapshot(expert) if expert else None
        reactivate_user(user_obj, restore_expert_status=restore)
        record_user_action(request, 'UPDATE', user_obj, 'Réactivation du compte.', old_snapshot)
        if expert:
            expert.refresh_from_db()
            if old_expert_snapshot and old_expert_snapshot.get('status') != expert.status:
                record_admin_action(
                    request, 'UPDATE', expert,
                    'Rétablissement du statut expert après réactivation.',
                    old_expert_snapshot,
                )
        messages.success(request, 'Compte réactivé.')
        return redirect('console:user_detail', user_obj.pk)
    return render(request, 'dashboard/console/confirm_user.html', {
        'page_title': 'Réactiver le compte',
        'object': user_obj,
        'expert': expert,
        'previous_expert_status': previous_expert_status(user_obj),
        'action': 'reactivate',
        'cancel_url': reverse('console:user_detail', args=[user_obj.pk]),
    })


def _changes_summary(changes):
    if not changes:
        return ''
    parts = []
    for field, values in list(changes.items())[:6]:
        parts.append(f'{field}: {values.get("old", "—")} → {values.get("new", "—")}')
    if len(changes) > 6:
        parts.append(f'+{len(changes) - 6} autre(s)')
    return ' · '.join(parts)


@console_required
def audit(request):
    tab = request.GET.get('tab', 'admin')
    if tab not in {'admin', 'business'}:
        tab = 'admin'
    query = request.GET.get('q', '').strip()
    action = request.GET.get('action', '')
    if tab == 'admin':
        queryset = LogEntry.objects.select_related('user', 'content_type')
        if query:
            queryset = queryset.filter(
                Q(object_repr__icontains=query)
                | Q(change_message__icontains=query)
                | Q(user__username__icontains=query)
            )
        if action:
            queryset = queryset.filter(action_flag=action)
        queryset = queryset.order_by('-action_time')
        choices = [(1, 'Ajout'), (2, 'Modification'), (3, 'Suppression')]
    else:
        queryset = AuditLog.objects.select_related('user')
        if query:
            queryset = queryset.filter(
                Q(object_repr__icontains=query)
                | Q(content_type__icontains=query)
                | Q(user__username__icontains=query)
            )
        if action:
            queryset = queryset.filter(action=action)
        queryset = queryset.order_by('-timestamp')
        choices = AuditLog.ACTION_CHOICES
    page_obj = Paginator(queryset, 50).get_page(request.GET.get('p'))
    rows = []
    for log in page_obj.object_list:
        if tab == 'admin':
            rows.append({
                'when': log.action_time,
                'user': log.user,
                'action': log.get_action_flag_display(),
                'label': log.object_repr,
                'detail': log.get_change_message(),
            })
        else:
            rows.append({
                'when': log.timestamp,
                'user': log.user,
                'action': log.get_action_display(),
                'label': log.object_repr,
                'detail': _changes_summary(log.changes),
            })
    context = {
        'page_title': 'Journal d’audit',
        'tab': tab,
        'page_obj': page_obj,
        'rows': rows,
        'query': query,
        'action': action,
        'action_choices': choices,
    }
    context.update(_pagination_context(page_obj, request))
    return render(request, 'dashboard/console/audit.html', context)
