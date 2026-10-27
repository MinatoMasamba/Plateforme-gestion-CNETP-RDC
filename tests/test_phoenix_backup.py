import hashlib
import json
import sqlite3
from types import SimpleNamespace

from apps.governance.phoenix_backup import prepare_backup


def test_backup_restores_private_phoenix_documents(monkeypatch, tmp_path):
    database = tmp_path / 'source.sqlite3'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE core_user (id INTEGER PRIMARY KEY, password TEXT, last_login TEXT, updated_at TEXT)')
        connection.execute("INSERT INTO core_user VALUES (1, 'empreinte-de-recette', NULL, NULL)")
    monkeypatch.setattr(
        'apps.governance.phoenix_backup.settings',
        SimpleNamespace(
            BASE_DIR=tmp_path,
            MEDIA_ROOT=tmp_path / 'media',
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': str(database),
                },
            },
        ),
    )
    private = tmp_path / '.phoenix_documents'
    private.mkdir()
    (private / 'pv.txt').write_bytes(b'Proces-verbal de recette')
    destination = prepare_backup()
    manifest = json.loads((destination / 'manifest.json').read_text())
    assert manifest['restore_verified']
    assert manifest['private_documents']['pv.txt'] == hashlib.sha256(b'Proces-verbal de recette').hexdigest()
    assert (destination / 'restore-check' / 'private_documents' / 'pv.txt').read_bytes() == b'Proces-verbal de recette'
