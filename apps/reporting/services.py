"""Droits et sources des rapports, séparés des transitions normatives Phoenix."""
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.utils import timezone

from apps.experts.models import Expert
from apps.governance.models import (
    ActivitySession, CTCProcessus, GroupeCible, HabilitationAction,
    MandatOrganisation, OrganisationVersion, Tache,
)
from apps.norms.models import Norme, NormeVersion
from apps.validation.models import (
    EcologicalReview, EconomicReview, IndustrialConsultation, ISOReview,
    LegisticReview, ScheduleReview,
)

REPORT_ACTIONS = ('rapport.consulter', 'rapport.rediger', 'rapport.controler', 'rapport.approuver', 'rapport.transmettre')


def active_version():
    return OrganisationVersion.objects.filter(status='ACTIVE').first()


def reporting_mandates(user, action, version=None, pole=None, report_type=None, central_only=False):
    """Seuls mandat ST actif et habilitation explicite donnent un droit de rapport."""
    if not user.is_authenticated or not user.is_active or action not in REPORT_ACTIONS:
        return MandatOrganisation.objects.none()
    version = version or active_version()
    if not version or version.status != 'ACTIVE':
        return MandatOrganisation.objects.none()
    today = timezone.localdate()
    grants = HabilitationAction.objects.filter(
        action=action, enabled=True, perimeter__version=version, delegated_from__isnull=True,
        start_date__lte=today,
    ).filter(Q(end_date__isnull=True) | Q(end_date__gte=today)).exclude(decision_reference='')
    if report_type:
        grants = grants.filter(report_types__report_type=report_type, report_types__enabled=True)
    if central_only:
        grants = grants.filter(perimeter__type='ST')
    elif pole:
        grants = grants.filter(Q(perimeter=pole) | Q(perimeter__type='ST'))
    return MandatOrganisation.objects.filter(
        expert__user=user, expert__status='ACTIVE', poste__organe__version=version,
        poste__organe__type__in=['ST', 'ST_POLE'], capacity='ORGANISATION',
        status='ACTIVE', start_date__lte=today, habilitations__in=grants,
    ).filter(Q(end_date__isnull=True) | Q(end_date__gte=today)).exclude(appointment_reference='').distinct()


def require_action(user, action, report=None):
    version = report.version if report else active_version()
    pole = report.pole if report else None
    mandates = reporting_mandates(user, action, version, pole, report.report_type if report else None,
                                 central_only=bool(report and not report.pole_id))
    if report and action == 'rapport.rediger' and report.prepared_by_id != user.pk:
        raise PermissionDenied('Seul le préparateur peut modifier ce rapport.')
    mandate = mandates.first()
    if mandate is None:
        raise PermissionDenied('Mandat et habilitation de rapport en vigueur requis.')
    return mandate


def eligible_reviewer(user, report):
    mandates = reporting_mandates(user, 'rapport.controler', report.version, report.pole, report.report_type,
                                 central_only=not report.pole_id)
    if report.prepared_by_id == user.pk:
        return False
    return mandates.filter(poste__category='POLE_HEAD').exists()


def eligible_approver(user, report):
    return reporting_mandates(user, 'rapport.approuver', report.version, report.pole, report.report_type,
                             central_only=not report.pole_id).filter(
        poste__code='ST-COORD-01'
    ).exists()


