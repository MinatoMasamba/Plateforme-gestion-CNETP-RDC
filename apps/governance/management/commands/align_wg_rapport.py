"""
Aligne les groupes de travail (WG) des sous-commissions sur la nomenclature des
5 GT du rapport adopté du 15 octobre 2026, pour les sous-commissions dont le
catalogue est incomplet (moins de 5 groupes) ou dont la correspondance est
certaine.

Règles :
  * ne supprime aucun groupe existant (conservation des experts, normes et
    contributions rattachés) ;
  * renomme un groupe uniquement lorsque la correspondance est certaine ;
  * crée les groupes manquants du rapport ;
  * conserve les identifiants techniques et la numérotation existante : les
    nouveaux groupes reçoivent le numéro suivant disponible.

Idempotente : ``get_or_create`` et renommage conditionnel.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.governance.models import CTM, WG


# Sous-commissions à compléter : numéro CTM -> 5 GT du rapport (intitulés exacts).
SC_GT = {
    2: [
        'Évaluations environnementales et sociales (EES)',
        'Gestion et valorisation des déchets de construction',
        'Hygiène, santé et sécurité au travail (SST)',
        'Protection des ressources en eau et prévention des pollutions',
        'Résilience climatique et développement durable',
    ],
    7: [
        'Voiries et Réseaux Divers (VRD) et assainissement secondaire',
        'Installations électriques, courants forts et éclairage public',
        'Courants faibles, sécurité électronique et automatismes',
        'Chauffage, Ventilation, Climatisation (CVC) et traitement d\'air',
        'Plomberie, sanitaires, gaz et fluides spéciaux',
    ],
}

# Renommages dont la correspondance est certaine : (numéro SC, ancien intitulé) -> nouvel intitulé.
RENAMES = {
    (2, 'Déchets Solides & CET'): 'Gestion et valorisation des déchets de construction',
}


class Command(BaseCommand):
    help = 'Complète les GT manquants (SC-ENV, SC-VRD) et corrige les intitulés certains.'

    @transaction.atomic
    def handle(self, *args, **options):
        created = []
        renamed = []
        kept = []

        for ctm_number, gt_names in SC_GT.items():
            try:
                ctm = CTM.objects.get(number=ctm_number)
            except CTM.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Sous-commission {ctm_number} introuvable, ignorée.'))
                continue

            existing = {wg.name: wg for wg in WG.objects.filter(ctm=ctm)}
            for gt_name in gt_names:
                if gt_name in existing:
                    kept.append((ctm_number, gt_name))
                    continue

                rename_source = next(
                    (old for (num, old), new in RENAMES.items() if num == ctm_number and new == gt_name and old in existing),
                    None,
                )
                if rename_source:
                    wg = existing[rename_source]
                    wg.name = gt_name
                    wg.save(update_fields=['name', 'updated_at'])
                    existing.pop(rename_source)
                    existing[gt_name] = wg
                    renamed.append((ctm_number, rename_source, gt_name))
                    continue

                next_number = max([wg.number for wg in existing.values()] or [0]) + 1
                wg = WG.objects.create(
                    ctm=ctm,
                    number=next_number,
                    name=gt_name,
                    description='GT du rapport adopté du 15 octobre 2026.',
                )
                existing[gt_name] = wg
                created.append((ctm_number, next_number, gt_name))

        self.stdout.write(self.style.SUCCESS(f'Renommés : {len(renamed)}'))
        for num, old, new in renamed:
            self.stdout.write(f'   ~ SC{num} « {old} » -> « {new} »')
        self.stdout.write(self.style.SUCCESS(f'Créés : {len(created)}'))
        for num, wg_num, name in created:
            self.stdout.write(f'   + SC{num} WG{num}.{wg_num} « {name} »')
        self.stdout.write(self.style.SUCCESS(f'Déjà conformes : {len(kept)}'))
