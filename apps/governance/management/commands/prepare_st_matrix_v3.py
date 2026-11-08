from django.core.management.base import BaseCommand
from apps.governance.st_matrix import prepare_matrix


class Command(BaseCommand):
    help = 'Prépare les 19 postes ST v3 sans activer de compte ni remplacer la version en service.'

    def handle(self, *args, **options):
        version = prepare_matrix()
        self.stdout.write(self.style.SUCCESS(
            f'{version.code} : 19 postes ; aucun compte activé.'
        ))
