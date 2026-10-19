"""
Crée les groupes de travail manquants nécessaires aux 20 projets NCD du
catalogue prospectif du rapport adopté du 15 octobre 2026.

Les sous-commissions (CTM unifiés) sont déjà en place ; certaines ne disposent
pas encore d'un WG correspondant au GT du rapport. Cette commande comble ces
lacunes en miroir des GroupeCible (référentiel Phoenix), sans toucher aux
rattachements historiques.

Idempotente : ``get_or_create`` sur (ctm, name).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.governance.models import CTM, WG


# (numéro de SC, nom du GT du rapport adopté)
NCD_WORKING_GROUPS = [
    (4, "Ponts et ouvrages d'art"),
    (3, "Reconnaissance des sols et investigations in situ"),
    (7, "Installations électriques, courants forts et éclairage public"),
    (7, "Courants faibles, sécurité électronique et automatismes"),
    (2, "Évaluations environnementales et sociales (EES)"),
    (2, "Hygiène, santé et sécurité au travail (SST)"),
    (1, "Transition numérique et BIM (Building Information Modeling)"),
]


class Command(BaseCommand):
    help = "Comble les WG manquants pour les 20 projets NCD du rapport adopté."

    @transaction.atomic
    def handle(self, *args, **options):
        created = []
        existing = []
        for sc_number, wg_name in NCD_WORKING_GROUPS:
            try:
                ctm = CTM.objects.get(number=sc_number)
            except CTM.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"SC {sc_number} introuvable : WG « {wg_name} » ignoré."))
                continue
            wg, was_created = WG.objects.get_or_create(
                ctm=ctm,
                name=wg_name,
                defaults={'number': (ctm.working_groups.count() or 0) + 1,
                          'description': f'GT du rapport adopté du 15 octobre 2026 — {wg_name}.'},
            )
            (created if was_created else existing).append(wg)
            self.stdout.write(
                f"   {'+ créé' if was_created else '• déjà présent'} : SC{sc_number} WG{wg.number} « {wg.name} »"
            )
        self.stdout.write(self.style.SUCCESS(
            f"Terminé : {len(created)} WG créé(s), {len(existing)} déjà présent(s)."
        ))
