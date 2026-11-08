from django.core.management.base import BaseCommand
from apps.governance.st_operations import reset_legacy_access


class Command(BaseCommand):
    help = 'Bascule le ST sur les postes v3, sans titulaire ; conserve les anciennes adhésions sans droits.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        if not options['apply']:
            self.stdout.write('Simulation : ajouter --apply pour retirer les anciens accès CTC et sélectionner les postes ST v3.')
            return
        self.stdout.write(str(reset_legacy_access(None)))
