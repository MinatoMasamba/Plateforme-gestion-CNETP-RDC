"""Périmètres de lecture partagés par le web et l'API ST v3."""
from django.db.models import Q
from django.utils import timezone


def effective_mandates(context):
    from .models import MandatOrganisation
    today = timezone.localdate()
    poste = context.get('poste')
    qs = MandatOrganisation.objects.filter(
        status='ACTIVE', capacity='ORGANISATION', expert__status='ACTIVE',
        expert__user__is_active=True,
    ).filter(Q(start_date__isnull=True) | Q(start_date__lte=today)).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today))
    return qs.filter(poste__organe__version_id=poste.organe.version_id) if poste else qs.none()


def visible_tasks(expert, context):
    from .models import Tache
    qs = Tache.objects.all()
    if context.get('st_is_supervisor'):
        mandates = effective_mandates(context)
        if context.get('ctc_pole') != 'ST':
            mandates = mandates.filter(poste__organe__code=context.get('ctc_pole'))
        ids = mandates.values_list('expert_id', flat=True)
        return qs.filter(Q(assigned_to_id__in=ids) | Q(backup_assignee_id__in=ids)).distinct()
    return qs.filter(Q(assigned_to=expert) | Q(backup_assignee=expert)).distinct()


def visible_processus(expert, context):
    from .models import CTCProcessus
    qs = CTCProcessus.objects.select_related('norme', 'norme__ctm').order_by('-updated_at')
    code = context.get('st_post_code', '')
    if code in ('ST-V3-01', 'ST-V3-02', 'ST-V3-03', 'ST-V3-04', 'ST-V3-05', 'ST-V3-08'):
        return qs
    if code == 'ST-V3-06':
        return qs.filter(current_stage='RECEPTION')
    if code == 'ST-V3-10':
        return qs.filter(current_stage__in=['RECEPTION', 'GEOSPATIAL', 'MULTI_REVIEW'])
    if code == 'ST-V3-11':
        return qs.filter(current_stage='RECEPTION', sc_report_received_at__isnull=False)
    if code in ('ST-V3-13', 'ST-V3-14'):
        return qs.filter(current_stage__in=['MULTI_REVIEW', 'INDUSTRIAL'])
    return qs.filter(norme_id__in=visible_tasks(expert, context).values('norme_id'))


def visible_meetings(expert, context):
    from apps.meetings.models import Reunion
    qs = Reunion.objects.exclude(status='CANCELLED')
    own = Q(organisateur=expert) | Q(participants__expert=expert)
    if context.get('st_post_code') in ('ST-V3-01', 'ST-V3-02', 'ST-V3-03', 'ST-V3-04', 'ST-V3-05', 'ST-V3-06', 'ST-V3-07'):
        own |= Q(type='CTC')
    elif context.get('st_is_pole_head'):
        ids = effective_mandates(context).filter(
            poste__organe__code=context.get('ctc_pole')).values('expert_id')
        own |= Q(organisateur_id__in=ids)
    return qs.filter(own).distinct().order_by('date')


def visible_st_journal(mandate):
    """Lecture de supervision. L'auteur conserve son historique personnel.

    Le mandat enregistré sur l'événement fait foi, jamais le poste actuel de
    l'auteur. Cette lecture n'accorde aucun droit de contrôle indépendant.
    """
    from .models import JournalMigration
    post = mandate.poste
    own = Q(actor_id=mandate.expert.user_id)
    scope = own
    if post.category == 'POLE_HEAD':
        scope |= Q(mandate__poste__organe__code=post.organe.code)
    if post.code in ('ST-V3-01', 'ST-V3-02', 'ST-V3-03', 'ST-V3-04', 'ST-V3-05'):
        scope |= Q(mandate__poste__organe__code='ST') | Q(mandate__poste__category='POLE_HEAD')
    if post.code in ('ST-V3-13', 'ST-V3-14'):
        scope |= Q(mandate__poste__organe__code='ST') | Q(mandate__poste__code='ST-V3-18')
    return JournalMigration.objects.filter(version=mandate.organisation_version).filter(scope)
