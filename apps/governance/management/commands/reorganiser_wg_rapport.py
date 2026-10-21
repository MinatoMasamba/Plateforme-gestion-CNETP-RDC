"""
Réorganise les groupes de travail (WG) des sept sous-commissions pour qu'ils
correspondent exactement aux 5 GT du rapport adopté du 15 octobre 2026.

Comportement :
  * renomme les anciens groupes dont la correspondance est certaine (les
    identifiants techniques ``wg``/``ctm`` et les rattachements sont conservés) ;
  * supprime les groupes obsolètes (« bêtes ») après avoir reporté leurs normes,
    affectations, demandes et tâches vers le groupe de destination ;
  * crée les groupes manquants du rapport ;
  * les nouveaux groupes reçoivent le numéro suivant disponible de la SC.

Idempotente. Exécute tout dans une transaction atomique.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.governance.models import Affectation, CTM, Demande, Tache, WG
from apps.norms.models import Norme


# numéro CTM -> opérations de réorganisation
MAPPING = {
    1: {  # SC-BAT
        'renames': {
            'Structures et Sécurité': 'Conception architecturale et structurelle',
            'Performance Énergétique & Coûts': 'Efficacité énergétique, thermique et acoustique',
        },
        'deletes': {
            'Matériaux de Construction': 'Conception architecturale et structurelle',
        },
        'creates': [
            'Sécurité incendie et accessibilité',
            'Urbanisme et aménagement urbain',
        ],
    },
    2: {  # SC-ENV
        'renames': {
            'Déchets Solides & CET': 'Gestion et valorisation des déchets de construction',
        },
        'deletes': {},
        'creates': [
            'Protection des ressources en eau et prévention des pollutions',
            'Résilience climatique et développement durable',
        ],
    },
    3: {  # SC-GF
        'renames': {
            'Risques Naturels': 'Mécanique des roches et risques naturels',
            'Fondations': 'Fondations superficielles et profondes',
            'Stabilité & Érosions': 'Ouvrages de soutènement et amélioration des sols',
        },
        'deletes': {},
        'creates': [
            'Auscultation, diagnostic et pathologie géotechnique',
        ],
    },
    4: {  # SC-IT
        'renames': {
            'Ingénierie Routière': 'Routes, Conception géométrique & dimensionnement',
            'Voies Ferrées': 'Infrastructures ferroviaires',
            'Infrastructure Aéroportuaire': 'Infrastructures aéroportuaires',
            'Infrastructures Portuaires': 'Infrastructures portuaires et fluviales',
        },
        'deletes': {
            'Terminaux et Équipements': 'Infrastructures aéroportuaires',
            'Conformité OACI': 'Infrastructures aéroportuaires',
        },
        'creates': [],
    },
    5: {  # SC-OH
        'renames': {
            'Gestion des Eaux Pluviales': 'Hydrologie et modélisation des bassins versants',
            'Ouvrages Hydrauliques Lourds': 'Barrages, digues et réservoirs',
            'Réseaux d\'Assainissement': 'Drainage et assainissement routier/urbain',
            'Irrigation et Drainage': 'Aménagements hydro-agricoles et irrigation',
            'Adduction d\'Eau': 'Adduction d\'eau potable et ouvrages de captage',
        },
        'deletes': {
            'Forages et Captage': 'Adduction d\'eau potable et ouvrages de captage',
            'Traitement et Épuration': 'Drainage et assainissement routier/urbain',
        },
        'creates': [],
    },
    6: {  # SC-SOCLE
        'renames': {
            'Normalisation Appliquée': 'Terminologie, symboles et métrologie normative',
            'Matériaux de Construction Locaux': 'Valorisation des matériaux locaux et éco-matériaux',
            'Essais et Métrologie': 'Évaluation de la conformité et assurance qualité des laboratoires',
            'Composants et Circuits': 'Caractérisation physique et mécanique des matériaux',
            'Calcul Mécanique': 'Liants hydrauliques, bétons et produits manufacturés',
        },
        'deletes': {
            'Simulation et Recherche': 'Caractérisation physique et mécanique des matériaux',
            'Simulation, Recherche & Certification': 'Évaluation de la conformité et assurance qualité des laboratoires',
        },
        'creates': [],
    },
    7: {  # SC-VRD
        'renames': {},
        'deletes': {},
        'creates': [
            'Voiries et Réseaux Divers (VRD) et assainissement secondaire',
            'Chauffage, Ventilation, Climatisation (CVC) et traitement d\'air',
            'Plomberie, sanitaires, gaz et fluides spéciaux',
        ],
    },
}


def _migrate_references(source_wg, target_wg):
    """Reporte tous les rattachements du groupe source vers le groupe cible."""
    Norme.all_objects.filter(wg=source_wg).update(wg=target_wg)
    Affectation.objects.filter(wg=source_wg).update(wg=target_wg)
    Demande.objects.filter(groupe=source_wg).update(groupe=target_wg)
    Tache.objects.filter(working_group=source_wg).update(working_group=target_wg)


class Command(BaseCommand):
    help = 'Réorganise les WG des 7 SC selon les 5 GT du rapport adopté.'

    @transaction.atomic
    def handle(self, *args, **options):
        renamed = []
        deleted = []
        created = []

        for ctm_number, ops in MAPPING.items():
            try:
                ctm = CTM.objects.get(number=ctm_number)
            except CTM.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'SC {ctm_number} introuvable, ignorée.'))
                continue

            wgs = {wg.name: wg for wg in WG.objects.filter(ctm=ctm)}

            # 1. Renommages (conservent les identifiants et les rattachements).
            for old_name, new_name in ops['renames'].items():
                wg = wgs.get(old_name)
                if wg is None:
                    continue
                if wg.name != new_name:
                    wg.name = new_name
                    wg.save(update_fields=['name', 'updated_at'])
                    renamed.append((ctm_number, old_name, new_name))
                wgs.pop(old_name, None)
                wgs[new_name] = wg

            # 2. Suppressions après report des rattachements vers la destination.
            for old_name, target_name in ops['deletes'].items():
                wg = wgs.get(old_name)
                if wg is None:
                    continue
                target = wgs.get(target_name) or WG.objects.filter(ctm=ctm, name=target_name).first()
                if target is None:
                    self.stderr.write(self.style.ERROR(
                        f'SC {ctm_number} : destination « {target_name} » introuvable pour « {old_name} ».'
                    ))
                    continue
                _migrate_references(wg, target)
                wg.delete()
                wgs.pop(old_name, None)
                deleted.append((ctm_number, old_name, target_name))

            # 3. Créations des groupes manquants.
            for new_name in ops['creates']:
                if new_name in wgs:
                    continue
                next_number = max([wg.number for wg in wgs.values()] or [0]) + 1
                wg = WG.objects.create(
                    ctm=ctm,
                    number=next_number,
                    name=new_name,
                    description='GT du rapport adopté du 15 octobre 2026.',
                )
                wgs[new_name] = wg
                created.append((ctm_number, next_number, new_name))

        self.stdout.write(self.style.SUCCESS(f'Renommés : {len(renamed)}'))
        for num, old, new in renamed:
            self.stdout.write(f'   ~ SC{num} « {old} » -> « {new} »')
        self.stdout.write(self.style.SUCCESS(f'Supprimés : {len(deleted)}'))
        for num, old, target in deleted:
            self.stdout.write(f'   - SC{num} « {old} » (rattachements reportés vers « {target} »)')
        self.stdout.write(self.style.SUCCESS(f'Créés : {len(created)}'))
        for num, wg_num, name in created:
            self.stdout.write(f'   + SC{num} WG{num}.{wg_num} « {name} »')
