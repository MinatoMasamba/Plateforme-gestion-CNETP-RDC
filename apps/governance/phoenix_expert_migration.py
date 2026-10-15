"""Migration additive des experts historiques vers les sept sous-commissions."""
from __future__ import annotations

import hashlib
import sqlite3
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.experts.models import Expert
from .models import (
    Affectation, AffectationSousCommission, CorrespondanceGroupe,
    CorrespondanceStructure,
    CTM, JournalMigration, OrganisationVersion,
    Organe, WG,
)
from .phoenix_services import seed_phoenix


REQUIRED_SOURCE_TABLES = {
    'core_user', 'experts_expert', 'governance_ctm', 'governance_wg',
    'governance_affectation',
}

DIRECT_SC_BY_CTM = {1: 'SC-GF', 3: 'SC-BAT', 4: 'SC-IT', 5: 'SC-IT',
                    6: 'SC-OH', 7: 'SC-OH', 8: 'SC-SOCLE'}
EXPECTED_SC_CODES = {
    'SC-GF', 'SC-ESS', 'SC-IT', 'SC-BAT', 'SC-OH', 'SC-SE·GEO·RS', 'SC-SOCLE',
}


def inspect_legacy_database(source_path):
    """Lit la provenance utile en mode strictement read-only, sans secret utilisateur."""
    source = Path(source_path).expanduser().resolve()
    if not source.is_file():
        raise ValidationError(f'Base source introuvable : {source}.')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    connection = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValidationError('La base source ne passe pas le contrôle d’intégrité SQLite.')
        if connection.execute('PRAGMA foreign_key_check').fetchall():
            raise ValidationError('La base source contient des relations invalides.')
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        missing = sorted(REQUIRED_SOURCE_TABLES - tables)
        if missing:
            raise ValidationError('Tables historiques absentes : ' + ', '.join(missing))
        experts = [dict(row) for row in connection.execute(
            """
            SELECT e.id, e.user_id, e.status, e.ctm_id,
                   u.username, u.is_active AS user_is_active
            FROM experts_expert e
            JOIN core_user u ON u.id = e.user_id
            ORDER BY e.id
            """
        )]
        if not experts:
            raise ValidationError('La base source ne contient aucun expert à migrer.')
        assignments = [dict(row) for row in connection.execute(
            """
            SELECT a.id, a.expert_id, a.ctm_id, a.wg_id,
                   a.is_primary_ctm, a.is_primary_wg,
                   c.number AS ctm_number, w.number AS wg_number
            FROM governance_affectation a
            JOIN governance_ctm c ON c.id = a.ctm_id
            LEFT JOIN governance_wg w ON w.id = a.wg_id
            ORDER BY a.expert_id, a.is_primary_ctm DESC,
                     a.is_primary_wg DESC, a.id
            """
        )]
        ctm_numbers = {row['id']: row['number'] for row in connection.execute(
            'SELECT id, number FROM governance_ctm'
        )}
        wg_numbers = {
            row['id']: (row['ctm_number'], row['number'])
            for row in connection.execute(
                'SELECT w.id, c.number AS ctm_number, w.number '
                'FROM governance_wg w JOIN governance_ctm c ON c.id=w.ctm_id'
            )
        }
        return {
            'path': str(source), 'sha256': digest, 'experts': experts,
            'assignments': assignments, 'ctm_numbers': ctm_numbers,
            'wg_numbers': wg_numbers,
        }
    finally:
        connection.close()


def _unique_ctm_mapping(version, ctm_id):
    mappings = list(CorrespondanceStructure.objects.filter(
        version=version, ctm_id=ctm_id, nature='PRIMARY', sc__isnull=False,
    ).select_related('sc'))
    return mappings[0] if len(mappings) == 1 else None


def _explicit_wg_mapping(version, wg_id):
    mappings = list(CorrespondanceGroupe.objects.filter(
        version=version, wg_id=wg_id, sc__isnull=False,
    ).select_related('sc'))
    return mappings[0] if len(mappings) == 1 else None


def _batch_reference(source_sha, effective_date, decision_reference):
    payload = f'{source_sha}|{effective_date.isoformat()}|{decision_reference}'.encode()
    return 'SC-' + hashlib.sha256(payload).hexdigest()[:24].upper()


