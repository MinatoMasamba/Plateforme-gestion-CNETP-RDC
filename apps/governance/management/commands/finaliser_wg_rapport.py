"""
Finalise la conformité des groupes de travail (WG) des 7 sous-commissions avec
la liste de référence des 35 GT (rapport adopté) :

  * corrige les intitulés qui diffèrent de la référence ;
  * renumérote chaque sous-commission de 1 à 5 dans l'ordre des GT ;
  * ne touche ni aux identifiants (pk), ni aux rattachements experts/normes.

Idempotente. Transaction atomique.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.governance.models import CTM, WG


# numéro CTM -> 5 GT de référence, dans l'ordre officiel.
from apps.governance.catalogue import GT_CATALOGUE as CANONICAL

# Corrections d'intitulé : intitulé actuel -> intitulé de référence.
RENAMES = {
    'Sécurité incendie et accessibilité': 'Sécurité incendie et accessibilité PMR',
    'Conception géométrique, dimensionnement et chaussées': 'Routes, Conception géométrique & dimensionnement',
    'Drainage et assainissement routier et urbain': 'Drainage et assainissement routier/urbain',
    'Voiries et réseaux divers (VRD) et assainissement urbain secondaire': 'Voiries et Réseaux Divers (VRD) et assainissement secondaire',
    'Chauffage, Ventilation, Climatisation (CVC) et traitement d\'air': 'Chauffage, ventilation, climatisation (CVC) et traitement d\'air',
}


class Command(BaseCommand):
    help = 'Corrige les intitulés et renumérote les WG de 1 à 5 par sous-commission.'

    @transaction.atomic
    def handle(self, *args, **options):
        renamed = []
        renumbered = []

        for ctm_number, canonical in CANONICAL.items():
            try:
                ctm = CTM.objects.get(number=ctm_number)
            except CTM.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'SC {ctm_number} introuvable, ignorée.'))
                continue

            wgs = list(WG.objects.filter(ctm=ctm))

            # 1. Correction des intitulés.
            for wg in wgs:
                if wg.name in RENAMES and wg.name != RENAMES[wg.name]:
                    old = wg.name
                    wg.name = RENAMES[wg.name]
                    wg.save(update_fields=['name', 'updated_at'])
                    renamed.append((ctm_number, old, wg.name))

            # 2. Renumérotation de 1 à 5 dans l'ordre officiel.
            order = {name: idx for idx, name in enumerate(canonical)}
            for wg in wgs:
                target = order.get(wg.name)
                if target is None:
                    continue
                target_number = target + 1
                if wg.number != target_number:
                    wg.number = 1000 + target_number  # phase temporaire (évite les collisions)
                    wg.save(update_fields=['number', 'updated_at'])
                    renumbered.append((ctm_number, wg.name, target_number))

            for wg in wgs:
                target = order.get(wg.name)
                if target is not None and wg.number != target + 1:
                    wg.number = target + 1
                    wg.save(update_fields=['number', 'updated_at'])

        self.stdout.write(self.style.SUCCESS(f'Intitulés corrigés : {len(renamed)}'))
        for num, old, new in renamed:
            self.stdout.write(f'   ~ SC{num} « {old} » -> « {new} »')
        self.stdout.write(self.style.SUCCESS(f'Numéros réordonnés : {len(renumbered)}'))
        for num, name, target in renumbered:
            self.stdout.write(f'   # SC{num} « {name} » -> numéro {target}')
