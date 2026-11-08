"""Services ST partagés par API, admin et Neuronne ; aucune décision déduite d’un nom."""
from datetime import date
from decimal import Decimal, InvalidOperation
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from apps.core.models import User
from apps.experts.models import Expert
from .models import CTCMembership, MandatOrganisation, PosteOrganisation, JournalMigration, PlatformFreeze
from .st_operations_models import STAccessPolicy, STRecord, STRecordRevision, STConfirmation
from .phoenix_runtime import active_st_mandate, current_st_version
from .st_matrix import prepare_matrix, VERSION


def require_admin(user):
    if not user.is_authenticated or not user.is_active or not user.is_staff or not user.has_perm('governance.add_nominationctc'):
        raise PermissionDenied('Attribution réservée à un administrateur habilité aux nominations ST.')


def actor_mandate(user):
    if not user or not user.is_authenticated or not user.is_active:
        raise PermissionDenied('Authentification active requise.')
    expert = Expert.objects.filter(user=user, status='ACTIVE', user__is_active=True).first()
    mandate = active_st_mandate(expert) if expert else None
    if not mandate or not mandate.poste.st_sub_role or mandate.poste.status not in ('VALIDATED', 'ACTIVE'):
        raise PermissionDenied('Un mandat ST v3 en cours est requis.')
    return mandate


def writable():
    if PlatformFreeze.get_solo().is_locked:
        raise PermissionDenied('Plateforme verrouillée : écriture suspendue.')


@transaction.atomic
def reset_legacy_access(user):
    if user is not None:
        require_admin(user)
    version = prepare_matrix()
    policy, created = STAccessPolicy.objects.get_or_create(pk=1, defaults={'version': version})
    policy = STAccessPolicy.objects.select_for_update().get(pk=policy.pk)
    if not created and policy.version_id == version.pk and policy.enabled:
        return {'already_configured': True, 'version': VERSION}
    policy.version, policy.enabled = version, True
    policy.save()
    return _retire_legacy(user, version)


def _retire_legacy(user, version):
    count = CTCMembership.all_objects.filter(is_active=True).update(is_active=False)
    flags = User.objects.filter(is_ctc_staff=True).update(is_ctc_staff=False)
    JournalMigration.objects.create(version=version, actor=user, actor_name=(user.get_full_name() or user.username) if user else 'Backend ST — bascule demandée par l’utilisateur',
        operation='RETIRE_LEGACY_CTC', target='ST', before={'memberships': count, 'flags': flags},
        after={'version': VERSION, 'new_mandates': 0}, reason='Bascule ST v3 ; anciennes affectations conservées sans droits.')
    return {'version': VERSION, 'retired_memberships': count, 'retired_flags': flags}