def _assert_same_referential(source):
    current_ctm = dict(CTM.objects.values_list('pk', 'number'))
    current_wg = {
        pk: (ctm_number, number)
        for pk, ctm_number, number in WG.objects.values_list('pk', 'ctm__number', 'number')
    }
    errors = []
    for pk, number in source['ctm_numbers'].items():
        if current_ctm.get(pk) != number:
            errors.append(f'CTM source #{pk}/{number} différent de la base cible')
    for pk, identity in source['wg_numbers'].items():
        if current_wg.get(pk) != identity:
            errors.append(f'WG source #{pk}/{identity[0]}.{identity[1]} différent de la base cible')
    if errors:
        raise ValidationError(errors[:20])


def _desired_assignment(version, source, item, expert, historical, decision_reference, effective_date, batch):
    selected = historical[0] if historical else None
    # Une affectation formelle CTM/WG est plus précise que le CTM déclaré
    # sur le profil. Le profil ne sert de repli qu'en son absence.
    source_ctm_id = selected['ctm_id'] if selected else item['ctm_id']
    source_wg_id = selected['wg_id'] if selected else None
    source_kind = (
        'AFFECTATION_WG' if selected and source_wg_id else
        'AFFECTATION_CTM' if selected else
        'PROFILE_CTM' if source_ctm_id else 'NO_SOURCE'
    )

    ctm_number = source['ctm_numbers'].get(source_ctm_id)
    structure_mapping = _unique_ctm_mapping(version, source_ctm_id) if source_ctm_id else None
    expected_code = DIRECT_SC_BY_CTM.get(ctm_number)
    mapping = (structure_mapping if structure_mapping and expected_code
               and structure_mapping.sc.code == expected_code else None)
    group_mapping = _explicit_wg_mapping(version, source_wg_id) if source_wg_id else None
    if group_mapping and (not mapping or group_mapping.sc_id != mapping.sc_id):
        mapping = None
        group_mapping = None

    historical_targets = {
        DIRECT_SC_BY_CTM.get(source['ctm_numbers'].get(legacy['ctm_id']))
        for legacy in historical
    } - {None}
    eligible = item['status'] == 'ACTIVE' and bool(item['user_is_active'])
    if not eligible:
        reason = 'Profil ou compte source non actif.'
        mapping = None
        group_mapping = None
    elif not source_ctm_id:
        reason = 'Aucun CTM source n’est renseigné.'
    elif len(historical_targets) > 1:
        reason = 'Les affectations historiques conduisent à plusieurs sous-commissions.'
        mapping = None
        group_mapping = None
    elif not mapping:
        reason = 'CTM à examiner ou correspondance principale absente ou divergente.'
    else:
        reason = ''

    status = AffectationSousCommission.Status.MIGRATED if mapping else AffectationSousCommission.Status.REVIEW
    sc = mapping.sc if status == AffectationSousCommission.Status.MIGRATED else None
    current_affectation = None
    if selected:
        current_affectation = Affectation.objects.filter(
            pk=selected['id'], expert=expert, ctm_id=source_ctm_id, wg_id=source_wg_id,
        ).first()
        if not current_affectation:
            raise ValidationError(f'L’affectation historique #{selected["id"]} ne correspond pas à la base cible.')

    snapshot = {
        'source_expert_id': item['id'], 'source_user_id': item['user_id'],
        'source_status': item['status'], 'source_user_is_active': bool(item['user_is_active']),
        'profile_ctm_id': item['ctm_id'], 'source_ctm_id': source_ctm_id,
        'source_ctm_number': source['ctm_numbers'].get(source_ctm_id),
        'source_wg_id': source_wg_id,
        'source_wg_number': selected['wg_number'] if selected else None,
        'source_affectation_id': selected['id'] if selected else None,
        'all_source_affectation_ids': [legacy['id'] for legacy in historical],
        'used_profile_ctm_fallback': not bool(selected) and bool(source_ctm_id),
    }
    if not reason and selected and selected['ctm_id'] != item['ctm_id']:
        rationale = (
            'Affectation historique formelle prioritaire sur le CTM du profil ; '
            'aucun mandat ni droit transféré.'
        )
    else:
        rationale = reason or 'Correspondance directe du CTM source ; aucun mandat ni droit transféré.'
    return {
        'expert': expert, 'sc': sc, 'source_affectation': current_affectation,
        'source_ctm_id': source_ctm_id, 'source_wg_id': source_wg_id,
        'structure_mapping': mapping if status == AffectationSousCommission.Status.MIGRATED else None,
        'group_mapping': group_mapping,
        'source_kind': source_kind, 'status': status,
        'is_primary': status == AffectationSousCommission.Status.MIGRATED,
        'migration_reference': decision_reference, 'batch_reference': batch,
        'source_database_sha256': source['sha256'],
        'effective_from': effective_date if status == AffectationSousCommission.Status.MIGRATED else None,
        'effective_to': None,
        'rationale': rationale,
        'source_snapshot': snapshot,
    }, reason


