"""Classe directement les experts cités dans l'annexe 1 du rapport adopté.

La commande affecte les experts à leur sous-commission sans créer de mandat
ni d'habilitation et sans modifier les affectations historiques.
"""

import json
import unicodedata
from collections import Counter, defaultdict
from datetime import date
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
        "Affecte directement les experts de l'annexe 1 du rapport adopté "
        "à leur sous-commission (dry-run par défaut)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help="Enregistre les affectations ; sans ce drapeau, affiche seulement le plan.",
        )
        parser.add_argument(
            '--code', default=None,
            help="Code de la version d'organisation (défaut : la plus récente).",
        )
        parser.add_argument(
            '--effective-date', default='2026-10-15',
            help="Date de prise d'effet des affectations (AAAA-MM-JJ).",
        )

    def handle(self, *args, **options):
        try:
            effective_date = date.fromisoformat(options['effective_date'])
        except (TypeError, ValueError) as error:
            raise CommandError("La date de prise d'effet doit être au format AAAA-MM-JJ.") from error
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

        rows.sort(key=lambda row: (row['expert_id'], row['sc'].code))
        existing_primary_experts = set(
            AffectationSousCommission.objects.filter(
                version=version,
                status=AffectationSousCommission.Status.MIGRATED,
                is_primary=True,
            ).exclude(
                source_key__in=[row['source_key'] for row in rows],
            ).values_list('expert_id', flat=True)
        )
        primary_chosen = set()
        for row in rows:
            row['is_primary'] = (
                row['expert_id'] not in existing_primary_experts
                and row['expert_id'] not in primary_chosen
            )
            if row['is_primary']:
                primary_chosen.add(row['expert_id'])

        if not options['apply']:
            self.stdout.write(json.dumps({
                'version': version_code,
                'statut_version': version.get_status_display(),
                'mode': 'dry-run',
                'date_effet': effective_date.isoformat(),
                **stats,
                'details': details,
                'avertissement': (
                    "Aucune écriture. Relancer avec --apply pour enregistrer les affectations "
                    "directes au statut « Affecté »."
                ),
            }, ensure_ascii=False, indent=2))
            return

        with transaction.atomic():
            created = 0
            updated = 0
            existing = 0
            ignored = 0
            for row in rows:
                assignment = AffectationSousCommission.objects.select_for_update().filter(
                    version=version, source_key=row['source_key'],
                ).first()
                desired = {
                    'expert_id': row['expert_id'],
                    'sc': row['sc'],
                    'batch_reference': BATCH_REFERENCE,
                    'source_kind': 'REPORT_PROPOSAL',
                    'status': AffectationSousCommission.Status.MIGRATED,
                    'is_primary': row['is_primary'],
                    'migration_reference': 'Rapport adopté du 15 octobre 2026, annexe 1',
                    'source_database_sha256': catalogue['source_sha256'],
                    'effective_from': effective_date,
                    'effective_to': None,
                    'rationale': (
                        f"Affectation directe de l'annexe 1 ({row['nom']}) — "
                        "rapprochement exact et unique, sans mandat ni habilitation."
                    ),
                    'source_snapshot': {
                        'source': 'Rapport adopté du 15 octobre 2026, annexe 1',
                        'report_name': row['nom'],
                        'sc_code': row['sc'].code,
                        'expert_id': row['expert_id'],
                    },
                }
                if not assignment:
                    AffectationSousCommission.objects.create(
                        version=version, source_key=row['source_key'], **desired,
                    )
                    created += 1
                    continue
                if assignment.status in (
                    AffectationSousCommission.Status.ENDED,
                    AffectationSousCommission.Status.CANCELLED,
                ):
                    ignored += 1
                    continue
                changed = False
                for field, value in desired.items():
                    if field == 'sc':
                        if assignment.sc_id != value.pk:
                            assignment.sc = value
                            changed = True
                    elif getattr(assignment, field) != value:
                        setattr(assignment, field, value)
                        changed = True
                if changed:
                    assignment.save()
                    updated += 1
                else:
                    existing += 1
            if (created or updated) and not JournalMigration.objects.filter(
                version=version, operation='CLASSIFY_REPORT_EXPERTS', target=BATCH_REFERENCE,
            ).exists():
                JournalMigration.objects.create(
                    version=version, actor_name='Commande de classement',
                    operation='CLASSIFY_REPORT_EXPERTS', target=BATCH_REFERENCE,
                    after={**stats, 'created': created, 'updated': updated,
                           'existing': existing, 'ignored': ignored,
                           'rights_created': 0, 'mandates_created': 0},
                    reason='Affectation directe des experts de l’annexe 1 ; aucun droit créé.',
                )

        self.stdout.write(json.dumps({
            'version': version_code,
            'statut_version': version.get_status_display(),
            'mode': 'apply',
            'date_effet': effective_date.isoformat(),
            **stats,
            'created': created,
            'updated': updated,
            'existing': existing,
            'ignored': ignored,
            'details': details,
        }, ensure_ascii=False, indent=2))
