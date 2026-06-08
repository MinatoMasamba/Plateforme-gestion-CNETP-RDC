"""
Commande de management pour peupler PosteNominatifCTC avec les 20 postes
nominatifs officiels de la Cellule Technique de Coordination, tels que décrits
dans la section 3.2 « La Cellule Technique de Coordination / Secrétariat
Technique (20 Postes) » du Manuel Organisationnel CNETP 2026 (validé le
22/05/2026).

Chaque poste est rattaché à sa structure d'origine exigée (référence
« Quota Ligne X » du Tableau 1). Les postes sont créés VACANTS (holder=None) :
l'affectation nominative d'un expert à un poste se fera séparément, une fois
les experts inscrits — cf. CTCMembership pour les adhésions réelles.

Idempotente : utilise get_or_create sur (ctc, title).
"""

from django.core.management.base import BaseCommand, CommandError

from apps.experts.models import Structure
from apps.governance.models import TechnicalCell, PosteNominatifCTC


class Command(BaseCommand):
    help = (
        "Peuple PosteNominatifCTC avec les 20 postes nominatifs officiels de la "
        "Cellule Technique de Coordination (manuel organisationnel CNETP 2026, section 3.2)"
    )

    # (ordre, role, intitulé nominatif, nom de la Structure requise, n° Ligne / Tableau 1)
    POSTES = [
        # ---- Direction des Opérations (3 postes) ----
        (1, 'COORDINATOR',
         "Coordonnateur Technique Principal — Directeur du Service de Règlementation et Normes (Statutaire)",
         'Secrétariat Général aux ITP', 1),
        (2, 'VICE_COORDINATOR',
         "Coordonnateur Adjoint — Ingénieur expert en management de projets complexes",
         'Cabinet du Ministre des ITP', 2),
        (3, 'EXECUTIVE',
         "Assistant Exécutif de la Cellule — Cadre de direction",
         'Secrétariat Général aux ITP', 1),

        # ---- Pôle d'Analyse et d'Ingénierie Documentaire (7 postes) ----
        (4, 'ISO_EXPERT',
         "Expert en veille normative et traduction (1/2 — conformité ISO)",
         'Agence Congolaise des Grands Travaux', 6),
        (5, 'ISO_EXPERT',
         "Expert en veille normative et traduction (2/2)",
         'Secrétariat Général aux ITP', 1),
        (6, 'LEGAL',
         "Expert Juridique permanent — mise en conformité réglementaire avant plénière",
         'Experts Juridiques Spécialisés', 13),
        (7, 'ENVIRONMENTAL',
         "Expert en Sauvegardes Environnementales et Sociales",
         'Cellule Infrastructures', 9),
        (8, 'PLANNER',
         "Expert en Planification Opérationnelle",
         'Secrétariat Général à la Reconstruction', 3),
        (9, 'ECONOMIST',
         "Expert Économiste — étude d'impact financier",
         "Fonds National d'Entretien Routier", 8),
        (10, 'SCIENTIFIC',
         "Conseiller Scientifique permanent (quota Académique / INBTP)",
         'Institutions Académiques et de Recherche', 14),

        # ---- Pôle Logistique, Communication et Relations Extérieures (4 postes) ----
        (11, 'ACCOUNTANT',
         "Gestionnaire Administratif et Financier — Comptable commis par le SG-ITP",
         'Secrétariat Général aux ITP', 1),
        (12, 'ENQUIRY_MANAGER',
         "Responsable des Relations Extérieures et d'Organisation des Enquêtes Publiques",
         'Cabinet du Ministre des ITP', 2),
        (13, 'INDUSTRIAL',
         "Expert de Liaison Industrielle",
         'Fédération des Entreprises du Congo', 17),
        (14, 'COMMUNICATOR',
         "Spécialiste en Communication et Vulgarisation",
         'Cabinet du Ministre des ITP', 2),

        # ---- Bureau d'Appui Technique et Numérique (6 postes) ----
        (15, 'CARTOGRAPHER',
         "Ingénieur Cartographe / Expert SIG (1/2 — numérisation des tracés)",
         "Bureau d'Études d'Aménagement Urbain", 10),
        (16, 'CARTOGRAPHER',
         "Ingénieur Cartographe / Expert SIG (2/2 — numérisation des tracés)",
         'Office des Voiries et Drainage', 5),
        (17, 'DATA_ENTRY',
         "Opérateur de Saisie / Secrétaire d'administration (1/2 — mis à disposition par le BTC)",
         'Bureau Technique de Contrôle', 7),
        (18, 'DATA_ENTRY',
         "Opérateur de Saisie / Secrétaire d'administration (2/2 — mis à disposition par le BTC)",
         'Bureau Technique de Contrôle', 7),
        (19, 'IT_ADMIN',
         "Technicien IT / Administrateur de la Plateforme d'Enquête Publique (1/2)",
         'Bureau Technique de Contrôle', 7),
        (20, 'IT_ADMIN',
         "Technicien IT / Administrateur de la Plateforme d'Enquête Publique (2/2)",
         'Secrétariat Général aux ITP', 1),
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            "=== Peuplement des 20 postes nominatifs — Cellule Technique de Coordination "
            "(Manuel CNETP 2026, section 3.2) ===\n"
        ))

        try:
            ctc = TechnicalCell.objects.get(name="Cellule Technique de Coordination CNETP")
        except TechnicalCell.DoesNotExist:
            raise CommandError(
                "La Cellule Technique de Coordination CNETP n'existe pas. "
                "Exécutez d'abord : python manage.py init_pilotage_and_ctc"
            )

        created_count = 0
        existing_count = 0
        missing_structures = set()

        for order, role, title, structure_name, quota_line in self.POSTES:
            structure = Structure.objects.filter(name=structure_name).first()
            if structure is None:
                missing_structures.add(structure_name)

            poste, created = PosteNominatifCTC.objects.get_or_create(
                ctc=ctc,
                title=title,
                defaults={
                    'role': role,
                    'required_structure': structure,
                    'quota_line': quota_line,
                    'order': order,
                }
            )
            marker = "✓ créé" if created else "• déjà présent"
            if created:
                created_count += 1
            else:
                existing_count += 1
            structure_label = structure.acronym if structure else "⚠ STRUCTURE INTROUVABLE"
            self.stdout.write(f"  [{order:2d}] {marker:14s} {poste.title}  →  {structure_label} (Ligne {quota_line})")

        if missing_structures:
            self.stdout.write(self.style.ERROR(
                f"\n❌ Structures introuvables dans la table Structure (vérifiez "
                f"seed_official_structures) : {', '.join(sorted(missing_structures))}"
            ))

        total = PosteNominatifCTC.objects.filter(ctc=ctc).count()
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Terminé — {created_count} poste(s) créé(s), {existing_count} déjà présent(s).\n"
            f"Total postes nominatifs pour cette cellule : {total} / 20 attendus"
        ))
