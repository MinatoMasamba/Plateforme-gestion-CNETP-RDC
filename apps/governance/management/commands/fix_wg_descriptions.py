"""
Corrige les `WG.description` erronées ou sans rapport (ex. WG2.1 décrit comme
"normalisation des composants électroniques", WG1.3 portant la description de
WG1.2) pour les 5 GT couverts par un Code/Directive/Recommandation de la Note
Technique N°1 (Plan de Production Semestriel CNE-ITP/CTC/PPT-2026).

`WG.name` n'est PAS modifié : il reste aligné sur le Manuel Organisationnel
2026 (cf. seed_ctm_working_groups.py). Seule `WG.description` est mise à jour
avec le résumé du mandat du GT issu de la Note Technique N°1.

Idempotente : `update_or_create`-style (simple `.save()` sur des WG existants).
"""

from django.core.management.base import BaseCommand
from apps.governance.models import WG


# (ctm_number, wg_number) -> nouvelle description
WG_DESCRIPTIONS = {
    (1, 2): "Ce texte de loi sectoriel est directement opposable aux bureaux "
            "d'études. Il régit les obligations des concepteurs en s'appuyant "
            "sur un lot de 8 normes (NCD) fixant les paramètres de calcul de "
            "la capacité portante, les tassements des fondations superficielles, "
            "ainsi que le dimensionnement des pieux.",
    (1, 3): "Conçu comme un guide pratique d'aide à l'application pour les "
            "ingénieurs de terrain, ce document encadre les critères de "
            "stabilité des talus, le compactage lourd et la classification des "
            "géo-matériaux utilisables pour les remblais en contexte congolais.",
    (2, 1): "Ce code fixe les obligations légales de dimensionnement pour les "
            "structures lourdes et les ponts de la République. Il encadre "
            "l'application de 12 normes nationales liées aux règles de calcul "
            "de la fatigue des aciers, aux ponts suspendus, aux ponts-cadres et "
            "aux viaducs en béton précontraint.",
    (3, 2): "Acte réglementaire ministériel dictant les méthodologies "
            "d'instruction destinées à l'administration. Il s'adosse sur 10 "
            "normes (NCD) imposant des seuils sur l'éclairage naturel minimal, "
            "l'étanchéité des façades, l'isolation thermique passive et la "
            "valorisation de la norme africaine ARS 1333 sur les éco-matériaux.",
    (5, 1): "Catalogue officiel opposable servant de texte de référence pour la "
            "maîtrise d'œuvre routière. Il encadre la mise en œuvre de 12 normes "
            "dédiées aux structures de chaussées bitumineuses, au comportement "
            "des graves-latérites améliorées au ciment et aux spécificités des "
            "pistes en terre de l'OVDA.",
}


class Command(BaseCommand):
    help = (
        "Corrige les WG.description erronées des GT 1.2, 1.3, 2.1, 3.2 et 5.1 "
        "avec le mandat précis de la Note Technique N°1 (PPT-2026). WG.name "
        "n'est pas modifié."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Correction des descriptions WG (Note Technique N°1) ==="))

        for (ctm_num, wg_num), description in WG_DESCRIPTIONS.items():
            try:
                wg = WG.objects.get(ctm__number=ctm_num, number=wg_num)
            except WG.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"   ⚠️ WG {ctm_num}.{wg_num} introuvable."))
                continue

            old_description = wg.description
            wg.description = description
            wg.save(update_fields=['description'])

            self.stdout.write(f"   ✓ WG {ctm_num}.{wg_num} ({wg.name})")
            self.stdout.write(f"      avant : {old_description!r}")
            self.stdout.write(f"      après : {description[:80]}...")

        self.stdout.write(self.style.SUCCESS("\n✅ Descriptions WG corrigées."))