def _validate_applied_structure(version, decision_reference, actor, used_mapping_ids):
    """Valide les sept SC et les correspondances effectivement appliquées, sans activer le circuit."""
    sc_list = list(version.organes.select_for_update().filter(type=Organe.Type.SC))
    actual_codes = {sc.code for sc in sc_list}
    if actual_codes != EXPECTED_SC_CODES:
        raise ValidationError(
            'Le référentiel doit contenir exactement les sept sous-commissions attendues.'
        )
    for sc in sc_list:
        sc.status = OrganisationVersion.Status.VALIDATED
        sc.updated_by = actor
        sc.save()
    for mapping in CorrespondanceStructure.objects.select_for_update().filter(pk__in=used_mapping_ids):
        mapping.status = 'VALIDATED'
        mapping.decision_reference = decision_reference
        mapping.updated_by = actor
        mapping.save()
    version.status = OrganisationVersion.Status.VALIDATED
    version.updated_by = actor
    version.save()


@transaction.atomic
def migrate_legacy_experts(source_path, decision_reference, effective_date=None, actor=None, code='phoenix-2026-10'):
    """Crée des rattachements SC traçables sans créer mandat, habilitation ou GT."""
    decision_reference = str(decision_reference or '').strip()
    if not decision_reference:
        raise ValidationError('Une référence de migration est obligatoire.')
    effective_date = effective_date or timezone.localdate()
    if isinstance(effective_date, str):
        try:
            effective_date = date.fromisoformat(effective_date)
        except ValueError as error:
            raise ValidationError('La date de prise d’effet est invalide.') from error

    source = inspect_legacy_database(source_path)
    _assert_same_referential(source)
    version = OrganisationVersion.objects.filter(code=code).first()
    if version:
        preparation = version.journal.filter(operation='PREPARE_REFERENCE').first()
        missing_sources = preparation.after.get('missing_legacy_sources', []) if preparation else []
    else:
        version, missing_sources = seed_phoenix(code=code, actor=actor)
    version = OrganisationVersion.objects.select_for_update().get(pk=version.pk)
    if version.status not in ('PROPOSED', 'VALIDATED'):
        raise ValidationError('La migration des experts exige une organisation proposée ou validée.')
    batch = _batch_reference(source['sha256'], effective_date, decision_reference)
    previous = JournalMigration.objects.filter(
        version=version, operation='MIGRATE_EXPERTS', target=f'experts:{batch}',
    ).first()
    if previous:
        return version, previous.after
    if AffectationSousCommission.objects.select_for_update().filter(
        version=version, status='MIGRATED', is_primary=True,
    ).exclude(batch_reference=batch).exists():
        raise ValidationError('Une migration d’experts est déjà active ; la clôturer avant une nouvelle reprise.')

    current = {
        expert.pk: expert for expert in Expert.objects.select_related('user', 'ctm').filter(
            pk__in=[item['id'] for item in source['experts']]
        )
    }
    reconciliation_errors = []
    for item in source['experts']:
        expert = current.get(item['id'])
        if not expert:
            reconciliation_errors.append(f'expert source #{item["id"]} absent de la base cible')
        elif expert.user_id != item['user_id'] or expert.user.username != item['username']:
            reconciliation_errors.append(f'identité divergente pour l’expert source #{item["id"]}')
        elif (expert.ctm_id != item['ctm_id'] or expert.status != item['status']
              or expert.user.is_active != bool(item['user_is_active'])):
            reconciliation_errors.append(f'Profil divergent pour l’expert source #{item["id"]}')
    source_assignment_rows = {
        (row['id'], row['expert_id'], row['ctm_id'], row['wg_id'],
         bool(row['is_primary_ctm']), bool(row['is_primary_wg']))
        for row in source['assignments']
    }
    current_assignment_rows = {
        (row['id'], row['expert_id'], row['ctm_id'], row['wg_id'],
         row['is_primary_ctm'], row['is_primary_wg'])
        for row in Affectation.objects.values('id', 'expert_id', 'ctm_id', 'wg_id',
                                             'is_primary_ctm', 'is_primary_wg')
    }
    if current_assignment_rows != source_assignment_rows:
        reconciliation_errors.append('Les affectations historiques ont changé depuis la sauvegarde source.')
    if reconciliation_errors:
        raise ValidationError(reconciliation_errors[:20])

    source_assignments = defaultdict(list)
    for item in source['assignments']:
        source_assignments[item['expert_id']].append(item)

    counts = Counter()
    reasons = Counter()
    touched = []
    for item in source['experts']:
        expert = current[item['id']]
        desired, reason = _desired_assignment(
            version, source, item, expert, source_assignments.get(expert.pk, []),
            decision_reference, effective_date, batch,
        )
        source_key = f'{batch}:expert:{expert.pk}'
        assignment = AffectationSousCommission.objects.filter(version=version, source_key=source_key).first()
        if assignment:
            comparable = {key: value.pk if hasattr(value, 'pk') else value for key, value in desired.items() if key not in ('created_by', 'updated_by')}
            actual = {key: getattr(assignment, key + '_id') if hasattr(assignment, key + '_id') else getattr(assignment, key) for key in comparable}
            if actual != comparable:
                raise ValidationError(f'La reprise existante de l’expert #{expert.pk} diverge du lot demandé.')
        else:
            assignment = AffectationSousCommission.objects.create(
                version=version, source_key=source_key, created_by=actor, updated_by=actor, **desired,
            )
        touched.append(assignment.pk)
        if assignment.status == AffectationSousCommission.Status.MIGRATED:
            counts[assignment.sc.code] += 1
        else:
            counts['REVIEW'] += 1
            reasons[reason] += 1

    actual_sc_counts = {key: value for key, value in counts.items() if key != 'REVIEW'}
    used_mapping_ids = {
        assignment.structure_mapping_id
        for assignment in AffectationSousCommission.objects.filter(pk__in=touched, status='MIGRATED')
        if assignment.structure_mapping_id
    }
    status_before = version.status
    _validate_applied_structure(version, decision_reference, actor, used_mapping_ids)
    version.refresh_from_db()

    after = {
        'batch_reference': batch, 'source_path': source['path'], 'source_sha256': source['sha256'],
        'source_experts': len(source['experts']), 'source_affectations': len(source['assignments']),
        'migrated': sum(actual_sc_counts.values()),
        'review': counts['REVIEW'], 'by_sc': actual_sc_counts,
        'review_reasons': dict(reasons), 'assignment_ids': touched,
        'legacy_sources_missing_from_reference': missing_sources,
        'sc_status': 'VALIDATED', 'organisation_status': version.status,
        'validated_sc_codes': sorted(EXPECTED_SC_CODES),
        'validated_mapping_ids': sorted(used_mapping_ids),
        'rights_created': 0, 'mandates_created': 0, 'legacy_rows_modified': 0,
    }
    JournalMigration.objects.create(
        version=version, actor=actor,
        actor_name=(actor.get_full_name() or actor.username) if actor else 'Migration contrôlée',
        operation='MIGRATE_EXPERTS', target=f'experts:{batch}',
        before={'version_status': status_before},
        after=after, reason=decision_reference,
    )
    return version, after


