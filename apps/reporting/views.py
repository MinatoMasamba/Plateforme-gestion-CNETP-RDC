import uuid

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .catalog import FAMILIES, LABELS, TYPES, fields_for
from .forms import EvidenceForm, FinancialLineForm, ReportForm
from .models import FinancialLine, Report, ReportEvent
from .services import (
    active_version, eligible_approver, eligible_reviewer, missing_fields,
    reporting_mandates, require_action, source_suggestions,
)


def _visible(report, user):
    scope = {'central_only': not report.pole_id}
    if user.pk == report.prepared_by_id and reporting_mandates(user, 'rapport.rediger', report.version, report.pole, report.report_type, **scope).exists():
        return True
    return any(reporting_mandates(user, action, report.version, report.pole, report.report_type, **scope).exists() for action in ('rapport.consulter', 'rapport.controler', 'rapport.approuver', 'rapport.transmettre'))


def _get_report(pk, user):
    report = get_object_or_404(Report.objects.select_related('version', 'pole', 'norme', 'sc', 'gt', 'prepared_by'), pk=pk)
    if not _visible(report, user):
        raise PermissionDenied
    return report


def _event(report, actor, action, old, comment=''):
    ReportEvent.objects.create(report=report, actor=actor, action=action, from_status=old,
                               to_status=report.status, comment=comment,
                               snapshot={'revision': report.revision, 'fields': report.fields,
                                         'sources': report.source_snapshot})


@login_required(login_url='/se-connecter/')
def index(request):
    version = active_version()
    if not version:
        return render(request, 'reporting/unavailable.html', {'reason': 'Aucun référentiel d’organisation en vigueur.'})
    actions = ('rapport.consulter', 'rapport.rediger', 'rapport.controler', 'rapport.approuver', 'rapport.transmettre')
    if not any(reporting_mandates(request.user, action, version).exists() for action in actions):
        raise PermissionDenied
    reports = [report for report in Report.objects.filter(version=version).select_related('pole', 'prepared_by') if _visible(report, request.user)]
    code = request.GET.get('type', '')
    status = request.GET.get('status', '')
    q = request.GET.get('q', '').strip().casefold()
    if code:
        reports = [r for r in reports if r.report_type == code]
    if status:
        reports = [r for r in reports if r.status == status]
    if q:
        reports = [r for r in reports if q in (r.reference + ' ' + r.title).casefold()]
    return render(request, 'reporting/index.html', {
        'reports': reports, 'types': TYPES, 'families': FAMILIES,
        'can_create': reporting_mandates(request.user, 'rapport.rediger', version).exists(),
        'version': version, 'selected_type': code, 'selected_status': status, 'q': request.GET.get('q', ''),
        'statuses': Report.Status.choices,
    })


@login_required(login_url='/se-connecter/')
def create(request):
    version = active_version()
    require_action(request.user, 'rapport.rediger')
    form = ReportForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        report = form.save(commit=False)
        report.version = version
        report.prepared_by = request.user
        allowed = reporting_mandates(request.user, 'rapport.rediger', version, report.pole, report.report_type,
                                     central_only=not report.pole_id)
        if not allowed.exists():
            raise PermissionDenied
        report.prepared_mandate = allowed.first()
        report.reference = f'RPT-{timezone.localdate():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}'
        report.full_clean()
        report.save()
        _event(report, request.user, 'CREATE', '')
        return redirect('reporting:detail', pk=report.pk)
    return render(request, 'reporting/create.html', {'form': form, 'version': version, 'families': FAMILIES})


@login_required(login_url='/se-connecter/')
def detail(request, pk):
    report = _get_report(pk, request.user)
    keys = fields_for(report.report_type)
    suggestions = source_suggestions(report) if report.status in (Report.Status.DRAFT, Report.Status.RETURNED) else {}
    sections = [(key, LABELS[key], report.fields.get(key, {}), suggestions.get(key)) for key in keys]
    scope = {'central_only': not report.pole_id}
    editable = report.status in (Report.Status.DRAFT, Report.Status.RETURNED) and report.prepared_by_id == request.user.pk and reporting_mandates(request.user, 'rapport.rediger', report.version, report.pole, report.report_type, **scope).exists()
    return render(request, 'reporting/detail.html', {
        'report': report, 'sections': sections, 'missing': missing_fields(report, keys),
        'editable': editable, 'can_review': report.status == Report.Status.SUBMITTED and eligible_reviewer(request.user, report),
        'can_approve': report.status == Report.Status.REVIEWED and eligible_approver(request.user, report),
        'can_transmit': report.status == Report.Status.APPROVED and reporting_mandates(request.user, 'rapport.transmettre', report.version, report.pole, report.report_type, **scope).exists(),
        'can_revise': report.status == Report.Status.APPROVED and report.prepared_by_id == request.user.pk and reporting_mandates(request.user, 'rapport.rediger', report.version, report.pole, report.report_type, **scope).exists(),
        'evidence_form': EvidenceForm(), 'financial_form': FinancialLineForm(report=report),
        'is_financial': TYPES[report.report_type][0] == 'finance', 'type_title': TYPES[report.report_type][1],
        'family': FAMILIES[TYPES[report.report_type][0]],
    })


