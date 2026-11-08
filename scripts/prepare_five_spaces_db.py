"""Prépare une copie de la base avec les 19 mandats ST v3 pour les captures UI.

La base source n'est jamais modifiée. Usage :
    mon_env/bin/python scripts/prepare_five_spaces_db.py \
        --source db.sqlite3 --dest /tmp/five_spaces.sqlite3 \
        --manifest reports/5_espaces/roles.json
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))


def copy_database(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    src = sqlite3.connect(str(source))
    dst = sqlite3.connect(str(dest))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default=str(BASE_DIR / 'db.sqlite3'))
    parser.add_argument('--dest', default='/tmp/five_spaces.sqlite3')
    parser.add_argument('--manifest', default=str(BASE_DIR / 'reports' / '5_espaces' / 'roles.json'))
    args = parser.parse_args()

    copy_database(Path(args.source), Path(args.dest))
    os.environ['SQLITE_NAME'] = args.dest
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    import django
    from django.conf import settings
    # Les mandats déclenchent des signaux de notification : aucune sortie réseau
    # n'est autorisée pour des comptes de capture.
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    settings.NOTIFICATION_SETTINGS = {'EMAIL_ENABLED': False, 'FCM_ENABLED': False}
    settings.TWILIO_ACCOUNT_SID = ''
    settings.CELERY_TASK_ALWAYS_EAGER = True
    django.setup()

    from django.utils import timezone
    from apps.core.models import User
    from apps.experts.models import Expert, Structure
    from apps.governance.models import MandatOrganisation, PosteOrganisation
    from apps.governance.st_matrix import POSTS, prepare_matrix
    from apps.governance.st_operations_models import STAccessPolicy

    version = prepare_matrix()
    version.status = 'VALIDATED'
    version.save(update_fields=['status'])
    STAccessPolicy.objects.update_or_create(pk=1, defaults={'version': version, 'enabled': True})

    structure = Structure.objects.order_by('id').first()
    if structure is None:
        structure = Structure.objects.create(name='Secrétariat technique', acronym='ST', category='ADMIN')

    roles = {}
    for number, pole, title, sub_role, nominated_name, origin, head in POSTS:
        username = f'capture.st.{number:02d}'
        first, _, last = (nominated_name or f'Poste {number}').partition(' ')
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@cnetp.local', 'first_name': first, 'last_name': last},
        )
        user.email = user.email or f'{username}@cnetp.local'
        user.first_name = user.first_name or first
        user.last_name = user.last_name or last
        user.is_active = True
        user.is_expert = True
        user.set_unusable_password()
        user.save()
        expert, _ = Expert.objects.get_or_create(
            user=user,
            defaults={'structure': structure, 'status': 'ACTIVE'},
        )
        expert.status = 'ACTIVE'
        expert.structure = expert.structure or structure
        expert.save(update_fields=['status', 'structure'])
        post = PosteOrganisation.objects.get(code=f'ST-V3-{number:02}')
        MandatOrganisation.objects.filter(
            poste=post, capacity='ORGANISATION', status='ACTIVE',
        ).update(status='ENDED')
        MandatOrganisation.objects.get_or_create(
            expert=expert, poste=post, capacity='ORGANISATION',
            defaults={
                'function': title,
                'appointment_reference': 'Communiqué 003 — captures internes',
                'start_date': timezone.localdate(),
                'status': 'ACTIVE',
            },
        )
        roles[post.code] = {
            'post_code': post.code,
            'number': number,
            'pole': pole,
            'title': title,
            'head': head,
            'name': expert.full_name,
            'email': user.email,
        }

    manifest = Path(args.manifest)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(roles, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(roles)} mandats ST v3 prêts dans {args.dest}')
    print(f'Manifeste : {manifest}')


if __name__ == '__main__':
    main()
