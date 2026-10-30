"""Aligne les 35 WG et rattache les projets demandés au circuit historique."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import AuditLog
from apps.governance.models import CTM, WG, DossierPhoenix
from apps.governance.catalogue import GT_CATALOGUE as CANONICAL, SC_CATALOGUE
from apps.norms.models import Norme


# CTM et numéro du WG dans le catalogue des 35 GT.
PROJECT_GROUPS = {
    'NCD 003': (6, 2), 'NCD 004': (6, 4),
    'NCD 104': (4, 3), 'NCD 105': (4, 1),
    'NCD 204': (3, 3), 'NCD 302': (5, 3),
    'NCD 401': (7, 1), 'NCD 603': (1, 1),
}


class Command(BaseCommand):
    help = 'Aligne les noms des 35 WG et convertit les huit projets en LEGACY, avec audit.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        with transaction.atomic():
            groups = {}
            for number, names in CANONICAL.items():
                ctm = CTM.objects.get(number=number)
                sc_code, tome, sc_name = SC_CATALOGUE[number]
                target_name = f'{sc_name} ({sc_code})'
                if ctm.name != target_name and options['apply']:
                    old_name = ctm.name
                    ctm.name = target_name
                    ctm.save(update_fields=['name', 'updated_at'])
                    AuditLog.objects.create(action='UPDATE', content_type='CTM', object_id=ctm.pk,
                        object_repr=target_name[:200], changes={'name': {'before': old_name, 'after': target_name},
                            'tome': tome, 'source': 'Catalogue fourni le 29/10/2026'})
                wgs = list(WG.objects.select_for_update().filter(ctm=ctm).order_by('number'))
                if [wg.number for wg in wgs] != [1, 2, 3, 4, 5]:
                    raise CommandError(f'CTM {number} : cinq WG numérotés de 1 à 5 sont requis.')
                for wg, name in zip(wgs, names):
                    groups[(number, wg.number)] = wg
                    if wg.name != name:
                        self.stdout.write(f'WG {number}.{wg.number} : {wg.name} -> {name}')
                        if options['apply']:
                            old = wg.name
                            wg.name = name
                            wg.save(update_fields=['name', 'updated_at'])
                            AuditLog.objects.create(action='UPDATE', content_type='WG', object_id=wg.pk,
                                object_repr=str(wg)[:200], changes={'name': {'before': old, 'after': name},
                                    'source': 'Alignement des 35 GT demandé le 29/10/2026'})
            converted = 0
            for ref, key in PROJECT_GROUPS.items():
                norm = Norme.all_objects.select_for_update().get(reference_number=ref)
                wg = groups[key]
                if DossierPhoenix.objects.filter(norme=norm).exists():
                    raise CommandError(f'{ref} possède un workflow Phoenix ; conversion refusée.')
                if norm.circuit_version == 'LEGACY' and norm.ctm_id == wg.ctm_id and norm.wg_id == wg.pk:
                    continue
                self.stdout.write(f'{ref} -> CTM {key[0]} / WG {key[0]}.{key[1]}')
                if options['apply']:
                    old = {'circuit_version': norm.circuit_version, 'ctm_id': norm.ctm_id, 'wg_id': norm.wg_id}
                    norm.circuit_version = 'LEGACY'
                    norm.ctm_id = wg.ctm_id
                    norm.wg = wg
                    norm.full_clean()
                    norm.save(update_fields=['circuit_version', 'ctm', 'wg', 'updated_at'])
                    AuditLog.objects.create(action='UPDATE', content_type='Norme', object_id=norm.pk,
                        object_repr=str(norm)[:200], changes={'before': old,
                            'after': {'circuit_version': 'LEGACY', 'ctm_id': wg.ctm_id, 'wg_id': wg.pk},
                            'source': 'Retour au circuit historique demandé le 29/10/2026'})
                    converted += 1
            self.stdout.write(f'{converted} normes converties.' if options['apply'] else 'Vérification uniquement ; utiliser --apply pour appliquer.')