def _check_revision(report, request):
    try:
        revision = int(request.POST.get('revision', '-1'))
    except ValueError:
        revision = -1
    if revision != report.revision:
        raise ValueError('Le rapport a été modifié. Rechargez la page avant de poursuivre.')


@login_required(login_url='/se-connecter/')
@require_POST
@transaction.atomic
def save_fields(request, pk):
    report = Report.objects.select_for_update().get(pk=pk)
    require_action(request.user, 'rapport.rediger', report)
    if report.status not in (Report.Status.DRAFT, Report.Status.RETURNED):
        raise PermissionDenied
    try:
        _check_revision(report, request)
    except ValueError as exc:
        return HttpResponse(str(exc), status=409)
    suggestions = source_suggestions(report)
    fields = dict(report.fields)
    for key in fields_for(report.report_type):
        mode = request.POST.get(f'mode_{key}', 'manual')
        if mode == 'model' and key in suggestions:
            fields[key] = {'mode': 'model', **suggestions[key]}
        else:
            value = (request.POST.get(f'value_{key}') or '').strip()[:10000]
            reference = (request.POST.get(f'reference_{key}') or '').strip()[:500]
            fields[key] = {'mode': 'manual', 'value': value, 'source': reference, 'at': timezone.now().isoformat(),
                           'author': request.user.get_full_name() or request.user.username}
    old = report.status
    report.fields = fields
    report.reservations = (request.POST.get('reservations') or '').strip()[:10000]
    report.decision_requested = (request.POST.get('decision_requested') or '').strip()[:10000]
    report.revision += 1
    report.save(update_fields=['fields', 'reservations', 'decision_requested', 'revision', 'updated_at'])
    _event(report, request.user, 'SAVE', old)
    return redirect('reporting:detail', pk=pk)


@login_required(login_url='/se-connecter/')
@require_POST
@transaction.atomic
def add_evidence(request, pk):
    report = Report.objects.select_for_update().get(pk=pk)
    require_action(request.user, 'rapport.rediger', report)
    if report.status not in (Report.Status.DRAFT, Report.Status.RETURNED):
        raise PermissionDenied
    form = EvidenceForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseBadRequest(str(form.errors))
    item = form.save(commit=False)
    item.report = report
    item.uploaded_by = request.user
    item.save()
    report.revision += 1
    report.save(update_fields=['revision', 'updated_at'])
    _event(report, request.user, 'EVIDENCE', report.status, item.title)
    return redirect('reporting:detail', pk=pk)


@login_required(login_url='/se-connecter/')
def download_evidence(request, pk):
    from .models import ReportEvidence
    item = get_object_or_404(ReportEvidence.objects.select_related('report'), pk=pk)
    _get_report(item.report_id, request.user)
    if not item.file:
        raise Http404
    return FileResponse(item.file.open('rb'), as_attachment=True, filename=item.file.name.rsplit('/', 1)[-1])


@login_required(login_url='/se-connecter/')
@require_POST
@transaction.atomic
def add_financial_line(request, pk):
    report = Report.objects.select_for_update().get(pk=pk)
    require_action(request.user, 'rapport.rediger', report)
    if report.status not in (Report.Status.DRAFT, Report.Status.RETURNED) or TYPES[report.report_type][0] != 'finance':
        raise PermissionDenied
    form = FinancialLineForm(request.POST, report=report)
    if not form.is_valid():
        return HttpResponseBadRequest(str(form.errors))
    item = form.save(commit=False)
    item.report = report
    item.created_by = request.user
    item.full_clean()
    item.save()
    report.revision += 1
    report.save(update_fields=['revision', 'updated_at'])
    _event(report, request.user, 'FINANCIAL_LINE', report.status, item.need)
    return redirect('reporting:detail', pk=pk)


