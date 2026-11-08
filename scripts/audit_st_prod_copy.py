"""Teste les migrations et le backend ST sur une copie isolée d'un export SQLite."""
import argparse
from collections import Counter
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import traceback


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def snapshot(path):
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        result = {}
        for table in tables:
            columns = [r[1] for r in db.execute('PRAGMA table_info(' + quote(table) + ')')]
            result[table] = {'columns': columns, 'rows': db.execute('SELECT ' + ','.join(map(quote, columns)) + ' FROM ' + quote(table)).fetchall()}
        return result


def row_counts(rows, indices):
    def encode(row):
        values = [row[i].hex() if isinstance(row[i], bytes) else row[i] for i in indices]
        return hashlib.sha256(json.dumps(values, ensure_ascii=False, default=str).encode()).hexdigest()
    return Counter(encode(row) for row in rows)


def compare(before, after, ignore=None):
    ignore = ignore or {}
    failures = []
    for table, data in before.items():
        if table not in after:
            failures.append({'table': table, 'reason': 'table disparue'})
            continue
        columns = [c for c in data['columns'] if c not in ignore.get(table, ())]
        if not set(columns) <= set(after[table]['columns']):
            failures.append({'table': table, 'reason': 'colonnes disparues'})
            continue
        old = row_counts(data['rows'], [data['columns'].index(c) for c in columns])
        new = row_counts(after[table]['rows'], [after[table]['columns'].index(c) for c in columns])
        missing = sum((old - new).values())
        if missing:
            failures.append({'table': table, 'original_rows_changed_or_missing': missing})
    return {'original_tables_checked': len(before), 'failures': failures, 'preserved': not failures}


