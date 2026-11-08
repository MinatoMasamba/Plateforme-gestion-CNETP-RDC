from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import User
from apps.governance.models import CTCMembership
from apps.governance.phoenix_runtime import active_st_mandate


class Command(BaseCommand):
    help = (
        "Réactive les adhésions CTC historiques des experts actifs qui n'ont pas "
        "de mandat ST v3 ; l'accès /ctc/ est alors immédiatement rouvert."
    )

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        candidates = [
            membership
            for membership in CTCMembership.all_objects.filter(
                is_active=False,
                expert__status='ACTIVE',
                expert__user__is_active=True,
            ).select_related('expert__user')
            if not active_st_mandate(membership.expert)
        ]
        user_ids = {membership.expert.user_id for membership in candidates}

        if not options['apply']:
            self.stdout.write(
                f'Simulation : {len(candidates)} adhésion(s) seraient réactivées. '
                'Ajouter --apply pour appliquer.'
            )
            return

        for membership in candidates:
            membership.is_active = True
            membership.save(update_fields=['is_active', 'updated_at'])
        User.objects.filter(pk__in=user_ids).update(is_ctc_staff=True)
        self.stdout.write(self.style.SUCCESS(
            f'{len(candidates)} adhésion(s) CTC réactivée(s), '
            f'{len(user_ids)} compte(s) marqué(s) CTC.'
        ))
