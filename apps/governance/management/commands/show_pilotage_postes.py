"""
Commande d'affichage (lecture seule, ne modifie rien) des 27 postes nominatifs
du Comité de Pilotage Élargi : regroupés par collège, avec leur structure
d'origine exigée (référence "Ligne X" du Tableau 1) et leur statut
(vacant / pourvu).

Usage : python manage.py show_pilotage_postes
"""

from django.core.management.base import BaseCommand, CommandError

from apps.governance.models import ComitePilotage, PosteNominatif


GROUPES = [
    ("BUREAU DIRECTOIRE", ('PRESIDENT', 'VICE_PRESIDENT', 'SECRETARY', 'RAPPORTEUR')),
    ("COLLÈGE DES CONSEILLERS INSTITUTIONNELS ET POLITIQUES", ('CONSEILLER_POLITIQUE',)),
    ("COLLÈGE DES ADMINISTRATEURS TECHNIQUES ET FINANCIERS", ('ADMIN_TECH_FIN',)),
    ("COLLÈGE DES PARTENAIRES SECTORIELS ET DE LA SOCIÉTÉ CIVILE", ('PARTENAIRE_SOC_CIV',)),
]


class Command(BaseCommand):
    help = "Affiche (lecture seule) les 27 postes nominatifs du Comité de Pilotage Élargi, par collège"

    def handle(self, *args, **options):
        try:
            comite = ComitePilotage.objects.get(name="Comité de Pilotage Élargi CNETP")
        except ComitePilotage.DoesNotExist:
            raise CommandError(
                "Le Comité de Pilotage Élargi CNETP n'existe pas encore. "
                "Exécutez d'abord : python manage.py init_pilotage_and_ctc"
            )

        postes = list(
            PosteNominatif.objects
            .filter(comite=comite)
            .select_related('required_structure', 'holder')
            .order_by('order')
        )

        self.stdout.write(self.style.SUCCESS(
            "\n" + "=" * 78 +
            "\n  COMITÉ DE PILOTAGE ÉLARGI — 27 POSTES NOMINATIFS"
            "\n  (Manuel Organisationnel CNETP 2026, section 3.1 — quotas du Tableau 1)"
            "\n" + "=" * 78
        ))

        if not postes:
            self.stdout.write(self.style.WARNING(
                "\nAucun poste en base. Exécutez d'abord : python manage.py seed_pilotage_postes\n"
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
