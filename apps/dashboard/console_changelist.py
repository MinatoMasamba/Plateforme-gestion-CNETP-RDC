"""Listes paginées et filtres de la console."""
from copy import copy

from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import FieldDoesNotExist
from django.urls import reverse


class ConsoleChangeList(ChangeList):
    formset = None

    def url_for_result(self, result):
        return reverse(
            'console:model_detail',
            args=[
                self.opts.app_label,
                self.opts.model_name,
                getattr(result, self.pk_attname),
            ],
        )


def canonical_filter_request(request, model, list_filter):
    """Active le bon filtre Django pour les raccourcis de liens métier.

    La requête originale est conservée pour le formulaire de recherche.
    """
    params = request.GET.copy()
    for field_name in list_filter:
        if not isinstance(field_name, str) or '__' in field_name:
            continue
        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist:
            continue
        if not field.choices or field_name not in params:
            continue
        value = params.pop(field_name)[-1]
        if f'{field_name}__exact' not in params:
            params[f'{field_name}__exact'] = value
    if params == request.GET:
        return request
    normalized = copy(request)
    normalized.GET = params
    return normalized


def filter_groups(change_list):
    groups = []
    for spec in change_list.filter_specs:
        choices = []
        for choice in spec.choices(change_list):
            if isinstance(choice, dict):
                display = choice.get('display')
                query_string = choice.get('query_string', '')
                selected = choice.get('selected', False)
            else:
                display = getattr(choice, 'display', '')
                query_string = getattr(choice, 'query_string', '')
                selected = getattr(choice, 'selected', False)
            choices.append({
                'display': display,
                'query_string': query_string,
                'selected': selected,
            })
        groups.append({
            'title': ({'status': 'Statut', 'appointment_date': 'Date de nomination'}.get(
                getattr(spec, 'field_path', ''), spec.title,
            ) if change_list.opts.label_lower == 'experts.expert' else spec.title),
            'choices': choices,
        })
    return groups


def pagination(change_list):
    paginator = change_list.paginator
    if not paginator:
        return []
    try:
        page_number = paginator.validate_number(change_list.page_num)
    except Exception:
        page_number = 1
    return list(paginator.get_elided_page_range(page_number, on_each_side=2, on_ends=1))


def page_query_string(change_list, page_number):
    return change_list.get_query_string({'p': page_number})
