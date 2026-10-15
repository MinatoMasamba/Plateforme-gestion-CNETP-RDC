from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from apps.governance.phoenix_services import seed_phoenix


class Command(BaseCommand):
    help = 'Prépare idempotemment Phoenix : COPIL 22, ST 24, 7 SC et correspondances, sans réaffectation ni activation.'

    def add_arguments(self, parser):
        parser.add_argument('--code', default='phoenix-2026-10')

    def handle(self, *args, **options):
        try:
            version, missing = seed_phoenix(options['code'])
        except ValidationError as error:
            raise CommandError('; '.join(error.messages)) from error
        self.stdout.write(self.style.SUCCESS(f'{version.name} : proposée ; 22 postes COPIL, 24 postes ST, 7 SC ; aucun GT ou mandat créé.'))
        if missing:
            self.stdout.write(self.style.WARNING('Sources historiques absentes : ' + ', '.join(missing)))
