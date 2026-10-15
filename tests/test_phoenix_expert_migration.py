import sqlite3

import pytest
from django.core.exceptions import ValidationError

from apps.governance.models import (
    Affectation, AffectationSousCommission, CorrespondanceStructure,
    CTM, HabilitationAction, JournalMigration, MandatOrganisation, Organe, WG,
)
from apps.governance.phoenix_expert_migration import (
    migrate_legacy_experts, rollback_expert_migration,
)


def write_legacy_database(path, experts, assignments, ctms, groups):
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        PRAGMA foreign_keys=ON;
        CREATE TABLE core_user (id INTEGER PRIMARY KEY, username TEXT NOT NULL, is_active INTEGER NOT NULL);
        CREATE TABLE experts_expert (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, status TEXT NOT NULL, ctm_id INTEGER);
        CREATE TABLE governance_ctm (id INTEGER PRIMARY KEY, number INTEGER NOT NULL);
        CREATE TABLE governance_wg (id INTEGER PRIMARY KEY, ctm_id INTEGER NOT NULL, number INTEGER NOT NULL);
        CREATE TABLE governance_affectation (
            id INTEGER PRIMARY KEY, expert_id INTEGER NOT NULL, ctm_id INTEGER NOT NULL,
            wg_id INTEGER, is_primary_ctm INTEGER NOT NULL, is_primary_wg INTEGER NOT NULL
        );
        """
    )
    connection.executemany('INSERT INTO core_user VALUES (?,?,?)', [
        (expert.user_id, expert.user.username, int(expert.user.is_active)) for expert in experts
    ])
    connection.executemany('INSERT INTO experts_expert VALUES (?,?,?,?)', [
        (expert.pk, expert.user_id, expert.status, expert.ctm_id) for expert in experts
    ])
    connection.executemany('INSERT INTO governance_ctm VALUES (?,?)', [
        (ctm.pk, ctm.number) for ctm in ctms
    ])
    connection.executemany('INSERT INTO governance_wg VALUES (?,?,?)', [
        (group.pk, group.ctm_id, group.number) for group in groups
    ])
    connection.executemany('INSERT INTO governance_affectation VALUES (?,?,?,?,?,?)', [
        (assignment.pk, assignment.expert_id, assignment.ctm_id, assignment.wg_id,
         int(assignment.is_primary_ctm), int(assignment.is_primary_wg))
        for assignment in assignments
    ])
    connection.commit()
    connection.close()


@pytest.fixture
def legacy_source(tmp_path, ctm_factory, wg_factory, expert_factory, user_factory):
    ctms = [ctm_factory(number=number) for number in range(1, 9)]
    groups = [wg_factory(ctm=ctm, number=number) for ctm in ctms for number in range(1, 4)]
    formal_user = user_factory(username='formal', first_name='Eddie', last_name='Masamba')
    formal = expert_factory(user=formal_user, ctm=ctms[2])
    profile = expert_factory(user=user_factory(username='profile'), ctm=ctms[2])
    ambiguous = expert_factory(user=user_factory(username='ambiguous'), ctm=ctms[1])
    without_ctm = expert_factory(user=user_factory(username='without-ctm'))
    pending = expert_factory(user=user_factory(username='pending'), ctm=ctms[0])
    pending.status = 'PENDING'
    pending.save(update_fields=['status'])
    assignment = Affectation.objects.create(expert=formal, ctm=ctms[0], wg=groups[0])
    path = tmp_path / 'legacy.sqlite3'
    experts = [formal, profile, ambiguous, without_ctm, pending]
    write_legacy_database(path, experts, [assignment], ctms, groups)
    return path, experts, assignment


@pytest.mark.django_db
def test_experts_are_mapped_with_names_and_provenance_without_rights(legacy_source, client):
    path, experts, old_assignment = legacy_source
    before_ctm = list(CTM.objects.order_by('pk').values())
    before_wg = list(WG.objects.order_by('pk').values())
    before_assignment = list(Affectation.objects.order_by('pk').values())

    version, report = migrate_legacy_experts(
        path, 'Instruction de migration de recette', effective_date='2026-10-13',
    )

    assert report['migrated'] == 2 and report['review'] == 3
    assert report['by_sc'] == {'SC-GF': 1, 'SC-BAT': 1}
    assert version.status == 'VALIDATED'
    assert version.organes.filter(type='SC', status='VALIDATED').count() == 7
    assignments = AffectationSousCommission.objects.select_related('expert__user', 'source_ctm')
    assert assignments.count() == 5
    formal = assignments.get(expert=experts[0])
    assert formal.sc.code == 'SC-GF' and formal.source_affectation_id == old_assignment.pk
    assert formal.source_kind == 'AFFECTATION_WG' and formal.source_snapshot['source_ctm_number'] == 1
    assert formal.source_snapshot['profile_ctm_id'] == experts[0].ctm_id
    assert 'prioritaire' in formal.rationale
    profile = assignments.get(expert=experts[1])
    assert profile.sc.code == 'SC-BAT' and profile.source_kind == 'PROFILE_CTM'
    assert assignments.get(expert=experts[2]).status == 'REVIEW'
    assert assignments.get(expert=experts[3]).source_kind == 'NO_SOURCE'
    assert assignments.get(expert=experts[4]).rationale == 'Profil ou compte source non actif.'
    assert not MandatOrganisation.objects.exists() and not HabilitationAction.objects.exists()
    assert list(CTM.objects.order_by('pk').values()) == before_ctm
    assert list(WG.objects.order_by('pk').values()) == before_wg
    assert list(Affectation.objects.order_by('pk').values()) == before_assignment
    assert CorrespondanceStructure.objects.get(version=version, ctm__number=1, nature='PRIMARY').status == 'VALIDATED'
    assert CorrespondanceStructure.objects.get(version=version, ctm__number=2, nature='PRIMARY').status == 'PROPOSED'

    experts[0].user.is_superuser = True
    experts[0].user.is_staff = True
    experts[0].user.save(update_fields=['is_superuser', 'is_staff'])
    client.force_login(experts[0].user)
    response = client.get('/pilotage/organisation/')
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Eddie Masamba' in content
    assert 'SC-GF' in content
    assert 'CTM 1' not in content
    assert 'WG 1' not in content


@pytest.mark.django_db
def test_migration_is_idempotent_and_new_batch_requires_rollback(legacy_source):
    path, _, _ = legacy_source
    _, first = migrate_legacy_experts(path, 'Instruction stable', effective_date='2026-10-13')
    _, second = migrate_legacy_experts(path, 'Instruction stable', effective_date='2026-10-13')
    assert first == second
    assert AffectationSousCommission.objects.count() == 5
    assert JournalMigration.objects.filter(operation='MIGRATE_EXPERTS').count() == 1
    with pytest.raises(ValidationError, match='déjà active'):
        migrate_legacy_experts(path, 'Instruction différente', effective_date='2026-10-14')

    report = rollback_expert_migration(first['batch_reference'], 'Clôture de recette', effective_date='2026-10-14')
    assert report['closed'] == 5
    assert AffectationSousCommission.objects.filter(status='ENDED').count() == 2
    assert AffectationSousCommission.objects.filter(status='CANCELLED').count() == 3
    assert rollback_expert_migration(first['batch_reference'], 'Clôture de recette')['closed'] == 5
    _, replacement = migrate_legacy_experts(path, 'Instruction différente', effective_date='2026-10-14')
    assert replacement['migrated'] == 2
    assert AffectationSousCommission.objects.count() == 10


@pytest.mark.django_db
def test_empty_requested_backup_is_rejected(tmp_path):
    path = tmp_path / 'empty.sqlite3'
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE core_user (id INTEGER PRIMARY KEY, username TEXT, is_active INTEGER);
        CREATE TABLE experts_expert (id INTEGER PRIMARY KEY, user_id INTEGER, status TEXT, ctm_id INTEGER);
        CREATE TABLE governance_ctm (id INTEGER PRIMARY KEY, number INTEGER);
        CREATE TABLE governance_wg (id INTEGER PRIMARY KEY, ctm_id INTEGER, number INTEGER);
        CREATE TABLE governance_affectation (id INTEGER PRIMARY KEY, expert_id INTEGER, ctm_id INTEGER, wg_id INTEGER, is_primary_ctm INTEGER, is_primary_wg INTEGER);
        """
    )
    connection.close()
    with pytest.raises(ValidationError, match='aucun expert'):
        migrate_legacy_experts(path, 'Instruction de recette')
