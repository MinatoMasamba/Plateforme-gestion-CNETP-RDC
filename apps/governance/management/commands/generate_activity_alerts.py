from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from apps.governance.activity_supervision import task_state
from apps.governance.models import ActivityAlert, ActivitySilencePeriod, JustifiedAbsence, Tache


class Command(BaseCommand):
    help = "Prépare les alertes internes graduées pour le prochain résumé."

    def handle(self, *args, **options):
        now, today = timezone.now(), timezone.localdate()
        created = 0
        for task in Tache.objects.select_related('assigned_to').prefetch_related('blocked_by'):
            if ActivitySilencePeriod.objects.filter(starts_at__lte=now, ends_at__gte=now).filter(
                Q(ctm__isnull=True) | Q(ctm=task.working_group.ctm if task.working_group_id else None)
            ).exists():
                continue
            if task.assigned_to_id and JustifiedAbsence.objects.filter(
                expert=task.assigned_to, status='APPROVED', starts_on__lte=today, ends_on__gte=today
            ).exists():
                continue
            state = task_state(task, today)
            if state not in {'BLOCKED', 'LATE'} and task.assigned_to_id:
                continue
            severity = 'ACTION' if state in {'BLOCKED', 'LATE'} else 'WATCH'
            kind = state if state in {'BLOCKED', 'LATE'} else 'UNASSIGNED'
            _, was_created = ActivityAlert.objects.get_or_create(
                task=task, kind=kind, status='OPEN',
                defaults={
                    'severity': severity, 'expert': task.assigned_to, 'norme': task.norme,
                    'message': f'{task.titre} : {"action requise" if severity == "ACTION" else "à surveiller"}.',
                },
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f'{created} nouvelle(s) alerte(s) interne(s).'))
