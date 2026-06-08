"""
Commande d'affichage (lecture seule, ne modifie rien) des 20 postes nominatifs
de la Cellule Technique de Coordination : regroupés par pôle, avec leur
structure d'origine exigée (référence "Ligne X" du Tableau 1) et leur statut
(vacant / pourvu).

Usage : python manage.py show_ctc_postes
"""

from django.core.management.base import BaseCommand, CommandError

from apps.governance.models import TechnicalCell, PosteNominatifCTC


GROUPES = [
    ("DIRECTION DES OPÉRATIONS", ('COORDINATOR', 'VICE_COORDINATOR', 'EXECUTIVE')),
    ("PÔLE D'ANALYSE ET D'INGÉNIERIE DOCUMENTAIRE",
     ('ISO_EXPERT', 'LEGAL', 'ENVIRONMENTAL', 'PLANNER', 'ECONOMIST', 'SCIENTIFIC')),
    ("PÔLE LOGISTIQUE, COMMUNICATION ET RELATIONS EXTÉRIEURES",
     ('ACCOUNTANT', 'ENQUIRY_MANAGER', 'INDUSTRIAL', 'COMMUNICATOR')),
    ("BUREAU D'APPUI TECHNIQUE ET NUMÉRIQUE", ('CARTOGRAPHER', 'DATA_ENTRY', 'IT_ADMIN')),
]


class Command(BaseCommand):
    help = "Affiche (lecture seule) les 20 postes nominatifs de la Cellule Technique de Coordination, par pôle"

    def handle(self, *args, **options):
        try:
            ctc = TechnicalCell.objects.get(name="Cellule Technique de Coordination CNETP")
        except TechnicalCell.DoesNotExist:
            raise CommandError(
                "La Cellule Technique de Coordination CNETP n'existe pas encore. "
                "Exécutez d'abord : python manage.py init_pilotage_and_ctc"
            )

        postes = list(
            PosteNominatifCTC.objects
            .filter(ctc=ctc)
            .select_related('required_structure', 'holder')
            .order_by('order')
        )

        self.stdout.write(self.style.SUCCESS(
            "\n" + "=" * 78 +
            "\n  CELLULE TECHNIQUE DE COORDINATION — 20 POSTES NOMINATIFS"
            "\n  (Manuel Organisationnel CNETP 2026, section 3.2 — quotas du Tableau 1)"
            "\n" + "=" * 78
        ))

        if not postes:
            self.stdout.write(self.style.WARNING(
                "\nAucun poste en base. Exécutez d'abord : python manage.py seed_ctc_postes\n"
            ))
            return

        pourvus = 0
        for titre_groupe, roles in GROUPES:
            sous_ensemble = [p for p in postes if p.role in roles]
            if not sous_ensemble:
                continue
            pluriel = 's' if len(sous_ensemble) > 1 else ''
            self.stdout.write(self.style.MIGRATE_HEADING(
                f"\n▸ {titre_groupe} ({len(sous_ensemble)} poste{pluriel})"
            ))
            for p in sous_ensemble:
                if p.holder:
                    pourvus += 1
                    statut = self.style.SUCCESS(f"✓ Pourvu — {p.holder.full_name}")
                else:
                    statut = self.style.WARNING("⏳ Vacant")
                structure = (
                    f"{p.required_structure.name} ({p.required_structure.acronym})"
                    if p.required_structure else "— (structure non définie)"
                )
                ligne = f"Ligne {p.quota_line}" if p.quota_line else "—"
                self.stdout.write(f"  [{p.order:2d}] {p.title}")
                self.stdout.write(f"        → {structure}  ·  {ligne}  ·  {statut}")

        total = len(postes)
        self.stdout.write(
            "\n" + "-" * 60 +
            f"\nTOTAL : {total} poste(s)  ·  {pourvus} pourvu(s)  ·  {total - pourvus} vacant(s)\n"
        )