@login_required(login_url='/se-connecter/')
@require_POST
@transaction.atomic
def transition(request, pk):
    report = Report.objects.select_for_update().get(pk=pk)
    if not _visible(report, request.user):
        raise PermissionDenied
    try:
        _check_revision(report, request)
    except ValueError as exc:
        return HttpResponse(str(exc), status=409)
    action = request.POST.get('action')
    comment = (request.POST.get('comment') or '').strip()[:5000]
    old = report.status
    if action == 'submit' and old in (Report.Status.DRAFT, Report.Status.RETURNED):
        require_action(request.user, 'rapport.rediger', report)
        missing = missing_fields(report, fields_for(report.report_type))
        if missing:
            return HttpResponseBadRequest('Rubriques manquantes : ' + ', '.join(LABELS[k] for k in missing))
        if any(not item.get('source') for item in report.fields.values()):
            return HttpResponseBadRequest('Chaque rubrique doit préciser une source ou une référence vérifiable.')
        if TYPES[report.report_type][0] == 'finance' and not report.financial_lines.exists():
            return HttpResponseBadRequest('Ajouter au moins une ligne financière justifiée.')
        if not report.evidence.exists():
            return HttpResponseBadRequest('Ajouter au moins une pièce ou référence justificative.')
        report.source_snapshot = {'fields': report.fields, 'evidence': list(report.evidence.values('id', 'title', 'source_reference')),
                                  'financial_lines': [{'id': x.pk, 'need': x.need, 'total': str(x.total), 'currency': x.currency,
                                                       'confirmed_funding': str(x.confirmed_funding), 'committed': str(x.committed),
                                                       'liquidated': str(x.liquidated), 'ordered': str(x.ordered), 'paid': str(x.paid)}
                                                      for x in report.financial_lines.all()],
                                  'captured_at': timezone.now().isoformat()}
        report.status = Report.Status.SUBMITTED
        report.submitted_at = timezone.now()
    elif action in ('review', 'return') and old == Report.Status.SUBMITTED and eligible_reviewer(request.user, report):
        if action == 'return' and not comment:
            return HttpResponseBadRequest('Motif de renvoi requis.')
        report.status = Report.Status.REVIEWED if action == 'review' else Report.Status.RETURNED
        report.reviewed_by = request.user
        report.reviewed_at = timezone.now()
    elif action in ('approve', 'reject') and old == Report.Status.REVIEWED and eligible_approver(request.user, report):
        if action == 'reject' and not comment:
            return HttpResponseBadRequest('Motif de rejet requis.')
        report.status = Report.Status.APPROVED if action == 'approve' else Report.Status.REJECTED
        report.approved_by = request.user
        report.approved_at = timezone.now()
        if report.prepared_by_id == request.user.pk:
            comment = ('Approbation par le préparateur. ' + comment).strip()
    elif action == 'transmit' and old == Report.Status.APPROVED:
        require_action(request.user, 'rapport.transmettre', report)
        bordereau = (request.POST.get('bordereau') or '').strip()
        if not bordereau or not comment:
            return HttpResponseBadRequest('Référence du bordereau et commentaire de remise requis.')
        _event(report, request.user, 'TRANSMIT', old, f'{bordereau} · {comment}')
        return redirect('reporting:detail', pk=pk)
    else:
        raise PermissionDenied
    report.revision += 1
    report.save()
    _event(report, request.user, action.upper(), old, comment)
    return redirect('reporting:detail', pk=pk)


@login_required(login_url='/se-connecter/')
@require_POST
@transaction.atomic
def revise(request, pk):
    source = _get_report(pk, request.user)
    require_action(request.user, 'rapport.rediger', source)
    if source.status != Report.Status.APPROVED:
        raise PermissionDenied
    clone = Report.objects.create(
        reference=f'{source.reference}-R{uuid.uuid4().hex[:4].upper()}', report_type=source.report_type,
        title=source.title, version=source.version, pole=source.pole, norme=source.norme,
        supersedes=source,
        sc=source.sc, gt=source.gt, period_start=source.period_start, period_end=source.period_end,
        recipient=source.recipient, prepared_by=request.user,
        prepared_mandate=require_action(request.user, 'rapport.rediger', source),
        fields=source.fields, revision=1,
    )
    _event(clone, request.user, 'REVISE', '', f'Nouvelle version de {source.reference}')
    return redirect('reporting:detail', pk=clone.pk)


@login_required(login_url='/se-connecter/')
def export(request, pk, fmt):
    report = _get_report(pk, request.user)
    if report.status != Report.Status.APPROVED or fmt not in ('pdf', 'docx'):
        raise PermissionDenied
    from .exports import build_pdf, build_docx
    content = build_pdf(report) if fmt == 'pdf' else build_docx(report)
    content_type = 'application/pdf' if fmt == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    response = HttpResponse(content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{report.reference}.{fmt}"'
    return response
