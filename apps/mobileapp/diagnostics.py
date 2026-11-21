"""Journal privé, borné et expurgé des incidents transmis par Flutter."""
import json
import os
import re
import fcntl
from pathlib import Path

from django.conf import settings


def redact(value):
    text = str(value)
    text = re.sub(r'https?://[^\s<>]+', '[URL masquée]', text)
    text = re.sub(r'(?i)(authorization|password|passwd|token|secret|api[_-]?key)\s*[:=]\s*\S+', r'\1=[masqué]', text)
    text = re.sub(r'(?i)bearer\s+\S+', 'Bearer [masqué]', text)
    text = re.sub(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[jeton masqué]', text)
    return re.sub(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}', '[courriel masqué]', text)


def write_diagnostic(incident):
    root = Path(getattr(settings, 'CLIENT_DIAGNOSTICS_DIR', settings.BASE_DIR / '.client_diagnostics'))
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = root / 'flutter_errors.txt'
    payload = {'id': str(incident.pk), 'server_time': incident.created_at.isoformat(),
               'user_id': incident.user_id, 'category': incident.category,
               'version': incident.app_version, 'platform': incident.platform,
               'message': incident.message, **incident.details}
    line = json.dumps(payload, ensure_ascii=False) + '\n'
    # Verrou interprocessus : rotation et écriture restent cohérentes avec
    # plusieurs workers Django Linux. 5 fichiers de 5 Mo maximum environ.
    lock_fd = os.open(root / '.journal.lock', os.O_WRONLY | os.O_CREAT, 0o600)
    with os.fdopen(lock_fd, 'w') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if path.exists() and path.stat().st_size >= 5 * 1024 * 1024:
            for number in range(4, 0, -1):
                source = path if number == 1 else root / f'flutter_errors.{number - 1}.txt'
                target = root / f'flutter_errors.{number}.txt'
                if source.exists():
                    source.replace(target)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, 'a', encoding='utf-8') as stream:
            stream.write(line)
