import hashlib
import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, models
from django.utils import timezone

from .models import (
    CTM, WG, OrganisationVersion, Organe, PosteOrganisation, GroupeCible,
    CorrespondanceStructure, CorrespondanceGroupe, JournalMigration,
    RattachementDocumentaire, MandatOrganisation, HabilitationAction,
)

POLES = (
    ('ST-AD', 'Analyse documentaire'), ('ST-APP', 'Appui technique et formation'),
    ('ST-LC', 'Logistique et communication'), ('ST-RE', 'Relations extérieures et ARM'),
    ('ST-CSC', 'Coordination des sous-commissions'),
)


@transaction.atomic
def seed_phoenix(code='phoenix-2026-10', actor=None):
    reference = json.loads(Path(__file__).with_name('phoenix_reference.json').read_text(encoding='utf-8'))
    source = Path(settings.BASE_DIR) / reference['source_document']
    if not source.is_file():
        raise ValidationError('La note source Phoenix doit être présente avant le chargement du catalogue.')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    version, created = OrganisationVersion.objects.get_or_create(code=code, defaults={
        'name': 'CNE-ITP', 'source_document': reference['source_document'],
        'source_sha256': digest,
    })
    version = OrganisationVersion.objects.select_for_update().get(pk=version.pk)
    if version.status != 'PROPOSED':
        raise ValidationError('Le chargement ne peut modifier qu’une organisation proposée.')
    if version.source_sha256 != digest:
        raise ValidationError('La source a changé ; créer une nouvelle version de préparation.')
    existing_preparation = version.journal.filter(operation='PREPARE_REFERENCE').first()
    if existing_preparation:
        return version, existing_preparation.after.get('missing_legacy_sources', [])
    old_count = 0
    organs = {}
    for organ_code, kind, name, parent in (
        ('COPIL', 'COPIL', 'Comité de Pilotage', None),
        ('ST', 'ST', 'Secrétariat technique', None),
        *((pole_code, 'ST_POLE', name, 'ST') for pole_code, name in POLES),
    ):
        organs[organ_code], made = Organe.objects.get_or_create(version=version, code=organ_code, defaults={
            'type': kind, 'name': name, 'parent': organs.get(parent),
            'source_reference': 'Note Phoenix, sections 1 à 3',
        })
        old_count += int(made)
    for item in reference['sc']:
        organs[item['code']], made = Organe.objects.get_or_create(version=version, code=item['code'], defaults={
            'type': 'SC', 'name': item['name'], 'domain': item['domain'],
            'source_reference': 'Note Phoenix, section 4 — dénomination proposée',
            'composition': {'categories': ['Président', 'Vice-président', 'Secrétaire', 'Secrétaire adjoint', 'Membres', 'Observateurs', 'Appoints'],
                            'effectifs': None, 'titulaires': None, 'gt_catalogue': None},
        })
        old_count += int(made)
    for item in reference['posts']:
        _, made = PosteOrganisation.objects.get_or_create(organe=organs[item['organe']], code=item['code'], defaults={
            'category': item['category'], 'title': item['title'], 'origin_label': item['origin_label'],
            'source_reference': 'Note Phoenix, section 2' if item['code'].startswith('COPIL-') else 'Note Phoenix, section 3',
        })
        old_count += int(made)
    missing = []
    for item in reference['ctm_mappings']:
        ctm = CTM.objects.filter(number=item['number']).first()
        if not ctm:
            missing.append(f'CTM {item["number"]}')
            continue
        _, made = CorrespondanceStructure.objects.get_or_create(version=version, ctm=ctm, domain=item['domain'], defaults={
            'sc': organs.get(item['sc']), 'justification': item['justification'],
            'source_reference': 'Plan de migration Phoenix, section 5 — proposition',
        })
        old_count += int(made)
        if item['number'] == 2:
            for sc in ('SC-IT', 'SC-BAT', 'SC-OH', 'SC-SOCLE'):
                _, made = CorrespondanceStructure.objects.get_or_create(version=version, ctm=ctm, domain=f'Contribution candidate à {sc}', defaults={
                    'sc': organs[sc], 'nature': 'CONTRIBUTION', 'justification': 'Correspondance multiple proposée ; propriétaire à confirmer par dossier.',
                    'source_reference': 'Plan de migration Phoenix, section 5',
                })
                old_count += int(made)
        if item['number'] in (3, 4, 5):
            _, made = CorrespondanceStructure.objects.get_or_create(version=version, ctm=ctm, domain='Contribution candidate à SC-SE·GEO·RS', defaults={
                'sc': organs['SC-SE·GEO·RS'], 'nature': 'CONTRIBUTION',
                'justification': 'Hypothèse conditionnelle selon le contenu documentaire ; aucune réaffectation.',
                'source_reference': 'Plan de migration Phoenix, section 5',
            })
            old_count += int(made)
    for item in reference['wg_mappings']:
        ctm_number, wg_number = map(int, item['number'].split('.'))
        wg = WG.objects.filter(ctm__number=ctm_number, number=wg_number).first()
        if not wg:
            missing.append(f'WG {item["number"]}')
            continue
        _, made = CorrespondanceGroupe.objects.get_or_create(version=version, wg=wg, domain=item['domain'], defaults={
            'justification': item['justification'], 'source_reference': 'Plan de migration Phoenix, section 5 — domaine candidat, GT non renseigné',
        })
        old_count += int(made)
    if created or old_count:
        JournalMigration.objects.create(version=version, actor=actor,
            actor_name=(actor.get_full_name() or actor.username) if actor else 'Commande de préparation',
            operation='PREPARE_REFERENCE', target=version.code,
            after={'copil_posts': 22, 'st_posts': 24, 'sc': 7, 'gt': 0, 'created_records': old_count, 'missing_legacy_sources': missing},
            reason='Préparation additive ; données, mandats, habilitations et circuits historiques conservés.')
    return version, missing


