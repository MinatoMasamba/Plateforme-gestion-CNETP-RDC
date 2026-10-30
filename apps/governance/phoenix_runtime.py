"""Résolution dynamique de la version d'organisation à afficher ou utiliser."""

from django.db.models import Q
from django.utils import timezone

from .phoenix_models import MandatOrganisation, Organe, OrganisationVersion, PosteOrganisation

ST_ORGANE_TYPES = (Organe.Type.ST, Organe.Type.ST_POLE)


def current_organisation_version():
    """Retourne la version active, sinon la plus récente proposée ou validée.

    Aucun code de version n'est figé : le référentiel est toujours lu en base.
    """
    return (
        OrganisationVersion.objects.filter(
            status=OrganisationVersion.Status.ACTIVE,
        ).order_by('-created_at', '-id').first()
        or OrganisationVersion.objects.filter(
            status__in=[
                OrganisationVersion.Status.PROPOSED,
                OrganisationVersion.Status.VALIDATED,
            ],
        ).order_by('-created_at', '-id').first()
    )


def st_posts(version=None):
    """Les 24 postes de la Coordination du Secrétariat technique (4 + 5 × 4)."""
    version = version or current_organisation_version()
    if not version:
        return PosteOrganisation.objects.none()
    return (
        PosteOrganisation.objects.filter(
            organe__version=version, organe__type__in=ST_ORGANE_TYPES,
        )
        .select_related('organe')
        .order_by('organe__code', 'code')
    )


def active_st_mandate(expert, version=None):
    """Mandat en cours d'un expert sur un poste de la Coordination du ST."""
    version = version or current_organisation_version()
    if not version:
        return None
    today = timezone.localdate()
    return (
        MandatOrganisation.objects.filter(
            expert=expert,
            poste__organe__version=version,
            poste__organe__type__in=ST_ORGANE_TYPES,
            capacity='ORGANISATION',
            status='ACTIVE',
        )
        .filter(Q(start_date__isnull=True) | Q(start_date__lte=today))
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
        .select_related('poste__organe')
        .order_by('-start_date', '-pk')
        .first()
    )
