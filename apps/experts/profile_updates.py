"""Transitions explicites du suivi de profil, sans modifier les nominations."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import ProfileUpdate, ProfileUpdateEvent


TRANSITIONS = {
    'NOT_STARTED': {'IN_PROGRESS'},
    'IN_PROGRESS': {'SUBMITTED'},
    'SUBMITTED': {'UNDER_REVIEW'},
    'UNDER_REVIEW': {'COMPLETE', 'NEEDS_CORRECTION', 'REJECTED'},
    'NEEDS_CORRECTION': {'SUBMITTED'},
    'REJECTED': {'IN_PROGRESS'},
    'COMPLETE': {'EXPIRED'},
    'EXPIRED': {'IN_PROGRESS'},
}


def missing_requirements(expert, version):
    from apps.governance.models import ChoixOrganisationExpert

    user = expert.user
    missing = []
    if not user.first_name.strip() or not user.last_name.strip():
        missing.append('identity')
    if not user.email.strip() or not (user.phone or '').strip():
        missing.append('contact')
    if not expert.structure_id:
        missing.append('structure')
    if not expert.specialties.strip():
        missing.append('specialties')
    if not expert.cv:
        missing.append('cv')
    choices = ChoixOrganisationExpert.objects.filter(expert=expert, version=version)
    if not choices.exists():
        missing.append('subcommission')
        missing.append('group')
    elif not choices.filter(groupe__isnull=False).exists() and not choices.filter(source_wg__isnull=False).exists():
        missing.append('group')
    return missing


@transaction.atomic
def transition(expert, target, actor, *, version=None, comment=''):
    if not actor or not actor.is_authenticated:
        raise ValidationError('Un auteur authentifié est requis.')
    state, _ = ProfileUpdate.objects.get_or_create(expert=expert)
    state = ProfileUpdate.objects.select_for_update().get(pk=state.pk)
    old = state.status
    if target not in TRANSITIONS.get(old, set()):
        raise ValidationError(f'Transition de {old} vers {target} interdite.')
    administrative = {'UNDER_REVIEW', 'COMPLETE', 'NEEDS_CORRECTION', 'REJECTED'}
    staff = actor.is_superuser or actor.is_staff or getattr(actor, 'is_ctc_staff', False)
    if (target in administrative and not staff) or (target not in administrative and actor.pk != expert.user_id and not staff):
        raise ValidationError('Vous ne pouvez pas effectuer cette transition.')
    if target == 'REJECTED' and not comment.strip():
        raise ValidationError('Un motif de rejet est requis.')
    if target in {'SUBMITTED', 'COMPLETE'}:
        current_version = version or state.version
        if not current_version:
            raise ValidationError('Une version de l’organisation est requise.')
        missing = missing_requirements(expert, current_version)
        if missing:
            raise ValidationError({'profile': f'Informations manquantes : {", ".join(missing)}'})
        state.version = current_version
    elif version:
        state.version = version
    now = timezone.now()
    if target == 'IN_PROGRESS':
        state.started_at = now
    elif target == 'SUBMITTED':
        state.submitted_at = now
    elif target in administrative:
        state.reviewed_at = now
    if target == 'COMPLETE':
        state.completed_at = now
        state.validated_by = actor
    elif target in {'IN_PROGRESS', 'EXPIRED', 'NEEDS_CORRECTION', 'REJECTED'}:
        state.completed_at = None
        state.validated_by = None
    state.status = target
    state.review_comment = comment
    state.save()
    ProfileUpdateEvent.objects.create(profile_update=state, from_status=old, to_status=target, actor=actor, comment=comment)
    return state
