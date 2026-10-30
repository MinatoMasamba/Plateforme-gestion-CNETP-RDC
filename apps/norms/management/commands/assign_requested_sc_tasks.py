"""Adresse une tâche de prise en charge à la SC concernée par chaque projet demandé."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.governance.models import Organe, OrganisationVersion, RattachementDocumentaire, Tache
from apps.norms.models import Norme


SC_BY_REFERENCE = {
    'NCD 001': 'SC-SOCLE', 'NCD 002': 'SC-SOCLE', 'NCD 003': 'SC-SOCLE', 'NCD 004': 'SC-SOCLE',
    'NCD 101': 'SC-IT', 'NCD 102': 'SC-IT', 'NCD 103': 'SC-IT', 'NCD 104': 'SC-IT', 'NCD 105': 'SC-IT',
    'NCD 201': 'SC-GF', 'NCD 202': 'SC-GF', 'NCD 203': 'SC-GF', 'NCD 204': 'SC-GF',
    'NCD 301': 'SC-OH', 'NCD 302': 'SC-OH', 'NCD 303': 'SC-OH',
    'NCD 401': 'SC-VRD', 'NCD 402': 'SC-VRD', 'NCD 403': 'SC-VRD',
    'NCD 501': 'SC-ENV', 'NCD 502': 'SC-ENV', 'NCD 503': 'SC-ENV',
    'NCD 601': 'SC-BAT', 'NCD 602': 'SC-BAT', 'NCD 603': 'SC-BAT',
}


class Command(BaseCommand):
    help = 'Crée une tâche adressée à la SC pour chacun des 25 projets NCD demandés.'

    def handle(self, *args, **options):
        db = Path(str(settings.DATABASES['default']['NAME'])).resolve()
        if db != (Path(settings.BASE_DIR) / 'db.sqlite3').resolve():
            raise CommandError('La commande doit utiliser db.sqlite3 à la racine.')
        if len(SC_BY_REFERENCE) != 25:
            raise CommandError('Le portefeuille doit contenir exactement 25 références.')
        created = []
        with transaction.atomic():
            for ref, code in SC_BY_REFERENCE.items():
                norme = Norme.all_objects.get(reference_number=ref)
                version_code = 'reorganisation-2026-10-15' if code in {'SC-ENV', 'SC-VRD'} else 'phoenix-2026-10'
                version = OrganisationVersion.objects.get(code=version_code)
                sc = Organe.objects.get(version=version, type='SC', code=code)
                RattachementDocumentaire.objects.get_or_create(
                    norme=norme, version=version, role='OWNER',
                    defaults={'sc': sc, 'status': 'PROPOSED'},
                )
                state = 'ON_HOLD' if sc.status == 'PROPOSED' or norme.status == 'ARCHIVED' else 'PLANNED'
                for title, description in (
                    (f'Examiner {ref} et établir le programme de travail de la sous-commission',
                     f'Contrôler le périmètre de « {norme.title} », identifier le groupe compétent, les pièces disponibles, les contributions attendues et les réserves à transmettre à la CTC.'),
                    (f'Constituer le dossier des pièces et contributions pour {ref}',
                     f'Inventorier les versions, sources, observations et experts concernés par « {norme.title} ». Signaler les pièces manquantes avant toute validation.'),
                ):
                    task, was_created = Tache.objects.get_or_create(
                        norme=norme, target_sc=sc, titre=title,
                        defaults={'description': description, 'status': state,
                                  'priority': 'NORMAL', 'progress': 0},
                    )
                    if not was_created and state == 'ON_HOLD' and task.status == 'PLANNED':
                        task.status = 'ON_HOLD'
                        task.save(update_fields=['status', 'updated_at'])
                    if was_created:
                        created.append((ref, sc.code, task.status))
        self.stdout.write(f'{len(created)} tâches SC créées ; {sum(s == "ON_HOLD" for _, _, s in created)} en attente de confirmation ou de reprise du dossier.')
