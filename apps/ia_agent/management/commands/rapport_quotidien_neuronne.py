"""Commande de repli cron pour le rapport quotidien Neuronne."""
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.ia_agent.services.neuronne_admin import send_daily_report


class Command(BaseCommand):
    help = 'Génère et envoie le rapport quotidien des actions Neuronne.'

    def add_arguments(self, parser):
        parser.add_argument('--date', help='Date AAAA-MM-JJ (défaut : aujourd’hui).')

    def handle(self, *args, **options):
        day = options.get('date')
        if day:
            try:
                day = date.fromisoformat(day)
            except ValueError:
                raise CommandError('Date invalide ; format AAAA-MM-JJ attendu.')
        result = send_daily_report(day=day)
        self.stdout.write(self.style.SUCCESS(str(result)))