@transaction.atomic
def nominate_batch(user, assignments, apply=False):
    require_admin(user)
    writable()
    policy = STAccessPolicy.objects.select_for_update().filter(pk=1, enabled=True).first()
    if not policy or policy.version.code != VERSION:
        raise ValidationError('La bascule ST v3 doit être effectuée avant les nominations.')
    if not isinstance(assignments, list) or not 1 <= len(assignments) <= 19:
        raise ValidationError('Fournir entre 1 et 19 attributions explicites.')
    prepared, seen_posts, seen_experts = [], set(), set()
    for item in assignments:
        if not isinstance(item, dict):
            raise ValidationError('Chaque attribution doit être un objet.')
        code = item.get('post_code', '')
        post = PosteOrganisation.objects.select_for_update().filter(organe__version=policy.version, code=code).first()
        if not post or code in seen_posts:
            raise ValidationError(f'Poste inconnu ou répété : {code}.')
        qs = Expert.objects.filter(status='ACTIVE', user__is_active=True)
        if item.get('expert_id'):
            qs = qs.filter(pk=item['expert_id'])
        elif item.get('email'):
            qs = qs.filter(user__email__iexact=item['email'].strip())
        else:
            raise ValidationError('Un identifiant expert ou un email exact est obligatoire ; un nom seul ne suffit pas.')
        if qs.count() != 1:
            raise ValidationError(f'Compte absent ou ambigu pour {code}.')
        expert = qs.select_related('user').get()
        if expert.pk in seen_experts:
            raise ValidationError('Un même expert ne peut recevoir deux postes dans ce lot.')
        if MandatOrganisation.objects.filter(poste=post, status='ACTIVE', capacity='ORGANISATION').exists():
            raise ValidationError(f'Le poste {code} est déjà occupé ; clôturer son mandat avant remplacement.')
        if MandatOrganisation.objects.filter(expert=expert, poste__organe__version=policy.version, status='ACTIVE').exists():
            raise ValidationError(f'{expert.full_name} possède déjà un mandat ST v3.')
        try:
            start = date.fromisoformat(item['start_date'])
        except (KeyError, ValueError, TypeError):
            raise ValidationError('Date de début explicite requise (AAAA-MM-JJ).')
        reference = str(item.get('appointment_reference', '')).strip()
        if not reference:
            raise ValidationError('Référence de nomination obligatoire.')
        mandate = MandatOrganisation(expert=expert, poste=post, function=post.title,
            capacity='ORGANISATION', status='ACTIVE', start_date=start, appointment_reference=reference)
        mandate.full_clean()
        prepared.append((mandate, expert, post))
        seen_posts.add(code)
        seen_experts.add(expert.pk)
    results = []
    for mandate, expert, post in prepared:
        if apply:
            # Validation déjà effectuée ; l'e-mail part via le signal post_save.
            mandate.status = 'PROPOSED'
            mandate.save()
            mandate.status = 'ACTIVE'
            mandate.full_clean()
            # ``save`` et non ``update`` : le signal post_save envoie l'e-mail
            # de nomination, quel que soit le canal (admin, console, Neuronne).
            mandate.save(update_fields=['status'])
            JournalMigration.objects.create(version=policy.version, actor=user,
                actor_name=user.get_full_name() or user.username, operation='ST_NOMINATION',
                target=f'mandat:{mandate.pk}', after={'post': post.code, 'expert_id': expert.pk, 'start_date': str(mandate.start_date)},
                reason=mandate.appointment_reference)
        results.append({'post_code': post.code, 'expert_id': expert.pk, 'name': expert.full_name, 'mandate_id': mandate.pk, 'applied': apply, 'start_date': mandate.start_date.isoformat(), 'effective_now': bool(apply and mandate.start_date <= timezone.localdate())})
    return results


def visible_records(user):
    mandate = actor_mandate(user)
    qs = STRecord.objects.filter(version=mandate.organisation_version)
    role = mandate.poste.st_sub_role
    pole = mandate.poste.organe.code
    if role in ('coordonnateur_principal', 'coordonnateur_adjoint'):
        return qs
    if pole == 'ST-P3' and mandate.poste.category == 'POLE_HEAD':
        return qs
    if mandate.poste.category == 'POLE_HEAD':
        return qs.filter(pole=pole)
    return qs.filter(created_by=user)


def _validate_payload(kind, data):
    title = str(data.get('title', '')).strip()
    source = str(data.get('source_reference', '')).strip()
    if not title or not source:
        raise ValidationError('Titre et référence source obligatoires.')
    payload = {'title': title, 'source_reference': source, 'content': str(data.get('content', ''))}
    if kind == 'FINANCE':
        try:
            amount = Decimal(str(data['amount']))
            operation_date = date.fromisoformat(data['operation_date'])
        except (KeyError, ValueError, TypeError, InvalidOperation):
            raise ValidationError('Montant décimal et date financière obligatoires.')
        if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
            raise ValidationError('Montant strictement positif, avec deux décimales maximum.')
        currency = str(data.get('currency', '')).upper()
        movement = data.get('movement')
        if currency not in ('CDF', 'USD', 'EUR') or movement not in ('ENGAGEMENT', 'DEPENSE'):
            raise ValidationError('Devise CDF/USD/EUR et mouvement ENGAGEMENT/DEPENSE requis.')
        payload.update(amount=amount, currency=currency, movement=movement, operation_date=operation_date)
    return payload


