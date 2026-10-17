"""Référentiel organisationnel partagé par les trois interfaces de l'assistant."""

from apps.experts.models import Expert
from apps.governance.models import (
    Affectation,
    CTM,
    MandatOrganisation,
    WG,
)
from apps.governance.phoenix_models import (
    AffectationSousCommission,
    CorrespondanceGroupe,
    CorrespondanceStructure,
    GroupeCible,
    OrganisationVersion,
    Organe,
)
from . import register


ORGANISATION_MAPPING_SCHEMA = {
    'type': 'object',
    'properties': {
        'version_code': {
            'type': 'string',
            'description': "Code de la version d'organisation (optionnel ; par défaut la plus récente).",
        },
    },
}


def _latest_version(version_code=None):
    qs = OrganisationVersion.objects.all()
    if version_code:
        return qs.filter(code=version_code).first()
    return qs.order_by('-created_at', '-id').first()


@register(
    'get_organisation_mapping',
    "Retourne le référentiel organisationnel : ancienne structure (CTM/WG avec leurs bureaux), "
    "nouvelle structure (SC et GT), rattachement des GT aux SC et correspondances CTM/WG -> SC/GT. "
    "Précise toujours la version, son statut et l'absence éventuelle de correspondance validée.",
    ORGANISATION_MAPPING_SCHEMA,
    scopes=['expert', 'ctc', 'pilotage'],
)
def get_organisation_mapping(session, version_code=None):
    version = _latest_version(version_code)
    if not version:
        return {'error': "Aucune version d'organisation n'est enregistrée."}

    scs = (
        Organe.objects.filter(version=version, type=Organe.Type.SC)
        .prefetch_related('groupes')
        .order_by('code')
    )
    new_structure = []
    for sc in scs:
        new_structure.append({
            'code': sc.code,
            'name': sc.official_name or sc.name,
            'status': sc.get_status_display(),
            'domain': sc.domain,
            'groupes': [
                {
                    'code': gt.code,
                    'name': gt.name,
                    'mission': gt.mission,
                    'status': gt.get_status_display(),
                }
                for gt in sc.groupes.all().order_by('code')
            ],
        })

    old_structure = []
    for ctm in CTM.objects.prefetch_related('working_groups').order_by('number'):
        wgs = []
        for wg in ctm.working_groups.all().order_by('number'):
            wgs.append({
                'label': f'WG {ctm.number}.{wg.number}',
                'name': wg.name,
                'president': wg.president.full_name if wg.president else None,
                'rapporteur': wg.rapporteur.full_name if wg.rapporteur else None,
                'secretary': wg.secretary.full_name if wg.secretary else None,
            })
        old_structure.append({
            'number': ctm.number,
            'name': ctm.name,
            'president': ctm.scientific_president.full_name if ctm.scientific_president else None,
            'rapporteur': ctm.rapporteur.full_name if ctm.rapporteur else None,
            'secretary': ctm.secretary.full_name if ctm.secretary else None,
            'groupes': wgs,
        })

    structure_mappings = [
        {
            'ctm': f'CTM {item.ctm.number} — {item.ctm.name}',
            'sc': item.sc.code if item.sc else None,
            'nature': item.get_nature_display(),
            'domain': item.domain,
            'status': item.get_status_display(),
            'decision_reference': item.decision_reference,
        }
        for item in CorrespondanceStructure.objects.filter(version=version)
        .select_related('ctm', 'sc').order_by('ctm__number')
    ]
    group_mappings = [
        {
            'wg': f'WG {item.wg.ctm.number}.{item.wg.number} — {item.wg.name}',
            'sc': item.sc.code if item.sc else None,
            'gt': item.gt.code if item.gt else None,
            'domain': item.domain,
            'status': item.get_status_display(),
            'decision_reference': item.decision_reference,
        }
        for item in CorrespondanceGroupe.objects.filter(version=version)
        .select_related('wg__ctm', 'sc', 'gt').order_by('wg__ctm__number', 'wg__number')
    ]

    result = {
        'version': {
            'code': version.code,
            'name': version.name,
            'status': version.get_status_display(),
            'activated_at': version.activated_at.isoformat() if version.activated_at else None,
        },
        'nouvelle_structure': new_structure,
        'ancienne_structure': old_structure,
        'correspondances_ctm_sc': structure_mappings,
        'correspondances_wg_sc_gt': group_mappings,
    }
    if not structure_mappings and not group_mappings:
        result['avertissement'] = (
            "Aucune correspondance CTM/WG -> SC/GT n'est enregistrée pour cette version. "
            "Le rattachement officiel des GT aux SC reste celui porté par les GT de la nouvelle "
            "structure ; ne pas déduire une correspondance historique non documentée."
        )
    return result


EXPERTS_CLASSIFICATION_SCHEMA = {
    'type': 'object',
    'properties': {
        'version_code': {'type': 'string', 'description': "Version d'organisation (optionnel)."},
        'sc_code': {'type': 'string', 'description': 'Filtrer sur une sous-commission (optionnel).'},
        'limit': {'type': 'integer', 'description': 'Nombre maximum de lignes (défaut 250).'},
    },
}


