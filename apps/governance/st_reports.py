import copy
from datetime import date
import uuid
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .st_operations import actor_mandate, writable
from .st_report_models import STReport, STReportTemplate, STReportVersion, validate_report_sections
from .models import JournalMigration


def visible_reports(user):
    qs = STReport.objects.select_related('owner', 'template').prefetch_related('versions')
    if user.is_staff and user.has_perm('governance.view_streport'):
        return qs
    try:
        mandate = actor_mandate(user)
    except PermissionDenied:
        return qs.filter(owner=user)
    if mandate.poste.st_sub_role in ('coordonnateur_principal', 'coordonnateur_adjoint'):
        return qs
    if mandate.poste.category == 'POLE_HEAD':
        return qs.filter(Q(owner=user) | Q(pole_code=mandate.poste.organe.code))
    return qs.filter(owner=user)


def editor_mandate(user, report=None):
    mandate = actor_mandate(user)
    if report and (report.pole_code != mandate.poste.organe.code or (report.owner_id != user.pk and mandate.poste.category != 'POLE_HEAD')):
        raise PermissionDenied('Modification réservée à l’auteur ou au chef du pôle concerné.')
    return mandate


@transaction.atomic
def save_report(user, data, report_id=None):
    writable()
    report = get_object_or_404(visible_reports(user).select_for_update(), pk=report_id) if report_id else None
    mandate = editor_mandate(user, report)
    if report and data.get('revision') != report.revision:
        raise ValidationError('Révision obsolète ; recharger le rapport.', code='conflict')
    title = str(data.get('title', '')).strip()
    if not title or len(title) > 250:
        raise ValidationError('Titre requis, limité à 250 caractères.')
    sections = data.get('sections')
    template = None
    if data.get('template_id'):
        template = get_object_or_404(STReportTemplate, pk=data['template_id'])
    if sections is None and template:
        sections = copy.deepcopy(template.sections)
    validate_report_sections(sections)
    start, end = data.get('period_start'), data.get('period_end')
    try:
        start = date.fromisoformat(start) if isinstance(start, str) else start
        end = date.fromisoformat(end) if isinstance(end, str) else end
    except ValueError:
        raise ValidationError('Dates au format AAAA-MM-JJ attendues.')
    if start and end and start > end:
        raise ValidationError('La fin de période doit suivre le début.')
    if not report:
        report = STReport.objects.create(owner=user, pole_code=mandate.poste.organe.code, template=template,
            reference='RAP-ST-' + uuid.uuid4().hex[:12].upper())
    version = STReportVersion(report=report, number=report.revision + 1, title=title,
        sections=copy.deepcopy(sections), period_start=start, period_end=end, author=user,
        author_name=user.get_full_name() or user.username, mandate=mandate)
    version.full_clean()
    version.save()
    report.revision = version.number
    report.save(update_fields=['revision', 'updated_at'])
    if hasattr(report, '_prefetched_objects_cache'):
        report._prefetched_objects_cache.pop('versions', None)
    JournalMigration.objects.create(version=mandate.organisation_version, actor=user, actor_name=version.author_name,
        mandate=mandate, operation='ST_REPORT_SAVE', target=f'st-report:{report.pk}',
        after={'revision': version.number}, reason=title)
    return report


def get_report_version(user, report_id, number=None):
    report = get_object_or_404(visible_reports(user), pk=report_id)
    return get_object_or_404(report.versions.select_related('report', 'author'), number=number or report.revision)


def create_report_template(user, name, sections):
    actor_mandate(user)
    writable()
    validate_report_sections(sections)
    template = STReportTemplate(name=name, sections=copy.deepcopy(sections), creator=user)
    template.full_clean()
    template.save()
    return template