def has_organisation_action(user, mandat, action, norme=None, groupe=None):
    """Aucun nouveau mandat ne donne accès implicitement à un dossier historique."""
    today = timezone.localdate()
    if not user.is_authenticated or not user.is_active or not mandat.pk:
        return False
    mandat = MandatOrganisation.objects.select_related('expert__user', 'poste__organe__version', 'groupe__sc__version').filter(pk=mandat.pk).first()
    if not mandat or mandat.expert.user_id != user.pk or mandat.expert.status != 'ACTIVE' or not mandat.expert.user.is_active:
        return False
    version = mandat.organisation_version
    allowed_statuses = ('ACTIVE', 'SUSPENDED', 'ARCHIVED') if action == 'document.consulter' else ('ACTIVE',)
    if version.status not in allowed_statuses or mandat.status != 'ACTIVE' or not mandat.appointment_reference.strip() or not mandat.start_date:
        return False
    if mandat.start_date > today or (mandat.end_date and mandat.end_date < today):
        return False
    if mandat.groupe_id and groupe and mandat.groupe_id != groupe.pk:
        return False
    if mandat.groupe_id and norme and not RattachementDocumentaire.objects.filter(norme=norme, version=version, gt_id=mandat.groupe_id, status='VALIDATED').exists():
        return False
    grants = mandat.habilitations.filter(action=action, enabled=True, start_date__lte=today).select_related('perimeter', 'delegated_from__mandat__expert__user')
    for grant in grants:
        if grant.perimeter.version_id != version.pk or not grant.decision_reference or (grant.end_date and grant.end_date < today):
            continue
        if grant.delegated_from_id:
            source = grant.delegated_from
            origin = source.mandat
            if not source.enabled or source.start_date > today or (source.end_date and source.end_date < today) or origin.status != 'ACTIVE' or not origin.start_date or origin.start_date > today or (origin.end_date and origin.end_date < today) or origin.expert.status != 'ACTIVE' or not origin.expert.user.is_active:
                continue
        if norme is None:
            if action == 'organisation.consulter' or (action == 'document.creer' and groupe and groupe.sc.version_id == version.pk and (grant.perimeter_id == groupe.sc_id or grant.perimeter.type in ('ST', 'COPIL'))):
                return True
            continue
        bindings = RattachementDocumentaire.objects.filter(norme=norme, version=version, status='VALIDATED').filter(
            models.Q(effective_from__isnull=True) | models.Q(effective_from__lte=today)).filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=today))
        if grant.perimeter.type == 'SC':
            bindings = bindings.filter(sc=grant.perimeter)
        elif grant.perimeter.type not in ('COPIL', 'ST'):
            continue
        if bindings.exists():
            return True
    return False


@transaction.atomic
def propose_mapping(user, mapping_type, pk, sc_id, domain, justification):
    from .organisation_permissions import can_prepare_organisation
    if not can_prepare_organisation(user):
        raise PermissionDenied('Une habilitation de préparation CNE-ITP est nécessaire.')
    if mapping_type not in ('ctm', 'wg'):
        raise ValidationError('Type de correspondance invalide.')
    model = CorrespondanceStructure if mapping_type == 'ctm' else CorrespondanceGroupe
    mapping = model.objects.select_for_update().select_related('version').get(pk=pk)
    if mapping.version.status != 'PROPOSED' or mapping.status != 'PROPOSED':
        raise ValidationError('Seules les correspondances proposées peuvent être ajustées ici.')
    before = {'sc_id': mapping.sc_id, 'domain': mapping.domain, 'justification': mapping.justification}
    mapping.sc = Organe.objects.get(pk=sc_id, version=mapping.version, type='SC') if sc_id else None
    mapping.domain = domain.strip()
    mapping.justification = justification.strip()
    if not mapping.domain:
        raise ValidationError('Le périmètre de correspondance doit être renseigné.')
    mapping.updated_by = user
    mapping.save()
    JournalMigration.objects.create(version=mapping.version, actor=user,
        actor_name=user.get_full_name() or user.username, operation='PROPOSE_MAPPING',
        target=f'{mapping_type}:{mapping.pk}', before=before,
        after={'sc_id': mapping.sc_id, 'domain': mapping.domain, 'justification': mapping.justification},
        reason=mapping.justification)
    return mapping
