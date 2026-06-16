"""
Migration de données — AgentPosteContext
Pré-remplit les 27 postes du Comité de Pilotage Stratégique
et les 19 sous-rôles de la Cellule Technique de Coordination.

Source : Manuel d'Organisation Structurelle et Fonctionnelle CNETP 2026
         + Cartographie Nominative des 200 Postes (AFFECTATION 2026).
"""
from django.db import migrations


# ─── 27 postes Pilotage ───────────────────────────────────────────────────────
# Distribution :
#   Profil 1 — Bureau Directoire          :  5 postes  (niveaux 1-2)
#   Profil 2 — Conseillers Institutionnels : 12 postes  (niveau  3)
#   Profil 3 — Administrateurs Tech & Fin  :  5 postes  (niveau  4)
#   Profil 4 — Partenaires & Sté Civile    :  5 postes  (niveau  5)
# Total = 27 sous-rôles distincts (certains couvrent plusieurs postes physiques)

PILOTAGE_POSTES = [
    # ── Profil 1 : Bureau Directoire ─────────────────────────────────────────
    {
        'sub_role': 'president',
        'hierarchy_level': 1,
        'position_label': (
            "Président du Comité de Pilotage Stratégique CNETP "
            "(Haut Cadre du Cabinet du Ministre des ITP — Poste 1) "
            "— Plus haute autorité opérationnelle de la Commission"
        ),
        'mission_summary': (
            "Définit la politique nationale de normalisation des infrastructures. "
            "Arbitre les conflits d'intérêts sectoriels entre ministères et offices. "
            "Suit l'exécution du budget de la Commission. "
            "Valide formellement les projets de normes avant l'Assemblée Plénière. "
            "Ouvre les chantiers normatifs (Phase 1.1 — orientation stratégique). "
            "Signe les résolutions finales (Phase 2.3 — validation finale). "
            "Détient l'autorité souveraine de verrouillage/déverrouillage de la plateforme CTC/CTM."
        ),
        'tools_hint': (
            "Autorité souveraine — accès complet à tous les outils analytiques : "
            "get_chart_data (métriques : normes_by_status, normes_by_ctm, votes_participation, "
            "public_inquiry_status, experts_by_structure, wg_overlap_summary), "
            "detect_wg_overlap, flag_norm_overlap, search_external_referentials, "
            "propose_external_reference, synthesize_public_inquiry, list_ctm_norms."
        ),
    },
    {
        'sub_role': 'vice_president_onic',
        'hierarchy_level': 2,
        'position_label': (
            "1er Vice-Président du Comité de Pilotage "
            "(Représentant sénior de l'Ordre National des Ingénieurs Civils — ONIC, Poste 137)"
        ),
        'mission_summary': (
            "Représente l'Ordre National des Ingénieurs Civils (ONIC). "
            "Valide la légitimité technique des experts WG du giron Ingénierie (Phase 1.2 — EXPERTS_REVIEW). "
            "Émet le quitus de conformité technique du giron Ingénierie (Phase 2.2 — CONFORMITY_QUITUS). "
            "Remplace le Président en cas d'empêchement. "
            "Défend les règles de l'art de l'ingénierie civile dans tous les CTM."
        ),
        'tools_hint': (
            "Accès aux tableaux de bord des CTM du giron Ingénierie. "
            "Outils : get_chart_data, detect_wg_overlap, search_external_referentials, list_ctm_norms."
        ),
    },
    {
        'sub_role': 'vice_president_btp',
        'hierarchy_level': 2,
        'position_label': (
            "2nd Vice-Président du Comité de Pilotage "
            "(Représentant du secteur BTP / Construction — Bureau Directoire)"
        ),
        'mission_summary': (
            "Valide le mandat opérationnel des experts WG du secteur BTP/Construction (Phase 1.2). "
            "Émet le quitus de conformité technique du secteur BTP (Phase 2.2). "
            "Représente les intérêts des professionnels de la construction congolaise. "
            "Remplace le Président en l'absence du 1er Vice-Président."
        ),
        'tools_hint': (
            "Accès aux tableaux de bord des CTM du secteur BTP. "
            "Outils : get_chart_data, detect_wg_overlap, search_external_referentials, list_ctm_norms."
        ),
    },
    {
        'sub_role': 'secretary',
        'hierarchy_level': 2,
        'position_label': (
            "Secrétaire du Comité de Pilotage Stratégique "
            "(Professeur Ordinaire, Institutions Académiques — Poste 167)"
        ),
        'mission_summary': (
            "Formalise les mandats opérationnels transmis aux CTM (Phase 1.3 — MANDATE_FORMALIZATION). "
            "Vérifie la régularité procédurale du PV de l'Assemblée Plénière (Phase 2.1 — PV_VERIFICATION). "
            "Assure la rigueur académique et scientifique des travaux de la Commission. "
            "Représente les institutions académiques (ISTA, UNIKIN, INBTP)."
        ),
        'tools_hint': (
            "Accès aux documents de mandat, PV et rapports académiques. "
            "Outils : get_chart_data, synthesize_public_inquiry, list_ctm_norms."
        ),
    },
    {
        'sub_role': 'rapporteur',
        'hierarchy_level': 2,
        'position_label': (
            "Rapporteur Général du Comité de Pilotage Stratégique "
            "(Haut Cadre du Secrétariat Général aux ITP — Poste 13)"
        ),
        'mission_summary': (
            "Établit le chronogramme opérationnel et l'ordre de service à la CTC (Phase 1.4 — SCHEDULED). "
            "Réceptionne officiellement les dossiers nettoyés par la CTC (étape SIGNED_OUT). "
            "Produit le rapport consolidé des travaux pour l'Assemblée Plénière. "
            "Interface opérationnelle entre le Bureau Directoire et la CTC."
        ),
        'tools_hint': (
            "Accès aux processus CTC en attente de réception et aux chronogrammes. "
            "Outils : get_chart_data, list_ctm_norms, synthesize_public_inquiry."
        ),
    },

    # ── Profil 2 : Conseillers Institutionnels (12 postes physiques) ──────────
    # Couverts par 2 sous-rôles distincts (politique + juridique)
    {
        'sub_role': 'conseiller_politique',
        'hierarchy_level': 3,
        'position_label': (
            "Conseiller Institutionnel / Membre du Collège des Conseillers "
            "(Comité de Pilotage Stratégique — Postes 2, 3, 28, 29, 40, 41, 42)"
        ),
        'mission_summary': (
            "Représente sa structure d'origine au sein du Comité de Pilotage. "
            "Peut être issu du Cabinet du Ministre des ITP (Postes 2-3), "
            "du Secrétariat Général à la Reconstruction (Postes 28-29), "
            "ou des Ministères partenaires : Urbanisme, Aménagement du Territoire, Environnement (Postes 40-42). "
            "Apporte une vision interministérielle et sectorielle aux délibérations. "
            "Participe aux votes sur les projets de normes."
        ),
        'tools_hint': (
            "Accès en lecture aux tableaux de bord stratégiques et aux normes. "
            "Outils : get_chart_data, list_ctm_norms, detect_wg_overlap, "
            "search_external_referentials, synthesize_public_inquiry."
        ),
    },
    {
        'sub_role': 'juridique',
        'hierarchy_level': 3,
        'position_label': (
            "Conseiller Juridique / Membre du Collège des Conseillers "
            "(Experts Juridiques Spécialisés — Postes 53, 54)"
        ),
        'mission_summary': (
            "Assure la légistique et la conformité légale des projets de normes. "
            "Vérifie la cohérence des textes avec le cadre réglementaire congolais (codes, lois, arrêtés). "
            "Propose des amendements légaux sur tout avant-projet soumis au COPIL. "
            "Représente les Experts Juridiques Spécialisés (légistique contractuelle et administrative)."
        ),
        'tools_hint': (
            "Focus légistique. "
            "Outils : get_chart_data, list_ctm_norms, search_external_referentials, synthesize_public_inquiry."
        ),
    },

    # ── Profil 3 : Administrateurs Techniques et Financiers (5 postes) ────────
    {
        'sub_role': 'atf_or',
        'hierarchy_level': 4,
        'position_label': (
            "Directeur Technique / Administrateur Technique et Financier "
            "(Office des Routes — OR, Poste 61)"
        ),
        'mission_summary': (
            "Représente l'Office des Routes (OR) au Comité de Pilotage. "
            "Expert national du génie routier, des ponts lourds et de la géotechnique. "
            "Contribue à la normalisation des infrastructures de transport (CTM 5) "
            "et des fondations géotechniques (CTM 1). "
            "Apporte les données terrain du réseau routier national (RVA, routes nationales)."
        ),
        'tools_hint': (
            "Spécialiste routes et ponts. "
            "Outils : get_chart_data, list_ctm_norms, detect_wg_overlap, search_external_referentials."
        ),
    },
    {
        'sub_role': 'ovd',
        'hierarchy_level': 4,
        'position_label': (
            "Directeur Technique / Administrateur Technique et Financier "
            "(Office des Voiries et Drainage — OVD, Poste 73)"
        ),
        'mission_summary': (
            "Représente l'Office des Voiries et Drainage (OVD) au Comité de Pilotage. "
            "Expert des voiries urbaines, des réseaux de drainage et de la lutte antiérosive. "
            "Veille à l'intégration des normes de voirie dans les CTM concernés (CTM 5, CTM 7). "
            "Apporte les données du réseau urbain de Kinshasa et des villes secondaires."
        ),
        'tools_hint': (
            "Spécialiste voiries urbaines et drainage. "
            "Outils : get_chart_data, detect_wg_overlap, search_external_referentials, list_ctm_norms."
        ),
    },
    {
        'sub_role': 'acgt',
        'hierarchy_level': 4,
        'position_label': (
            "Directeur Technique / Administrateur Technique et Financier "
            "(Agence Congolaise des Grands Travaux — ACGT, Poste 85)"
        ),
        'mission_summary': (
            "Représente l'Agence Congolaise des Grands Travaux (ACGT) au Comité de Pilotage. "
            "Expert en ingénierie complexe, modélisation structurale et veille ISO/ARSO. "
            "Supervise les BIM Modélisateurs de la plateforme (WG 3.2). "
            "Apporte l'expertise des grands projets d'infrastructure nationaux."
        ),
        'tools_hint': (
            "Spécialiste ingénierie complexe et veille normative. "
            "Outils : get_chart_data, detect_wg_overlap, search_external_referentials, propose_external_reference."
        ),
    },
    {
        'sub_role': 'btc',
        'hierarchy_level': 4,
        'position_label': (
            "Directeur Technique / Administrateur Technique et Financier "
            "(Bureau Technique de Contrôle — BTC, Poste 97)"
        ),
        'mission_summary': (
            "Représente le Bureau Technique de Contrôle (BTC) au Comité de Pilotage. "
            "Expert en audit de conformité et essais en laboratoire (métrologie). "
            "Supervise les Opérateurs de Saisie et les Administrateurs IT de la plateforme. "
            "Veille à la rigueur des protocoles d'essais physiques (ISO/CEI 17025)."
        ),
        'tools_hint': (
            "Spécialiste contrôle qualité et laboratoire. "
            "Outils : get_chart_data, list_ctm_norms, detect_wg_overlap."
        ),
    },
    {
        'sub_role': 'foner',
        'hierarchy_level': 4,
        'position_label': (
            "Directeur Technique / Administrateur Technique et Financier "
            "(Fonds National d'Entretien Routier — FONER, Poste 109)"
        ),
        'mission_summary': (
            "Représente le Fonds National d'Entretien Routier (FONER) au Comité de Pilotage. "
            "Expert en analyse d'impact financier et ratios coût-durabilité des infrastructures. "
            "Analyse la viabilité budgétaire des standards de construction routière. "
            "Fournit les données de rentabilité du cycle de vie des chaussées."
        ),
        'tools_hint': (
            "Spécialiste financement et durabilité des infrastructures. "
            "Outils : get_chart_data (normes_by_status, normes_by_ctm), "
            "detect_wg_overlap, search_external_referentials."
        ),
    },

    # ── Profil 4 : Partenaires Sectoriels & Société Civile (5 postes) ─────────
    {
        'sub_role': 'occ',
        'hierarchy_level': 5,
        'position_label': (
            "Représentant de l'OCC / Partenaire Sectoriel "
            "(Office Congolais de Contrôle — OCC/SCOT, Poste 179)"
        ),
        'mission_summary': (
            "Représente l'Office Congolais de Contrôle (OCC) et la Société Civile. "
            "Expert en métrologie économique et accessibilité universelle. "
            "Vérifie la conformité métrologique des protocoles d'essais (WG 8.2). "
            "Supervise l'étalonnage des appareils de laboratoire (ISO/CEI 17025). "
            "Garant de la qualité des marquages de conformité nationale."
        ),
        'tools_hint': (
            "Expert métrologie et conformité industrielle. "
            "Outils : get_chart_data, list_ctm_norms, detect_wg_overlap."
        ),
    },
    {
        'sub_role': 'ona',
        'hierarchy_level': 5,
        'position_label': (
            "Architecte Senior / Représentant de l'ONA "
            "(Ordre National des Architectes — ONA, Poste 153)"
        ),
        'mission_summary': (
            "Représente l'Ordre National des Architectes (ONA). "
            "Défend les règles de l'art dans le secteur architectural congolais. "
            "Contribue aux normes du CTM 3 (Bâtiments, Urbanisme, Transition Numérique) "
            "et du CTM 8 (Matériaux locaux — BTC, bois d'œuvre). "
            "Garant de la qualité architecturale et de la conformité des codes nationaux."
        ),
        'tools_hint': (
            "Expert architecture, urbanisme et matériaux. "
            "Outils : get_chart_data, list_ctm_norms, detect_wg_overlap, search_external_referentials."
        ),
    },
    {
        'sub_role': 'beau',
        'hierarchy_level': 5,
        'position_label': (
            "Directeur Général / Représentant du BEAU "
            "(Bureau d'Études d'Aménagement Urbain — BEAU, Poste 129)"
        ),
        'mission_summary': (
            "Représente le Bureau d'Études d'Aménagement Urbain (BEAU). "
            "Expert en urbanisme, cartographie SIG et plans directeurs. "
            "Contribue aux normes d'aménagement des villes et d'interface ville-port (CTM 3, CTM 5). "
            "Supervise la cartographie numérique et les études macro-spatiales."
        ),
        'tools_hint': (
            "Expert urbanisme et cartographie. "
            "Outils : get_chart_data, list_ctm_norms, search_external_referentials."
        ),
    },
    {
        'sub_role': 'fec',
        'hierarchy_level': 5,
        'position_label': (
            "Représentant Sectoriel / Partenaire Industriel "
            "(Fédération des Entreprises du Congo — FEC, Poste 194)"
        ),
        'mission_summary': (
            "Représente la Fédération des Entreprises du Congo (FEC). "
            "Assure la faisabilité industrielle des normes : cimentiers, aciéristes, "
            "fabricants de matériaux, grands entrepreneurs. "
            "Consulte sur les procédés de coulage du béton (WG 2.3) et les normes "
            "de production du clinker (WG 8.3). "
            "Interface entre la Commission et le secteur privé industriel."
        ),
        'tools_hint': (
            "Représentant secteur privé industriel. "
            "Outils : get_chart_data, list_ctm_norms, search_external_referentials."
        ),
    },
]

