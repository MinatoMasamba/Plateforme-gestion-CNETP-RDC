"""Active durablement le mode WAL sur la base SQLite locale/production."""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Active le journal WAL et vérifie les réglages SQLite de concurrence."

    def handle(self, *args, **options):
        if connection.vendor != 'sqlite':
            self.stdout.write(
                self.style.WARNING(
                    f"Base '{connection.vendor}' détectée : cette commande ne concerne que SQLite."
                )
            )
            return

        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode=WAL;')
            journal_mode = cursor.fetchone()[0]
            cursor.execute('PRAGMA synchronous=NORMAL;')
            cursor.execute('PRAGMA busy_timeout=30000;')

        self.stdout.write(
            self.style.SUCCESS(f"SQLite configurée : journal_mode={journal_mode}, busy_timeout=30000 ms.")
        )
