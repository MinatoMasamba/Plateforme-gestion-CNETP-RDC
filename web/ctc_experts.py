"""Consultation en lecture seule des experts, affectations et traçabilité depuis la CTC.

Réutilise exclusivement les modèles et services existants. Aucune écriture,
aucune donnée inventée. Le référentiel Phoenix n'est pas présenté comme actif :
son statut est conservé et affiché tel quel.
"""
from collections import defaultdict

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.core.models import AuditLog
from apps.experts.models import Expert, ProfileUpdate
from apps.governance.activity_supervision import activity_access_for
from apps.governance.models import (
    ActivitySession, AffectationSousCommission, ChoixOrganisationExpert,
    MandatOrganisation, Organe,
)
from apps.governance.phoenix_runtime import current_organisation_version
from apps.norms.models import NormeVersion

AFFECTATION_LABELS = {
    'validée': 'Affectation validée',
    'à examiner': 'Affectation proposée',
    'choix': "Choix exprimé par l'expert",
    'aucune': 'Non affectée',
}


def _completeness(expert):
    """État documentaire simple, dérivé des champs déjà enregistrés."""
    missing = []
    if not expert.cv:
        missing.append('CV')
    if not (expert.specialties or '').strip():
        missing.append('domaine de compétence')
    if not (expert.user.phone or '').strip():
        missing.append('téléphone')
    if not (expert.user.email or '').strip():
        missing.append('email')
    return missing


def build_expert_directory(expert):
    """Annuaire des experts (lecture seule) + effectifs et postes des SC."""
    access = activity_access_for(expert.user)
    version = current_organisation_version()
    today = timezone.localdate()

    experts = list(
        Expert.objects.select_related('user', 'structure')
        .filter(user__is_active=True)
        .order_by('user__last_name', 'user__first_name')
    )
    expert_ids = [item.pk for item in experts]
    user_ids = [item.user_id for item in experts]

    assignments = defaultdict(list)
    for row in AffectationSousCommission.objects.filter(
        version=version, expert_id__in=expert_ids,
    ).select_related('sc'):
        assignments[row.expert_id].append(row)

    choices = defaultdict(list)
    for row in ChoixOrganisationExpert.objects.filter(
        version=version, expert_id__in=expert_ids,
    ).select_related('sc'):
        choices[row.expert_id].append(row)

    profile_map = {
        row.expert_id: row for row in ProfileUpdate.objects.filter(expert_id__in=expert_ids)
    }

    session_map = {
        row['user_id']: row
        for row in ActivitySession.objects.filter(user_id__in=user_ids)
        .values('user_id').annotate(seconds=Sum('active_seconds'), n=Count('id'))
    }
    edition_map = {
        row['version_author_id']: row['editions']
        for row in NormeVersion.all_objects.filter(version_author_id__in=user_ids)
        .values('version_author_id').annotate(editions=Count('id'))
    }

    rows = []
    complete = incomplete = without_login = 0
    for item in experts:
        asg = assignments.get(item.pk, [])
        migrated = [a for a in asg if a.status == 'MIGRATED' and a.sc_id]
        review = [a for a in asg if a.status == 'REVIEW']
        choice = choices.get(item.pk, [])
        sc = migrated[0].sc if migrated else (review[0].sc if review and review[0].sc else (choice[0].sc if choice else None))

        if migrated:
            affectation = 'validée'
        elif review:
            affectation = 'à examiner'
        elif choice:
            affectation = 'choix'
        else:
            affectation = 'aucune'

        missing = _completeness(item)
        profile = profile_map.get(item.pk)
        if missing:
            incomplete += 1
        else:
            complete += 1
        if item.user.last_login is None:
            without_login += 1

        session = session_map.get(item.user_id, {})
        rows.append({
            'id': item.pk, 'name': item.full_name or item.user.username,
            'email': item.user.email, 'structure': item.structure.acronym if item.structure else '',
            'structure_name': item.structure.name if item.structure else '',
            'sc_code': sc.code if sc else None,
            'sc_name': sc.official_name or sc.name if sc else None,
            'affectation': affectation,
            'affectation_label': AFFECTATION_LABELS[affectation],
            'missing': missing,
            'complete': not missing,
            'profile_status': profile.get_status_display() if profile else 'Aucun dossier de mise à jour',
            'last_login': item.user.last_login,
            'minutes': (session.get('seconds') or 0) // 60,
            'editions': edition_map.get(item.user_id, 0),
        })

    # Effectifs et postes des sept sous-commissions.
    scs = []
    for sc in Organe.objects.filter(version=version, type=Organe.Type.SC).order_by('code'):
        post_rows = []
        for post in sc.postes.prefetch_related('mandates__expert__user').order_by('code'):
            mandate = next((m for m in post.mandates.all()
                            if m.status == 'ACTIVE' and m.capacity == 'ORGANISATION'
                            and (not m.start_date or m.start_date <= today)
                            and (not m.end_date or m.end_date >= today)), None)
            post_rows.append({
                'title': post.title or post.code,
                'holder': mandate.expert.full_name if mandate else None,
            })
        migrated_count = AffectationSousCommission.objects.filter(
            version=version, sc=sc, status='MIGRATED',
        ).count()
        scs.append({
            'code': sc.code, 'name': sc.official_name or sc.name,
            'experts': migrated_count, 'gt_count': sc.groupes.count(),
            'posts': post_rows,
            'vacant': sum(1 for p in post_rows if p['holder'] is None),
        })

    return {
        'rows': rows,
        'total': len(rows),
        'complete': complete,
        'incomplete': incomplete,
        'without_login': without_login,
        'scs': scs,
        'referential': {'code': version.code, 'status': version.get_status_display(), 'is_active': version.status == 'ACTIVE'} if version else None,
        'can_view_contributions': access.get('can_view_contributions', False),
    }


def build_traceability(expert, limit=60):
    """Journal CTC/CTM en lecture seule, limité aux événements pertinents."""
    logs = AuditLog.objects.filter(changes__scope__in=['ctc', 'ctm']).select_related('user').order_by('-timestamp', '-pk')[:limit]
    rows = []
    for log in logs:
        meta = log.changes or {}
        rows.append({
            'id': log.pk, 'timestamp': log.timestamp,
            'actor': log.user.get_full_name() or log.user.username if log.user else 'Auteur non enregistré',
            'action': log.get_action_display(),
            'object': log.object_repr,
            'reference': meta.get('reference', ''),
            'title': meta.get('title', ''),
            'channel': meta.get('channel', 'Plateforme'),
            'model': log.content_type,
        })
    return rows