@transaction.atomic
def rollback_expert_migration(batch_reference, reason, actor=None, code='phoenix-2026-10', effective_date=None):
    """Clôture un lot sans supprimer son historique ni restaurer l'ancien circuit."""
    reason = str(reason or '').strip()
    if not reason:
        raise ValidationError('Le motif de clôture du lot est obligatoire.')
    version = OrganisationVersion.objects.select_for_update().get(code=code)
    assignments = list(AffectationSousCommission.objects.select_for_update().filter(
        version=version, batch_reference=batch_reference,
    ))
    if not assignments:
        raise ValidationError('Lot de migration introuvable.')
    existing = JournalMigration.objects.filter(
        version=version, operation='ROLLBACK_EXPERTS', target=f'experts:{batch_reference}',
    ).first()
    if existing:
        return existing.after
    ended_on = effective_date or timezone.localdate()
    if isinstance(ended_on, str):
        try:
            ended_on = date.fromisoformat(ended_on)
        except ValueError as error:
            raise ValidationError('La date de clôture est invalide.') from error
    for assignment in assignments:
        if assignment.status == AffectationSousCommission.Status.MIGRATED:
            assignment.status = AffectationSousCommission.Status.ENDED
            assignment.effective_to = max(assignment.effective_from, ended_on - timedelta(days=1))
        elif assignment.status == AffectationSousCommission.Status.REVIEW:
            assignment.status = AffectationSousCommission.Status.CANCELLED
        assignment.updated_by = actor
        assignment.save()
    after = {'batch_reference': batch_reference, 'closed': len(assignments), 'effective_date': ended_on.isoformat()}
    JournalMigration.objects.create(
        version=version, actor=actor,
        actor_name=(actor.get_full_name() or actor.username) if actor else 'Migration contrôlée',
        operation='ROLLBACK_EXPERTS', target=f'experts:{batch_reference}',
        before={'active': len(assignments)}, after=after, reason=reason,
    )
    return after