def integrity(path):
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
        return {'integrity_check': [r[0] for r in db.execute('PRAGMA integrity_check')],
                'foreign_key_violations': len(db.execute('PRAGMA foreign_key_check').fetchall())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--report-dir', required=True)
    parser.add_argument('--in-place', action='store_true', help='Appliquer migrations et bascule directement à la base fournie, sans nouvelle copie.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = Path(args.source).resolve(strict=True)
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(report_dir, 0o700)
    report = {'in_place': args.in_place, 'source': str(source), 'started_at': datetime.now(dt_timezone.utc).isoformat(), 'passed': False}
    original_hash = digest(source)
    report['source_sha256_before'] = original_hash
    workspace = Path(tempfile.mkdtemp(prefix='st-prod-audit-'))
    report['isolated_workspace'] = str(workspace)
    frozen = workspace / 'source_snapshot.sqlite3'
    working = source if args.in_place else workspace / 'working.sqlite3'
    try:
        if not args.in_place:
            wal = Path(str(source) + '-wal')
            if wal.exists() and wal.stat().st_size:
                raise RuntimeError('Un WAL non vide accompagne la source : fournir un export SQLite cohérent avant de poursuivre.')
            shutil.copyfile(source, frozen)
            assert digest(frozen) == original_hash == digest(source), 'La source a changé pendant la copie.'
            shutil.copyfile(frozen, working)
            os.chmod(frozen, 0o600)
            os.chmod(working, 0o600)
        baseline = snapshot(working)
        report['source_table_counts'] = {name: len(data['rows']) for name, data in baseline.items()}
        report['initial_integrity'] = integrity(working)
        assert report['initial_integrity'] == {'integrity_check': ['ok'], 'foreign_key_violations': 0}, 'La base fournie présente déjà des anomalies d’intégrité.'

        os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_test'
        os.environ['SQLITE_NAME'] = str(working)
        os.environ['DB_ENGINE'] = 'sqlite'
        sys.path.insert(0, str(root))
        from django.conf import settings
        settings.MEDIA_ROOT = str(workspace / 'media')
        settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
        import django
        django.setup()
        from django.core.management import call_command
        from django.db import connection, transaction
        from django.db.migrations.executor import MigrationExecutor
        from django.test import Client
        from django.utils import timezone
        from types import SimpleNamespace
        from django.core.exceptions import PermissionDenied, ValidationError
        from django.db.models import Sum
        from apps.core.models import User
        from apps.experts.models import Expert, Structure
        from apps.governance.models import CTCMembership, MandatOrganisation, PlatformFreeze
        from apps.governance.phoenix_runtime import current_organisation_version, current_st_version, st_posts, active_st_mandate
        from apps.governance.st_operations import reset_legacy_access, write_record, confirm_record
        from apps.governance.st_operations_models import STRecord, STRecordRevision
        from apps.ia_agent.tools.st_tools import list_st_posts, assign_st_posts
        from apps.payments.models import Paiement
        from web.ctc_views import get_ctc_context

        assert Path(connection.settings_dict['NAME']).resolve() == working
        assert args.in_place or working != source
        assert settings.EMAIL_BACKEND == 'django.core.mail.backends.locmem.EmailBackend'
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        report['migration_plan'] = [f'{migration.app_label}.{migration.name}' for migration, _ in plan]
        output = io.StringIO()
        call_command('migrate', interactive=False, verbosity=1, stdout=output)
        (report_dir / 'migrations.log').write_text(output.getvalue())
        executor = MigrationExecutor(connection)
        assert not executor.migration_plan(executor.loader.graph.leaf_nodes()), 'Migrations encore en attente.'
        report['preservation_after_migrations'] = compare(baseline, snapshot(working))
        assert report['preservation_after_migrations']['preserved'], 'Des données existantes ont changé pendant les migrations.'
        report['integrity_after_migrations'] = integrity(working)
        assert report['integrity_after_migrations'] == report['initial_integrity']
        call_command('check', stdout=io.StringIO())
        model_output = io.StringIO()
        try:
            call_command('makemigrations', check=True, dry_run=True, stdout=model_output)
            report['model_migration_drift'] = False
        except SystemExit as exc:
            report['model_migration_drift'] = bool(exc.code)
        (report_dir / 'model-check.log').write_text(model_output.getvalue())

        old_experts = list(Expert.objects.filter(ctcmembership__is_active=True).distinct())
        previous_version = current_organisation_version()
        migrated = snapshot(working)
        report['reset_result'] = reset_legacy_access(None)
        reset_snapshot = snapshot(working)
        report['preservation_after_reset'] = compare(migrated, reset_snapshot,
            {'core_user': ['is_ctc_staff'], 'governance_ctcmembership': ['is_active']})
        assert report['preservation_after_reset']['preserved'], 'La bascule a modifié des données autres que les droits prévus.'
        assert current_organisation_version() == previous_version, 'La version globale Phoenix a changé.'
        assert st_posts().count() == 19
        assert CTCMembership.objects.count() == 0
        assert not User.objects.filter(is_ctc_staff=True).exists()
        assert not MandatOrganisation.objects.filter(poste__organe__version=current_st_version(), status='ACTIVE').exists()
        assert all(get_ctc_context(expert) is None for expert in old_experts)
        report['old_ctc_accounts_checked'] = len(old_experts)
        report['vacant_posts'] = 19
        report['reset_idempotent'] = reset_legacy_access(None).get('already_configured') is True
        assert report['reset_idempotent']

        checks = []
        # Les données de ces essais sont annulées, y compris les sessions de test.
        with transaction.atomic():
            freeze = PlatformFreeze.get_solo()
            report['source_platform_locked'] = freeze.is_locked
            if freeze.is_locked:
                freeze.is_locked = False
                freeze.save(update_fields=['is_locked'])
            admin = User.objects.create_user(username='__st_prod_audit_admin', is_staff=True, is_superuser=True)
            structure = Structure.objects.create(name='__ST_PROD_AUDIT_STRUCTURE', acronym='AUDIT-ST', category='ADMIN')
            actors = {}
            assignments = []
            for number in (10, 12, 14, 15):
                user = User.objects.create_user(username=f'__st_prod_audit_{number}', email=f'st-audit-{number}@example.invalid')
                expert = Expert.objects.create(user=user, structure=structure, status='ACTIVE')
                actors[number] = (user, expert)
                assignments.append({'post_code': f'ST-V3-{number:02}', 'expert_id': expert.pk,
                    'start_date': timezone.localdate().isoformat(), 'appointment_reference': 'ESSAI ISOLÉ — SANS VALEUR OFFICIELLE'})
            session = SimpleNamespace(user=admin)
            assert len(list_st_posts(session)) == 19
            assert all(not r['applied'] for r in assign_st_posts(session, assignments, apply=False)['results'])
            assert not MandatOrganisation.objects.filter(poste__organe__version=current_st_version(), status='ACTIVE').exists()
            assert all(r['applied'] for r in assign_st_posts(session, assignments, apply=True)['results'])
            assert all(active_st_mandate(expert) for _, expert in actors.values())
            checks.append('Nominations Neuronne : simulation puis activation explicite sur comptes synthétiques')
            try:
                assign_st_posts(SimpleNamespace(user=actors[12][0]), assignments, apply=True)
                raise AssertionError('Une nomination non administrateur a été acceptée.')
            except PermissionDenied:
                checks.append('Refus des nominations par un non-administrateur')

            client = Client()
            client.force_login(admin)
            assert client.get('/admin/governance/nominationctc/add/').status_code == 200
            assert client.get('/admin/governance/ctcmembership/').status_code == 200
            assert client.get('/admin/governance/ctcmembership/add/').status_code == 403
            assert client.get('/admin/governance/postenominatifctc/add/').status_code == 403
            checks.append('Admin : nouveaux postes accessibles, historique consultable et anciennes attributions interdites')
            for expert in old_experts:
                if expert.user.is_active:
                    client.force_login(expert.user)
                    assert client.get('/api/v1/mobile/ctc/dashboard/').status_code == 403
            checks.append('Refus API des anciens comptes CTC actifs dans la sauvegarde')

            client.force_login(actors[12][0])
            response = client.post('/api/v1/st/records/', {'kind': 'PTN', 'reference': '__AUDIT_PTN',
                'title': 'PTN de contrôle', 'content': 'Essai isolé', 'source_reference': 'Audit de migration'}, content_type='application/json')
            assert response.status_code == 201, f'Création PTN : HTTP {response.status_code}'
            record_id = response.json()['id']
            url = f'/api/v1/st/records/{record_id}/'
            decision = {'revision': 1, 'decision': 'CONFIRMED', 'comment': 'Essai isolé'}
            assert client.post(url + 'confirm/', decision, content_type='application/json').status_code == 403
            client.force_login(actors[10][0])
            assert client.post(url + 'confirm/', decision, content_type='application/json').status_code == 200
            assert client.post(url + 'confirm/', decision, content_type='application/json').status_code == 409
            assert client.get('/api/v1/st/records/ptn-register/').json()['confirmed_count'] == 1
            client.force_login(actors[12][0])
            data = {'revision': 1, 'title': 'PTN révisé', 'content': 'Version 2', 'source_reference': 'Audit de migration'}
            assert client.post(url + 'revise/', data, content_type='application/json').status_code == 200
            assert client.post(url + 'revise/', data, content_type='application/json').status_code == 409
            assert STRecordRevision.objects.filter(record_id=record_id).count() == 2
            checks.append('PTN : versions conservées, confirmation par le chef, refus des doublons et révisions obsolètes')

            record = write_record(actors[15][0], {'kind': 'FINANCE', 'reference': '__AUDIT_FINANCE',
                'title': 'Essai financier isolé', 'source_reference': 'Audit de migration',
                'amount': '125.50', 'currency': 'USD', 'movement': 'DEPENSE',
                'operation_date': timezone.localdate().isoformat()})
            try:
                confirm_record(actors[15][0], record.pk, 1, 'CONFIRMED', 'Essai')
                raise AssertionError('Un membre financier a confirmé son état sans être chef.')
            except PermissionDenied:
                pass
            confirm_record(actors[14][0], record.pk, 1, 'CONFIRMED', 'Essai isolé')
            client.force_login(actors[14][0])
            summary = client.get('/api/v1/st/records/finance-summary/')
            assert summary.status_code == 200
            assert summary.json()['ledger'] == [{'currency': 'USD', 'movement': 'DEPENSE', 'amount': '125.50'}]
            expected = Paiement.objects.filter(status='CONFIRMED').aggregate(value=Sum('montant'))['value'] or Decimal('0')
            assert Decimal(summary.json()['legacy']['cotisations_confirmed']) == expected
            checks.append('Finances : montants persistés, devises séparées, confirmation par le co-chef et totaux historiques exacts')
            client.force_login(actors[15][0])
            assert client.post('/api/v1/jetons/999999/mark_as_paid/').status_code == 403
            checks.append('Refus de paiement définitif par un membre financier sans fonction de chef')
            transaction.set_rollback(True)
        report['functional_checks'] = checks
        final_snapshot = snapshot(working)
        report['fixture_rollback_verified'] = all(
            row_counts(data['rows'], range(len(data['columns']))) == row_counts(final_snapshot[table]['rows'], range(len(data['columns'])))
            for table, data in reset_snapshot.items()
        )
        assert report['fixture_rollback_verified'], 'Les données de contrôle n’ont pas toutes été annulées.'
        report['final_integrity'] = integrity(working)
        assert report['final_integrity'] == report['initial_integrity']
        report['final_active_st_mandates'] = MandatOrganisation.objects.filter(poste__organe__version=current_st_version(), status='ACTIVE').count()
        assert report['final_active_st_mandates'] == 0
        connection.close()
        if not args.in_place:
            restored = workspace / 'restore_check.sqlite3'
            shutil.copyfile(frozen, restored)
            os.chmod(restored, 0o600)
            report['restore_verified'] = digest(restored) == original_hash and integrity(restored) == report['initial_integrity']
            assert report['restore_verified']
        else:
            report['restore_verified'] = None
            report['restore_note'] = 'Aucune nouvelle copie ni restauration, conformément à la demande utilisateur.'
        report['passed'] = not report['model_migration_drift']
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
        (report_dir / 'failure.log').write_text(traceback.format_exc())
    finally:
        report['source_sha256_after'] = digest(source)
        report['source_unchanged'] = None if args.in_place else report['source_sha256_after'] == original_hash
        if not args.in_place:
            report['passed'] = report['passed'] and report['source_unchanged']
        report['finished_at'] = datetime.now(dt_timezone.utc).isoformat()
        target = report_dir / 'report.json'
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
        for entry in report_dir.iterdir():
            if entry.is_file():
                os.chmod(entry, 0o600)
        print(json.dumps({key: report[key] for key in ('passed', 'source_unchanged', 'error', 'model_migration_drift', 'old_ctc_accounts_checked', 'final_active_st_mandates') if key in report}, ensure_ascii=False))
        print('Rapport :', target)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
