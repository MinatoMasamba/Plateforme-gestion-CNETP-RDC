"""
Commande de management pour peupler PosteNominatif avec les 27 postes
nominatifs officiels du Comité de Pilotage Élargi, tels que décrits dans la
section 3.1 « Le Comité de Pilotage Élargi (27 Postes) » du Manuel
Organisationnel CNETP 2026 (validé le 22/05/2026).

Chaque poste est rattaché à sa structure d'origine exigée (référence
« Quota Ligne X » du Tableau 1). Les postes sont créés VACANTS (holder=None) :
l'affectation nominative d'un expert à un poste se fera séparément, une fois
les experts inscrits — cf. PilotageMembreship pour les adhésions réelles.

Idempotente : utilise get_or_create sur (comite, title).
"""

from django.core.management.base import BaseCommand, CommandError

from apps.experts.models import Structure
from apps.governance.models import ComitePilotage, PilotageMembreship, PosteNominatif


class Command(BaseCommand):
    help = (
        "Peuple PosteNominatif avec les 27 postes nominatifs officiels du "
        "Comité de Pilotage Élargi (manuel organisationnel CNETP 2026, section 3.1)"
    )

    # (ordre, role, intitulé nominatif, nom de la Structure requise, n° Ligne / Tableau 1)
    # Intitulés conformes à la section 3.1 « Le Comité de Pilotage Élargi (27
    # Postes) » et à la Cartographie des 200 Postes (Annexe) du Manuel
    # Organisationnel CNETP 2026.
    POSTES = [
        # ---- Bureau Directoire (5 postes) ----
        (1, 'PRESIDENT',
         "Président du Comité de Pilotage Élargi",
         'Cabinet du Ministre des ITP', 2),
        (2, 'VICE_PRESIDENT',
         "Vice-Président — Ordre National des Ingénieurs Civils (ONIC)",
         'Ordres Professionnels et Associations Professionnelles', 15),
        (3, 'VICE_PRESIDENT',
         "Vice-Président — Association des Ingénieurs BTP (AIBTP)",
         'Ordres Professionnels et Associations Professionnelles', 15),
        (4, 'SECRETARY',
         "Secrétaire du Comité de Pilotage Élargi",
         'Institutions Académiques et de Recherche', 14),
        (5, 'RAPPORTEUR',
         "Rapporteur Général du Comité de Pilotage Élargi",
         'Secrétariat Général aux ITP', 1),

        # ---- Collège des Conseillers Institutionnels et Politiques (12 postes) ----
        (6, 'CONSEILLER_POLITIQUE',
         "Conseiller Technique — Cabinet du Ministre des ITP (1/2)",
         'Cabinet du Ministre des ITP', 2),
        (7, 'CONSEILLER_POLITIQUE',
         "Conseiller Technique — Cabinet du Ministre des ITP (2/2)",
         'Cabinet du Ministre des ITP', 2),
        (8, 'CONSEILLER_POLITIQUE',
         "Conseiller en Planification — Secrétariat Général aux ITP",
         'Secrétariat Général aux ITP', 1),
        (9, 'CONSEILLER_POLITIQUE',
         "Cadre Supérieur — Secrétariat Général à la Reconstruction (1/2)",
         'Secrétariat Général à la Reconstruction', 3),
        (10, 'CONSEILLER_POLITIQUE',
         "Cadre Supérieur — Secrétariat Général à la Reconstruction (2/2)",
         'Secrétariat Général à la Reconstruction', 3),
        (11, 'CONSEILLER_POLITIQUE',
         "Représentant expert du Ministère de l'Urbanisme et Habitat",
         'Autres Ministères', 12),
        (12, 'CONSEILLER_POLITIQUE',
         "Représentant expert du Ministère de l'Aménagement du Territoire",
         'Autres Ministères', 12),
        (13, 'CONSEILLER_POLITIQUE',
         "Représentant expert du Ministère de l'Environnement",
         'Autres Ministères', 12),
        (14, 'CONSEILLER_POLITIQUE',
         "Représentant expert du Ministère des Affaires Foncières",
         'Autres Ministères', 12),
        (15, 'CONSEILLER_POLITIQUE',
         "Représentant expert de la Division des ITP / Ville de Kinshasa",
         'Autres Ministères', 12),
        (16, 'CONSEILLER_POLITIQUE',
         "Conseiller Juridique expert en légistique (1/2)",
         'Experts Juridiques Spécialisés', 13),
        (17, 'CONSEILLER_POLITIQUE',
         "Conseiller Juridique expert en légistique (2/2)",
         'Experts Juridiques Spécialisés', 13),

        # ---- Collège des Administrateurs Techniques et Financiers (5 postes) ----
        (18, 'ADMIN_TECH_FIN',
         "Directeur Technique — Office des Routes (OR)",
         'Office des Routes', 4),
        (19, 'ADMIN_TECH_FIN',
         "Directeur Technique — Office des Voiries et Drainage (OVD)",
         'Office des Voiries et Drainage', 5),
        (20, 'ADMIN_TECH_FIN',
         "Directeur des Normes et de l'Innovation — Agence Congolaise des Grands Travaux (ACGT)",
         'Agence Congolaise des Grands Travaux', 6),
        (21, 'ADMIN_TECH_FIN',
         "Directeur d'Expertise — Bureau Technique de Contrôle (BTC)",
         'Bureau Technique de Contrôle', 7),
        (22, 'ADMIN_TECH_FIN',
         "Directeur des Études Financières — Fonds National d'Entretien Routier (FONER)",
         "Fonds National d'Entretien Routier", 8),

        # ---- Collège des Partenaires Sectoriels et de la Société Civile (5 postes) ----
        (23, 'PARTENAIRE_SOC_CIV',
         "Représentant de l'Ordre National des Architectes (ONA)",
         'Ordres Professionnels et Associations Professionnelles', 15),
        (24, 'PARTENAIRE_SOC_CIV',
         "Représentant des Syndicats et Organismes de Régulation",
         'Ordres Professionnels et Associations Professionnelles', 15),
        (25, 'PARTENAIRE_SOC_CIV',
         "Administrateur Technique — Bureau d'Études d'Aménagement Urbain (BEAU)",
         "Bureau d'Études d'Aménagement Urbain", 10),
        (26, 'PARTENAIRE_SOC_CIV',
         "Représentant du Patronat et du Secteur BTP Privé — Fédération des Entreprises du Congo (FEC)",
         'Fédération des Entreprises du Congo', 17),
        (27, 'PARTENAIRE_SOC_CIV',
         "Directeur Technique — Office Congolais de Contrôle (OCC)",
         'Société Civile et Organismes Techniques', 16),
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            "=== Peuplement des 27 postes nominatifs — Comité de Pilotage Élargi "
            "(Manuel CNETP 2026, section 3.1) ===\n"
        ))

        try:
            comite = ComitePilotage.objects.get(name="Comité de Pilotage Élargi CNETP")
        except ComitePilotage.DoesNotExist:
            raise CommandError(
                "Le Comité de Pilotage Élargi CNETP n'existe pas. "
                "Exécutez d'abord : python manage.py init_pilotage_and_ctc"
            )

        created_count = 0
        existing_count = 0
        missing_structures = set()

        for order, role, title, structure_name, quota_line in self.POSTES:
            structure = Structure.objects.filter(name=structure_name).first()
            if structure is None:
                missing_structures.add(structure_name)

            poste, created = PosteNominatif.objects.get_or_create(
                comite=comite,
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

        total = PosteNominatif.objects.filter(comite=comite).count()
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Terminé — {created_count} poste(s) créé(s), {existing_count} déjà présent(s).\n"
            f"Total postes nominatifs pour ce comité : {total} / 27 attendus"
        ))

        self._signaler_incoherences(comite)

    def _signaler_incoherences(self, comite):
        """Signale (sans la corriger) une réconciliation de données restant à faire."""
        # L'adhésion Rapporteur pré-existante correspond-elle à la Ligne 1 (SG-ITP) ?
        rapporteur = (
            PilotageMembreship.objects
            .filter(comite=comite, role='RAPPORTEUR')
            .select_related('expert', 'expert__structure')
            .first()
        )
        if rapporteur and rapporteur.expert:
            structure_actuelle = rapporteur.expert.structure.name if rapporteur.expert.structure else "—"
            if structure_actuelle != 'Secrétariat Général aux ITP':
                self.stdout.write(self.style.WARNING(
                    "\n--- ⚠️  Point à arbitrer manuellement (non corrigé automatiquement) ---"
                ))
                self.stdout.write(
                    f"  PilotageMembreship existante : le Rapporteur Général affecté "
                    f"« {rapporteur.expert.full_name} » provient de « {structure_actuelle} », "
                    f"alors que le manuel exige la Ligne 1 (Secrétariat Général aux ITP). "
                    f"Cette adhésion n'a PAS été modifiée — à réconcilier une fois sa "
                    f"vraie structure d'origine confirmée."
                )
