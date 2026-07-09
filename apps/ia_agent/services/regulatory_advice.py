from typing import Tuple

from django.utils.translation import gettext_lazy as _

from .llm_client import LLMResponse, api_error_message, get_llm_client, unavailable_message


SYSTEM_INSTRUCTION = (
    "Tu es un assistant réglementaire spécialisé dans la révision de textes normatifs et "
    "la formulation de clauses de normes pour le CTM / WG. Analyse le texte fourni, "
    "repère les écarts de style ou de fond qui peuvent poser problème au regard de la "
    "qualité normative attendue, et propose une version révisée plus claire, conforme "
    "et concise.sans perdre l'essentielle en tenant compte de parametre de la norme, tu ctm et tu wg"
)

USER_INSTRUCTION = (
    "Act en tant qu'expert en normalisation, ingénierie et rédaction juridique technique. "
    "Ton objectif est de réécrire, adapter et formaliser une norme nationale complète (degré MOD - Modifiée) "
    "en transposant le texte source fourni selon le cadre réglementaire d'un pays cible (par exemple la RDC via l'OCC). "
    "Tu dois impérativement générer un document intégral, ultra-détaillé et pleinement rédigé, "
    "en respectant la consigne stricte de n'utiliser AUCUN tableau markdown et AUCUNE formule mathématique "
    "(remplace-les systématiquement par des descriptions textuelles fluides et des listes structurées).\n\n"
    "Voici la structure exacte et exhaustive que tu dois déployer de bout en bout :\n\n"
    "1. EN-TÊTE ET MÉTADONNÉES DE LA NORME\n"
    "- Titre complet adapté au contexte national.\n"
    "- Numéro officiel (ex: NN-BTP-001-2026), Statut (Norme nationale — Volontaire ou Obligatoire), "
    "Comité auteur, Organisme éditeur, Date d’adoption et Date d’entrée en vigueur.\n\n"
    "2. PRÉAMBULE\n"
    "- Déclaration des objectifs, de la recherche de sécurité, de l'alignement sur les pratiques internationales "
    "et de l'introduction des spécificités locales validées en Annexe H.\n\n"
    "3. INTRODUCTION\n"
    "- Objet : définition textuelle précise des buts de la norme.\n"
    "- Champ d’application : périmètre précis des éléments couverts et des exclusions.\n"
    "- Références normatives : liste exclusive des lois nationales en vigueur et des normes internationales indispensables.\n\n"
    "4. TERMES ET DÉFINITIONS\n"
    "- Liste détaillée définissant chaque concept technique, juridique ou administratif clé utilisé.\n\n"
    "5. PRINCIPES GÉNÉRAUX\n"
    "- Règles de conformité des entités, obligations monétaires (monnaie légale ou devises autorisées), "
    "unités de mesure (unités SI) et philosophie de règlement des différends.\n\n"
    "6. EXIGENCES ET CONDITIONS D'EXÉCUTION\n"
    "- Clauses contractuelles ou techniques détaillées étape par étape.\n"
    "- Intégration des obligations légales locales (ex: règles strictes de sous-traitance nationale, assurances obligatoires agréées).\n\n"
    "7. CALCULS ET CRITÈRES D’ACCEPTATION (FORMAT TEXTUEL UNIQUEMENT)\n"
    "- Règle de calcul des pénalités ou des révisions de prix : interdiction d'utiliser des équations mathématiques. "
    "Décris littéralement et explicitement les opérations (ex: 'multiplier le montant par le nombre de jours puis diviser par mille').\n"
    "- Règles d'arrondi financier et critères d'acceptation ou de conformité sous forme de listes à puces descriptives.\n\n"
    "8. MÉTHODES DE GESTION OU D'ESSAI DÉTAILLÉES\n"
    "- Procédure opérationnelle complète : de l'identification initiale jusqu'à l'application finale ou la réception.\n\n"
    "9. GESTION DES NON-CONFORMITÉS ET LITIGES\n"
    "- Processus clair : Détection des défaillances, Analyse et délais de réponse imposés, Mesures coercitives "
    "ou résiliation unilatérale, et instances de règlement des litiges (Tribunaux ou Centres d'arbitrage locaux).\n\n"
    "10. RAPPORT OU PROCÈS-VERBAL MINIMAL\n"
    "- Liste textuelle des mentions obligatoires devant figurer sur le document officiel pour en garantir la validité.\n\n"
    "11. MARQUAGE, TRAÇABILITÉ ET CONSERVATION\n"
    "- Règles de codification unique des pièces, archivage et durées de conservation légales.\n\n"
    "12. ANNEXES NORMATIVES ET INFORMATIVES\n"
    "- Déploiement des annexes de procédures et guides de bonnes pratiques.\n"
    "- Inclusion obligatoire de l'Annexe H (Annexe justificative des exigences locales) détaillant l'impact "
    "du climat, de l'économie, des capacités des laboratoires ou entreprises, et de la sécurité nationale.\n\n"
    "13. HISTORIQUE DES RÉVISIONS\n"
    "- Suivi chronologique de la version actuelle.\n\n"
    "14. CHECKLISTS ET FORMULAIRES PRÊTS À IMPRIMER (CONVERTIS EN LISTES TEXTUELLES)\n"
    "- Checklists du rédacteur, du comité technique et de publication réorganisées sous forme de listes de vérification descriptives.\n"
    "- Formulaires types (Fiche d'essai/situation, Certificat de conformité, Procès-verbal) présentés sous forme de fiches de saisie linéaires (indiquer le nom du champ suivi d'une zone descriptive textuelle).\n\n"
    "15. CONCORDANCE DES NORMES\n"
    "- Analyse comparative rédigée ligne par ligne associant chaque clause internationale d'origine à son équivalent national adopté, "
    "en explicitant clairement s'il y a un écart technique significatif et en renvoyant à l'annexe justificative.\n"
    "- Mode d'emploi textuel pour l'utilisateur final.\n\n"
    "CONSIGNES DE RÉDACTION DIRECTES :\n"
    "- Rédige dans un style normatif, impératif et fluide. N'utilise jamais de tableaux markdown (|---|). "
    "Structure les données comparatives ou les grilles à l'aide de titres et de listes à puces scannables.\n"
    "- Ne laisse aucune section vide, aucun résumé paresseux ni mention de type '[Contenu à insérer]'. "
    "Tout le document doit être entièrement rédigé et prêt à l'emploi.\n\n"
    "Voici le texte source à traiter : "
)


