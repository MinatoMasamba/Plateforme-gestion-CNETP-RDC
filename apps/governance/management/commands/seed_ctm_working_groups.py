"""
Commande de management pour peupler et corriger les Working Groups (WG) des 8 Comités Techniques Miroirs (CTM)
conformément au Manuel Organisationnel CNETP 2026.

Cette commande corrige les erreurs d'hallucination et d'inversion identifiées :
1. CTM 1 : Harmonisation des intitulés.
2. CTM 2 : Correction des intitulés (Calcul Structural, Parasismique, Hydraulique).
3. CTM 3 : Correction des intitulés (Habitabilité, BIM, Performance).
4. CTM 7 : Correction de l'inversion (7.1 : Macro-drainage, 7.3 : Déchets).
5. CTM 8 : Suppression du WG 8.4 (Orphelin) et correction des 3 WG restants.

Idempotente : utilise update_or_create.
"""

from django.core.management.base import BaseCommand, CommandError
from apps.governance.models import CTM, WG


class Command(BaseCommand):
    help = "Peuple et corrige les Working Groups (WG) des 8 CTM selon le manuel officiel."

    # Structure de correction : { ctm_number: { wg_number: "Intitule" } }
    CTM_CORRECTIONS = {
        1: {
            1.1: "Sols & Géomécanique",
            1.2: "Risques Naturels",
            1.3: "Stabilité & Érosions",
        },
        2: {
            2.1: "Calcul Structural & Eurocodes",
            2.2: "Génie Parasismique",
            2.3: "Ouvrages Hydrauliques Lourds",
        },
        3: {
            3.1: "Habitabilité & Sécurité",
            3.2: "BIM & Transition Numérique",
            3.3: "Performance Énergétique & Coûts",
        },
        4: {
            4.1: "Infrastructure Aéroportuaire",
            4.2: "Terminaux et Équipements",
            4.3: "Conformité OACI",
        },
        5: {
            5.1: "Ingénierie Routière",
            5.2: "Voies Ferrées",
            5.3: "Infrastructures Portuaires",
        },
        6: {
            6.1: "Adduction d'Eau",
            6.2: "Irrigation et Drainage",
            6.3: "Forages et Captage",
        },
        7: {
            7.1: "Macro-drainage & Eaux Pluviales",
            7.2: "Eaux Usées & Réseaux d'Égouts",
            7.3: "Déchets Solides & CET",
        },
        8: {
            8.1: "Matériaux Géo-sourcés & Locaux",
            8.2: "Essais & Métrologie Légale",
            8.3: "Simulation, Recherche & Certification",
        },
    }

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            "=== Correction et Peuplement des Working Groups (WG) des CTM ==="
        ))

        for ctm_num, wgs in self.CTM_CORRECTIONS.items():
            try:
                ctm = CTM.objects.get(number=ctm_num)
            except CTM.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠️ CTM {ctm_num} non trouvé. Passage au suivant."))
                continue

            self.stdout.write(f"▸ CTM {ctm_num} : {ctm.name}")

            # 1. Identify current WGs for this CTM
            current_wgs = WG.objects.filter(ctm=ctm)
            target_wg_nums = list(wgs.keys())

            # 2. Handle WGs that are NOT in the target list (the "orphans")
            # Instead of deleting (which causes ProtectedError), we rename them to avoid breaking Norme references.
            for wg in current_wgs:
                if wg.number not in target_wg_nums:
                    old_name = wg.name
                    wg.name = f"SURPLUS - {old_name}"
                    wg.save()
                    self.stdout.write(f"   ⚠️ Renommé (Surplus) : WG {ctm_num}.{wg.number} — {old_name}")

            # 3. Create or update the target WGs
            for wg_num, wg_name in wgs.items():
                wg, created = WG.objects.update_or_create(
                    ctm=ctm,
                    number=wg_num,
                    defaults={'name': wg_name}
                )
                status = "✓ créé" if created else "• mis à jour"
                self.stdout.write(f"   {status} : WG {ctm_num}.{wg_num} — {wg_name}")

        self.stdout.write(self.style.SUCCESS("\n✅ Correction des WG terminée."))

