"""Sauvegarde locale cohérente et preuve de restauration avant ajouts Phoenix."""
import hashlib
import json
import sqlite3
import tarfile
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings

PRESERVED_TABLES = (
    'core_user', 'experts_expert', 'experts_structure', 'governance_ctm',
    'governance_wg', 'governance_affectation', 'governance_comitepilotage',
    'governance_pilotagemembreship', 'governance_postenominatif',
    'governance_technicalcell', 'governance_ctcmembership', 'governance_postenominatifctc',
    'norms_norme', 'norms_normeversion', 'norms_changementversion', 'documents_documentfile',
)


def legacy_manifest(connection):
    manifest = {}
    for table in PRESERVED_TABLES:
        columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]
        if not columns:
            continue
        if table == 'core_user':
            columns = [name for name in columns if name not in ('last_login', 'updated_at')]
        if table == 'norms_norme':
            # Compare les colonnes historiques ; le nouvel identifiant de circuit est ajouté avec sa valeur LEGACY.
            columns = [name for name in columns if name != 'circuit_version']
        projection = ','.join('"' + name + '"' for name in columns)
        rows = connection.execute(f'SELECT {projection} FROM "{table}" ORDER BY id').fetchall()
        payload = json.dumps(rows, default=str, ensure_ascii=False).encode()
        id_index = columns.index('id')
        manifest[table] = {'count': len(rows), 'ids': [row[id_index] for row in rows],
                           'sha256': hashlib.sha256(payload).hexdigest()}
    return manifest


def prepare_backup():
    database = settings.DATABASES['default']
    if database['ENGINE'] != 'django.db.backends.sqlite3':
        raise ValueError('Cette sauvegarde locale est destinée à SQLite ; préparer un export PostgreSQL cohérent pour cet environnement.')
    source = Path(database['NAME']).resolve()
    destination = Path(settings.BASE_DIR) / '.local_backups' / ('phoenix-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    destination.mkdir(parents=True, mode=0o700)
    backup = destination / 'database.sqlite3'
    with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as original:
        with sqlite3.connect(backup) as copy:
            original.backup(copy)
            manifest = legacy_manifest(copy)
    backup.chmod(0o600)
    media = Path(settings.MEDIA_ROOT)
    private = Path(settings.BASE_DIR) / '.phoenix_documents'
    hashes = {str(path.relative_to(media)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in media.rglob('*') if path.is_file()} if media.exists() else {}
    archive = destination / 'media.tar.gz'
    private_hashes = {str(path.relative_to(private)): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in private.rglob('*') if path.is_file()} if private.exists() else {}
    with tarfile.open(archive, 'w:gz') as tar:
        if media.exists():
            tar.add(media, arcname='media')
        if private.exists():
            tar.add(private, arcname='private_documents')
    archive.chmod(0o600)
    restored_database = destination / 'restore-check.sqlite3'
    with sqlite3.connect(backup) as saved, sqlite3.connect(restored_database) as restored:
        saved.backup(restored)
        assert restored.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not restored.execute('PRAGMA foreign_key_check').fetchall()
        assert legacy_manifest(restored) == manifest
    restored_database.chmod(0o600)
    restored_media = destination / 'restore-check'
    with tarfile.open(archive, 'r:gz') as tar:
        tar.extractall(restored_media, filter='data')
    for name, digest in hashes.items():
        assert hashlib.sha256((restored_media / 'media' / name).read_bytes()).hexdigest() == digest
    for name, digest in private_hashes.items():
        assert hashlib.sha256((restored_media / 'private_documents' / name).read_bytes()).hexdigest() == digest
    report = {'database': str(source), 'backup': str(backup), 'legacy': manifest,
              'media': hashes, 'private_documents': private_hashes, 'restore_verified': True,
              'user_fields_excluded': ['last_login', 'updated_at']}
    report_path = destination / 'manifest.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    report_path.chmod(0o600)
    return destination
