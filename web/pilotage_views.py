"""
Vues dynamiques du Comité de Pilotage Élargi (27 postes).

Logique : chaque expert du Comité de Pilotage se voit attribuer un `pilotage_sub_role`
dérivé de son rôle PilotageMembreship ET de l'acronyme de sa structure d'origine.
Ce sous-rôle alimente des booléens de privilèges injectés dans le contexte du template,
qui masque ou déverrouille les modules en conséquence.

4 collèges — 4 profils de privilèges :
  Profil 1 — Bureau Directoire          (5 postes)
  Profil 2 — Conseillers Institutionnels (12 postes)
  Profil 3 — Administrateurs Tech. & Fin.(5 postes)
  Profil 4 — Partenaires & Société Civile(5 postes)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from apps.experts.models import Expert
from apps.governance.models import (
    ComitePilotage, PilotageMembreship, PosteNominatif,
    CTM, WG, Affectation, PermissionRequest, CTCProcessus, NormeCadrage,
    PlatformFreeze,
)
from apps.norms.models import Norme


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES DE MAPPAGE STRUCTURE → SOUS-RÔLE
# ─────────────────────────────────────────────────────────────────────────────

# Structures dont l'acronyme (en majuscules) détermine un sous-rôle spécialisé
# pour les collèges ATF et Partenaires.
_STRUCTURE_ACRONYM_TO_SUB = {
    # Collège ATF (5 postes)
    'FONER': 'foner',
    'BTC':   'btc',
    'OVD':   'ovd',
    'OR':    'atf_or',
    'ACGT':  'acgt',
    # Collège Partenaires (5 postes)
    'FEC':   'fec',
    'OCC':   'occ',
    'SCOT':  'occ',  # Poste 27 : structure réelle en base = SCOT (OCC n'existe pas comme acronyme distinct)
    'ONA':   'ona',
    'BEAU':  'beau',
}

# Rôles du Bureau Directoire
_DIRECTOIRE_ROLES = {'PRESIDENT', 'VICE_PRESIDENT', 'SECRETARY', 'RAPPORTEUR'}


def _vp_sub_role_from_title(poste_title_lower: str) -> str:
    """
    Distingue le 1er Vice-Président (ONIC, giron Ingénierie) du 2nd
    Vice-Président (AIBTP/CNIRS-BTP, giron Construction) à partir de
    l'intitulé exact de leur PosteNominatif (Manuel Organisationnel 2026).
    """
    return 'vice_president_onic' if 'onic' in poste_title_lower else 'vice_president_btp'


# Cadrage Bureau Directoire (NormeCadrage) : pour chaque sous-rôle du Directoire,
# liste des (current_stage, action, libellé) représentant une action en attente.
_CADRAGE_ACTIONS_BY_SUBROLE = {
    'president': [
        ('PROPOSED', 'open', "Phase 1.1 — Ouvrir le chantier (orientation stratégique)"),
        ('FINAL_VALIDATION', 'final_validate', "Phase 2.3 — Validation finale & signature de la résolution"),
    ],
    'vice_president_onic': [
        ('EXPERTS_REVIEW', 'validate_onic', "Phase 1.2 — Valider les experts WG (giron Ingénierie)"),
        ('CONFORMITY_QUITUS', 'quitus_onic', "Phase 2.2 — Quitus de conformité technique"),
    ],
    'vice_president_btp': [
        ('EXPERTS_REVIEW', 'validate_btp', "Phase 1.2 — Valider le mandat des experts WG (secteur BTP)"),
        ('CONFORMITY_QUITUS', 'quitus_btp', "Phase 2.2 — Quitus de conformité technique"),
    ],
    'secretary': [
        ('MANDATE_FORMALIZATION', 'formalize_mandate', "Phase 1.3 — Formaliser le mandat opérationnel"),
        ('PV_VERIFICATION', 'verify_pv', "Phase 2.1 — Vérifier le PV de l'Assemblée Plénière"),
    ],
    'rapporteur': [
        ('SCHEDULED', 'schedule', "Phase 1.4 — Chronogramme & ordre de service à la CTC"),
    ],
}

# Pour les étapes à double validateur, champ à vérifier pour exclure les
# cadrages déjà traités par CET acteur précis (l'autre VP doit encore agir).
_CADRAGE_ACTION_EXCLUDE_FIELD = {
    'validate_onic': 'onic_validated_at',
    'validate_btp':  'btp_validated_at',
    'quitus_onic':   'onic_quitus_at',
    'quitus_btp':    'btp_quitus_at',
}

# ─────────────────────────────────────────────────────────────────────────────
# ESPACE ADMINISTRATIF — BUREAU DIRECTOIRE (Postes 1 à 5)
# ─────────────────────────────────────────────────────────────────────────────

# Métadonnées d'identité et de mission pour chacun des 5 postes du Bureau
# Directoire, utilisées par l'interface `pilotage/app/` (sidebar + composant_post_n).
_BUREAU_DIRECTOIRE_POSTES = [
    {
        'n': 1,
        'sub_role': 'president',
        'title': 'Président du Comité de Pilotage',
        'origin': 'Cabinet du Ministre des ITP',
        'icon': 'crown',
        'accent': 'amber',
        'mission': (
            "Autorité d'impulsion stratégique et de validation finale du Comité de "
            "Pilotage Élargi. Ouvre chaque chantier normatif par ses orientations et "
            "clôt le circuit par la signature de la résolution finale."
        ),
        'phase1_title': "Cadrage stratégique",
        'phase1_description': (
            "Avant toute saisine de la CTC, le Président examine la proposition de "
            "norme et fixe les orientations stratégiques qui guideront l'ensemble du "
            "chantier (priorités, portée, articulation avec les politiques "
            "sectorielles en cours)."
        ),
        'phase2_title': "Validation finale & signature",
        'phase2_description': (
            "Une fois le PV de l'Assemblée Plénière vérifié par le Secrétaire et les "
            "quitus de conformité technique donnés par les deux Vice-Présidents, le "
            "Président valide et signe la résolution finale qui consacre la norme et "
            "autorise sa transmission au Ministre des ITP."
        ),
        'phase3_title': "Réception du dossier nettoyé par la CTC",
    },
    {
        'n': 2,
        'sub_role': 'vice_president_onic',
        'title': '1er Vice-Président',
        'origin': 'ONIC — giron Ingénierie',
        'icon': 'shield-check',
        'accent': 'sky',
        'mission': (
            "Garant technique du giron Ingénierie. Valide la légitimité des experts "
            "des Groupes de Travail et certifie la conformité technique des normes "
            "relevant de son périmètre."
        ),
        'phase1_title': "Validation des experts WG (Ingénierie)",
        'phase1_description': (
            "Avant le lancement des travaux, le 1er Vice-Président examine la liste "
            "des experts pressentis pour les Groupes de Travail du giron Ingénierie "
            "et valide leur légitimité technique."
        ),
        'phase2_title': "Quitus de conformité technique",
        'phase2_description': (
            "Après vérification du PV de l'Assemblée Plénière, le 1er Vice-Président "
            "donne son quitus de conformité technique pour le volet Ingénierie de la "
            "norme, condition nécessaire à la validation finale du Président."
        ),
    },
    {
        'n': 3,
        'sub_role': 'vice_president_btp',
        'title': '2nd Vice-Président',
        'origin': 'AIBTP / CNIRS-BTP — secteur BTP',
        'icon': 'hard-hat',
        'accent': 'orange',
        'mission': (
            "Garant technique du secteur BTP. Valide le mandat des experts des "
            "Groupes de Travail BTP et certifie la conformité technique des normes "
            "relevant de son périmètre."
        ),
        'phase1_title': "Validation du mandat des experts WG (BTP)",
        'phase1_description': (
            "Avant le lancement des travaux, le 2nd Vice-Président examine et valide "
            "le mandat des experts pressentis pour les Groupes de Travail du secteur "
            "BTP."
        ),
        'phase2_title': "Quitus de conformité technique",
        'phase2_description': (
            "Après vérification du PV de l'Assemblée Plénière, le 2nd Vice-Président "
            "donne son quitus de conformité technique pour le volet BTP de la norme, "
            "condition nécessaire à la validation finale du Président."
        ),
    },
    {
        'n': 4,
        'sub_role': 'secretary',
        'title': 'Secrétaire',
        'origin': 'Membre académique',
        'icon': 'file-text',
        'accent': 'violet',
        'mission': (
            "Cheville opérationnelle du Comité. Formalise le mandat opérationnel "
            "transmis aux CTM et audite la conformité formelle du Procès-Verbal de "
            "l'Assemblée Plénière avant transmission aux Vice-Présidents."
        ),
        'phase1_title': "Mandat opérationnel",
        'phase1_description': (
            "Une fois les experts validés par les Vice-Présidents, le Secrétaire "
            "rédige et formalise le mandat opérationnel ainsi que la méthodologie "
            "scientifique transmis aux Comités Techniques Mixtes (CTM)."
        ),
        'phase2_title': "Vérification du PV de l'Assemblée Plénière",
        'phase2_description': (
            "Dès que la CTC a transmis le dossier nettoyé (Étape 5 — accusés de "
            "réception du Président et du Rapporteur Général), le Secrétaire audite "
            "la conformité du Procès-Verbal de l'Assemblée Plénière avant de le "
            "transmettre aux Vice-Présidents pour quitus."
        ),
    },
    {
        'n': 5,
        'sub_role': 'rapporteur',
        'title': 'Rapporteur Général',
        'origin': 'Secrétariat Général des ITP (SG-ITP)',
        'icon': 'calendar-clock',
        'accent': 'emerald',
        'mission': (
            "Architecte du calendrier du chantier normatif. Fixe le chronogramme et "
            "transmet l'ordre de service à la CTC ; co-réceptionne avec le Président "
            "le dossier nettoyé renvoyé par la CTC."
        ),
        'phase1_title': "Chronogramme & ordre de service",
        'phase1_description': (
            "Une fois le mandat opérationnel formalisé par le Secrétaire, le "
            "Rapporteur Général fixe les dates butoirs (travaux CTM/WG, transmission "
            "à la CTC, retour au Pilotage) et transmet l'ordre de service à la CTC, "
            "ouvrant ainsi le traitement interne de la CTC (Étapes 1 à 5)."
        ),
        'phase2_title': "Réception du dossier nettoyé par la CTC",
        'phase2_description': (
            "À l'issue du traitement interne de la CTC (toilettage, enquête "
            "publique, certification), le Rapporteur Général accuse réception du "
            "dossier nettoyé, conjointement avec le Président — ce double accusé de "
            "réception débloque la Phase 2.1 (vérification du PV) du Secrétaire."
        ),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# ESPACE ADMINISTRATIF — COLLÈGE DES CONSEILLERS INSTITUTIONNELS ET POLITIQUES
# (Postes 6 à 10 — premier lot des 12 postes du collège)
# ─────────────────────────────────────────────────────────────────────────────

# Métadonnées d'identité et de mission pour les Postes 6 à 15 du Collège des
# Conseillers Institutionnels et Politiques, utilisées par l'interface
# `pilotage/app_conseillers/` (sidebar + composant_post_n). Tous ces postes
# partagent le même sous-rôle `conseiller_politique` (Profil 2) : lecture
# seule sur les CTM/WG, Widget Planification (jalons Enquête Publique
# Nationale) et téléversement de rapports institutionnels.
#
# Postes 11 à 15 = "Représentants des Ministères Partenaires" (1/5 à 5/5,
# structure AUTRES-MIN, quota Ligne 12). Le Poste 15 porte une note
# d'arbitrage (`arbitration_note`) : le Manuel Organisationnel annonce 5
# sièges mais nomme 6 ministères candidats — ce 5e siège reste vacant en
# attendant la décision du Bureau Directoire (cf. mémoire de session).
_CONSEILLERS_POSTES = [
    {
        'n': 6,
        'title': 'Conseiller — Cabinet du Ministre des ITP (1/2)',
        'origin': 'Cabinet du Ministre des ITP',
        'quota_line': 2,
        'icon': 'landmark',
        'accent': 'blue',
        'mission': (
            "Représente le Cabinet du Ministre des Infrastructures, Travaux Publics "
            "et Reconstruction au sein du Comité de Pilotage Élargi. Porte la vision "
            "politique du Ministre sur les chantiers normatifs et veille à leur "
            "articulation avec les priorités gouvernementales du secteur."
        ),
        'interface_role': (
            "Premier point de contact entre le Cabinet et le Comité de Pilotage en "
            "amont des chantiers normatifs : relaie les priorités politiques du "
            "Ministre dès l'ouverture d'un dossier (Phase 1.1 du Bureau Directoire) "
            "et alerte sur les arbitrages sensibles à anticiper."
        ),
    },
    {
        'n': 7,
        'title': 'Conseiller — Cabinet du Ministre des ITP (2/2)',
        'origin': 'Cabinet du Ministre des ITP',
        'quota_line': 2,
        'icon': 'landmark',
        'accent': 'blue',
        'mission': (
            "Second représentant du Cabinet du Ministre au sein du Comité de "
            "Pilotage Élargi. Assure la liaison entre les décisions du Comité et les "
            "services ministériels chargés de leur mise en œuvre."
        ),
        'interface_role': (
            "Assure le suivi de la mise en œuvre côté Cabinet une fois les normes "
            "validées : relaie aux services ministériels concernés les résolutions "
            "adoptées par le Comité de Pilotage et veille à leur articulation avec "
            "la communication gouvernementale."
        ),
    },
    {
        'n': 8,
        'title': 'Conseiller — Secrétariat Général aux ITP',
        'origin': 'Secrétariat Général aux ITP (SG-ITP)',
        'quota_line': 1,
        'icon': 'building-2',
        'accent': 'sky',
        'mission': (
            "Représente le Secrétariat Général aux Infrastructures, Travaux Publics "
            "et Reconstruction — l'administration centrale chargée de la mise en "
            "œuvre opérationnelle des politiques sectorielles. Assure la cohérence "
            "entre le travail normatif de la CNETP et les procédures administratives "
            "en vigueur."
        ),
        'interface_role': (
            "Garant de la cohérence administrative : veille à l'articulation entre "
            "les futures normes et les procédures du Secrétariat Général, et relaie "
            "au Comité de Pilotage l'état d'avancement des dossiers administratifs "
            "connexes aux chantiers normatifs en cours."
        ),
    },
    {
        'n': 9,
        'title': 'Conseiller — Secrétariat Général à la Reconstruction (1/2)',
        'origin': 'Secrétariat Général à la Reconstruction (SG-RECONS)',
        'quota_line': 3,
        'icon': 'hammer',
        'accent': 'indigo',
        'mission': (
            "Représente le Secrétariat Général à la Reconstruction, en charge des "
            "grands programmes de reconstruction des infrastructures routières et "
            "de transport. Veille à l'arrimage des normes en cours d'élaboration "
            "avec ces chantiers prioritaires."
        ),
        'interface_role': (
            "Interface privilégiée pour les normes touchant au volet routier et aux "
            "corridors de transport de la reconstruction : signale les contraintes "
            "de terrain et les urgences opérationnelles des chantiers en cours."
        ),
    },
    {
        'n': 10,
        'title': 'Conseiller — Secrétariat Général à la Reconstruction (2/2)',
        'origin': 'Secrétariat Général à la Reconstruction (SG-RECONS)',
        'quota_line': 3,
        'icon': 'hammer',
        'accent': 'indigo',
        'mission': (
            "Second représentant du Secrétariat Général à la Reconstruction, en "
            "charge du volet bâtiments publics et équipements collectifs. Veille à "
            "ce que les normes élaborées par la CNETP répondent aux besoins de ces "
            "programmes de reconstruction."
        ),
        'interface_role': (
            "Interface privilégiée pour les normes touchant aux bâtiments publics et "
            "équipements collectifs des programmes de reconstruction : relaie au "
            "Comité de Pilotage les besoins normatifs émergents de ces chantiers."
        ),
    },
    {
        'n': 11,
        'title': "Conseiller — Représentant du Ministère de l'Urbanisme et de l'Habitat (1/5)",
        'origin': "Ministère de l'Urbanisme et de l'Habitat",
        'quota_line': 12,
        'icon': 'building',
        'accent': 'cyan',
        'mission': (
            "Représente le Ministère de l'Urbanisme et de l'Habitat au sein du "
            "Comité de Pilotage Élargi, premier des cinq sièges réservés aux "
            "Ministères Partenaires. Veille à ce que les normes élaborées par la "
            "CNETP s'articulent avec la réglementation foncière, les plans "
            "d'aménagement urbain et les permis de construire."
        ),
        'interface_role': (
            "Alerte le Comité de Pilotage sur les chantiers normatifs susceptibles "
            "d'entrer en conflit avec les schémas directeurs d'urbanisme ou les "
            "normes d'habitat existantes, et relaie les besoins de mise à jour "
            "réglementaire identifiés par son Ministère."
        ),
    },
    {
        'n': 12,
        'title': "Conseiller — Représentant du Ministère de l'Aménagement du Territoire (2/5)",
        'origin': "Ministère de l'Aménagement du Territoire",
        'quota_line': 12,
        'icon': 'map',
        'accent': 'cyan',
        'mission': (
            "Représente le Ministère de l'Aménagement du Territoire au sein du "
            "Comité de Pilotage Élargi. Veille à la cohérence entre les normes "
            "infrastructurelles en cours d'élaboration et les schémas nationaux et "
            "provinciaux d'aménagement du territoire."
        ),
        'interface_role': (
            "Signale au Comité de Pilotage les implications territoriales des "
            "normes à l'étude — notamment pour les projets traversant plusieurs "
            "provinces — et veille à leur articulation avec les priorités "
            "d'aménagement du territoire."
        ),
    },
    {
        'n': 13,
        'title': (
            "Conseiller — Représentant du Ministère de l'Environnement et du "
            "Développement Durable (3/5)"
        ),
        'origin': "Ministère de l'Environnement et du Développement Durable",
        'quota_line': 12,
        'icon': 'leaf',
        'accent': 'cyan',
        'mission': (
            "Représente le Ministère de l'Environnement et du Développement "
            "Durable au sein du Comité de Pilotage Élargi. Veille à l'intégration "
            "des exigences environnementales — études d'impact, normes de "
            "durabilité — dans les référentiels élaborés par la CNETP."
        ),
        'interface_role': (
            "Examine les projets de normes sous l'angle environnemental, relaie "
            "les exigences d'étude d'impact environnemental et social (EIES) et "
            "propose des critères de durabilité et de résilience climatique."
        ),
    },
    {
        'n': 14,
        'title': "Conseiller — Représentant du Ministère des Affaires Foncières (4/5)",
        'origin': "Ministère des Affaires Foncières",
        'quota_line': 12,
        'icon': 'map-pin',
        'accent': 'cyan',
        'mission': (
            "Représente le Ministère des Affaires Foncières au sein du Comité de "
            "Pilotage Élargi. Veille à ce que les normes touchant à l'implantation "
            "des infrastructures tiennent compte du régime foncier et des "
            "procédures de cession, concession et expropriation en vigueur."
        ),
        'interface_role': (
            "Alerte sur les risques fonciers liés aux emprises nécessaires aux "
            "projets normés — titres de propriété, expropriations, occupations "
            "informelles — et relaie les procédures foncières applicables."
        ),
    },
    {
        'n': 15,
        'title': "Conseiller — Représentant de la Division ITP / Ville de Kinshasa (5/5)",
        'origin': "Division des ITP / Ville de Kinshasa",
        'quota_line': 12,
        'icon': 'landmark',
        'accent': 'cyan',
        'mission': (
            "Représente la Division des Infrastructures et Travaux Publics de la "
            "Ville de Kinshasa au sein du Comité de Pilotage Élargi, cinquième et "
            "dernier siège réservé aux Ministères Partenaires. Veille à ce que les "
            "normes élaborées par la CNETP intègrent les contraintes spécifiques du "
            "tissu urbain dense de la capitale."
        ),
        'interface_role': (
            "Alerte le Comité de Pilotage sur les spécificités d'application des "
            "normes à l'étude dans la Ville de Kinshasa — réseaux existants, "
            "densité urbaine, chantiers en cours — et relaie les retours "
            "opérationnels des services techniques municipaux."
        ),
    },
    {
        'n': 16,
        'title': 'Conseiller Juridique Spécialisé (1/2)',
        'origin': 'Experts Juridiques Spécialisés (EJS)',
        'quota_line': 13,
        'icon': 'scale',
        'accent': 'violet',
        'mission': (
            "Premier des deux Conseillers Juridiques Spécialisés du Comité de "
            "Pilotage Élargi, issu du corps des Experts Juridiques Spécialisés "
            "(Ligne 13). Pilote la rédaction des projets d'Arrêtés Ministériels "
            "d'homologation pour les normes ayant achevé leur cycle de validation."
        ),
        'interface_role': (
            "Dispose du droit exclusif d'édition du Module Légistique : rédige les "
            "projets d'Arrêtés d'homologation pour chaque norme achevant son "
            "cycle, en s'appuyant sur les références juridiques applicables au "
            "processus d'homologation CNETP."
        ),
    },
    {
        'n': 17,
        'title': 'Conseiller Juridique Spécialisé (2/2)',
        'origin': 'Experts Juridiques Spécialisés (EJS)',
        'quota_line': 13,
        'icon': 'scale',
        'accent': 'violet',
        'mission': (
            "Second Conseiller Juridique Spécialisé du Comité de Pilotage Élargi, "
            "issu du corps des Experts Juridiques Spécialisés (Ligne 13). Assure "
            "la relecture croisée et la validation collégiale des projets "
            "d'Arrêtés Ministériels avant leur transmission au Bureau Directoire."
        ),
        'interface_role': (
            "Partage avec le Poste 16 le droit exclusif d'édition du Module "
            "Légistique : relit, amende et co-valide chaque projet d'Arrêté avant "
            "qu'il ne soit transmis au Bureau Directoire pour validation finale et "
            "signature."
        ),
    },
]

# Regroupement de la sidebar `app_conseillers` par sous-collège (utilisé par
# `{% regroup %}` dans sidebar_module.html — la liste ci-dessus est déjà
# ordonnée de façon à ce que chaque groupe soit contigu).
_CONSEILLERS_GROUPS = [
    (range(6, 11), "Cabinet du Ministre des ITP & Secrétariats Généraux"),
    (range(11, 16), "Représentants des Ministères Partenaires"),
    (range(16, 18), "Conseillers Juridiques Spécialisés"),
]


def _conseillers_group_label(n: int) -> str:
    for rng, label in _CONSEILLERS_GROUPS:
        if n in rng:
            return label
    return ''


def _cadrages_for_subrole(sub_role: str) -> list[dict]:
    """
    Pour un sous-rôle du Bureau Directoire, retourne la liste des groupes
    d'action de cadrage (Phase 1 puis Phase 2), chacun avec ses dossiers
    actuellement en attente (liste `items` vide si aucun dossier n'est à
    cette étape pour le moment).
    """
    groups = []
    for phase, (stage, action, label) in enumerate(_CADRAGE_ACTIONS_BY_SUBROLE.get(sub_role, []), start=1):
        qs = NormeCadrage.objects.filter(current_stage=stage)
        exclude_field = _CADRAGE_ACTION_EXCLUDE_FIELD.get(action)
        if exclude_field:
            qs = qs.filter(**{f'{exclude_field}__isnull': True})
        items = []
        for cadrage in qs.select_related('norme', 'norme__ctc_processus').order_by('-created_at'):
            # Phase 2.1 : le Secrétaire ne peut vérifier le PV que si la CTC a
            # transmis le dossier nettoyé (Étape 5 — accusé de réception complet).
            blocked = action == 'verify_pv' and not cadrage.ctc_handoff_complete
            items.append({'cadrage': cadrage, 'action': action, 'label': label, 'blocked': blocked})
        groups.append({'phase': phase, 'stage': stage, 'action': action, 'label': label, 'items': items})
    return groups

# CTMs couverts par chaque spécialiste ATF (accès privilégié sans demande de permission)
_ATF_SPECIALTY_CTM = {
    'atf_or': [1],        # Office des Routes → CTM 1 Géotechnique/Chaussées
    'ovd':    [7],        # OVD → CTM 7 Assainissement & Macro-drainage
    'acgt':   [1, 2, 3],  # ACGT → CTM 1 à 3 (Normes & Innovation)
    'btc':    list(range(1, 9)),  # BTC a un contrôle transverse sur tous les CTM
    'foner':  [],         # FONER : rôle financier, pas de CTM direct
}

# Libellés des collèges pour l'interface
COLLEGE_LABELS = {
    'directoire':          'Bureau Directoire',
    'conseiller_politique': 'Collège des Conseillers Institutionnels et Politiques',
    'atf':                 'Collège des Administrateurs Techniques et Financiers',
    'partenaire':          'Collège des Partenaires Sectoriels et de la Société Civile',
}

COLLEGE_BADGE_COLORS = {
    'directoire':          'bg-amber-500/15 text-amber-400 border-amber-500/30',
    'conseiller_politique': 'bg-blue-500/15 text-blue-400 border-blue-500/30',
    'atf':                 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    'partenaire':          'bg-purple-500/15 text-purple-400 border-purple-500/30',
}


# ─────────────────────────────────────────────────────────────────────────────
# MOTEUR DE PRIVILÈGES
# ─────────────────────────────────────────────────────────────────────────────

def get_pilotage_context(expert: Expert) -> dict | None:
    """
    Calcule et retourne le dictionnaire complet de contexte de privilèges
    pour un expert membre du Comité de Pilotage.

    Retourne None si l'expert n'est pas membre du Comité de Pilotage.
    """
    membership = (
        PilotageMembreship.objects
        .filter(expert=expert)
        .select_related('comite')
        .first()
    )
    if not membership:
        return None

    role = membership.role  # ex: 'PRESIDENT', 'ADMIN_TECH_FIN', …
    acronym = (expert.structure.acronym or '').upper() if expert.structure else ''

    # ── Détermination du collège ──────────────────────────────────────────────
    is_directoire = role in _DIRECTOIRE_ROLES
    is_conseiller = role == 'CONSEILLER_POLITIQUE'
    is_atf        = role == 'ADMIN_TECH_FIN'
    is_partenaire = role == 'PARTENAIRE_SOC_CIV'

    college = (
        'directoire'           if is_directoire else
        'conseiller_politique' if is_conseiller else
        'atf'                  if is_atf        else
        'partenaire'           if is_partenaire else
        'membre'
    )

    # ── Poste nominatif (si disponible) ──────────────────────────────────────
    poste = PosteNominatif.objects.filter(holder=expert).select_related('required_structure').first()
    poste_title_lower = poste.title.lower() if poste else ''

    # ── Sous-rôle précis ─────────────────────────────────────────────────────
    if is_directoire:
        if role == 'VICE_PRESIDENT':
            sub_role = _vp_sub_role_from_title(poste_title_lower)
        else:
            sub_role = role.lower()  # 'president', 'secretary', 'rapporteur'
    elif is_atf or is_partenaire:
        # On dérive depuis la structure d'origine
        sub_role = _STRUCTURE_ACRONYM_TO_SUB.get(acronym, role.lower())
    elif is_conseiller:
        # Conseillers Juridiques : identifiés par leur PosteNominatif ou structure
        title_lower = poste_title_lower + acronym.lower()
        sub_role = 'juridique' if ('juridique' in title_lower or 'lgistique' in title_lower) else 'conseiller_politique'
    else:
        sub_role = role.lower()

    # ── CTMs de spécialité (ATF uniquement) ──────────────────────────────────
    specialty_ctm_ids = _ATF_SPECIALTY_CTM.get(sub_role, [])
    specialty_ctms = CTM.objects.filter(number__in=specialty_ctm_ids) if specialty_ctm_ids else []

    # ── Demandes de permission en attente (Directoire seulement) ─────────────
    pending_requests = (
        PermissionRequest.objects
        .filter(status='PENDING')
        .select_related('requester__user', 'requester__structure')
        .order_by('-created_at')
        if is_directoire else []
    )

    # ── Étape 5 : normes transmises par la CTC en attente de réception ───────
    # Section 5.4.3 — le Président (Poste 16) et le Rapporteur Général (Poste 1)
    # réceptionnent officiellement la norme nettoyée par la CTC.
    can_acknowledge_reception = role in ('PRESIDENT', 'RAPPORTEUR')
    pending_pilotage_reception = []
    if can_acknowledge_reception:
        ack_filter = (
            {'received_by_president__isnull': True} if role == 'PRESIDENT'
            else {'received_by_rapporteur__isnull': True}
        )
        pending_pilotage_reception = list(
            CTCProcessus.objects
            .filter(current_stage='SIGNED_OUT', **ack_filter)
            .select_related('norme', 'signed_out_by')
            .order_by('-signed_out_at')
        )

    # ── Cadrage Bureau Directoire (Phases 1 & 2 — Postes 1 à 5) ───────────────
    pending_cadrages = []
    if is_directoire:
        for group in _cadrages_for_subrole(sub_role):
            pending_cadrages.extend(group['items'])

    # ── Verrouillage plateforme CTC/CTM (action souveraine du Président) ─────
    freeze = PlatformFreeze.get_solo()

    # ─────────────────────────────────────────────────────────────────────────
    # BOOLÉENS DE PRIVILÈGES (injectés dans le template)
    # ─────────────────────────────────────────────────────────────────────────
    ctx = {
        # Identification
        'is_pilotage':     True,
        'user_sub_role':   sub_role,
        'pilotage_college': college,
        'college_label':   COLLEGE_LABELS.get(college, 'Membre'),
        'college_badge':   COLLEGE_BADGE_COLORS.get(college, ''),
        'poste':           poste,
        'membership':      membership,

        # ── Profil 1 : Bureau Directoire ─────────────────────────────────────
        # Bouton d'Action Maître — validation des étapes 1→7
        'can_trigger_steps':      is_directoire,
        # Console Globale — visibilité totale sur CTMs + WGs
        'can_view_global_console': is_directoire,
        # Gestion accès experts (déblocage / suspension)
        'can_manage_access':      is_directoire,
        # Approbation des demandes de permission
        'can_approve_requests':   is_directoire,

        # ── Profil 2 : Conseillers Institutionnels ───────────────────────────
        # Module Légistique — édition projets d'Arrêtés Ministériels
        'can_edit_legistique':    (sub_role == 'juridique'),
        # Widget Planification — jalons Enquête Publique Nationale
        'can_use_planification':  is_conseiller,
        # Téléversement rapports institutionnels
        'can_upload_reports':     is_conseiller,

        # ── Profil 3 : Administrateurs Techniques & Financiers ───────────────
        # Console Audit Technique — CTMs de spécialité
        'can_audit_ctm':          is_atf,
        'specialty_ctms':         specialty_ctms,
        'specialty_ctm_ids':      specialty_ctm_ids,
        # Widget Validation Financière — exclusif FONER
        'can_audit_financials':   (sub_role == 'foner'),
        # Module Contrôle Labo — exclusif BTC
        'can_control_labo':       (sub_role == 'btc'),
        # Accès CTM tiers = demande de permission
        'atf_requires_permission_for_tiers': is_atf,

        # ── Profil 4 : Partenaires & Société Civile ──────────────────────────
        # Widget Avis Secteur Privé — exclusif FEC
        'can_avis_prive':         (sub_role == 'fec'),
        # Console Agréation Métrologique — exclusif OCC
        'can_agrement_metro':     (sub_role == 'occ'),
        # Blocage total sur processus décisionnels administratifs
        'blocked_admin_decisions': is_partenaire,

        # ── Lecture seule WG/documents ───────────────────────────────────────
        # Tous les membres pilotage : lecture seule sur brouillons WG
        'can_read_wg_drafts':     True,
        'can_edit_wg_drafts':     False,  # réservé aux experts WG

        # ── Données pour le Directoire ────────────────────────────────────────
        'pending_requests':       pending_requests,
        'pending_requests_count': len(pending_requests) if is_directoire else 0,

        # ── Étape 5 : réception des normes transmises par la CTC ─────────────
        'can_acknowledge_reception':       can_acknowledge_reception,
        'pending_pilotage_reception':       pending_pilotage_reception,
        'pending_pilotage_reception_count': len(pending_pilotage_reception),

        # ── Cadrage Bureau Directoire (Phases 1 & 2) ──────────────────────────
        'pending_cadrages':       pending_cadrages,
        'pending_cadrages_count': len(pending_cadrages),

        # ── Verrouillage plateforme CTC/CTM (action souveraine du Président) ─
        'platform_locked':        freeze.is_locked,
        'platform_locked_by':     freeze.locked_by.user.get_full_name() if freeze.locked_by else '',
        'platform_locked_at':     freeze.locked_at,
    }

    return ctx


# ─────────────────────────────────────────────────────────────────────────────
# VUE PRINCIPALE DU TABLEAU DE BORD PILOTAGE
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageDashboardView(View):
    """
    Tableau de bord principal pour les 27 membres du Comité de Pilotage Élargi.
    Adapte dynamiquement les modules affichés selon le profil de privilèges.
    """
    template_name = 'pilotage/dashboard.html'

    def get(self, request):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        priv = get_pilotage_context(expert)
        if not priv:
            messages.info(
                request,
                "Vous n'êtes pas membre du Comité de Pilotage. "
                "Accédez à votre espace de travail habituel."
            )
            return redirect('web:app')

        # Données globales pour le Directoire (console de supervision)
        ctms = CTM.objects.prefetch_related('working_groups').order_by('number')
        ctms_with_stats = []
        total_wgs = 0
        for ctm in ctms:
            wgs = ctm.working_groups.all()
            wg_count = wgs.count()
            total_wgs += wg_count
            ctms_with_stats.append({
                'ctm': ctm,
                'wg_count': wg_count,
                'member_count': ctm.affectations.count(),
            })

        # My permission requests (autres collèges)
        my_requests = (
            PermissionRequest.objects
            .filter(requester=expert)
            .order_by('-created_at')[:10]
        )

        context = {
            'expert': expert,
            'ctms_with_stats': ctms_with_stats,
            'total_wgs': total_wgs,
            'total_ctms': len(ctms_with_stats),
            'my_permission_requests': my_requests,
            **priv,
        }
        return render(request, self.template_name, context)


# ─────────────────────────────────────────────────────────────────────────────
# VUE DEMANDE DE PERMISSION (blocage intelligent)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotagePermissionRequestView(View):
    """
    Soumet une demande de dérogation d'accès.
    Affichée automatiquement quand un membre tente d'accéder à un module restreint.
    La demande est routée vers le Bureau Directoire (statut PENDING).
    """

    def post(self, request):
        expert = Expert.objects.filter(user=request.user).first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        # Vérifier que l'expert est bien du Comité de Pilotage
        if not PilotageMembreship.objects.filter(expert=expert).exists():
            return JsonResponse({'ok': False, 'error': 'Accès non autorisé.'}, status=403)

        restricted_resource = (request.POST.get('restricted_resource') or '').strip()
        reason = (request.POST.get('reason') or '').strip()

        if not restricted_resource or not reason:
            return JsonResponse(
                {'ok': False, 'error': 'Veuillez renseigner la ressource et le motif.'},
                status=400
            )

        # Éviter les doublons : une seule demande PENDING par ressource
        existing = PermissionRequest.objects.filter(
            requester=expert,
            restricted_resource=restricted_resource,
            status='PENDING',
        ).first()
        if existing:
            return JsonResponse({
                'ok': True,
                'message': 'Une demande est déjà en cours de traitement pour cette ressource.',
                'request_id': existing.id,
            })

        perm_req = PermissionRequest.objects.create(
            requester=expert,
            restricted_resource=restricted_resource,
            reason=reason,
        )

        return JsonResponse({
            'ok': True,
            'message': 'Votre demande a été transmise au Bureau Directoire.',
            'request_id': perm_req.id,
        })


# ─────────────────────────────────────────────────────────────────────────────
# VUE APPROBATION / REJET (Bureau Directoire uniquement)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageApproveRequestView(View):
    """
    Approuve ou rejette une demande de permission.
    Réservée aux membres du Bureau Directoire.
    """

    def post(self, request, pk):
        expert = Expert.objects.filter(user=request.user).first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        # Vérifier que c'est bien un membre du Directoire
        membership = PilotageMembreship.objects.filter(
            expert=expert, role__in=_DIRECTOIRE_ROLES
        ).first()
        if not membership:
            return JsonResponse(
                {'ok': False, 'error': 'Action réservée au Bureau Directoire.'},
                status=403
            )

        perm_req = get_object_or_404(PermissionRequest, pk=pk, status='PENDING')
        decision = (request.POST.get('decision') or '').strip().upper()
        comment  = (request.POST.get('comment') or '').strip()

        if decision not in ('APPROVED', 'REJECTED'):
            return JsonResponse({'ok': False, 'error': 'Décision invalide.'}, status=400)

        perm_req.status      = decision
        perm_req.reviewed_by = expert
        perm_req.reviewed_at = timezone.now()
        perm_req.review_comment = comment
        perm_req.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_comment'])

        action = 'approuvée' if decision == 'APPROVED' else 'refusée'
        return JsonResponse({
            'ok': True,
            'message': f'La demande de {perm_req.requester.full_name} a été {action}.',
            'new_status': decision,
        })


# ─────────────────────────────────────────────────────────────────────────────
# VUE RÉCEPTION CTC (Étape 5 — Président & Rapporteur Général uniquement)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageAcknowledgeReceptionView(View):
    """
    Accuse réception officielle d'une norme transmise par la CTC (Étape 5,
    Section 5.4.3). Réservée au Président du Comité de Pilotage Élargi
    (Poste 16) et à son Rapporteur Général (Poste 1).
    """

    def post(self, request, pk):
        if PlatformFreeze.get_solo().is_locked:
            return JsonResponse(
                {'ok': False, 'error': "Plateforme verrouillée par le Président du Comité de Pilotage — action suspendue."},
                status=423
            )

        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        membership = PilotageMembreship.objects.filter(expert=expert).first()
        if not membership or membership.role not in ('PRESIDENT', 'RAPPORTEUR'):
            return JsonResponse(
                {'ok': False, 'error': 'Réservé au Président et au Rapporteur Général du Comité de Pilotage.'},
                status=403
            )

        processus = get_object_or_404(CTCProcessus, pk=pk, current_stage='SIGNED_OUT')

        if membership.role == 'PRESIDENT':
            processus.mark_received_by_president(expert)
        else:
            processus.mark_received_by_rapporteur(expert)

        return JsonResponse({
            'ok': True,
            'message': f"Réception de {processus.norme.reference_number} confirmée.",
            'reception_complete': processus.pilotage_reception_complete,
        })


# ─────────────────────────────────────────────────────────────────────────────
# VUE CADRAGE BUREAU DIRECTOIRE (Phases 1 & 2 — Postes 1 à 5)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageCadrageActionView(View):
    """
    Traite les actions de cadrage du Bureau Directoire sur un NormeCadrage :

      Phase 1 — 'open' (Président), 'validate_onic'/'validate_btp' (1er/2nd VP),
                'formalize_mandate' (Secrétaire), 'schedule' (Rapporteur Général)
      Phase 2 — 'verify_pv' (Secrétaire), 'quitus_onic'/'quitus_btp' (1er/2nd VP),
                'final_validate' (Président)

    Chaque action n'est acceptée que si elle correspond au rôle (et, pour les
    Vice-Présidents, au sous-rôle ONIC/BTP déduit du PosteNominatif) ET à
    l'étape courante (`current_stage`) du cadrage.
    """

    def post(self, request, pk):
        if PlatformFreeze.get_solo().is_locked:
            return JsonResponse(
                {'ok': False, 'error': "Plateforme verrouillée par le Président du Comité de Pilotage — action suspendue."},
                status=423
            )

        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        membership = PilotageMembreship.objects.filter(expert=expert, role__in=_DIRECTOIRE_ROLES).first()
        if not membership:
            return JsonResponse({'ok': False, 'error': 'Action réservée au Bureau Directoire.'}, status=403)

        cadrage = get_object_or_404(NormeCadrage, pk=pk)
        action = (request.POST.get('action') or '').strip()
        role = membership.role

        poste = PosteNominatif.objects.filter(holder=expert).first()
        is_onic_vp = role == 'VICE_PRESIDENT' and _vp_sub_role_from_title(poste.title.lower() if poste else '') == 'vice_president_onic'
        is_btp_vp = role == 'VICE_PRESIDENT' and not is_onic_vp

        if action == 'open' and role == 'PRESIDENT' and cadrage.current_stage == 'PROPOSED':
            cadrage.mark_opened(expert, orientation=(request.POST.get('strategic_orientation') or '').strip())

        elif action == 'validate_onic' and is_onic_vp and cadrage.current_stage == 'EXPERTS_REVIEW':
            cadrage.mark_onic_validated(expert, notes=(request.POST.get('notes') or '').strip())

        elif action == 'validate_btp' and is_btp_vp and cadrage.current_stage == 'EXPERTS_REVIEW':
            cadrage.mark_btp_validated(expert, notes=(request.POST.get('notes') or '').strip())

        elif action == 'formalize_mandate' and role == 'SECRETARY' and cadrage.current_stage == 'MANDATE_FORMALIZATION':
            cadrage.mark_mandate_formalized(expert, mandate_text=(request.POST.get('operational_mandate') or '').strip())

        elif action == 'schedule' and role == 'RAPPORTEUR' and cadrage.current_stage == 'SCHEDULED':
            cadrage.mark_scheduled(
                expert,
                deadline_ctm_review=parse_date(request.POST.get('deadline_ctm_review') or ''),
                deadline_ctc_handoff=parse_date(request.POST.get('deadline_ctc_handoff') or ''),
                deadline_pilotage_review=parse_date(request.POST.get('deadline_pilotage_review') or ''),
            )

        elif action == 'verify_pv' and role == 'SECRETARY' and cadrage.current_stage == 'PV_VERIFICATION':
            if not cadrage.ctc_handoff_complete:
                return JsonResponse({
                    'ok': False,
                    'error': "La CTC n'a pas encore transmis le dossier nettoyé au Comité de Pilotage "
                             "(Étape 5 — accusé de réception du Président et du Rapporteur Général en attente).",
                }, status=400)
            cadrage.mark_pv_verified(expert, pv_reference=(request.POST.get('pv_reference') or '').strip())

        elif action == 'quitus_onic' and is_onic_vp and cadrage.current_stage == 'CONFORMITY_QUITUS':
            cadrage.mark_onic_quitus(expert)

        elif action == 'quitus_btp' and is_btp_vp and cadrage.current_stage == 'CONFORMITY_QUITUS':
            cadrage.mark_btp_quitus(expert)

        elif action == 'final_validate' and role == 'PRESIDENT' and cadrage.current_stage == 'FINAL_VALIDATION':
            cadrage.mark_final_validated(expert, resolution_reference=(request.POST.get('resolution_reference') or '').strip())

        else:
            return JsonResponse(
                {'ok': False, 'error': "Action invalide, ou non autorisée pour votre rôle à cette étape."},
                status=400
            )

        return JsonResponse({
            'ok': True,
            'message': f"Cadrage {cadrage.norme.reference_number} mis à jour.",
            'new_stage': cadrage.current_stage,
            'new_stage_label': cadrage.get_current_stage_display(),
        })


# ─────────────────────────────────────────────────────────────────────────────
# VUE API : CONTEXTE PILOTAGE (pour appels AJAX depuis le dashboard existant)
# ─────────────────────────────────────────────────────────────────────────────

@login_required(login_url='/se-connecter/')
def pilotage_context_api(request):
    """
    Retourne le contexte de privilèges en JSON.
    Permet aux composants JS de connaître les droits de l'utilisateur courant.
    """
    expert = Expert.objects.filter(user=request.user).select_related('structure').first()
    if not expert:
        return JsonResponse({'is_pilotage': False})

    priv = get_pilotage_context(expert)
    if not priv:
        return JsonResponse({'is_pilotage': False})

    # Sérialiser uniquement les champs JSON-compatibles
    payload = {k: v for k, v in priv.items() if isinstance(v, (bool, str, int, list, type(None)))}
    payload['specialty_ctm_ids'] = list(priv.get('specialty_ctm_ids', []))
    return JsonResponse(payload)


# ─────────────────────────────────────────────────────────────────────────────
# ESPACE ADMINISTRATIF DU BUREAU DIRECTOIRE (Postes 1 à 5)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageDirectoireAppView(View):
    """
    Interface administrative dédiée au Bureau Directoire : navigation par
    sidebar entre les 5 postes (Président, 1er/2nd Vice-Présidents,
    Secrétaire, Rapporteur Général), chacun affichant sa mission ainsi que
    ses actions de cadrage Phase 1 / Phase 2 (interactives pour le titulaire,
    en lecture seule pour les autres membres du Directoire).
    """
    template_name = 'pilotage/app/app.html'

    def get(self, request):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        priv = get_pilotage_context(expert)
        if not priv or not priv['can_trigger_steps']:
            messages.info(
                request,
                "L'espace administratif du Bureau Directoire est réservé aux Postes 1 à 5 "
                "du Comité de Pilotage."
            )
            return redirect('web:pilotage_dashboard')

        postes = []
        default_post_n = 1
        for meta in _BUREAU_DIRECTOIRE_POSTES:
            is_mine = meta['sub_role'] == priv['user_sub_role']
            if is_mine:
                default_post_n = meta['n']
            postes.append({
                **meta,
                'is_mine': is_mine,
                'cadrage_groups': _cadrages_for_subrole(meta['sub_role']),
            })

        my_poste = next((p for p in postes if p['is_mine']), postes[0])

        # ── Étape 5 : réception du dossier nettoyé par la CTC (Postes 1 & 5) ──
        pending_reception_president = list(
            CTCProcessus.objects
            .filter(current_stage='SIGNED_OUT', received_by_president__isnull=True)
            .select_related('norme', 'signed_out_by')
            .order_by('-signed_out_at')
        )
        pending_reception_rapporteur = list(
            CTCProcessus.objects
            .filter(current_stage='SIGNED_OUT', received_by_rapporteur__isnull=True)
            .select_related('norme', 'signed_out_by')
            .order_by('-signed_out_at')
        )

        context = {
            'expert': expert,
            'postes': postes,
            'my_poste': my_poste,
            'default_post_n': default_post_n,
            'pending_reception_president': pending_reception_president,
            'pending_reception_rapporteur': pending_reception_rapporteur,
            **priv,
        }
        return render(request, self.template_name, context)


# ─────────────────────────────────────────────────────────────────────────────
# ESPACE ADMINISTRATIF DU COLLÈGE DES CONSEILLERS INSTITUTIONNELS ET POLITIQUES
# (Postes 6 à 17)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageConseillersAppView(View):
    """
    Interface administrative dédiée au Collège des Conseillers Institutionnels
    et Politiques : navigation par sidebar (groupée par sous-collège) entre les
    Postes 6 à 17 (Cabinet du Ministre des ITP ×2, Secrétariat Général aux ITP,
    Secrétariat Général à la Reconstruction ×2, Représentants des Ministères
    Partenaires ×5, Conseillers Juridiques Spécialisés ×2), chacun affichant sa
    mission, son cadre d'intervention (Profil 2) et les widgets partagés du
    collège (Planification EPN pour tous, Module Légistique pour les Postes
    16-17 uniquement).
    """
    template_name = 'pilotage/app_conseillers/app.html'

    def get(self, request):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        priv = get_pilotage_context(expert)
        if not priv or priv['pilotage_college'] != 'conseiller_politique':
            messages.info(
                request,
                "L'espace administratif des Conseillers Institutionnels et "
                "Politiques est réservé aux membres de ce collège."
            )
            return redirect('web:pilotage_dashboard')

        my_poste_order = priv['poste'].order if priv['poste'] else None

        postes = []
        default_post_n = _CONSEILLERS_POSTES[0]['n']
        for meta in _CONSEILLERS_POSTES:
            is_mine = meta['n'] == my_poste_order
            if is_mine:
                default_post_n = meta['n']
            postes.append({
                **meta,
                'is_mine': is_mine,
                'group_label': _conseillers_group_label(meta['n']),
            })

        context = {
            'expert': expert,
            'postes': postes,
            'default_post_n': default_post_n,
            **priv,
        }
        return render(request, self.template_name, context)


# ─────────────────────────────────────────────────────────────────────────────
# ESPACE ADMINISTRATIF DU COLLÈGE DES ADMINISTRATEURS TECHNIQUES ET FINANCIERS
# (Postes 18 à 22)
# ─────────────────────────────────────────────────────────────────────────────

# Métadonnées d'identité et de mission pour les Postes 18 à 22 du Collège des
# Administrateurs Techniques et Financiers (5 postes, collège complet),
# utilisées par l'interface `pilotage/app_atf/` (sidebar + composant_post_n).
# Tous ces postes partagent le sous-rôle dérivé de leur structure d'origine via
# `_STRUCTURE_ACRONYM_TO_SUB` (Profil 3) : lecture seule sur CTM/WG, accès
# privilégié (audit) sur leurs CTM de spécialité (`_ATF_SPECIALTY_CTM`), accès
# aux autres CTM par demande de permission au Bureau Directoire.
_ATF_POSTES = [
    {
        'n': 18,
        'title': 'Administrateur Technique et Financier — Office des Routes (OR)',
        'origin': 'Office des Routes (OR)',
        'quota_line': 4,
        'icon': 'route',
        'accent': 'emerald',
        'mission': (
            "Représente l'Office des Routes, agence publique en charge de la "
            "construction et de l'entretien du réseau routier national, au sein "
            "du Comité de Pilotage Élargi. Apporte l'expertise de terrain sur les "
            "normes de géotechnique et de chaussées en cours d'élaboration."
        ),
        'interface_role': (
            "Dispose d'un accès privilégié au CTM 1 — Géotechnique & Chaussées : "
            "audite les brouillons techniques sous l'angle de leur applicabilité "
            "aux chantiers routiers et signale les contraintes opérationnelles du "
            "réseau national. Pour tout autre CTM, l'accès passe par une demande "
            "de permission au Bureau Directoire."
        ),
    },
    {
        'n': 19,
        'title': 'Administrateur Technique et Financier — Office des Voiries et Drainage (OVD)',
        'origin': 'Office des Voiries et Drainage (OVD)',
        'quota_line': 5,
        'icon': 'waves',
        'accent': 'teal',
        'mission': (
            "Représente l'Office des Voiries et Drainage, agence publique en "
            "charge des voiries urbaines et des réseaux de drainage, au sein du "
            "Comité de Pilotage Élargi. Apporte l'expertise de terrain sur les "
            "normes d'assainissement et de macro-drainage en cours d'élaboration."
        ),
        'interface_role': (
            "Dispose d'un accès privilégié au CTM 7 — Assainissement & "
            "Macro-drainage : audite les brouillons techniques sous l'angle de "
            "leur applicabilité aux ouvrages de drainage urbain. Pour tout autre "
            "CTM, l'accès passe par une demande de permission au Bureau "
            "Directoire."
        ),
    },
    {
        'n': 20,
        'title': 'Administrateur Technique et Financier — Agence Congolaise des Grands Travaux (ACGT)',
        'origin': 'Agence Congolaise des Grands Travaux (ACGT)',
        'quota_line': 6,
        'icon': 'hard-hat',
        'accent': 'green',
        'mission': (
            "Représente l'Agence Congolaise des Grands Travaux, maître d'ouvrage "
            "délégué des grands projets d'infrastructure, au sein du Comité de "
            "Pilotage Élargi. Apporte une vision transversale sur la faisabilité "
            "opérationnelle des normes couvrant la géotechnique, les chaussées "
            "et l'innovation."
        ),
        'interface_role': (
            "Dispose d'un accès privilégié aux CTM 1 à 3 — Normes & Innovation : "
            "audite les brouillons techniques de ces trois groupes sous l'angle "
            "de leur faisabilité pour les grands chantiers. Pour tout autre CTM, "
            "l'accès passe par une demande de permission au Bureau Directoire."
        ),
    },
    {
        'n': 21,
        'title': "Directeur d'Expertise — Bureau Technique de Contrôle (BTC)",
        'origin': 'Bureau Technique de Contrôle (BTC)',
        'quota_line': 7,
        'icon': 'flask-conical',
        'accent': 'teal',
        'mission': (
            "Représente le Bureau Technique de Contrôle, organisme chargé de la "
            "vérification des protocoles d'essais de laboratoire (mécaniques, "
            "thermiques, hydrauliques), au sein du Comité de Pilotage Élargi. "
            "Garantit la conformité des essais réalisés aux normes de référence "
            "ISO/ARSO sur l'ensemble des Comités Techniques Métiers."
        ),
        'interface_role': (
            "Dispose d'un accès de contrôle transverse sur les 8 CTM via le "
            "Module Contrôle BTC : vérifie les protocoles d'essais de "
            "laboratoire CTM par CTM. N'intervient pas sur l'édition des "
            "textes normatifs ni sur la validation financière (exclusive au "
            "FONER)."
        ),
    },
    {
        'n': 22,
        'title': "Directeur des Études Financières — Fonds National d'Entretien Routier (FONER)",
        'origin': "Fonds National d'Entretien Routier (FONER)",
        'quota_line': 8,
        'icon': 'calculator',
        'accent': 'emerald',
        'mission': (
            "Représente le Fonds National d'Entretien Routier au sein du "
            "Comité de Pilotage Élargi. Seul habilité à évaluer et valider les "
            "études d'impact financier du cycle de vie des chaussées produites "
            "par les Groupes de Travail."
        ),
        'interface_role': (
            "Dispose du Widget de Validation Financière : évalue, valide ou "
            "rejette les études de coût soumises par les WG. N'a pas d'accès "
            "CTM direct (rôle financier transverse) et n'intervient ni sur "
            "l'ingénierie ni sur la légistique."
        ),
    },
]


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageATFAppView(View):
    """
    Interface administrative dédiée au Collège des Administrateurs Techniques
    et Financiers : navigation par sidebar entre les Postes 18 à 22 (Office des
    Routes, Office des Voiries et Drainage, Agence Congolaise des Grands
    Travaux, Bureau Technique de Contrôle, FONER), chacun affichant sa
    mission, son cadre d'intervention (Profil 3 : lecture seule WG/CTM, accès
    privilégié sur ses CTM de spécialité) et sa console spécialisée (Audit
    Technique / Module Contrôle BTC / Validation Financière FONER).
    """
    template_name = 'pilotage/app_atf/app.html'

    def get(self, request):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        priv = get_pilotage_context(expert)
        if not priv or priv['pilotage_college'] != 'atf':
            messages.info(
                request,
                "L'espace administratif des Administrateurs Techniques et "
                "Financiers est réservé aux membres de ce collège."
            )
            return redirect('web:pilotage_dashboard')

        my_poste_order = priv['poste'].order if priv['poste'] else None

        postes = []
        default_post_n = _ATF_POSTES[0]['n']
        for meta in _ATF_POSTES:
            is_mine = meta['n'] == my_poste_order
            if is_mine:
                default_post_n = meta['n']
            postes.append({**meta, 'is_mine': is_mine})

        context = {
            'expert': expert,
            'postes': postes,
            'default_post_n': default_post_n,
            **priv,
        }
        return render(request, self.template_name, context)


# ─────────────────────────────────────────────────────────────────────────────
# VUE DÉTAIL D'UN CTM (Console Globale — Bureau Directoire)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageCTMDetailView(View):
    """
    Vue détaillée d'un Comité Technique Miroir : ses Groupes de Travail,
    ses experts membres, ses normes en cours et ses normes déjà publiées.
    Accessible depuis la Console Globale du Bureau Directoire.
    """
    template_name = 'pilotage/ctm_detail.html'

    def get(self, request, number):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        priv = get_pilotage_context(expert)
        if not priv or not priv['can_view_global_console']:
            messages.info(
                request,
                "Le détail des Comités Techniques Miroirs est réservé au Bureau Directoire."
            )
            return redirect('web:pilotage_dashboard')

        ctm = get_object_or_404(CTM, number=number)

        wgs_with_stats = []
        for wg in ctm.working_groups.select_related(
            'president__user', 'rapporteur__user', 'secretary__user'
        ).order_by('number'):
            wgs_with_stats.append({'wg': wg, 'member_count': wg.affectations.count()})

        affectations = (
            ctm.affectations
            .select_related('expert__user', 'expert__structure', 'wg')
            .order_by('wg__number', 'expert__user__last_name')
        )

        normes_en_cours = (
            ctm.normes.exclude(status='PUBLISHED')
            .select_related('wg')
            .order_by('wg__number', '-created_at')
        )
        normes_publiees = (
            ctm.normes.filter(status='PUBLISHED')
            .select_related('wg')
            .order_by('-publication_date')
        )

        context = {
            'ctm': ctm,
            'wgs_with_stats': wgs_with_stats,
            'affectations': affectations,
            'normes_en_cours': normes_en_cours,
            'normes_publiees': normes_publiees,
            **priv,
        }
        return render(request, self.template_name, context)


# ─────────────────────────────────────────────────────────────────────────────
# VUE GESTION DES ACCÈS EXPERTS (Console Globale — Bureau Directoire)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageExpertAccessView(View):
    """
    Liste l'ensemble des experts et leurs affectations CTM/WG. Permet au
    Bureau Directoire de débloquer/suspendre l'accès d'un expert à la
    plateforme et de l'exclure d'un Groupe de Travail / CTM.
    """
    template_name = 'pilotage/expert_access.html'

    def get(self, request):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            messages.warning(request, "Votre compte expert n'est pas encore activé.")
            return redirect('web:home')

        priv = get_pilotage_context(expert)
        if not priv or not priv['can_manage_access']:
            messages.info(
                request,
                "La gestion des accès experts est réservée au Bureau Directoire."
            )
            return redirect('web:pilotage_dashboard')

        experts = (
            Expert.objects
            .select_related('user', 'structure', 'ctm')
            .prefetch_related(
                Prefetch(
                    'governance_affectations',
                    queryset=Affectation.objects.select_related('ctm', 'wg').order_by('ctm__number', 'wg__number'),
                )
            )
            .order_by('user__last_name', 'user__first_name')
        )

        context = {
            'experts': experts,
            **priv,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageExpertStatusActionView(View):
    """
    Débloque ou suspend l'accès d'un expert à la plateforme (Expert.status).
    Réservée au Bureau Directoire.
    """

    def post(self, request, pk):
        expert = Expert.objects.filter(user=request.user).first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        membership = PilotageMembreship.objects.filter(
            expert=expert, role__in=_DIRECTOIRE_ROLES
        ).first()
        if not membership:
            return JsonResponse(
                {'ok': False, 'error': 'Action réservée au Bureau Directoire.'},
                status=403
            )

        target = get_object_or_404(Expert, pk=pk)
        action = (request.POST.get('action') or '').strip().lower()

        if action == 'suspend':
            target.status = 'SUSPENDED'
        elif action == 'activate':
            target.status = 'ACTIVE'
        else:
            return JsonResponse({'ok': False, 'error': 'Action invalide.'}, status=400)

        target.save(update_fields=['status'])

        verb = 'suspendu' if action == 'suspend' else 'rétabli'
        return JsonResponse({
            'ok': True,
            'message': f"Accès de {target.full_name} {verb}.",
            'new_status': target.status,
            'new_status_label': target.get_status_display(),
        })


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotageAffectationExcludeView(View):
    """
    Exclut un expert d'un Groupe de Travail / CTM (suppression de l'Affectation).
    Réservée au Bureau Directoire.
    """

    def post(self, request, pk):
        expert = Expert.objects.filter(user=request.user).first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        membership = PilotageMembreship.objects.filter(
            expert=expert, role__in=_DIRECTOIRE_ROLES
        ).first()
        if not membership:
            return JsonResponse(
                {'ok': False, 'error': 'Action réservée au Bureau Directoire.'},
                status=403
            )

        affectation = get_object_or_404(Affectation, pk=pk)
        message = (
            f"{affectation.expert.full_name} retiré du {affectation.wg} "
            f"(CTM {affectation.ctm.number})."
        )
        affectation.delete()

        return JsonResponse({'ok': True, 'message': message})


@method_decorator(login_required(login_url='/se-connecter/'), name='dispatch')
class PilotagePlatformFreezeToggleView(View):
    """
    Bascule le verrou plateforme CTC/CTM — réservé au Président du Comité de Pilotage.
    """

    def post(self, request):
        expert = Expert.objects.filter(user=request.user).select_related('structure').first()
        if not expert:
            return JsonResponse({'ok': False, 'error': 'Expert introuvable.'}, status=403)

        priv = get_pilotage_context(expert)
        if not priv or priv['user_sub_role'] != 'president':
            return JsonResponse(
                {'ok': False, 'error': 'Action réservée au Président du Comité de Pilotage.'},
                status=403
            )

        freeze = PlatformFreeze.get_solo()
        freeze.is_locked = not freeze.is_locked
        freeze.locked_by = expert if freeze.is_locked else None
        freeze.locked_at = timezone.now() if freeze.is_locked else None
        freeze.save(update_fields=['is_locked', 'locked_by', 'locked_at'])

        return JsonResponse({
            'ok': True,
            'is_locked': freeze.is_locked,
            'message': (
                "Plateforme verrouillée : toutes les actions CTC et CTM sont suspendues."
                if freeze.is_locked else
                "Plateforme déverrouillée : les actions CTC et CTM sont rétablies."
            ),
        })
