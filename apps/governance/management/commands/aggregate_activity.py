from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from apps.governance.activity_supervision import aggregate_activity_day, close_stale_sessions
from apps.governance.models import ActivityAggregate


class Command(BaseCommand):
    help = "Recalcule les agrégats d'activité sans reconstruire les anciennes durées."

    def add_arguments(self, parser):
        parser.add_argument('--date', dest='day')

    def handle(self, *args, **options):
        day = date.fromisoformat(options['day']) if options.get('day') else timezone.localdate()
        closed = close_stale_sessions()
        count = aggregate_activity_day(day)
        month_start = day.replace(day=1)
        daily = ActivityAggregate.objects.filter(period_type='DAY', period_start__gte=month_start, period_start__lte=day)
        for user_id in daily.values_list('user_id', flat=True).distinct():
            totals = daily.filter(user_id=user_id).aggregate(
                active=Sum('active_seconds'), declared=Sum('declared_seconds'), sources=Sum('source_count')
            )
            ActivityAggregate.objects.update_or_create(
                period_type='MONTH', period_start=month_start, user_id=user_id,
                ctm=None, working_group=None, target_group=None,
                defaults={'active_seconds': totals['active'] or 0, 'declared_seconds': totals['declared'] or 0, 'source_count': totals['sources'] or 0},
            )
        self.stdout.write(self.style.SUCCESS(f'{count} agrégat(s) journalier(s), {closed} session(s) clôturée(s).'))
