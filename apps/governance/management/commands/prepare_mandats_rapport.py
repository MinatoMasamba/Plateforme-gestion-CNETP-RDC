"""Prépare les fonctions nominatives de l'annexe sans les activer."""

import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.experts.models import Expert
from apps.governance.models import JournalMigration, MandatOrganisation, OrganisationVersion, PosteOrganisation


def normalize_name(value):
    value = unicodedata.normalize('NFKD', value.casefold())
    return ''.join(char for char in value if char.isalnum() and not unicodedata.combining(char))


class Command(BaseCommand):
    help = 'Crée uniquement des mandats proposés pour les noms uniques de l’annexe 1, sans habilitation.'

    @transaction.atomic
    def handle(self, *args, **options):
        catalogue = json.loads(Path(__file__).resolve().parents[2].joinpath('rapport_adopte_2026_reference.json').read_text(encoding='utf-8'))
        version = OrganisationVersion.objects.select_for_update().get(code=catalogue['version_code'])
        if version.status != OrganisationVersion.Status.PROPOSED:
            raise ValueError('Les propositions ne peuvent être préparées que dans une version non activée.')
        by_name = defaultdict(set)
        for expert in Expert.objects.select_related('user'):
            user = expert.user
            for name in (f'{user.first_name} {user.last_name}', f'{user.last_name} {user.first_name}'):
                by_name[normalize_name(name)].add(expert.pk)
        stats = Counter()
        for sc in catalogue['sc']:
            for number, bureau in enumerate(sc['bureau_posts'], start=1):
                if not bureau['holder_name']:
                    stats['poste_sans_nom'] += 1
                    continue
                matches = by_name.get(normalize_name(bureau['holder_name']), set())
                if len(matches) != 1:
                    stats['nom_absent' if not matches else 'nom_ambigu'] += 1
                    continue
                poste = PosteOrganisation.objects.get(
                    organe__version=version, organe__code=sc['code'],
                    code=f"{sc['code']}-BUREAU-{number:02d}",
                )
                expert_id = next(iter(matches))
                existing = list(MandatOrganisation.objects.filter(poste=poste))
                if existing:
                    if len(existing) != 1 or existing[0].expert_id != expert_id or existing[0].status != 'PROPOSED':
                        stats['poste_a_reexaminer'] += 1
                        continue
                else:
                    MandatOrganisation.objects.create(
                        poste=poste, expert_id=expert_id, function=bureau['role'],
                        capacity='ORGANISATION', status='PROPOSED',
                    )
                stats['mandats_proposes'] += 1
        if not JournalMigration.objects.filter(version=version, operation='PREPARE_ANNEXE_ROLES').exists():
            JournalMigration.objects.create(
                version=version, actor_name='Commande de préparation', operation='PREPARE_ANNEXE_ROLES',
                target=version.code, after={**stats, 'active_mandates': 0, 'rights_created': 0},
                reason='Correspondance nominative exacte et unique avec l’annexe 1 ; propositions sans effet sur les droits.',
            )
        self.stdout.write(json.dumps(stats, ensure_ascii=False, indent=2))
