"""Statistiques documentaires, distinctes des nominations et affectations."""
from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from apps.experts.models import Expert, ProfileUpdate
from apps.governance.models import AffectationSousCommission, ChoixOrganisationExpert


class Command(BaseCommand):
    help = 'Afficher le suivi des profils sans inférer leur conformité du CV ou des dates de modification.'

    def handle(self, *args, **options):
        total = Expert.objects.count()
        states = dict(ProfileUpdate.objects.values_list('status').annotate(total=Count('pk')))
        self.stdout.write(f'Experts : {total}')
        self.stdout.write(f'Comptes actifs : {Expert.objects.filter(user__is_active=True).count()}')
        self.stdout.write(f'Profils NOT_STARTED : {total - ProfileUpdate.objects.exclude(status="NOT_STARTED").count()}')
        for status, _ in ProfileUpdate.Status.choices:
            if status != 'NOT_STARTED':
                self.stdout.write(f'Profils {status} : {states.get(status, 0)}')
        self.stdout.write(f'CV présents : {Expert.objects.exclude(Q(cv="") | Q(cv__isnull=True)).count()}')
        self.stdout.write(f'Experts avec choix SC : {ChoixOrganisationExpert.objects.values("expert_id").distinct().count()}')
        self.stdout.write(f'Experts avec affectation migrée : {AffectationSousCommission.objects.filter(status="MIGRATED").values("expert_id").distinct().count()}')
        self.stdout.write('Affectations approuvées : non représentées par un statut explicite dans ce modèle')
