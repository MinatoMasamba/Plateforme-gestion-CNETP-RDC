"""Espace de lecture des normes et performances pour une présidence confirmée."""

from collections import defaultdict
import unicodedata

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.experts.models import Expert
from apps.governance.models import CTM, Organe, WG, Tache, GroupeCible
from apps.governance.phoenix_models import DossierPhoenix, MandatOrganisation, OrganisationVersion, RattachementDocumentaire
from apps.governance.phoenix_workflow import can_consult
from apps.norms.models import Norme, NormeVersion


def _sc_bureau_ids(expert, today):
    if not expert or not expert.user.is_active or expert.status != 'ACTIVE':
        return []
    mandates = MandatOrganisation.objects.filter(
        expert=expert, status='ACTIVE', capacity='ORGANISATION',
        poste__status__in=[OrganisationVersion.Status.VALIDATED, OrganisationVersion.Status.ACTIVE],
        poste__organe__type='SC',
        poste__organe__status__in=[OrganisationVersion.Status.VALIDATED, OrganisationVersion.Status.ACTIVE],
        poste__organe__version__status=OrganisationVersion.Status.ACTIVE,
    ).filter(Q(start_date__isnull=True) | Q(start_date__lte=today)).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    ).select_related('poste')
    ids = set()
    for mandate in mandates:
        title = ''.join(char for char in unicodedata.normalize('NFKD', mandate.poste.title.casefold())
                        if not unicodedata.combining(char)).replace('‑', '-').replace('–', '-')
        if (title.startswith('president') or title.startswith('rapporteur') or
                title.startswith('secretaire') or 'vice-president' in title or 'vice president' in title):
            ids.add(mandate.poste.organe_id)
    return sorted(ids)


def _scope(request):
    expert = Expert.objects.filter(user=request.user).first()
    today = timezone.localdate()
    sc_ids = _sc_bureau_ids(expert, today)
    scopes = [{'kind': 'sc', 'id': row.pk, 'code': row.code, 'name': row.official_name or row.name}
              for row in Organe.objects.filter(pk__in=sc_ids).order_by('code')]
    if not scopes:
        raise PermissionDenied('Accès réservé au bureau confirmé d’une sous-commission.')

    ctm_raw, wg_raw, sc_raw = (request.GET.get(key, '') for key in ('ctm', 'wg', 'sc'))
    if sc_raw:
        if not sc_raw.isdecimal() or int(sc_raw) not in sc_ids:
            raise PermissionDenied
        selected = next(item for item in scopes if item['id'] == int(sc_raw))
    else:
        selected = scopes[0]

    ctm = None
    if ctm_raw:
        if not ctm_raw.isdecimal():
            raise PermissionDenied
        ctm = CTM.objects.filter(pk=int(ctm_raw)).first()
        if ctm is None:
            raise PermissionDenied
    wg = None
    if wg_raw:
        if not wg_raw.isdecimal():
            raise PermissionDenied
        wg = WG.objects.filter(pk=int(wg_raw)).first()
        if wg is None:
            raise PermissionDenied
        if ctm and wg.ctm_id != ctm.pk:
            raise PermissionDenied
    return selected, scopes, ctm, wg, today


def _norms(selected, ctm, wg, today, user):
    bindings = RattachementDocumentaire.objects.filter(
        sc_id=selected['id'], status='VALIDATED', version__status=OrganisationVersion.Status.ACTIVE,
    ).filter(Q(effective_from__isnull=True) | Q(effective_from__lte=today)).filter(
        Q(effective_to__isnull=True) | Q(effective_to__gte=today)
    )
    norms = Norme.all_objects.filter(pk__in=bindings.values('norme_id'))
    if ctm:
        norms = norms.filter(ctm=ctm)
    if wg:
        norms = norms.filter(wg=wg)
    result = list(norms.distinct().order_by('reference_number', 'pk'))
    dossiers = {item.norme_id: item for item in DossierPhoenix.objects.filter(norme_id__in=[norm.pk for norm in result]).select_related('norme', 'gt__sc', 'circuit__version')}
    return [norm for norm in result if norm.circuit_version != 'PHOENIX' or
            (norm.pk in dossiers and can_consult(user, dossiers[norm.pk]))]


