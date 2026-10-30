"""Prepare an anonymised copy of the database for CTC screenshots.

The working database is never modified: this script copies it with the SQLite
backup API, then ensures one representative expert per CTC sub-role and replaces
the identity of every CTC member with a role-based display name.

Usage:
    mon_env/bin/python scripts/prepare_ctc_capture_db.py \
        --source db.sqlite3 --dest /tmp/ctc_capture.sqlite3 \
        --manifest captures_ctc/roles.json
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

# 19 sub-roles derived by web/ctc_views.py, in pole order.
ROLE_SPECS = [
    ('coordonnateur_principal', 'COORDINATOR', None, 'Direction des Opérations'),
    ('coordonnateur_adjoint', 'VICE_COORDINATOR', 'Cabinet du Ministre des ITP', 'Direction des Opérations'),
    ('assistant_executif', 'EXECUTIVE', None, 'Direction des Opérations'),
    ('veille_acgt', 'ISO_EXPERT', 'ACGT', "Pôle d'Analyse et d'Ingénierie Documentaire"),
    ('veille_sg', 'ISO_EXPERT', None, "Pôle d'Analyse et d'Ingénierie Documentaire"),
    ('expert_juridique', 'LEGAL', 'EJS', "Pôle d'Analyse et d'Ingénierie Documentaire"),
    ('sauvegardes_ci', 'ENVIRONMENTAL', 'CI', "Pôle d'Analyse et d'Ingénierie Documentaire"),
    ('planification_recons', 'PLANNER', None, "Pôle d'Analyse et d'Ingénierie Documentaire"),
    ('economiste_foner', 'ECONOMIST', 'FONER', "Pôle d'Analyse et d'Ingénierie Documentaire"),
    ('scientifique_inbtp', 'SCIENTIFIC', None, "Pôle d'Analyse et d'Ingénierie Documentaire"),
    ('gaf', 'ACCOUNTANT', None, 'Pôle Logistique, Communication et Relations Extérieures'),
    ('responsable_enquetes', 'ENQUIRY_MANAGER', None, 'Pôle Logistique, Communication et Relations Extérieures'),
    ('liaison_fec', 'INDUSTRIAL', 'FEC', 'Pôle Logistique, Communication et Relations Extérieures'),
    ('communicateur', 'COMMUNICATOR', None, 'Pôle Logistique, Communication et Relations Extérieures'),
    ('sig_beau', 'CARTOGRAPHER', 'BEAU', "Bureau d'Appui Technique et Numérique"),
    ('sig_ovd', 'CARTOGRAPHER', 'OVD', "Bureau d'Appui Technique et Numérique"),
    ('operateur_saisie', 'DATA_ENTRY', None, "Bureau d'Appui Technique et Numérique"),
    ('it_btc', 'IT_ADMIN', 'BTC', "Bureau d'Appui Technique et Numérique"),
    ('it_sg_itp', 'IT_ADMIN', 'SG-ITP', "Bureau d'Appui Technique et Numérique"),
]

NAME_PARTS = {
    'coordonnateur_principal': ('Coordonnateur', 'Principal'),
    'coordonnateur_adjoint': ('Coordonnateur', 'Adjoint'),
    'assistant_executif': ('Assistant', 'Exécutif'),
    'veille_acgt': ('Expert Veille', 'ACGT'),
    'veille_sg': ('Expert Veille', 'SG-ITP'),
    'expert_juridique': ('Expert', 'Juridique'),
    'sauvegardes_ci': ('Sauvegardes', 'CI'),
    'planification_recons': ('Planification', 'RECONS'),
    'economiste_foner': ('Économiste', 'FONER'),
    'scientifique_inbtp': ('Conseiller', 'Scientifique'),
    'gaf': ('Gestionnaire', 'Administratif et Financier'),
    'responsable_enquetes': ('Responsable', 'Enquêtes'),
    'liaison_fec': ('Liaison', 'FEC'),
    'communicateur': ('Communicateur', 'CTC'),
    'sig_beau': ('Cartographe', 'BEAU'),
    'sig_ovd': ('Cartographe', 'OVD'),
    'operateur_saisie': ('Opérateur', 'Saisie'),
    'it_btc': ('Administrateur', 'IT BTC'),
    'it_sg_itp': ('Administrateur', 'IT SG-ITP'),
}


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
    parser.add_argument('--dest', default='/tmp/ctc_capture.sqlite3')
    parser.add_argument('--manifest', default=str(BASE_DIR / 'captures_ctc' / 'roles.json'))
    args = parser.parse_args()

    copy_database(Path(args.source), Path(args.dest))
    os.environ['SQLITE_NAME'] = args.dest
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    import django
    django.setup()

    from apps.core.models import User
    from apps.experts.models import Expert, Structure
    from apps.governance.models import CTCMembership, TechnicalCell
    from apps.validation.models import (
        EcologicalReview, EconomicReview, ISOReview, LegisticReview, ScheduleReview,
    )
    from web.ctc_views import _resolve_ctc_sub_role

    specs = {row[0]: row for row in ROLE_SPECS}
    ctc = TechnicalCell.objects.order_by('id').first()
    if ctc is None:
        raise SystemExit('Aucune TechnicalCell en base : impossible de préparer les captures.')

    def structure_for(acronym: str | None) -> Structure:
        if acronym:
            found = Structure.objects.filter(acronym__iexact=acronym).order_by('id').first()
            if found:
                return found
        return Structure.objects.filter(acronym__iexact='DS').first() or Structure.objects.order_by('id').first()

    review_models = {
        'veille_acgt': (ISOReview, 'expert', 'status'),
        'veille_sg': (ISOReview, 'expert', 'status'),
        'expert_juridique': (LegisticReview, 'legist', 'status'),
        'sauvegardes_ci': (EcologicalReview, 'expert', 'status'),
        'economiste_foner': (EconomicReview, 'expert', 'status'),
        'planification_recons': (ScheduleReview, 'planner', 'planner_status'),
        'scientifique_inbtp': (ScheduleReview, 'scientist', 'scientist_status'),
        'liaison_fec': (None, None, None),
    }

    def pending_reviews(expert: Expert, sub_role: str) -> int:
        model, field, status_field = review_models.get(sub_role, (None, None, None))
        if model is None:
            return 0
        return model.objects.filter(
            **{field: expert, f'{status_field}__in': ['PENDING', 'ASSIGNED', 'IN_REVIEW']},
        ).count()

    memberships = list(
        CTCMembership.objects.select_related('expert__user', 'expert__structure').order_by('expert_id')
    )
    by_sub_role: dict[str, list[CTCMembership]] = {key: [] for key in specs}
    for membership in memberships:
        acronym = (membership.expert.structure.acronym or '').upper() if membership.expert.structure else ''
        sub_role = _resolve_ctc_sub_role(membership.role, acronym)
        by_sub_role.setdefault(sub_role, []).append(membership)

    created = []
    for sub_role, (membership_role, acronym, _pole) in (
        (key, (spec[1], spec[2], spec[3])) for key, spec in specs.items()
    ):
        if by_sub_role.get(sub_role):
            continue
        local = f'capture.{sub_role}'.replace('_', '-')
        user, _ = User.objects.get_or_create(
            username=local,
            defaults={'email': f'{local}@cnetp.local'},
        )
        user.is_expert = True
        user.is_active = True
        user.set_unusable_password()
        user.save()
        expert, _ = Expert.objects.get_or_create(
            user=user,
            defaults={'structure': structure_for(acronym), 'status': 'ACTIVE'},
        )
        expert.status = 'ACTIVE'
        expert.save(update_fields=['status', 'updated_at'])
        membership = CTCMembership.objects.create(ctc=ctc, expert=expert, role=membership_role)
        by_sub_role[sub_role] = [membership]
        created.append(sub_role)

    representatives: dict[str, dict] = {}
    for sub_role, rows in by_sub_role.items():
        if not rows:
            continue
        rows.sort(key=lambda m: (-pending_reviews(m.expert, sub_role), m.expert_id))
        first_name, last_name = NAME_PARTS[sub_role]
        for index, membership in enumerate(rows):
            user = membership.expert.user
            suffix = '' if index == 0 else f' {index + 1}'
            user.first_name = first_name
            user.last_name = f'{last_name}{suffix}'
            local = f'capture.{sub_role}'.replace('_', '-')
            if index:
                local = f'{local}.{index + 1}'
            user.email = f'{local}@cnetp.local'
            user.username = local
            user.is_expert = True
            user.is_active = True
            user.set_unusable_password()
            user.save()
            membership.expert.status = 'ACTIVE'
            membership.expert.save(update_fields=['status', 'updated_at'])
        chosen = rows[0]
        representatives[sub_role] = {
            'sub_role': sub_role,
            'email': chosen.expert.user.email,
            'user_id': chosen.expert.user_id,
            'expert_id': chosen.expert_id,
            'membership_role': chosen.role,
            'structure': chosen.expert.structure.acronym if chosen.expert.structure else '',
            'pole': specs[sub_role][3],
            'display_name': chosen.expert.user.get_full_name(),
        }

    missing = [key for key in specs if key not in representatives]
    if missing:
        raise SystemExit(f'Sous-rôles sans représentant : {missing}')

    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(representatives, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'Base de capture : {args.dest}')
    print(f'Comptes CTC anonymisés : {len(memberships)} + {len(created)} créés')
    print(f'Manifeste : {manifest_path}')
    for sub_role, info in representatives.items():
        print(f'  {sub_role:24s} {info["email"]:42s} {info["display_name"]}')


if __name__ == '__main__':
    main()