# ─── 19 sous-rôles CTC ────────────────────────────────────────────────────────
# Distribution :
#   Profil 1 — Direction des Opérations           :  3 postes  (niveau 6)
#   Profil 2 — Pôle Analyse & Ingénierie Doc.      :  7 postes  (niveau 7)
#   Profil 3 — Pôle Logistique, Comm. & Ext.       :  4 postes  (niveau 7)
#   Profil 4 — Bureau d'Appui Technique Numérique  :  5 postes  (niveau 7)

CTC_POSTES = [
    # ── Profil 1 : Direction des Opérations ──────────────────────────────────
    {
        'sub_role': 'coordonnateur_principal',
        'hierarchy_level': 6,
        'position_label': (
            "Coordonnateur Technique Principal de la CTC "
            "(Directeur du Service de Réglementation et Normes, SG-ITP — Poste 14)"
        ),
        'mission_summary': (
            "Dirige la Cellule Technique de Coordination (CTC) — Secrétariat Technique de la CNETP. "
            "Gère les flux documentaires ISO/ARSO, pilote la plateforme d'enquête publique numérique. "
            "Effectue le toilettage légistique des textes et consolide les rapports des CTM. "
            "Arbitre les délais de traitement des dossiers. "
            "Transmet les dossiers finalisés au Comité de Pilotage (étape SIGNED_OUT). "
            "Accède à toutes les étapes du processus CTC."
        ),
        'tools_hint': (
            "Direction opérationnelle — accès complet au processus CTC. "
            "Outils : list_ctm_norms, detect_wg_overlap, flag_norm_overlap, "
            "search_external_referentials, propose_external_reference, synthesize_public_inquiry, "
            "get_chart_data, create_email_draft."
        ),
    },
    {
        'sub_role': 'coordonnateur_adjoint',
        'hierarchy_level': 6,
        'position_label': (
            "Coordonnateur Adjoint de la CTC "
            "(Ingénieur expert en management de projets, Cabinet du Ministre — Poste 4)"
        ),
        'mission_summary': (
            "Seconde le Coordonnateur Technique Principal dans la gestion opérationnelle de la CTC. "
            "Représente le Cabinet du Ministre au sein de la CTC. "
            "Assure la coordination interministérielle et la liaison avec le Cabinet. "
            "Accède à toutes les étapes du processus CTC, arbitre les délais. "
            "Remplace le Coordonnateur Principal en cas d'absence."
        ),
        'tools_hint': (
            "Accès complet au processus CTC. "
            "Outils : list_ctm_norms, detect_wg_overlap, flag_norm_overlap, "
            "search_external_referentials, synthesize_public_inquiry, get_chart_data, create_email_draft."
        ),
    },
    {
        'sub_role': 'assistant_executif',
        'hierarchy_level': 6,
        'position_label': (
            "Assistant Exécutif de la Direction des Opérations — CTC "
            "(SG-ITP — Poste 15)"
        ),
        'mission_summary': (
            "Gère les demandes d'accès opérationnelles des membres CTC (PermissionRequest). "
            "Suit les dossiers en attente de traitement dans la file CTC. "
            "Assure le secrétariat administratif central de la CTC. "
            "Coordonne la logistique des réunions et des échanges documentaires."
        ),
        'tools_hint': (
            "Gestion administrative et suivi des demandes. "
            "Outils : list_ctm_norms, synthesize_public_inquiry, create_email_draft."
        ),
    },

    # ── Profil 2 : Pôle d'Analyse et d'Ingénierie Documentaire (7 postes) ────
    {
        'sub_role': 'veille_acgt',
        'hierarchy_level': 7,
        'position_label': (
            "Expert Veille Normative ISO/ARSO — Pôle d'Ingénierie Documentaire, CTC "
            "(ACGT — Poste 86)"
        ),
        'mission_summary': (
            "Effectue la veille normative internationale (ISO) et africaine (ARSO). "
            "Identifie les normes de référence applicables à chaque CTM. "
            "Traduit et adapte les textes ISO/ARSO pour transposition au contexte congolais. "
            "Représente l'ACGT au sein du Pôle d'Ingénierie Documentaire."
        ),
        'tools_hint': (
            "Spécialiste veille ISO/ARSO. "
            "Outils : search_external_referentials, propose_external_reference, "
            "list_ctm_norms, detect_wg_overlap."
        ),
    },
    {
        'sub_role': 'veille_sg',
        'hierarchy_level': 7,
        'position_label': (
            "Expert Veille Normative — Pôle d'Ingénierie Documentaire, CTC "
            "(SG-ITP — Poste 180)"
        ),
        'mission_summary': (
            "Effectue la veille normative internationale (ISO, ARSO, EAC, SADC, COMESA). "
            "Représente le Secrétariat Général aux ITP au sein du Pôle Analyse. "
            "Alimente la matrice de convergence régionale de la CNETP. "
            "Produit les fiches d'alignement normatif pour chaque CTM."
        ),
        'tools_hint': (
            "Veille normative multi-organismes. "
            "Outils : search_external_referentials, propose_external_reference, list_ctm_norms."
        ),
    },
    {
        'sub_role': 'expert_juridique',
        'hierarchy_level': 7,
        'position_label': (
            "Expert Légiste / Légistique — Pôle d'Ingénierie Documentaire, CTC "
            "(Experts Juridiques Spécialisés — Poste 55)"
        ),
        'mission_summary': (
            "Effectue le toilettage légistique des avant-projets de normes. "
            "Vérifie la cohérence des textes avec le droit congolais. "
            "Rédige les exposés des motifs et clauses de transposition légale. "
            "Prépare les textes pour publication au Journal Officiel."
        ),
        'tools_hint': (
            "Focus légistique et rédaction normative. "
            "Outils : list_ctm_norms, search_external_referentials, synthesize_public_inquiry."
        ),
    },
    {
        'sub_role': 'sauvegardes_ci',
        'hierarchy_level': 7,
        'position_label': (
            "Expert Sauvegardes Environnementales — Pôle d'Ingénierie Documentaire, CTC "
            "(Cellule Infrastructure — CI, Poste 122)"
        ),
        'mission_summary': (
            "Intègre les sauvegardes environnementales (Banque Mondiale/BAD) dans les normes. "
            "Analyse l'impact environnemental de chaque standard proposé. "
            "Assure la conformité avec les politiques opérationnelles PO 4.01 (Évaluation Environnementale). "
            "Représente la Cellule Infrastructure au sein du Pôle Analyse."
        ),
        'tools_hint': (
            "Spécialiste sauvegardes éco-environnementales. "
            "Outils : list_ctm_norms, search_external_referentials, detect_wg_overlap."
        ),
    },
    {
        'sub_role': 'planification_recons',
        'hierarchy_level': 7,
        'position_label': (
            "Expert Planification & Reconstruction — Pôle d'Ingénierie Documentaire, CTC "
            "(Secrétariat Général à la Reconstruction — Poste 30)"
        ),
        'mission_summary': (
            "Apporte l'expertise en planification macro-spatiale et reconstruction post-conflit. "
            "Analyse l'impact des normes sur les programmes nationaux de reconstruction. "
            "Produit le chronogramme méthodologique et scientifique pour les CTM. "
            "Représente le Secrétariat Général à la Reconstruction."
        ),
        'tools_hint': (
            "Spécialiste planification et méthodologie. "
            "Outils : list_ctm_norms, search_external_referentials, synthesize_public_inquiry."
        ),
    },
    {
        'sub_role': 'economiste_foner',
        'hierarchy_level': 7,
        'position_label': (
            "Économiste / Analyse Coût-Durabilité — Pôle d'Ingénierie Documentaire, CTC "
            "(FONER — Poste 110)"
        ),
        'mission_summary': (
            "Réalise les études économiques d'impact des normes (coûts de mise en œuvre, "
            "ratios durabilité, rentabilité sur cycle de vie). "
            "Représente le FONER au sein du Pôle Analyse. "
            "Alimente les analyses coût-bénéfice des standards de construction."
        ),
        'tools_hint': (
            "Analyse économique et financière des normes. "
            "Outils : list_ctm_norms, get_chart_data, search_external_referentials."
        ),
    },
    {
        'sub_role': 'scientifique_inbtp',
        'hierarchy_level': 7,
        'position_label': (
            "Conseiller Scientifique — Pôle d'Ingénierie Documentaire, CTC "
            "(INBTP / Institutions Académiques — Poste 180b)"
        ),
        'mission_summary': (
            "Apporte la rigueur scientifique aux avant-projets de normes. "
            "Valide la cohérence des méthodes d'essais avec les standards académiques. "
            "Représente l'Institut National du Bâtiment et des Travaux Publics (INBTP). "
            "Liaisons avec les Présidents Scientifiques des CTM."
        ),
        'tools_hint': (
            "Validation scientifique et académique. "
            "Outils : list_ctm_norms, search_external_referentials, detect_wg_overlap."
        ),
    },

    # ── Profil 3 : Pôle Logistique, Communication et Relations Extérieures ────
    {
        'sub_role': 'gaf',
        'hierarchy_level': 7,
        'position_label': (
            "Gestionnaire Comptable et Financier — Pôle Logistique & Relations Extérieures, CTC "
            "(SG-ITP — Poste 110b)"
        ),
        'mission_summary': (
            "Gère la comptabilité et les finances opérationnelles de la CTC. "
            "Suit le grand livre des dépenses et des allocations de recherche (jetons de présence). "
            "Représente le SG-ITP au sein du Pôle Logistique."
        ),
        'tools_hint': (
            "Gestion administrative et financière. "
            "Outils : get_chart_data, create_email_draft."
        ),
    },
    {
        'sub_role': 'responsable_enquetes',
        'hierarchy_level': 7,
        'position_label': (
            "Responsable des Enquêtes Publiques Numériques — Pôle Logistique, CTC "
            "(Cabinet du Ministre des ITP)"
        ),
        'mission_summary': (
            "Pilote la plateforme d'enquête publique numérique (portail web dédié). "
            "Organise la mise en ligne des avant-projets de normes pour consultation publique. "
            "Collecte et consolide les amendements de la population et des ingénieurs de province. "
            "Représente le Cabinet du Ministre au sein du Pôle Logistique."
        ),
        'tools_hint': (
            "Gestion des enquêtes publiques numériques. "
            "Outils : synthesize_public_inquiry, list_ctm_norms, create_email_draft."
        ),
    },
    {
        'sub_role': 'liaison_fec',
        'hierarchy_level': 7,
        'position_label': (
            "Agent de Liaison Industrielle — Pôle Logistique & Relations Extérieures, CTC "
            "(Fédération des Entreprises du Congo — FEC, Poste 195)"
        ),
        'mission_summary': (
            "Assure la liaison entre la CTC et le secteur privé industriel (cimentiers, aciéristes). "
            "Organise les consultations industrielles (étape INDUSTRIAL du processus CTC). "
            "Collecte les avis techniques du secteur privé sur les avant-projets. "
            "Représente la FEC au sein du Pôle Logistique."
        ),
        'tools_hint': (
            "Liaison secteur privé industriel. "
            "Outils : list_ctm_norms, synthesize_public_inquiry, create_email_draft."
        ),
    },
    {
        'sub_role': 'communicateur',
        'hierarchy_level': 7,
        'position_label': (
            "Spécialiste Médias & Communication — Pôle Logistique & Relations Extérieures, CTC "
            "(OCC / Société Civile — Poste 181)"
        ),
        'mission_summary': (
            "Gère la communication institutionnelle de la CNETP. "
            "Prépare les communiqués, notes d'information et supports de vulgarisation normative. "
            "Représente la Société Civile et l'OCC au sein du Pôle Logistique. "
            "Assure la visibilité publique des travaux de la Commission."
        ),
        'tools_hint': (
            "Communication et vulgarisation. "
            "Outils : list_ctm_norms, synthesize_public_inquiry, create_email_draft."
        ),
    },

    # ── Profil 4 : Bureau d'Appui Technique et Numérique (5 postes) ──────────
    {
        'sub_role': 'sig_beau',
        'hierarchy_level': 7,
        'position_label': (
            "Ingénieur Cartographe/SIG — Bureau d'Appui Technique Numérique, CTC "
            "(BEAU — Poste 130)"
        ),
        'mission_summary': (
            "Produit les cartes et données géospatiales (SIG) pour les avant-projets de normes. "
            "Traite les couches géographiques (zonage, réseaux, topographie) nécessaires aux CTM. "
            "Représente le BEAU au sein du Bureau d'Appui Technique Numérique. "
            "Prend en charge la revue géospatiale (étape GEOSPATIAL du processus CTC)."
        ),
        'tools_hint': (
            "Cartographie SIG et données géospatiales. "
            "Outils : list_ctm_norms, search_external_referentials."
        ),
    },
    {
        'sub_role': 'sig_ovd',
        'hierarchy_level': 7,
        'position_label': (
            "Ingénieur des Sols Urbains / Cartographe — Bureau d'Appui Technique Numérique, CTC "
            "(OVD — Poste 74)"
        ),
        'mission_summary': (
            "Produit les données géospatiales urbaines (réseaux de voirie, drainage, érosions). "
            "Représente l'OVD au sein du Bureau d'Appui Technique Numérique. "
            "Contribue à la revue géospatiale des avant-projets concernant les voiries."
        ),
        'tools_hint': (
            "Cartographie urbaine et voiries. "
            "Outils : list_ctm_norms, search_external_referentials."
        ),
    },
    {
        'sub_role': 'operateur_saisie',
        'hierarchy_level': 7,
        'position_label': (
            "Opérateur de Saisie — Bureau d'Appui Technique Numérique, CTC "
            "(BTC — Postes 98-99)"
        ),
        'mission_summary': (
            "Saisit et encode les données normatives dans la plateforme numérique. "
            "Assure la qualité de la saisie des textes et des métadonnées des normes. "
            "Représente le BTC au sein du Bureau d'Appui Technique Numérique. "
            "Opère sous supervision de l'Administrateur IT."
        ),
        'tools_hint': (
            "Saisie et encodage des données. "
            "Outils : list_ctm_norms."
        ),
    },
    {
        'sub_role': 'it_btc',
        'hierarchy_level': 7,
        'position_label': (
            "Administrateur Système IT — Bureau d'Appui Technique Numérique, CTC "
            "(Bureau Technique de Contrôle — BTC)"
        ),
        'mission_summary': (
            "Administre les serveurs et l'infrastructure technique de la plateforme CNETP. "
            "Gère les accès utilisateurs, la sécurité des données et les sauvegardes. "
            "Représente le BTC pour l'administration système. "
            "Supervise les Opérateurs de Saisie et le portail web d'enquête publique."
        ),
        'tools_hint': (
            "Administration système et sécurité de la plateforme. "
            "Outils : list_ctm_norms, create_email_draft."
        ),
    },
    {
        'sub_role': 'it_sg_itp',
        'hierarchy_level': 7,
        'position_label': (
            "Administrateur IT — Bureau d'Appui Technique Numérique, CTC "
            "(Secrétariat Général aux ITP)"
        ),
        'mission_summary': (
            "Administre le portail web d'enquête publique (Poste 100). "
            "Gère les comptes utilisateurs de la plateforme CNETP (200 experts). "
            "Représente le SG-ITP pour l'administration informatique. "
            "Maintient l'infrastructure numérique du Secrétariat Technique."
        ),
        'tools_hint': (
            "Administration du portail et des comptes. "
            "Outils : list_ctm_norms, create_email_draft."
        ),
    },
]


