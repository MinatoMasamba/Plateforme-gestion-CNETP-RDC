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
    POSTES = [
        # ---- Bureau Directoire (5 postes) ----
        (1, 'PRESIDENT',
         "Président — Cabinet du Ministre des ITP",
         'Cabinet du Ministre des ITP', 2),
        (2, 'VICE_PRESIDENT',
         "Vice-Président — Ordre National des Ingénieurs du Congo (ONIC)",
         'Ordres Professionnels et Associations Professionnelles', 15),
        (3, 'VICE_PRESIDENT',
         "Vice-Président — Association/Conseil Interprofessionnel du BTP (AIBTP/CNIRS-BTP)",
         'Ordres Professionnels et Associations Professionnelles', 15),
        (4, 'SECRETARY',
         "Secrétaire — Institutions Académiques et de Recherche",
         'Institutions Académiques et de Recherche', 14),
        (5, 'RAPPORTEUR',
         "Rapporteur Général — Secrétariat Général aux ITP",
         'Secrétariat Général aux ITP', 1),

        # ---- Collège des Conseillers Institutionnels et Politiques (12 postes) ----
        (6, 'CONSEILLER_POLITIQUE',
         "Conseiller Institutionnel et Politique — Cabinet du Ministre des ITP (1/2)",
         'Cabinet du Ministre des ITP', 2),
        (7, 'CONSEILLER_POLITIQUE',
         "Conseiller Institutionnel et Politique — Cabinet du Ministre des ITP (2/2)",
         'Cabinet du Ministre des ITP', 2),
        (8, 'CONSEILLER_POLITIQUE',
         "Conseiller Institutionnel et Politique — Secrétariat Général aux ITP",
         'Secrétariat Général aux ITP', 1),
        (9, 'CONSEILLER_POLITIQUE',
         "Conseiller Institutionnel et Politique — Secrétariat Général à la Reconstruction (1/2)",
         'Secrétariat Général à la Reconstruction', 3),
        (10, 'CONSEILLER_POLITIQUE',
         "Conseiller Institutionnel et Politique — Secrétariat Général à la Reconstruction (2/2)",
         'Secrétariat Général à la Reconstruction', 3),
        (11, 'CONSEILLER_POLITIQUE',
         "Conseiller Institutionnel et Politique — Représentant des Ministères Partenaires (1/5)",
         'Autres Ministères', 12),
        (12, 'CONSEILLER_POLITIQUE',
         "Conseiller Institutionnel et Politique — Représentant des Ministères Partenaires (2/5)",
         'Autres Ministères', 12),
        (13, 'CONSEILLER_POLITIQUE',
         "Conseiller Institutionnel et Politique — Représentant des Ministères Partenaires (3/5)",
         'Autres Ministères', 12),
        (14, 'CONSEILLER_POLITIQUE',
         "Conseiller Institutionnel et Politique — Représentant des Ministères Partenaires (4/5)",
         'Autres Ministères', 12),
        (15, 'CONSEILLER_POLITIQUE',
         "Conseiller Institutionnel et Politique — Représentant des Ministères Partenaires (5/5) "
         "[⚠ le manuel annonce 5 postes mais nomme 6 ministères — cf. avertissement final]",
         'Autres Ministères', 12),
        (16, 'CONSEILLER_POLITIQUE',
         "Conseiller Juridique Spécialisé (1/2)",
         'Experts Juridiques Spécialisés', 13),
        (17, 'CONSEILLER_POLITIQUE',
         "Conseiller Juridique Spécialisé (2/2)",
         'Experts Juridiques Spécialisés', 13),

        # ---- Collège des Administrateurs Techniques et Financiers (5 postes) ----
        (18, 'ADMIN_TECH_FIN',
         "Administrateur Technique et Financier — Office des Routes (OR)",
         'Office des Routes', 4),
        (19, 'ADMIN_TECH_FIN',
         "Administrateur Technique et Financier — Office des Voiries et Drainage (OVD)",
         'Office des Voiries et Drainage', 5),
        (20, 'ADMIN_TECH_FIN',
         "Administrateur Technique et Financier — Agence Congolaise des Grands Travaux (ACGT)",
         'Agence Congolaise des Grands Travaux', 6),
        (21, 'ADMIN_TECH_FIN',
         "Administrateur Technique et Financier — Bureau Technique de Contrôle (BTC)",
         'Bureau Technique de Contrôle', 7),
        (22, 'ADMIN_TECH_FIN',
         "Administrateur Technique et Financier — Fonds National d'Entretien Routier (FONER)",
         "Fonds National d'Entretien Routier", 8),

        # ---- Collège des Partenaires Sectoriels et de la Société Civile (5 postes) ----
        (23, 'PARTENAIRE_SOC_CIV',
         "Partenaire Sectoriel et Société Civile — Ordre National des Architectes (ONA)",
         'Ordres Professionnels et Associations Professionnelles', 15),
        (24, 'PARTENAIRE_SOC_CIV',
         "Partenaire Sectoriel et Société Civile — Syndicats Professionnels du BTP",
         'Ordres Professionnels et Associations Professionnelles', 15),
        (25, 'PARTENAIRE_SOC_CIV',
         "Partenaire Sectoriel et Société Civile — Bureau d'Études d'Aménagement Urbain (BEAU)",
         "Bureau d'Études d'Aménagement Urbain", 10),
        (26, 'PARTENAIRE_SOC_CIV',
         "Partenaire Sectoriel et Société Civile — Fédération des Entreprises du Congo (FEC)",
         'Fédération des Entreprises du Congo', 17),
        (27, 'PARTENAIRE_SOC_CIV',
         "Partenaire Sectoriel et Société Civile — Office Congolais de Contrôle (OCC)",
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
        """Signale (sans les corriger) deux écarts de données qui nécessitent un arbitrage humain."""
        self.stdout.write(self.style.WARNING(
            "\n--- ⚠️  Points à arbitrer manuellement (non corrigés automatiquement) ---"
        ))

        # 1. L'adhésion Rapporteur pré-existante correspond-elle à la Ligne 1 (SG-ITP) ?
        rapporteur = (
            PilotageMembreship.objects
            .filter(comite=comite, role='RAPPORTEUR')
            .select_related('expert', 'expert__structure')
            .first()
        )
        if rapporteur and rapporteur.expert:
            structure_actuelle = rapporteur.expert.structure.name if rapporteur.expert.structure else "—"
            if structure_actuelle != 'Secrétariat Général aux ITP':
                self.stdout.write(
                    f"  1. PilotageMembreship existante : le Rapporteur Général affecté "
                    f"« {rapporteur.expert.full_name} » provient de « {structure_actuelle} », "
                    f"alors que le manuel exige la Ligne 1 (Secrétariat Général aux ITP). "
                    f"Cette adhésion n'a PAS été modifiée — à réconcilier une fois sa "
                    f"vraie structure d'origine confirmée."
                )

        # 2. Incohérence interne du manuel : 5 postes annoncés mais 6 ministères nommés
        self.stdout.write(
            "  2. Le manuel annonce « 5 Représentants des Ministères Partenaires » "
            "(Collège des Conseillers, Ligne 12) mais en NOMME 6 (Urbanisme, Aménagement "
            "du Territoire, Environnement, Affaires Foncières, ITP/Ville de Kinshasa, "
            "OVDA). J'ai créé exactement 5 postes — conforme au total officiel "
            "(12 = 2+1+2+5+2 et 27/200 au global) — le 5e porte une note ⚠ ; "
            "tranchez lequel des 6 organismes occupe ce poste quand vous aurez la "
            "clarification du Bureau."
        )
