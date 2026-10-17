"""Rattache les titulaires identifiés dans l'annexe 1 aux bureaux des SC.

La commande n'accorde aucune habilitation et ne met pas le circuit en service.
"""

import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_date

from apps.experts.models import Expert
from apps.governance.management.commands.prepare_mandats_rapport import normalize_name
from apps.governance.models import JournalMigration, MandatOrganisation, OrganisationVersion, PosteOrganisation


CATALOGUE = Path(__file__).resolve().parents[2] / 'rapport_adopte_2026_reference.json'


class Command(BaseCommand):
    help = 'Affecte les titulaires uniques de l’annexe 1 à leurs postes SC, sans créer de droits.'

    def add_arguments(self, parser):
        parser.add_argument('--decision-reference', required=True, help='Référence exacte de la confirmation des titulaires.')
        parser.add_argument('--effective-date', required=True, help='Date de prise d’effet au format AAAA-MM-JJ.')

    @transaction.atomic
    def handle(self, *args, **options):
        reference = options['decision_reference'].strip()
        effective_date = parse_date(options['effective_date'])
        if not reference or len(reference) > 250 or not isinstance(effective_date, date):
            raise CommandError('Référence non vide (250 caractères maximum) et date AAAA-MM-JJ requises.')
        catalogue = json.loads(CATALOGUE.read_text(encoding='utf-8'))
        source = Path(settings.BASE_DIR) / catalogue['source_document']
        if source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest() != catalogue['source_sha256']:
            raise CommandError('Le rapport source a changé ; vérifier le catalogue avant toute affectation.')
        version = OrganisationVersion.objects.select_for_update().get(code=catalogue['version_code'])
        if version.status == OrganisationVersion.Status.ARCHIVED:
            raise CommandError('Une organisation archivée ne peut recevoir de nouveaux mandats.')

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
                expert = Expert.objects.select_related('user').get(pk=next(iter(matches)))
                if expert.status != 'ACTIVE' or not expert.user.is_active:
                    stats['compte_inactif'] += 1
                    continue
                poste = PosteOrganisation.objects.get(
                    organe__version=version, organe__code=sc['code'],
                    code=f"{sc['code']}-BUREAU-{number:02d}",
                )
                if poste.title != bureau['role']:
                    raise CommandError(f'La fonction du poste {poste.code} ne correspond plus au rapport.')
                existing = list(MandatOrganisation.objects.select_for_update().filter(poste=poste))
                if len(existing) > 1 or (existing and existing[0].expert_id != expert.pk):
                    stats['poste_a_reexaminer'] += 1
                    continue
                mandate = existing[0] if existing else MandatOrganisation(
                    poste=poste, expert=expert, capacity='ORGANISATION',
                )
                if mandate.status == 'ACTIVE':
                    if mandate.appointment_reference == reference and mandate.start_date == effective_date:
                        stats['deja_affecte'] += 1
                    else:
                        stats['poste_a_reexaminer'] += 1
                    continue
                if mandate.status != 'PROPOSED':
                    stats['poste_a_reexaminer'] += 1
                    continue
                mandate.function = bureau['role']
                mandate.appointment_reference = reference
                mandate.start_date = effective_date
                mandate.status = 'ACTIVE'
                mandate.save()
                stats['affectes'] += 1

        if stats['affectes']:
            JournalMigration.objects.create(
                version=version, actor_name='Instruction utilisateur', operation='AFFECT_SC_BUREAUX',
                target=version.code, after={**stats, 'reference': reference, 'effective_date': effective_date.isoformat(), 'rights_created': 0},
                reason='Titulaires uniques de l’annexe 1 affectés à leurs postes sur confirmation utilisateur ; aucune habilitation créée.',
            )
        self.stdout.write(json.dumps(stats, ensure_ascii=False, indent=2))
