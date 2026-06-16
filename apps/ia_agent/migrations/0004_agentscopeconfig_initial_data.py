from django.db import migrations

INITIAL_CONFIGS = [
    {
        "scope": "pilotage",
        "role_key": "pilotage_directoire",
        "label": "Bureau Directoire (Postes 1–5)",
        "system_prompt_extra": (
            "Vous êtes membre du Bureau Directoire (Postes 1 à 5) — organe exécutif du Comité de Pilotage. "
            "Vous avez accès à l'ensemble des fonctionnalités IA : graphiques d'activité, détection de "
            "chevauchements entre groupes de travail, recherche dans les référentiels ISO/ARSO, synthèse "
            "des enquêtes publiques, rédaction de brouillons de messages et signalements formels. "
            "Vos recommandations engagent la coordination stratégique de la CNETP."
        ),
        "allowed_tools": None,
    },
    {
        "scope": "pilotage",
        "role_key": "pilotage_conseiller_politique",
        "label": "Conseillers Institutionnels et Politiques (Postes 6–17)",
        "system_prompt_extra": (
            "Vous êtes Conseiller Institutionnel et Politique (Postes 6 à 17). "
            "Vous avez accès aux tableaux de bord et indicateurs d'activité, à la liste des normes par CTM/WG, "
            "à la recherche dans les référentiels internationaux (ISO/ARSO) et à la synthèse des enquêtes "
            "publiques. Vous pouvez également préparer des brouillons de messages. "
            "La création formelle de signalements de chevauchements et de propositions officielles de nouvelles "
            "normes relève du Bureau Directoire et de la CTC — vous pouvez cependant consulter et commenter."
        ),
        "allowed_tools": [
            "get_chart_data", "list_ctm_norms", "search_external_referentials",
            "synthesize_public_inquiry", "create_email_draft",
        ],
    },
    {
        "scope": "pilotage",
        "role_key": "pilotage_atf",
        "label": "Administrateurs Techniques et Financiers (Postes 18–20)",
        "system_prompt_extra": (
            "Vous êtes Administrateur Technique et Financier (Postes 18 à 20). "
            "Vous avez accès aux indicateurs d'activité et de participation (graphiques), à la liste des "
            "normes en cours par CTM/WG, et à la préparation de brouillons de messages à caractère "
            "administratif. L'analyse normative approfondie (chevauchements, propositions référentiels) "
            "est réservée aux instances techniques (Bureau Directoire, CTC)."
        ),
        "allowed_tools": ["get_chart_data", "list_ctm_norms", "create_email_draft"],
    },
    {
        "scope": "pilotage",
        "role_key": "pilotage_observateur",
        "label": "Membres Observateurs (Postes 21–27)",
        "system_prompt_extra": (
            "Vous avez un accès en observation au Comité de Pilotage (Postes 21 à 27). "
            "Vous pouvez consulter les indicateurs d'activité (graphiques) et la liste des normes en cours. "
            "La création de propositions, signalements ou brouillons de messages n'est pas disponible "
            "dans votre rôle — adressez-vous au Bureau Directoire pour toute demande formelle."
        ),
        "allowed_tools": ["get_chart_data", "list_ctm_norms"],
    },
    {
        "scope": "ctc",
        "role_key": "ctc_member",
        "label": "Membre CTC",
        "system_prompt_extra": (
            "Vous êtes membre de la Cellule Technique de Coordination (CTC). "
            "Vous disposez de l'ensemble des fonctions CTC : consultation des normes par CTM/WG, "
            "détection et signalement de chevauchements entre groupes de travail, recherche dans les "
            "référentiels ISO/ARSO et proposition de nouvelles normes ou commentaires, synthèse des "
            "enquêtes publiques, et rédaction de brouillons de messages officiels."
        ),
        "allowed_tools": None,
    },
    {
        "scope": "expert",
        "role_key": "expert_active",
        "label": "Expert Actif",
        "system_prompt_extra": (
            "Vous êtes Expert actif sur la plateforme CNETP. "
            "Vous pouvez consulter votre dossier complet (CV, affectations CTM/WG, historique de votes), "
            "lister les groupes de travail disponibles, et préparer des demandes d'attribution à un "
            "groupe de travail accompagnées d'un brouillon d'email pour la CTC. "
            "Vos demandes sont soumises à validation par la CTC avant toute attribution officielle."
        ),
        "allowed_tools": None,
    },
]


def create_initial_configs(apps, schema_editor):
    AgentScopeConfig = apps.get_model('ia_agent', 'AgentScopeConfig')
    for cfg in INITIAL_CONFIGS:
        AgentScopeConfig.objects.get_or_create(
            scope=cfg['scope'],
            role_key=cfg['role_key'],
            defaults={
                'label': cfg['label'],
                'system_prompt_extra': cfg['system_prompt_extra'],
                'allowed_tools': cfg['allowed_tools'],
                'is_active': True,
            }
        )


def remove_initial_configs(apps, schema_editor):
    AgentScopeConfig = apps.get_model('ia_agent', 'AgentScopeConfig')
    AgentScopeConfig.objects.filter(
        role_key__in=[c['role_key'] for c in INITIAL_CONFIGS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('ia_agent', '0003_agentscopeconfig'),
    ]
    operations = [
        migrations.RunPython(create_initial_configs, remove_initial_configs),
    ]
