"""Archive les anciennes versions d'organisation dans les Communiqués.

Les données historiques sont sérialisées dans le modèle ``Draft`` (communiqués)
avant que l'interface ne cesse de lire les anciennes versions. Aucune donnée
n'est supprimée de la base par défaut.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.gemini_drafts.models import Draft
from apps.governance.models import CTM, WG, Affectation, MandatOrganisation
from apps.governance.phoenix_models import (
    AffectationSousCommission,
    CorrespondanceGroupe,
    CorrespondanceStructure,
    GroupeCible,
    OrganisationVersion,
    Organe,
    PosteOrganisation,
)
from apps.governance.phoenix_runtime import current_organisation_version


ARCHIVE_TYPE = 'ARCHIVE_ORGANISATION'


def _expert_name(expert):
    return expert.full_name if expert else None


def _legacy_payload():
    rows = []
    for ctm in CTM.objects.prefetch_related('working_groups').order_by('number'):
        rows.append({
            'number': ctm.number,
            'name': ctm.name,
            'description': ctm.description,
            'iso_reference': ctm.iso_reference,
            'arso_reference': ctm.arso_reference,
            'president': _expert_name(ctm.scientific_president),
            'rapporteur': _expert_name(ctm.rapporteur),
            'secretary': _expert_name(ctm.secretary),
            'working_groups': [
                {
                    'number': wg.number,
                    'name': wg.name,
                    'description': wg.description,
                    'president': _expert_name(wg.president),
                    'rapporteur': _expert_name(wg.rapporteur),
                    'secretary': _expert_name(wg.secretary),
                }
                for wg in ctm.working_groups.all().order_by('number')
            ],
        })
    return rows


def _version_payload(version):
    organes = []
    for organe in Organe.objects.filter(version=version).order_by('type', 'code'):
        organes.append({
            'code': organe.code,
            'name': organe.name,
            'official_name': organe.official_name,
            'type': organe.type,
            'status': organe.status,
            'domain': organe.domain,
            'composition': organe.composition,
            'postes': [
                {
                    'code': poste.code,
                    'category': poste.category,
                    'title': poste.title,
                    'origin_label': poste.origin_label,
                    'status': poste.status,
                    'required_structure': poste.required_structure.acronym
                    if poste.required_structure else None,
                }
                for poste in organe.postes.all().order_by('code')
            ],
            'groupes': [
                {
                    'code': groupe.code,
                    'name': groupe.name,
                    'mission': groupe.mission,
                    'activity': groupe.activity,
                    'status': groupe.status,
                    'source_reference': groupe.source_reference,
                }
                for groupe in organe.groupes.all().order_by('code')
            ],
        })

    mandats = [
        {
            'expert': _expert_name(mandat.expert),
            'poste': mandat.poste.code if mandat.poste else None,
            'poste_titre': mandat.poste.title if mandat.poste else None,
            'organe': mandat.poste.organe.code if mandat.poste else None,
            'groupe': mandat.groupe.code if mandat.groupe else None,
            'function': mandat.function,
            'capacity': mandat.capacity,
            'status': mandat.status,
            'appointment_reference': mandat.appointment_reference,
            'start_date': mandat.start_date.isoformat() if mandat.start_date else None,
            'end_date': mandat.end_date.isoformat() if mandat.end_date else None,
        }
        for mandat in MandatOrganisation.objects.filter(
            poste__organe__version=version,
        ).select_related('expert__user', 'poste__organe', 'groupe').order_by('poste__code')
    ]

    affectations = [
        {
            'expert': _expert_name(item.expert),
            'sc': item.sc.code if item.sc else None,
            'source_ctm': item.source_ctm.number if item.source_ctm else None,
            'source_wg': f'{item.source_wg.ctm.number}.{item.source_wg.number}'
            if item.source_wg else None,
            'status': item.status,
            'is_primary': item.is_primary,
            'source_kind': item.source_kind,
            'rationale': item.rationale,
            'effective_from': item.effective_from.isoformat() if item.effective_from else None,
        }
        for item in AffectationSousCommission.objects.filter(version=version)
        .select_related('expert__user', 'sc', 'source_ctm', 'source_wg__ctm')
        .order_by('sc__code', 'expert__user__last_name')
    ]

    correspondances = {
        'ctm': [
            {
                'ctm': mapping.ctm.number,
                'sc': mapping.sc.code if mapping.sc else None,
                'nature': mapping.nature,
                'domain': mapping.domain,
                'status': mapping.status,
                'justification': mapping.justification,
                'source_reference': mapping.source_reference,
                'decision_reference': mapping.decision_reference,
            }
            for mapping in CorrespondanceStructure.objects.filter(version=version)
            .select_related('ctm', 'sc').order_by('ctm__number')
        ],
        'wg': [
            {
                'wg': f'{mapping.wg.ctm.number}.{mapping.wg.number}',
                'sc': mapping.sc.code if mapping.sc else None,
                'gt': mapping.gt.code if mapping.gt else None,
                'domain': mapping.domain,
                'status': mapping.status,
                'justification': mapping.justification,
                'source_reference': mapping.source_reference,
                'decision_reference': mapping.decision_reference,
            }
            for mapping in CorrespondanceGroupe.objects.filter(version=version)
            .select_related('wg__ctm', 'sc', 'gt').order_by('wg__ctm__number', 'wg__number')
        ],
    }

    return {
        'version': {
            'code': version.code,
            'name': version.name,
            'status': version.status,
            'source_document': version.source_document,
            'activated_at': version.activated_at.isoformat() if version.activated_at else None,
        },
        'organes': organes,
        'mandats': mandats,
        'affectations_experts': affectations,
        'correspondances': correspondances,
        'legacy_ctm_wg': _legacy_payload(),
        'legacy_affectations': [
            {
                'expert': _expert_name(item.expert),
                'ctm': item.ctm.number if item.ctm else None,
                'wg': f'{item.wg.ctm.number}.{item.wg.number}' if item.wg else None,
                'ctm_role': item.ctm_role,
                'wg_role': item.wg_role,
            }
            for item in Affectation.objects.select_related('expert__user', 'ctm', 'wg__ctm')
            .order_by('ctm__number', 'wg__number')
        ],
    }


def _markdown(payload):
    version = payload['version']
    lines = [
        f"# Archive organisation — {version['name']}",
        '',
        f"- **Code** : {version['code']}",
        f"- **Statut au moment de l'archivage** : {version['status']}",
        f"- **Document source** : {version['source_document']}",
        f"- **Archivé le** : {timezone.localtime().strftime('%d/%m/%Y %H:%M')}",
        '',
        '## Sous-commissions et groupes',
    ]
    for organe in payload['organes']:
        if organe['type'] != 'SC':
            continue
        lines.append(f"### {organe['code']} — {organe['official_name'] or organe['name']}")
        for groupe in organe['groupes']:
            lines.append(f"- {groupe['code']} — {groupe['name']}")
    lines.extend([
        '',
        '## Postes et titulaires',
    ])
    for mandat in payload['mandats']:
        lines.append(
            f"- {mandat['poste_titre'] or mandat['poste']} ({mandat['organe']}) : "
            f"{mandat['expert'] or 'vacant'} — {mandat['status']}"
        )
    lines.extend([
        '',
        '## Ancienne structure CTM/WG',
    ])
    for ctm in payload['legacy_ctm_wg']:
        lines.append(f"### CTM {ctm['number']} — {ctm['name']}")
        for wg in ctm['working_groups']:
            lines.append(f"- WG {ctm['number']}.{wg['number']} — {wg['name']}")
    return '\n'.join(lines)


class Command(BaseCommand):
    help = "Archive les anciennes versions d'organisation dans les Communiqués, sans supprimer la base."

    def add_arguments(self, parser):
        parser.add_argument(
            '--code', action='append', default=[],
            help="Code d'une version à archiver (répétable). Par défaut : toutes sauf la version courante.",
        )
        parser.add_argument(
            '--include-current', action='store_true',
            help="Archiver aussi la version courante.",
        )

    def handle(self, *args, **options):
        current = current_organisation_version()
        codes = set(options['code'])
        versions = list(OrganisationVersion.objects.order_by('created_at', 'id'))
        if codes:
            versions = [version for version in versions if version.code in codes]
            missing = codes - {version.code for version in versions}
            if missing:
                raise CommandError(f"Version(s) introuvable(s) : {', '.join(sorted(missing))}")
        elif not options['include_current'] and current:
            versions = [version for version in versions if version.pk != current.pk]

        if not versions:
            self.stdout.write(self.style.WARNING("Aucune version à archiver."))
            return

        created = 0
        skipped = 0
        for version in versions:
            key = f"organisation:{version.code}"
            if Draft.objects.filter(
                type=ARCHIVE_TYPE, input_json__archive_key=key,
            ).exists():
                skipped += 1
                self.stdout.write(f"  = {version.code} : déjà archivé")
                continue
            payload = _version_payload(version)
            payload['archive_key'] = key
            with transaction.atomic():
                Draft.objects.create(
                    title=f"Archive organisation — {version.name} ({version.code})",
                    ctm='',
                    wg='',
                    type=ARCHIVE_TYPE,
                    domain='gouvernance',
                    input_json=payload,
                    draft_text=_markdown(payload),
                    status=Draft.STATUS_ARCHIVED,
                    classification_reason=(
                        "Archivage des anciennes versions avant suppression de leur logique de lecture."
                    ),
                )
            created += 1
            self.stdout.write(self.style.SUCCESS(f"  + {version.code} archivé"))

        self.stdout.write(self.style.SUCCESS(
            f"Archivage terminé : {created} version(s) archivée(s), {skipped} déjà présente(s)."
        ))
