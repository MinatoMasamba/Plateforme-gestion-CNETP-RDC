"""Référentiel additif du rapport adopté le 15 octobre 2026.

La préparation crée les structures et leurs missions sans activer de circuit,
nommer des personnes ou modifier les rattachements historiques.
"""

import hashlib
import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import GroupeCible, JournalMigration, Organe, OrganisationVersion, PosteOrganisation
from .phoenix_services import POLES


REFERENCE = Path(__file__).with_name('rapport_adopte_2026_reference.json')
POSTES_REFERENCE = Path(__file__).with_name('phoenix_reference.json')


@transaction.atomic
def prepare_adopted_organisation():
    catalogue = json.loads(REFERENCE.read_text(encoding='utf-8'))
    source = Path(settings.BASE_DIR) / catalogue['source_document']
    digest = catalogue['source_sha256']
    if source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise ValidationError('Le rapport adopté a changé ; vérifier le catalogue avant de le charger.')
    sc_items = catalogue['sc']
    if len(sc_items) != 7 or len({item['code'] for item in sc_items}) != 7:
        raise ValidationError('Le catalogue doit contenir sept sous-commissions distinctes.')
    if any(len(item['groups']) != 5 or
           {group['number'] for group in item['groups']} != set(range(1, 6)) or
           not item['mission'] or any(not group['mission'] for group in item['groups'])
           for item in sc_items):
        raise ValidationError('Chaque sous-commission doit contenir cinq GT avec leur mission.')

    posts = json.loads(POSTES_REFERENCE.read_text(encoding='utf-8'))['posts']
    if sum(item['organe'] == 'COPIL' for item in posts) != 22 or sum(item['organe'].startswith('ST') for item in posts) != 24:
        raise ValidationError('Le catalogue des postes doit contenir 22 postes COPIL et 24 postes ST.')

    version, _ = OrganisationVersion.objects.get_or_create(
        code=catalogue['version_code'],
        defaults={
            'name': 'Organisation CNE-ITP du 15 octobre 2026',
            'source_document': catalogue['source_document'],
            'source_sha256': digest,
            'gt_catalogue_reference': 'Rapport adopté du 15 octobre 2026, déclinaison opérationnelle des tomes 0 à 6',
        },
    )
    version = OrganisationVersion.objects.select_for_update().get(pk=version.pk)
    if version.status != OrganisationVersion.Status.PROPOSED or version.source_sha256 != digest:
        raise ValidationError('Cette préparation ne peut modifier qu’une version proposée issue du même rapport.')

    organs = {}
    definitions = [
        ('COPIL', Organe.Type.COPIL, 'Comité de pilotage', None, {'postes': 22, 'permanent': False}),
        ('ST', Organe.Type.ST, 'Coordination du Secrétariat technique', None, {'postes': 24, 'permanent': True}),
        *((code, Organe.Type.ST_POLE, name, 'ST', {'postes': 4}) for code, name in POLES),
        *((item['code'], Organe.Type.SC, item['name'], None,
           {'tome': item['tome'], 'gt': 5, 'designation': 'à confirmer' if item['code'] == 'SC-VRD' else 'rapport adopté'})
          for item in sc_items),
    ]
    sc_by_code = {item['code']: item for item in sc_items}
    for code, kind, name, parent_code, composition in definitions:
        source_reference = 'Rapport adopté du 15 octobre 2026, section 2' if kind != Organe.Type.SC else f"Rapport adopté, tome {sc_by_code[code]['tome']}"
        domain = sc_by_code[code]['mission'] if kind == Organe.Type.SC else ''
        obj, _ = Organe.objects.get_or_create(version=version, code=code, defaults={
            'name': name, 'official_name': name, 'type': kind, 'parent': organs.get(parent_code),
            'domain': domain, 'composition': composition, 'source_reference': source_reference,
        })
        if obj.type != kind or obj.name != name or obj.parent_id != (organs[parent_code].pk if parent_code else None):
            raise ValidationError(f'L’organe {code} diffère du rapport adopté.')
        organs[code] = obj

    for item in posts:
        organe = organs[item['organe']]
        obj, _ = PosteOrganisation.objects.get_or_create(organe=organe, code=item['code'], defaults={
            'category': item['category'], 'title': item['title'], 'origin_label': item['origin_label'],
            'source_reference': 'Rapport adopté du 15 octobre 2026, section 2',
        })
        if (obj.category, obj.title, obj.origin_label) != (item['category'], item['title'], item['origin_label']):
            raise ValidationError(f'Le poste {item["code"]} diffère du catalogue vérifié.')

    for item in sc_items:
        for number, bureau in enumerate(item['bureau_posts'], start=1):
            role = bureau['role']
            category = (PosteOrganisation.Category.PRESIDENCY if 'Président' in role else
                        PosteOrganisation.Category.SECRETARIAT if role == 'Secrétaire' else
                        PosteOrganisation.Category.MEMBER)
            code = f"{item['code']}-BUREAU-{number:02d}"
            obj, _ = PosteOrganisation.objects.get_or_create(organe=organs[item['code']], code=code, defaults={
                'category': category, 'title': role,
                'origin_label': bureau['origin'] if bureau['holder_name'] else '',
                'source_reference': f"Rapport adopté du 15 octobre 2026, annexe 1, tome {item['tome']}",
            })
            if (obj.category, obj.title) != (category, role):
                raise ValidationError(f'Le poste {code} diffère du rapport adopté.')

    for item in sc_items:
        for group in item['groups']:
            obj, _ = GroupeCible.objects.get_or_create(sc=organs[item['code']], code=group['code'], defaults={
                'name': group['name'], 'mission': group['mission'], 'activity': 'PRODUCTION',
                'source_reference': f"Rapport adopté du 15 octobre 2026, tome {item['tome']}, GT {group['number']}",
            })
            if (obj.name, obj.mission) != (group['name'], group['mission']):
                raise ValidationError(f'Le groupe {group["code"]} diffère du rapport adopté.')

    counts = {
        'copil_posts': PosteOrganisation.objects.filter(organe=organs['COPIL']).count(),
        'st_posts': PosteOrganisation.objects.filter(organe__version=version, organe__type__in=[Organe.Type.ST, Organe.Type.ST_POLE]).count(),
        'sc': Organe.objects.filter(version=version, type=Organe.Type.SC).count(),
        'gt': GroupeCible.objects.filter(sc__version=version).count(),
        'sc_bureau_posts': PosteOrganisation.objects.filter(organe__version=version, organe__type=Organe.Type.SC).count(),
    }
    if counts != {'copil_posts': 22, 'st_posts': 24, 'sc': 7, 'gt': 35, 'sc_bureau_posts': 30}:
        raise ValidationError('Les effectifs chargés ne correspondent pas au rapport adopté.')
    if not JournalMigration.objects.filter(version=version, operation='PREPARE_ADOPTED_REPORT').exists():
        JournalMigration.objects.create(
            version=version, actor_name='Commande de préparation', operation='PREPARE_ADOPTED_REPORT',
            target=version.code, after={**counts, 'source_sha256': digest, 'mandates_created': 0,
                                        'rights_created': 0, 'legacy_rows_modified': 0},
            reason='Référentiel préparé sans nomination, droit ni activation de circuit.',
        )
    if not JournalMigration.objects.filter(version=version, operation='PREPARE_SC_BUREAUX').exists():
        JournalMigration.objects.create(
            version=version, actor_name='Commande de préparation', operation='PREPARE_SC_BUREAUX',
            target=version.code, after={'sc_bureau_posts': counts['sc_bureau_posts'], 'mandates_created': 0},
            reason='Postes de bureau issus de l’annexe 1 ; nominations encore à vérifier.',
        )
    return version, counts
