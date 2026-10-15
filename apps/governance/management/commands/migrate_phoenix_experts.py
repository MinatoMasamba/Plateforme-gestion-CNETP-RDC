from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.governance.phoenix_expert_migration import migrate_legacy_experts


class Command(BaseCommand):
    help = 'Migre les experts historiques vers les 7 SC sans supprimer CTM/WG ni créer de droits.'

    def add_arguments(self, parser):
        parser.add_argument('--source-db', required=True)
        parser.add_argument('--decision-reference', required=True)
        parser.add_argument('--effective-date')
        parser.add_argument('--code', default='phoenix-2026-10')

    def handle(self, *args, **options):
        try:
            version, report = migrate_legacy_experts(
                options['source_db'], options['decision_reference'],
                effective_date=options.get('effective_date'), code=options['code'],
            )
        except ValidationError as error:
            raise CommandError('; '.join(error.messages)) from error
        self.stdout.write(self.style.SUCCESS(
            f'{version.name} : {report["migrated"]} expert(s) affecté(s), '
            f'{report["review"]} à examiner ; ancien circuit conservé.'
        ))
        for code, count in sorted(report['by_sc'].items()):
            self.stdout.write(f'  {code}: {count}')
        for reason, count in sorted(report['review_reasons'].items()):
            self.stdout.write(self.style.WARNING(f'  À examiner ({count}) : {reason}'))