@transaction.atomic
def write_record(user, data, record_id=None):
    writable()
    mandate = actor_mandate(user)
    pole, role = mandate.poste.organe.code, mandate.poste.st_sub_role
    record = None
    if record_id is not None:
        record = visible_records(user).select_for_update().filter(pk=record_id).first()
        if not record:
            raise PermissionDenied('Travail inaccessible.')
        if data.get('revision') != record.revision:
            raise ValidationError('Révision obsolète ; recharger le dossier.', code='conflict')
        kind = record.kind
    else:
        kind = data.get('kind')
    if pole not in ('ST-P1', 'ST-P2', 'ST-P3', 'ST-P4'):
        raise PermissionDenied('La préparation de ces registres est réservée aux pôles.')
    if kind not in STRecord.Kind.values:
        raise ValidationError('Type PTN, FINANCE ou WORK requis.')
    if kind == 'PTN' and not (pole == 'ST-P2' and (role == 'gestionnaire_ptn' or mandate.poste.category == 'POLE_HEAD')):
        raise PermissionDenied('Registre PTN réservé au gestionnaire et au chef du pôle 2.')
    if kind == 'FINANCE' and pole != 'ST-P3':
        raise PermissionDenied('Écritures financières réservées au pôle 3.')
    if record and record.pole != pole:
        raise PermissionDenied('Un lecteur d’audit ne peut modifier un autre pôle.')
    payload = _validate_payload(kind, data)
    if record is None:
        reference = str(data.get('reference', '')).strip()
        if not reference:
            raise ValidationError('Référence du travail obligatoire.')
        record = STRecord(kind=kind, version=mandate.organisation_version, pole=pole,
            reference=reference, created_by=user)
        record.full_clean()
        record.save()
    number = record.revision + 1
    revision = STRecordRevision(record=record, number=number, author=user, mandate=mandate, **payload)
    revision.full_clean()
    revision.save()
    record.revision = number
    record.save(update_fields=['revision', 'updated_at'])
    _journal(user, mandate, 'ST_PREPARE', record, {'revision': number})
    return record


@transaction.atomic
def confirm_record(user, record_id, revision, decision, comment):
    writable()
    mandate = actor_mandate(user)
    record = visible_records(user).select_for_update().filter(pk=record_id).first()
    if not record:
        raise PermissionDenied('Travail inaccessible.')
    if mandate.poste.category != 'POLE_HEAD' or mandate.poste.organe.code != record.pole:
        raise PermissionDenied('Confirmation réservée au chef du pôle concerné.')
    if revision != record.revision:
        raise ValidationError('Révision obsolète.', code='conflict')
    if decision not in ('CONFIRMED', 'REJECTED') or not str(comment or '').strip():
        raise ValidationError('Décision et commentaire obligatoires.')
    version = record.versions.get(number=revision)
    if version.author_id == user.pk:
        raise PermissionDenied('Un contrôle indépendant est requis : vous ne pouvez confirmer votre propre travail.')
    if STConfirmation.objects.filter(revision=version).exists():
        raise ValidationError('Cette version a déjà une décision.', code='conflict')
    confirmation = STConfirmation.objects.create(revision=version, decision=decision,
        comment=comment, author=user, mandate=mandate)
    _journal(user, mandate, 'ST_CONFIRM', record, {'revision': revision, 'decision': decision})
    return confirmation


def _journal(user, mandate, operation, record, after):
    JournalMigration.objects.create(version=record.version, actor=user, actor_name=user.get_full_name() or user.username,
        mandate=mandate, operation=operation, target=f'st-record:{record.pk}', after=after,
        reason=record.reference)
