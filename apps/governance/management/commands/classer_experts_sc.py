"""Classe les experts cités dans l'annexe 1 du rapport adopté dans les SC.

La commande utilise la base du projet (aucun chemin source externe) et crée
uniquement des propositions au statut « À examiner » : elle ne crée aucun
mandat, aucune habilitation et ne modifie pas les affectations historiques.
"""

import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.experts.models import Expert
from apps.governance.models import JournalMigration, OrganisationVersion, Organe
from apps.governance.phoenix_models import AffectationSousCommission


CATALOGUE = Path(__file__).resolve().parents[2] / 'rapport_adopte_2026_reference.json'
BATCH_REFERENCE = 'RAPPORT-ADOPTE-2026-10-15'


def normalize_name(value):
    decomposed = unicodedata.normalize('NFKD', value.casefold())
    return ''.join(char for char in decomposed if char.isalnum() and not unicodedata.combining(char))


class Command(BaseCommand):
    help = (
        "Classe les experts de l'annexe 1 du rapport adopté dans les SC, "
        "en propositions à examiner (dry-run par défaut)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help="Enregistre les propositions ; sans ce drapeau, affiche seulement le plan.",
        )
        parser.add_argument(
            '--code', default=None,
            help="Code de la version d'organisation (défaut : la plus récente).",
        )

    def handle(self, *args, **options):
        catalogue = json.loads(CATALOGUE.read_text(encoding='utf-8'))
        version = (
            OrganisationVersion.objects.filter(code=options['code']).first()
            if options.get('code') else
            OrganisationVersion.objects.order_by('-created_at', '-id').first()
        )
        if not version:
            raise CommandError("Aucune version d'organisation enregistrée.")
        if version.status not in ('PROPOSED', 'VALIDATED'):
            raise CommandError("La version doit être au statut Proposée ou Validée.")

        version_code = version.code
        sc_par_code = {
            sc.code: sc
            for sc in Organe.objects.filter(version=version, type=Organe.Type.SC)
        }
        by_name = defaultdict(set)
        for expert in Expert.objects.select_related('user'):
            user = expert.user
            for name in (f'{user.first_name} {user.last_name}', f'{user.last_name} {user.first_name}'):
                by_name[normalize_name(name)].add(expert.pk)

        stats = Counter()
        details = []
        rows = []
        for sc_item in catalogue['sc']:
            sc = sc_par_code.get(sc_item['code'])
            if not sc:
                stats['sc_absente'] += 1
                continue
            for person in sc_item['expert_proposals']:
                matches = sorted(by_name.get(normalize_name(person['name']), set()))
                if not matches:
                    stats['nom_absent'] += 1
                    details.append({'sc': sc_item['code'], 'nom': person['name'], 'etat': 'nom absent'})
                    continue
                if len(matches) > 1:
                    stats['nom_ambigu'] += 1
                    details.append({'sc': sc_item['code'], 'nom': person['name'], 'etat': 'nom ambigu', 'expert_ids': matches})
                    continue
                expert_id = matches[0]
                source_key = f'{BATCH_REFERENCE}:{version_code}:{sc.code}:expert:{expert_id}'
                rows.append({
                    'expert_id': expert_id,
                    'sc': sc,
                    'source_key': source_key,
                    'nom': person['name'],
                })
                stats['propositions'] += 1

        if not options['apply']:
            self.stdout.write(json.dumps({
                'version': version_code,
                'statut_version': version.get_status_display(),
                'mode': 'dry-run',
                **stats,
                'details': details,
                'avertissement': (
                    "Aucune écriture. Relancer avec --apply pour enregistrer les propositions "
                    "au statut « À examiner »."
                ),
            }, ensure_ascii=False, indent=2))
            return

        with transaction.atomic():
            created = 0
            existing = 0
            for row in rows:
                assignment, was_created = AffectationSousCommission.objects.get_or_create(
                    version=version,
                    source_key=row['source_key'],
                    defaults={
                        'expert_id': row['expert_id'],
                        'sc': row['sc'],
                        'batch_reference': BATCH_REFERENCE,
                        'source_kind': 'REPORT_PROPOSAL',
                        'status': AffectationSousCommission.Status.REVIEW,
                        'is_primary': False,
                        'migration_reference': 'Rapport adopté du 15 octobre 2026, annexe 1',
                        'source_database_sha256': catalogue['source_sha256'],
                        'rationale': (
                            f"Proposition nominative de l'annexe 1 ({row['nom']}) — "
                            "rapprochement exact et unique, à examiner sans effet sur les droits."
                        ),
                        'source_snapshot': {
                            'source': 'Rapport adopté du 15 octobre 2026, annexe 1',
                            'report_name': row['nom'],
                            'sc_code': row['sc'].code,
                            'expert_id': row['expert_id'],
                        },
                    },
                )
                if was_created:
                    created += 1
                else:
                    existing += 1
            if created and not JournalMigration.objects.filter(
                version=version, operation='CLASSIFY_REPORT_EXPERTS', target=BATCH_REFERENCE,
            ).exists():
                JournalMigration.objects.create(
                    version=version, actor_name='Commande de classement',
                    operation='CLASSIFY_REPORT_EXPERTS', target=BATCH_REFERENCE,
                    after={**stats, 'created': created, 'existing': existing,
                           'rights_created': 0, 'mandates_created': 0},
                    reason='Rapprochement nominatif avec l’annexe 1 ; propositions à examiner.',
                )

        self.stdout.write(json.dumps({
            'version': version_code,
            'statut_version': version.get_status_display(),
            'mode': 'apply',
            **stats,
            'created': created,
            'existing': existing,
            'details': details,
        }, ensure_ascii=False, indent=2))
