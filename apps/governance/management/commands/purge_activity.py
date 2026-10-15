from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.governance.models import ActivityAggregate, ActivitySession


class Command(BaseCommand):
    help = "Applique les durées de conservation des sessions et agrégats."

    def handle(self, *args, **options):
        today = timezone.localdate()
        session_cutoff = timezone.now() - timedelta(days=365)
        monthly_cutoff = today - timedelta(days=3 * 365)
        sessions, _ = ActivitySession.objects.filter(last_seen_at__lt=session_cutoff).delete()
        aggregates, _ = ActivityAggregate.objects.filter(period_type='MONTH', period_start__lt=monthly_cutoff).delete()
        # Les agrégats journaliers ne sont utiles que durant la période de détail.
        daily, _ = ActivityAggregate.objects.filter(period_type='DAY', period_start__lt=session_cutoff.date()).delete()
        self.stdout.write(self.style.SUCCESS(f'{sessions} détail(s) de session et {aggregates + daily} agrégat(s) arrivés à échéance supprimés.'))