def load_postes(apps, schema_editor):
    AgentPosteContext = apps.get_model('ia_agent', 'AgentPosteContext')

    for data in PILOTAGE_POSTES:
        AgentPosteContext.objects.get_or_create(
            organ='pilotage',
            sub_role=data['sub_role'],
            defaults={
                'hierarchy_level': data['hierarchy_level'],
                'position_label':  data['position_label'],
                'mission_summary': data['mission_summary'],
                'tools_hint':      data['tools_hint'],
                'is_active':       True,
            },
        )

    for data in CTC_POSTES:
        AgentPosteContext.objects.get_or_create(
            organ='ctc',
            sub_role=data['sub_role'],
            defaults={
                'hierarchy_level': data['hierarchy_level'],
                'position_label':  data['position_label'],
                'mission_summary': data['mission_summary'],
                'tools_hint':      data['tools_hint'],
                'is_active':       True,
            },
        )


def unload_postes(apps, schema_editor):
    AgentPosteContext = apps.get_model('ia_agent', 'AgentPosteContext')
    AgentPosteContext.objects.filter(organ__in=['pilotage', 'ctc']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ia_agent', '0005_agentpostecontext'),
    ]

    operations = [
        migrations.RunPython(load_postes, reverse_code=unload_postes),
    ]