def source_suggestions(report):
    """Valeurs candidates affichées avec provenance ; rien n'est assimilé à une validation."""
    result = {}
    norm = report.norme
    if norm:
        result['objet'] = {'value': f'{norm.reference_number} — {norm.title}', 'source': f'Norme #{norm.pk}', 'at': norm.updated_at.isoformat()}
        result['normes'] = {'value': f'{norm.reference_number} — {norm.get_status_display()} ({norm.get_circuit_version_display()})', 'source': f'Norme #{norm.pk}', 'at': norm.updated_at.isoformat()}
        versions = NormeVersion.all_objects.filter(norme=norm).select_related('version_author').order_by('-version_number')[:30]
        result['versions'] = {
            'value': '\n'.join(f'v{v.version_number} · {v.created_at:%d/%m/%Y} · {v.version_author or "auteur non enregistré"} · {v.summary or "résumé absent"}' for v in versions) or 'Aucune version enregistrée',
            'source': f'NormeVersion norme #{norm.pk}', 'at': timezone.now().isoformat(),
        }
        process = CTCProcessus.objects.filter(norme=norm).select_related('received_by').first()
        if process:
            received = process.received_at.isoformat() if process.received_at else 'Réception non enregistrée'
            result['origine'] = {'value': f'CTM historique : {norm.ctm or "non renseigné"}\nRéception : {received}\nÉtape CTC : {process.get_current_stage_display()}', 'source': f'CTCProcessus #{process.pk}', 'at': process.updated_at.isoformat()}
            result['transmission'] = {'value': f'Transmission : {process.transmitted_to_pilotage_at.isoformat() if process.transmitted_to_pilotage_at else "non enregistrée"}', 'source': f'CTCProcessus #{process.pk}', 'at': process.updated_at.isoformat()}
        review_models = (ISOReview, LegisticReview, EcologicalReview, EconomicReview, ScheduleReview, IndustrialConsultation)
        reviews = []
        for model in review_models:
            item = model.objects.filter(norme=norm).first()
            if item:
                reviews.append(f'{model._meta.verbose_name} : {getattr(item, "status", "à vérifier")} · début {item.review_start_date or "non indiqué"} · fin {item.review_end_date or "non indiquée"}')
        result['examens'] = {'value': '\n'.join(reviews) or 'Aucun examen enregistré', 'source': f'Revues norme #{norm.pk}', 'at': timezone.now().isoformat()}
        tasks = Tache.objects.filter(norme=norm).select_related('assigned_to')
        result['prochaines_actions'] = {'value': '\n'.join(f'{t.titre} · {t.get_status_display()} · {t.due_date or "sans échéance"}' for t in tasks) or 'Aucune tâche enregistrée', 'source': f'Tache norme #{norm.pk}', 'at': timezone.now().isoformat()}
    if report.sc:
        groups = GroupeCible.objects.filter(sc=report.sc).order_by('code')
        result['groupes'] = {'value': '\n'.join(f'{g.code} — {g.name} ({g.get_status_display()})' for g in groups) or 'Aucun GT enregistré', 'source': f'GroupeCible SC #{report.sc_id}', 'at': timezone.now().isoformat()}
    if report.report_type in {'M3', 'P4', 'ITP-01', 'ITP-04'}:
        experts = Expert.objects.filter(user__is_staff=False, user__is_superuser=False)
        sessions = ActivitySession.objects.filter(user__in=experts.values('user_id'), started_at__date__gte=report.period_start, started_at__date__lte=report.period_end)
        minutes = (sessions.aggregate(n=Sum('active_seconds'))['n'] or 0) // 60
        result['activite'] = {'value': f'{experts.count()} profils experts hors administration ; {sessions.values("user_id").distinct().count()} personnes avec session mesurée sur la période ; {minutes} minutes actives mesurées. Les connexions et minutes ne prouvent pas une production.', 'source': 'Expert + ActivitySession', 'at': timezone.now().isoformat()}
    if report.report_type in {'M1', 'M2', 'C2', 'ITP-02'} and 'normes' not in result:
        norms = Norme.all_objects.all()
        result['normes'] = {'value': f'{norms.count()} projets enregistrés ; {NormeVersion.all_objects.count()} versions enregistrées. Période des créations à préciser.', 'source': 'Norme + NormeVersion', 'at': timezone.now().isoformat()}
    return result


def field_value(item):
    return (item or {}).get('value', '').strip()


def missing_fields(report, keys):
    return [key for key in keys if not field_value(report.fields.get(key))]
