"""Présentation de l'annuaire, fondée sur le queryset et les droits existants."""
from copy import copy

from django.contrib import admin
from django.db.models import Count, Prefetch, Q
from django.urls import reverse

from apps.governance.models import Affectation, CTCMembership, PilotageMembreship


COMMITTEES = (
    ('', 'Tous les comités'), ('pilotage', 'Comité de pilotage'),
    ('ctc', 'Cellule technique (CTC)'), ('ctm', 'Comités techniques (CTM)'),
    ('none', 'Sans affectation'),
)
PAGE_SIZES = (25, 50, 100)
CONTROLLED_FILTERS = {
    'q', 'p', 'status', 'status__exact', 'structure', 'structure__id__exact',
    'structure__id__in', 'committee', 'per_page',
    'appointment_date__gte', 'appointment_date__lte',
}


def directory_admin(model_admin, request):
    """Adapte uniquement la liste ; conserve les méthodes CRUD et permissions."""
    committee = request.GET.get('committee', '')
    if committee not in dict(COMMITTEES):
        committee = ''
    try:
        page_size = int(request.GET.get('per_page', 25))
    except (TypeError, ValueError):
        page_size = 25
    if page_size not in PAGE_SIZES:
        page_size = 25

    base_queryset = model_admin.get_queryset(request)

    class ExpertDirectoryAdmin(model_admin.__class__):
        @admin.display(description='Nom complet', ordering='user__last_name')
        def console_name(self, obj):
            return obj.full_name or obj.user.username

        def get_list_display(self, request):
            return tuple('console_name' if name == 'full_name' else name
                         for name in super().get_list_display(request))

        def get_queryset(self, request):
            queryset = super().get_queryset(request)
            pilotage = PilotageMembreship.objects.values('expert_id')
            ctc = CTCMembership.objects.values('expert_id')
            assignments = Affectation.objects.values('expert_id')
            if committee == 'pilotage':
                queryset = queryset.filter(pk__in=pilotage)
            elif committee == 'ctc':
                queryset = queryset.filter(pk__in=ctc)
            elif committee == 'ctm':
                queryset = queryset.filter(Q(ctm__isnull=False) | Q(pk__in=assignments))
            elif committee == 'none':
                queryset = queryset.exclude(
                    Q(ctm__isnull=False) | Q(pk__in=assignments) |
                    Q(pk__in=pilotage) | Q(pk__in=ctc)
                )
            return queryset.select_related('user', 'structure', 'ctm').prefetch_related(
                'pilotagemembreship_set', 'ctcmembership_set',
                Prefetch('governance_affectations', queryset=Affectation.objects.select_related('ctm')),
            )

    configured = ExpertDirectoryAdmin(model_admin.model, admin.site)
    configured.list_per_page = page_size
    adapted = copy(request)
    adapted.GET = request.GET.copy()
    for key in ('committee', 'per_page'):
        adapted.GET.pop(key, None)
    for key in ('status__exact', 'status', 'appointment_date__gte', 'appointment_date__lte'):
        if key in adapted.GET and not adapted.GET[key]:
            adapted.GET.pop(key)
    if 'structure__id__in' in adapted.GET:
        values = ','.join(adapted.GET.getlist('structure__id__in'))
        if values:
            adapted.GET['structure__id__in'] = values
        else:
            adapted.GET.pop('structure__id__in')
    return configured, adapted, base_queryset, {'committee': committee, 'per_page': page_size}


def restore_directory_parameters(change_list, state):
    # Les paramètres de présentation ne doivent pas devenir des lookups ORM.
    for key, value in state.items():
        if value != '':
            change_list.params[key] = str(value)
            change_list.filter_params[key] = [str(value)]