def _historical_roles(expert):
    roles = []
    for ctm in expert.ctm_president_of.all():
        roles.append(f'Président scientifique CTM {ctm.number}')
    for ctm in expert.ctm_rapporteur_of.all():
        roles.append(f'Rapporteur CTM {ctm.number}')
    for ctm in expert.ctm_secretary_of.all():
        roles.append(f'Secrétaire CTM {ctm.number}')
    for wg in expert.wg_president_of.all():
        roles.append(f'Président WG {wg.ctm.number}.{wg.number}')
    for wg in expert.wg_rapporteur_of.all():
        roles.append(f'Rapporteur WG {wg.ctm.number}.{wg.number}')
    for wg in expert.wg_secretary_of.all():
        roles.append(f'Secrétaire WG {wg.ctm.number}.{wg.number}')
    return roles


@register(
    'get_experts_classification',
    "Liste les experts avec leurs rôles historiques (président, rapporteur, secrétaire, membre), "
    "leur ancienne affectation CTM/WG, leur rattachement à une SC et leurs mandats/postes dans la "
    "nouvelle organisation. Dans l'espace Expert, retourne uniquement le dossier de l'utilisateur.",
    EXPERTS_CLASSIFICATION_SCHEMA,
    scopes=['expert', 'ctc', 'pilotage'],
)
def get_experts_classification(session, version_code=None, sc_code=None, limit=250):
    version = _latest_version(version_code)
    if not version:
        return {'error': "Aucune version d'organisation n'est enregistrée."}

    try:
        limit = max(1, min(int(limit), 500))
    except (TypeError, ValueError):
        limit = 250

    experts = (
        Expert.objects.select_related('user', 'structure', 'ctm')
        .prefetch_related(
            'ctm_president_of', 'ctm_rapporteur_of', 'ctm_secretary_of',
            'wg_president_of', 'wg_rapporteur_of', 'wg_secretary_of',
        )
    )
    if session.scope == 'expert':
        experts = experts.filter(user=session.user)
    if sc_code:
        experts = experts.filter(
            subcommission_assignments__version=version,
            subcommission_assignments__sc__code=sc_code,
        ).distinct()

    rows = []
    for expert in experts.order_by('user__last_name', 'user__first_name')[:limit]:
        legacy = [
            {
                'ctm': f'CTM {a.ctm.number} — {a.ctm.name}',
                'wg': f'WG {a.wg.ctm.number}.{a.wg.number} — {a.wg.name}' if a.wg else None,
                'ctm_role': a.ctm_role,
                'wg_role': a.wg_role,
            }
            for a in Affectation.objects.filter(expert=expert).select_related('ctm', 'wg', 'wg__ctm')
        ]
        assignments = [
            {
                'sc': item.sc.code if item.sc else None,
                'sc_name': (item.sc.official_name or item.sc.name) if item.sc else None,
                'status': item.get_status_display(),
                'source': f'WG {item.source_wg.ctm.number}.{item.source_wg.number}'
                if item.source_wg else (f'CTM {item.source_ctm.number}' if item.source_ctm else None),
                'rationale': item.rationale,
            }
            for item in AffectationSousCommission.objects.filter(expert=expert, version=version)
            .select_related('sc', 'source_ctm', 'source_wg__ctm')
        ]
        mandates = [
            {
                'poste': mandate.poste.title or mandate.poste.code,
                'poste_code': mandate.poste.code,
                'organe': mandate.poste.organe.code,
                'function': mandate.function,
                'status': mandate.get_status_display(),
                'groupe': mandate.groupe.code if mandate.groupe else None,
            }
            for mandate in MandatOrganisation.objects.filter(expert=expert)
            .filter(poste__organe__version=version)
            .select_related('poste__organe', 'groupe')
        ]
        new_sc = sorted({item['sc'] for item in assignments if item['sc']})
        new_sc += sorted({
            item['organe'] for item in mandates
            if item['organe'] not in new_sc and item['organe'].startswith('SC-')
        })
        rows.append({
            'expert_id': expert.id,
            'full_name': expert.full_name,
            'structure': expert.structure.acronym if expert.structure else None,
            'status': expert.get_status_display(),
            'ancienne_affectation': {
                'ctm_principal': f'CTM {expert.ctm.number} — {expert.ctm.name}' if expert.ctm else None,
                'affectations': legacy,
            },
            'roles_historiques': _historical_roles(expert),
            'nouvelle_sc': new_sc,
            'nouveaux_postes': mandates,
        })

    return {
        'version': {'code': version.code, 'status': version.get_status_display()},
        'total': len(rows),
        'experts': rows,
        'note': (
            "Un rattachement ou un mandat proposé n'est ni une nomination ni une habilitation. "
            "Les rôles historiques servent au rapprochement et ne créent aucun droit."
        ),
    }