def _norm_payload(norms, selected, today):
    if not norms:
        return []
    norm_ids = [norm.pk for norm in norms]
    tasks = list(Tache.objects.filter(norme_id__in=norm_ids).filter(
        Q(assigned_to__isnull=False) | Q(backup_assignee__isnull=False)
    ).select_related('assigned_to__user', 'backup_assignee__user'))
    group_ids = set(GroupeCible.objects.filter(sc_id=selected['id']).values_list('pk', flat=True))
    tasks = [task for task in tasks if task.target_group_id in group_ids]
    by_norm = defaultdict(lambda: defaultdict(list))
    experts = {}
    for task in tasks:
        for expert in {task.assigned_to_id: task.assigned_to, task.backup_assignee_id: task.backup_assignee}.values():
            if expert is None:
                continue
            experts[expert.pk] = expert
            by_norm[task.norme_id][expert.pk].append(task)
    version_rows = defaultdict(list)
    dossier_ids = dict(DossierPhoenix.objects.filter(norme_id__in=norm_ids).values_list('norme_id', 'pk'))
    for version in NormeVersion.all_objects.filter(norme_id__in=norm_ids).select_related('version_author').order_by('norme_id', '-version_number'):
        author = version.version_author
        version_rows[version.norme_id].append({
            'number': version.version_number,
            'date': timezone.localtime(version.created_at).strftime('%d/%m/%Y') if version.created_at else '',
            'author': author.get_full_name() or author.username if author else 'Auteur non renseigné',
            'content': version.content,
            'title': version.title,
            'document_url': version.document.url if version.document else None,
        })
    payload = []
    for norm in norms:
        rows = []
        for expert_id, owned in by_norm[norm.pk].items():
            expert = experts[expert_id]
            completed = sum(task.status == 'COMPLETED' for task in owned)
            overdue = any(task.due_date and task.due_date < today and task.status != 'COMPLETED' for task in owned)
            state = 'En retard' if overdue else 'Terminé' if completed == len(owned) else 'En cours'
            rows.append({'id': expert_id, 'name': expert.full_name or expert.user.username, 'total': len(owned),
                         'done': completed, 'state': state})
        rows.sort(key=lambda row: row['name'].casefold())
        payload.append({
            'id': norm.pk, 'code': norm.reference_number, 'title': norm.title,
            'status': norm.get_status_display(), 'rows': rows,
            'versions': version_rows[norm.pk], 'description': norm.description,
            'dossier_url': reverse('web:phoenix_dossier', args=[dossier_ids[norm.pk]]) if norm.pk in dossier_ids else None,
        })
    return payload


@login_required(login_url='/se-connecter/')
@require_GET
def president_sc_page(request):
    selected, scopes, ctm, wg, today = _scope(request)
    available_norms = _norms(selected, None, None, today, request.user)
    ctm_ids = {norm.ctm_id for norm in available_norms if norm.ctm_id}
    wg_ids = {norm.wg_id for norm in available_norms if norm.wg_id and (not ctm or norm.ctm_id == ctm.pk)}
    return render(request, 'pilotage/president_sc.html', {
        'selected': selected, 'scopes': scopes, 'ctm': ctm, 'wg': wg,
        'historical_ctms': CTM.objects.filter(pk__in=ctm_ids).order_by('number'),
        'working_groups': WG.objects.filter(pk__in=wg_ids).order_by('number'),
    })


@login_required(login_url='/se-connecter/')
@require_GET
def president_sc_data(request):
    selected, scopes, ctm, wg, today = _scope(request)
    return JsonResponse({
        'scope': selected, 'scopes': scopes,
        'norms': _norm_payload(_norms(selected, ctm, wg, today, request.user), selected, today),
    })