def directory_context(request, change_list, model_admin, base_queryset, state):
    """Calcule les indicateurs réels dans le périmètre du ModelAdmin existant."""
    from apps.experts.models import Expert, Structure

    stats = base_queryset.aggregate(
        total=Count('pk'), active=Count('pk', filter=Q(status='ACTIVE')),
        pending=Count('pk', filter=Q(status='PENDING')),
        inactive=Count('pk', filter=Q(status__in=['INACTIVE', 'SUSPENDED'])),
    )
    show_incomplete_stat = (
        request.user.has_perm('experts.view_profileupdate')
        and base_queryset.filter(profile_update__isnull=False).exists()
    )
    if show_incomplete_stat:
        stats['incomplete'] = base_queryset.filter(
            profile_update__status__in=['NOT_STARTED', 'IN_PROGRESS', 'NEEDS_CORRECTION'],
        ).count()
    status = change_list.params.get('status__exact', request.GET.get('status', ''))
    selected_ids = set()
    for key in ('structure__id__in', 'structure__id__exact', 'structure'):
        for value in request.GET.getlist(key):
            selected_ids.update(part for part in value.split(',') if part.isdecimal())
    structures = [
        {'id': str(item.pk), 'name': item.name, 'acronym': item.acronym,
         'selected': str(item.pk) in selected_ids}
        for item in Structure.objects.order_by('name')
    ]
    base_url = reverse('console:model_list', args=['experts', 'expert'])

    def removal_url(*keys, structure_id=None):
        params = request.GET.copy()
        params.pop('p', None)
        for key in keys:
            params.pop(key, None)
        if structure_id is not None:
            remaining = sorted(selected_ids - {structure_id}, key=int)
            for key in ('structure', 'structure__id__exact', 'structure__id__in'):
                params.pop(key, None)
            if remaining:
                params['structure__id__in'] = ','.join(remaining)
        return base_url + ('?' + params.urlencode() if params else '')

    active_filters = []
    query = request.GET.get('q', '')
    if query:
        active_filters.append({'label': f'Recherche : {query}', 'url': removal_url('q')})
    if status:
        active_filters.append({'label': dict(Expert.STATUS_CHOICES).get(status, status),
                               'url': removal_url('status', 'status__exact')})
    for item in structures:
        if item['selected']:
            active_filters.append({'label': item['name'], 'url': removal_url(structure_id=item['id'])})
    if state['committee']:
        active_filters.append({'label': dict(COMMITTEES)[state['committee']], 'url': removal_url('committee')})
    date_keys = [key for key in request.GET if key.startswith('appointment_date__') and request.GET[key]]
    if any(key not in {'appointment_date__gte', 'appointment_date__lte'} for key in date_keys):
        # Conserve les raccourcis historiques (année, mois, date absente, borne exclusive).
        label = 'Date de nomination'
        for group in change_list.filter_specs:
            if getattr(group, 'field_path', '') == 'appointment_date':
                selected = next((choice for choice in group.choices(change_list) if choice.get('selected')), None)
                if selected:
                    label = str(selected['display'])
        active_filters.append({'label': label, 'url': removal_url(*date_keys)})
    else:
        for key, label in (('appointment_date__gte', 'Nommé à partir du'), ('appointment_date__lte', "Nommé jusqu’au")):
            if request.GET.get(key):
                active_filters.append({'label': f'{label} {request.GET[key]}', 'url': removal_url(key)})

    rows = []
    for expert in change_list.result_list:
        name = expert.full_name.strip() or expert.user.username
        words = name.split()
        initials = (words[0][:1] + (words[-1][:1] if len(words) > 1 else '')).upper()
        committees = []
        for membership in expert.pilotagemembreship_set.all():
            committees.append({'label': 'Pilotage', 'detail': membership.get_role_display()})
        for membership in expert.ctcmembership_set.all():
            committees.append({'label': 'CTC', 'detail': membership.get_role_display()})
        ctms = {assignment.ctm.pk: assignment.ctm for assignment in expert.governance_affectations.all()}
        if expert.ctm_id:
            ctms[expert.ctm_id] = expert.ctm
        committees.extend({'label': f'CTM {ctm.number}', 'detail': ctm.name} for ctm in ctms.values())
        rows.append({
            'expert': expert, 'name': name, 'initials': initials, 'committees': committees,
            'secondary': expert.user.email or expert.user.username,
            'status_tone': {'ACTIVE': 'success', 'PENDING': 'warning', 'SUSPENDED': 'danger',
                            'REJECTED': 'danger'}.get(expert.status, 'neutral'),
            'can_change': model_admin.has_change_permission(request, expert),
            'can_delete': model_admin.has_delete_permission(request, expert),
        })
    ordering = change_list.get_ordering_field_columns()
    headers = []
    for label, index in [('Expert', 0), ('Structure', 2), ('Statut', 3), ('Comité / affectation', None),
                         ('Date de nomination', 5), ('Présences', 6), ('Actions', None)]:
        direction = ordering.get(index)
        headers.append({'label': label, 'direction': direction,
                        'aria_sort': {'asc': 'ascending', 'desc': 'descending'}.get(direction, 'none'),
                        'url': change_list.get_query_string({'o': f'-{index}' if direction == 'asc' else str(index), 'p': None})
                        if index is not None else None})
    return {
        'page_title': 'Gestion des experts', 'expert_stats': stats, 'expert_rows': rows,
        'show_incomplete_stat': show_incomplete_stat,
        'expert_headers': headers, 'expert_structures': structures,
        'expert_status_choices': Expert.STATUS_CHOICES, 'selected_status': status,
        'selected_structure_count': len(selected_ids), 'selected_structure_ids': ','.join(sorted(selected_ids, key=int)),
        'committee_choices': COMMITTEES, 'directory_state': state, 'active_filters': active_filters,
        'directory_query': query, 'directory_reset_url': base_url, 'page_sizes': PAGE_SIZES,
        'date_from': request.GET.get('appointment_date__gte', ''),
        'date_to': request.GET.get('appointment_date__lte', ''),
        'directory_hidden_params': [(key, value) for key, values in request.GET.lists()
                                    if key not in CONTROLLED_FILTERS for value in values],
        'pagination_hidden_params': [(key, value) for key, values in request.GET.lists()
                                     if key not in {'p', 'per_page'} for value in values],
    }
