"""Résolution dynamique de la version d'organisation à afficher ou utiliser."""

from .phoenix_models import OrganisationVersion


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
