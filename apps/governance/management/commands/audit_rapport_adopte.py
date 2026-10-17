"""Audit en lecture seule des propositions nominatives du rapport adopté."""

import json
import unicodedata
from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.experts.models import Expert
from apps.governance.models import AffectationSousCommission, MandatOrganisation, OrganisationVersion


def normalize_name(value):
    decomposed = unicodedata.normalize('NFKD', value.casefold())
    return ''.join(char for char in decomposed if char.isalnum() and not unicodedata.combining(char))


class Command(BaseCommand):
    help = 'Compare sans écriture les propositions nominatives du rapport et les experts de la base.'

    def handle(self, *args, **options):
        catalogue = json.loads(Path(__file__).resolve().parents[2].joinpath('rapport_adopte_2026_reference.json').read_text(encoding='utf-8'))
        experts = list(Expert.objects.select_related('user').order_by('pk'))
        by_name = defaultdict(set)
        for expert in experts:
            user = expert.user
            for name in (f'{user.first_name} {user.last_name}', f'{user.last_name} {user.first_name}'):
                by_name[normalize_name(name)].add(expert.pk)
        proposals = []
        matched_sc = defaultdict(set)
        for sc in catalogue['sc']:
            for person in sc['expert_proposals']:
                ids = sorted(by_name.get(normalize_name(person['name']), set()))
                proposals.append((sc['code'], ids))
                if len(ids) == 1:
                    matched_sc[ids[0]].add(sc['code'])
        version = OrganisationVersion.objects.get(code=catalogue['version_code'])
        duplicate_names = defaultdict(set)
        for expert in experts:
            user = expert.user
            duplicate_names[normalize_name(f'{user.first_name} {user.last_name}')].add(expert.pk)
        counts = {
            'database_expert_rows': len(experts),
            'database_duplicate_name_groups': sum(len(ids) > 1 for ids in duplicate_names.values()),
            'report_proposal_rows': len(proposals),
            'proposal_exact_unique_matches': sum(len(ids) == 1 for _, ids in proposals),
            'proposal_no_exact_match': sum(len(ids) == 0 for _, ids in proposals),
            'proposal_duplicate_name_matches': sum(len(ids) > 1 for _, ids in proposals),
            'matched_distinct_experts': len(matched_sc),
            'matched_experts_in_multiple_sc': sum(len(codes) > 1 for codes in matched_sc.values()),
            'single_sc_candidates_for_review': sum(len(codes) == 1 for codes in matched_sc.values()),
            'adopted_version_assignments': AffectationSousCommission.objects.filter(version=version).count(),
            'new_mandates': MandatOrganisation.objects.filter(
                Q(poste__organe__version=version) | Q(groupe__sc__version=version)
            ).distinct().count(),
        }
        self.stdout.write(json.dumps(counts, ensure_ascii=False, indent=2))
