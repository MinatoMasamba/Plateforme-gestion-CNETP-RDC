"""Notifie les titulaires des postes de bureau des SC de leur affectation."""

from django.core.management.base import BaseCommand, CommandError

from apps.governance.models import MandatOrganisation
from apps.governance.nomination_notifications import _send_sc_nomination_mail


class Command(BaseCommand):
    help = (
        "Envoie la notification officielle d'enregistrement de fonction aux titulaires "
        "des postes de bureau des sous-commissions (lien vers leur SC)."
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help="Affiche sans envoyer.")
        parser.add_argument('--sc', default='', help="Limiter à un code de sous-commission (ex. SC-SOCLE).")
        parser.add_argument('--email', action='append', default=[], help="Limiter à une ou plusieurs adresses.")
        parser.add_argument('--limit', type=int, default=0, help="Limiter le nombre d'envois.")

    def handle(self, *args, **options):
        mandats = (
            MandatOrganisation.objects
            .filter(
                status='ACTIVE',
                capacity='ORGANISATION',
                poste__isnull=False,
                poste__organe__type='SC',
            )
            .select_related('expert__user', 'poste__organe', 'groupe')
            .order_by('poste__organe__code', 'poste__code')
        )
        if options['sc']:
            mandats = mandats.filter(poste__organe__code=options['sc'])
        if options['email']:
            mandats = mandats.filter(expert__user__email__in=options['email'])
        mandats = list(mandats)
        if options['limit']:
            mandats = mandats[:options['limit']]

        if not mandats:
            raise CommandError("Aucun mandat actif de bureau SC ne correspond aux critères.")

        for mandat in mandats:
            organ = mandat.poste.organe
            title = mandat.poste.title or mandat.function
            email = mandat.expert.user.email
            self.stdout.write(
                f"- {mandat.expert.full_name or mandat.expert.user.username} | "
                f"{title} | {organ.code} | {email or 'sans email'}"
            )
            if not options['dry_run'] and email:
                _send_sc_nomination_mail(mandat.expert_id, mandat, organ, title)

        if options['dry_run']:
            self.stdout.write(self.style.WARNING("Dry-run : aucun email envoyé."))
        else:
            self.stdout.write(self.style.SUCCESS(f"{len(mandats)} notification(s) traitée(s)."))
