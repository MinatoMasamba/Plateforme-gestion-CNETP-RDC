from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.governance.phoenix_expert_migration import rollback_expert_migration


class Command(BaseCommand):
    help = 'Clôture un lot de rattachement SC sans supprimer son historique.'

    def add_arguments(self, parser):
        parser.add_argument('--batch', required=True)
        parser.add_argument('--reason', required=True)
        parser.add_argument('--effective-date')
        parser.add_argument('--code', default='phoenix-2026-10')

    def handle(self, *args, **options):
        try:
            report = rollback_expert_migration(
                options['batch'], options['reason'], code=options['code'],
                effective_date=options.get('effective_date'),
            )
        except ValidationError as error:
            raise CommandError('; '.join(error.messages)) from error
        self.stdout.write(self.style.SUCCESS(
            f'Lot {report["batch_reference"]} clôturé : {report["closed"]} rattachement(s) conservé(s).'
        ))