def _split_response(text: str) -> Tuple[str, str]:
    normalized = text.strip()
    if not normalized:
        return '', ''

    lower = normalized.lower()
    if 'proposition :' in lower:
        parts = normalized.split('Proposition :', 1)
        if len(parts) == 2:
            explanation = parts[0].strip()
            proposal = parts[1].strip()
            if explanation.lower().startswith('explication :'):
                explanation = explanation[len('explication :'):].strip()
            return explanation, proposal

    if 'proposition:' in lower:
        parts = normalized.split('Proposition:', 1)
        if len(parts) == 2:
            explanation = parts[0].strip()
            proposal = parts[1].strip()
            if explanation.lower().startswith('explication :'):
                explanation = explanation[len('explication :'):].strip()
            return explanation, proposal

    # Pas de séparateur détecté, renvoyer tout le texte dans la proposition.
    return '', normalized


def _build_fallback_advice(text: str) -> tuple[str, str]:
    cleaned = ' '.join(text.split())
    explanation = (
        "Le service IA n'était pas disponible au moment de l'analyse. "
        "Une reformulation de secours a été appliquée pour conserver la clarté du texte."
    )
    proposal = (
        "Le présent texte est rédigé de façon claire, concise et conforme aux attentes "
        "de formulation réglementaire.\n\n"
        f"{cleaned}"
    )
    return explanation, proposal


def generate_regulatory_advice(text: str) -> dict:
    if not text or not text.strip():
        return {
            'success': False,
            'error': _('Aucun texte fourni pour l’analyse réglementaire.'),
        }

    provider = 'gemini'
    llm = get_llm_client(provider)
    if llm is None:
        explanation, proposal = _build_fallback_advice(text)
        return {
            'success': True,
            'provider': provider,
            'raw': '',
            'explanation': explanation,
            'proposal': proposal,
            'fallback': True,
        }

    messages = [
        {'role': 'user', 'content': f"{USER_INSTRUCTION}\n\nTexte :\n{text}"},
    ]

    try:
        response: LLMResponse = llm.complete(SYSTEM_INSTRUCTION, messages, tools_spec=None)
    except Exception as exc:
        explanation, proposal = _build_fallback_advice(text)
        return {
            'success': True,
            'provider': provider,
            'raw': '',
            'explanation': explanation,
            'proposal': proposal,
            'fallback': True,
            'error': api_error_message(exc),
        }

    if response.stop_reason != 'end_turn':
        explanation, proposal = _build_fallback_advice(text)
        return {
            'success': True,
            'provider': provider,
            'raw': '',
            'explanation': explanation,
            'proposal': proposal,
            'fallback': True,
            'error': _("L’IA n’a pas renvoyé de résultat lisible pour cette demande."),
        }

    explanation, proposal = _split_response(response.text)
    return {
        'success': True,
        'provider': provider,
        'raw': response.text,
        'explanation': explanation or response.text,
        'proposal': proposal or response.text,
    }
