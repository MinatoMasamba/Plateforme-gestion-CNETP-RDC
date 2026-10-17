from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.governance.rapport_adopte_2026 import prepare_adopted_organisation


class Command(BaseCommand):
    help = 'Prépare le référentiel du rapport adopté : 22 COPIL, 24 ST, 7 SC et 35 GT, sans activation.'

    def handle(self, *args, **options):
        try:
            version, counts = prepare_adopted_organisation()
        except ValidationError as error:
            raise CommandError('; '.join(error.messages)) from error
        self.stdout.write(self.style.SUCCESS(f'{version.code} ({version.status}) : {counts}'))
