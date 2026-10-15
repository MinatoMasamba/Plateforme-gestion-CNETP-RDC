from django.core.management.base import BaseCommand, CommandError
from apps.governance.phoenix_backup import prepare_backup


class Command(BaseCommand):
    help = 'Sauvegarde la base SQLite et les médias locaux, puis vérifie leur restauration isolée.'

    def handle(self, *args, **options):
        try:
            destination = prepare_backup()
        except ValueError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(f'Sauvegarde et restauration vérifiées : {destination}'))
