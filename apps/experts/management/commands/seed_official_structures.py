"""
Commande de management pour peupler la table Structure avec les 17 lignes
officielles du Tableau 1 du Manuel Organisationnel CNETP 2026 (validé le 22/05/2026).

Idempotente : utilise get_or_create, peut être ré-exécutée sans créer de doublons
ni modifier les structures déjà présentes (ex: Université de Kinshasa, Default Structure).
"""

from django.core.management.base import BaseCommand
from apps.experts.models import Structure


class Command(BaseCommand):
    help = "Peuple Structure avec les 17 lignes officielles du Tableau 1 (quotas CNETP, total = 200 sièges)"

    STRUCTURES = [
        # (name, acronym, category, description)
        ('Secrétariat Général aux ITP', 'SG-ITP', 'ADMIN',
         'Quota Ligne 1 — 15 sièges (7,50 %)'),
        ('Cabinet du Ministre des ITP', 'CAB-MIN-ITP', 'ADMIN',
         'Quota Ligne 2 — 12 sièges (6,00 %)'),
        ('Secrétariat Général à la Reconstruction', 'SG-RECONS', 'ADMIN',
         'Quota Ligne 3 — 12 sièges (6,00 %)'),
        ('Office des Routes', 'OR', 'PUBLIC',
         'Quota Ligne 4 — 12 sièges (6,00 %)'),
        ('Office des Voiries et Drainage', 'OVD', 'PUBLIC',
         'Quota Ligne 5 — 12 sièges (6,00 %)'),
        ('Agence Congolaise des Grands Travaux', 'ACGT', 'PUBLIC',
         'Quota Ligne 6 — 12 sièges (6,00 %)'),
        ('Bureau Technique de Contrôle', 'BTC', 'PUBLIC',
         'Quota Ligne 7 — 10 sièges (5,00 %)'),
        ("Fonds National d'Entretien Routier", 'FONER', 'PUBLIC',
         'Quota Ligne 8 — 10 sièges (5,00 %)'),
        ('Cellule Infrastructures', 'CI', 'PUBLIC',
         'Quota Ligne 9 — 10 sièges (5,00 %)'),
        ("Bureau d'Études d'Aménagement Urbain", 'BEAU', 'PUBLIC',
         'Quota Ligne 10 — 8 sièges (4,00 %)'),
        ('Office des Voies de Desserte Agricole', 'OVDA', 'PUBLIC',
         'Quota Ligne 11 — 8 sièges (4,00 %)'),
        ('Autres Ministères', 'AUTRES-MIN', 'ADMIN',
         "Regroupe : Urbanisme, Aménagement du Territoire, Affaires Foncières, "
         "Développement Rural, Environnement, ITP/Ville de Kinshasa — "
         "Quota Ligne 12 — 15 sièges (7,50 %)"),
        ('Experts Juridiques Spécialisés', 'EJS', 'ADMIN',
         'Quota Ligne 13 — 8 sièges (4,00 %)'),
        ('Institutions Académiques et de Recherche', 'IAR', 'ACAD',
         "Regroupe : ISTA, INBTP, UNIKIN, etc. — Quota Ligne 14 — 20 sièges (10,00 %)"),
        ('Ordres Professionnels et Associations Professionnelles', 'OPA', 'PROF',
         "Regroupe : ordres/régulateurs (ONIC, ONA, CUC) et associations "
         "(CNIRS-BTP, FIGT, CEICO, etc.) — Quota Ligne 15 — 22 sièges (11,00 %)"),
        ('Société Civile et Organismes Techniques', 'SCOT', 'METRO',
         "Regroupe notamment l'OCC (Office Congolais de Contrôle), etc. — "
         "Quota Ligne 16 — 8 sièges (4,00 %)"),
        ('Fédération des Entreprises du Congo', 'FEC', 'PRIVATE',
         'Quota Ligne 17 — 6 sièges (3,00 %)'),
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            "=== Peuplement des structures officielles (Tableau 1 — Manuel CNETP 2026) ===\n"
        ))

        created_count = 0
        existing_count = 0

        for name, acronym, category, description in self.STRUCTURES:
            structure, created = Structure.objects.get_or_create(
                name=name,
                defaults={
                    'acronym': acronym,
                    'category': category,
                    'description': description,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"  ✓ Créée : {structure.name} ({structure.acronym})")
            else:
                existing_count += 1
                self.stdout.write(f"  • Déjà existante : {structure.name} ({structure.acronym})")

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Terminé — {created_count} structure(s) créée(s), "
            f"{existing_count} déjà présente(s).\n"
            f"Total structures en base : {Structure.objects.count()}"
        ))
