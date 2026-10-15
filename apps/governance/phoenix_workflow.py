"""Circuit Phoenix : versions, pièces, quorum et transitions atomiques séparées du circuit historique."""
import hashlib
import json
from ipaddress import ip_address

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from datetime import timedelta

from apps.norms.models import Norme, NormeVersion
from .models import (OrganisationVersion, CircuitOrganisation, DossierPhoenix, PiecePhoenix, DecisionPhoenix,
                     MandatOrganisation, GroupeCible, RattachementDocumentaire, EnquetePhoenix, ReunionPhoenix, ParticipationPhoenix)
from .phoenix_services import has_organisation_action
from .phoenix_operations import journal
from .phoenix_rules import ACTIONS, FINAL_ACTIONS


class PhoenixConflict(ValidationError):
    pass


def mandates_for(user):
    if not user.is_authenticated or not user.is_active:
        return MandatOrganisation.objects.none()
    return MandatOrganisation.objects.filter(expert__user=user).select_related('expert__user', 'poste__organe__version', 'groupe__sc__version')


def can_consult(user, dossier):
    if not user.is_authenticated or not user.is_active:
        return False
    if user.has_perm('governance.manage_phoenix'):
        return True
    return any(has_organisation_action(user, mandate, 'document.consulter', dossier.norme, dossier.gt) for mandate in mandates_for(user))


def accessible_dossiers(user):
    queryset = DossierPhoenix.objects.select_related('norme', 'gt__sc', 'circuit__version', 'document_version')
    if user.is_authenticated and user.is_active and user.has_perm('governance.manage_phoenix'):
        return queryset
    identifiers = [dossier.pk for dossier in queryset if can_consult(user, dossier)]
    return queryset.filter(pk__in=identifiers)


def selected_mandate(user, pk):
    return mandates_for(user).get(pk=pk)


def require_action(user, mandate, action, dossier=None, groupe=None):
    norme = dossier.norme if dossier else None
    groupe = dossier.gt if dossier else groupe
    if not has_organisation_action(user, mandate, action, norme, groupe):
        raise PermissionDenied('Cette action n’est pas habilitée pour le mandat et le périmètre sélectionnés.')
    mandate = MandatOrganisation.objects.select_related('poste__organe', 'groupe__sc').get(pk=mandate.pk)
    target = mandate.poste if mandate.poste_id else mandate.groupe
    organ = mandate.poste.organe if mandate.poste_id else mandate.groupe.sc
    if action != 'document.consulter' and (target.status not in ('VALIDATED', 'ACTIVE') or organ.status not in ('VALIDATED', 'ACTIVE')):
        raise PermissionDenied('Le poste ou le groupe et son organe doivent être confirmés avant toute opération.')
    if dossier:
        if dossier.circuit.status != 'VALIDATED' or dossier.suspended:
            raise PermissionDenied('Le circuit de ce dossier est suspendu ou non validé.')
        if action != 'document.consulter' and norme.locked_by_id and norme.locked_by_id != user.pk and norme.lock_timeout and norme.lock_timeout > timezone.now():
            raise PhoenixConflict('Le dossier est verrouillé par un autre utilisateur.')


def _lock(dossier, expected_revision):
    if expected_revision != dossier.revision:
        raise PhoenixConflict('Le dossier a changé. Actualiser avant de recommencer.')
    changed = DossierPhoenix.objects.filter(pk=dossier.pk, revision=expected_revision).update(revision=F('revision') + 1)
    if not changed:
        raise PhoenixConflict('Une autre opération a déjà modifié ce dossier.')
    dossier.revision += 1


@transaction.atomic
def create_dossier(user, mandate, circuit, gt, reference_number, title, content, description='', origin=None):
    version = OrganisationVersion.objects.select_for_update().get(pk=circuit.version_id)
    circuit = CircuitOrganisation.objects.get(pk=circuit.pk, version=version, status='VALIDATED')
    gt = GroupeCible.objects.get(pk=gt.pk, sc__version=version)
    if version.status != 'ACTIVE' or gt.status not in ('VALIDATED', 'ACTIVE') or gt.sc.status not in ('VALIDATED', 'ACTIVE'):
        raise ValidationError('La création exige une organisation, un circuit et un groupe confirmés.')
    if circuit.decision_reference != version.circuit_reference:
        raise ValidationError('Ce circuit n’est pas celui mis en service pour les nouveaux dossiers.')
    require_action(user, mandate, 'document.creer', groupe=gt)
    if not title.strip() or not reference_number.strip() or not content.strip():
        raise ValidationError('La référence, le titre et la première version sont obligatoires.')
    norme = Norme.all_objects.create(reference_number=reference_number.strip(), title=title.strip(), description=description,
                                    circuit_version='PHOENIX', created_by=user, updated_by=user)
    document = NormeVersion.all_objects.create(norme=norme, version_number=1, title=norme.title, content=content,
                                               version_author=user, summary='Première version du dossier Phoenix.')
    RattachementDocumentaire.objects.create(norme=norme, version=version, sc=gt.sc, gt=gt, role='OWNER', status='VALIDATED',
                                           decision_reference=version.activation_reference, effective_from=timezone.localdate(), created_by=user)
    dossier = DossierPhoenix.objects.create(norme=norme, circuit=circuit, gt=gt, creator_mandate=mandate,
                                           state=circuit.configuration['initial'], document_version=document, created_by=user)
    journal(user, version, 'CREATE_DOSSIER', f'dossier:{dossier.pk}', after={'norme_id': norme.pk, 'gt': gt.code, 'circuit': circuit.code, 'version_id': document.pk}, reason='Nouveau dossier ; aucune réaffectation historique.', mandate=mandate, origin=origin)
    return dossier


def _locked_dossier(pk):
    dossier = DossierPhoenix.objects.select_for_update().select_related('norme', 'gt__sc', 'circuit__version', 'document_version').get(pk=pk)
    OrganisationVersion.objects.select_for_update().get(pk=dossier.circuit.version_id)
    return dossier


@transaction.atomic
def save_version(user, mandate, dossier_id, expected_revision, content, summary, origin=None):
    dossier = _locked_dossier(dossier_id)
    require_action(user, mandate, 'document.editer', dossier)
    if dossier.state not in dossier.circuit.configuration.get('editable_states', [dossier.circuit.configuration['initial']]):
        raise ValidationError('Un retour vers une étape de rédaction est nécessaire pour modifier le texte.')
    if not content.strip() or not summary.strip():
        raise ValidationError('Le texte et le résumé des modifications sont obligatoires.')
    _lock(dossier, expected_revision)
    number = (NormeVersion.all_objects.filter(norme=dossier.norme).order_by('-version_number').values_list('version_number', flat=True).first() or 0) + 1
    version = NormeVersion.all_objects.create(norme=dossier.norme, version_number=number, title=dossier.norme.title,
                                             content=content, summary=summary, version_author=user)
    previous = dossier.document_version_id
    dossier.document_version = version
    dossier.stage_sequence += 1  # Les signatures d’une ancienne version ne valent pas pour le nouveau texte.
    dossier.updated_by = user
    dossier.save()
    journal(user, dossier.circuit.version, 'EDIT_DOCUMENT', f'dossier:{dossier.pk}', {'version_id': previous}, {'version_id': version.pk}, summary, mandate=mandate, origin=origin)
    return dossier


@transaction.atomic
def attach_piece(user, mandate, dossier_id, expected_revision, kind, reference, content='', upload=None, origin=None):
    dossier = _locked_dossier(dossier_id)
    require_action(user, mandate, 'document.joindre', dossier)
    if not dossier.document_version_id:
        raise ValidationError('Une version documentaire est requise.')
    if not kind.strip() or not reference.strip():
        raise ValidationError('Préciser le type et la référence de la pièce.')
    _lock(dossier, expected_revision)
    digest = hashlib.sha256()
    if upload:
        for chunk in upload.chunks():
            digest.update(chunk)
        upload.seek(0)
    else:
        digest.update(content.encode())
    piece = PiecePhoenix(dossier=dossier, version=dossier.document_version, mandate=mandate, kind=kind.strip(),
                         reference=reference.strip(), content=content, sha256=digest.hexdigest(), created_by=user)
    if upload:
        piece.file = upload
    piece.save()
    journal(user, dossier.circuit.version, 'ATTACH_PIECE', f'dossier:{dossier.pk}', after={'piece_id': piece.pk, 'kind': piece.kind, 'version_id': piece.version_id, 'sha256': piece.sha256}, reason=piece.reference, mandate=mandate, origin=origin)
    return piece


def _rule_permits(mandate, dossier, rule):
    required_capacity = {'document.homologuer': 'HOMOLOGATION', 'document.publier': 'PUBLICATION'}.get(rule['action'], 'ORGANISATION')
    if mandate.capacity != required_capacity:
        return False
    kind = mandate.poste.organe.type if mandate.poste_id else 'GT'
    if kind not in rule['organe_types']:
        return False
    if rule.get('categories') and (not mandate.poste_id or mandate.poste.category not in rule['categories']):
        return False
    if kind == 'SC' and mandate.poste.organe_id != dossier.gt.sc_id and not rule.get('allow_contributors', False):
        return False
    if rule.get('independent_review') and dossier.document_version.version_author_id == mandate.expert.user_id:
        return False
    return True


def permitted_transitions(user, mandate, dossier):
    if not dossier.document_version_id or dossier.suspended:
        return []
    return [rule for rule in dossier.circuit.configuration['transitions'] if rule['from'] == dossier.state
            and _rule_permits(mandate, dossier, rule)
            and has_organisation_action(user, mandate, rule['action'], dossier.norme, dossier.gt)]


@transaction.atomic
def decide(user, mandate, dossier_id, expected_revision, transition_id, decision_reference, reason, request_key, origin=None):
    dossier = _locked_dossier(dossier_id)
    payload = {'mandate': mandate.pk, 'transition': transition_id, 'reference': decision_reference, 'reason': reason}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    previous = dossier.decisions.filter(request_key=request_key).first()
    if previous:
        if previous.expert.user_id != user.pk or previous.payload_sha256 != digest:
            raise PhoenixConflict('Cet identifiant d’opération a déjà été utilisé avec un autre contenu.')
        require_action(user, mandate, 'document.consulter', dossier)
        return previous
    if not request_key or len(request_key) > 100 or not decision_reference.strip() or not reason.strip():
        raise ValidationError('La décision, son motif et son identifiant d’opération sont obligatoires.')
    rule = next((item for item in dossier.circuit.configuration['transitions'] if item['id'] == transition_id and item['from'] == dossier.state), None)
    if not rule:
        raise PhoenixConflict('Cette transition ne correspond plus à l’état du dossier.')
    require_action(user, mandate, rule['action'], dossier)
    if not dossier.document_version_id or not _rule_permits(mandate, dossier, rule):
        raise PermissionDenied('Le mandat, la catégorie ou l’indépendance de l’examen ne permet pas cette décision.')
    pieces = dossier.pieces.filter(version=dossier.document_version)
    if any(not pieces.filter(kind=kind).exists() for kind in rule.get('required_evidence', [])):
        raise ValidationError('Les pièces exigées pour cette version ne sont pas toutes présentes.')
    if rule.get('requires_public_inquiry') and not dossier.enquetes.filter(version=dossier.document_version, ends_at__lte=timezone.localdate(), report__isnull=False).exists():
        raise ValidationError('Une enquête terminée et son rapport sont exigés pour cette version.')
    if dossier.decisions.filter(stage_sequence=dossier.stage_sequence, transition=transition_id, expert_id=mandate.expert_id).exists():
        raise PhoenixConflict('Cette personne a déjà pris part à cette décision pour cette version.')
    if rule['action'] == 'document.homologuer' and dossier.norme.status != 'ADOPTED':
        raise ValidationError('L’homologation exige une adoption préalablement enregistrée.')
    if rule['action'] == 'document.publier' and dossier.norme.status != 'HOMOLOGATED':
        raise ValidationError('La publication exige une homologation préalablement enregistrée.')
    _lock(dossier, expected_revision)
    votes = dossier.decisions.filter(stage_sequence=dossier.stage_sequence, transition=transition_id).count() + 1
    completed = votes >= rule['quorum']
    origin = origin or {}
    try:
        address = str(ip_address(origin.get('ip', '')))
    except ValueError:
        address = None
    event = DecisionPhoenix.objects.create(dossier=dossier, mandate=mandate, expert_id=mandate.expert_id,
        document_version=dossier.document_version, stage_sequence=dossier.stage_sequence, transition=transition_id,
        from_state=dossier.state, to_state=rule['to'], decision_reference=decision_reference.strip(), reason=reason.strip(),
        request_key=request_key, payload_sha256=digest, completed=completed, ip_address=address, channel=origin.get('channel', 'Web'))
    if completed:
        dossier.state = rule['to']
        dossier.stage_sequence += 1
        if rule['action'].endswith('.retour') and dossier.norme.status in ('ADOPTED', 'HOMOLOGATED', 'PUBLISHED'):
            Norme.all_objects.filter(pk=dossier.norme_id).update(status='DRAFT', is_public=False, updated_at=timezone.now())
        if rule['action'] in FINAL_ACTIONS:
            fields = {'status': FINAL_ACTIONS[rule['action']], 'updated_at': timezone.now()}
            date_field = {'document.adopter': 'adoption_date', 'document.homologuer': 'homologation_date', 'document.publier': 'publication_date'}[rule['action']]
            fields[date_field] = timezone.localdate()
            if rule['action'] == 'document.publier':
                fields.update({'jo_reference': decision_reference.strip(), 'is_public': True})
            Norme.all_objects.filter(pk=dossier.norme_id).update(**fields)
        dossier.updated_by = user
        dossier.save()
    journal(user, dossier.circuit.version, 'TRANSITION' if completed else 'RECORD_APPROVAL', f'dossier:{dossier.pk}',
            {'state': event.from_state, 'version_id': event.document_version_id},
            {'state': dossier.state, 'transition': transition_id, 'votes': votes, 'quorum': rule['quorum'], 'decision_id': event.pk}, reason, mandate=mandate, origin=origin)
    if completed:
        transaction.on_commit(lambda: _notify_transition(dossier.pk, event.pk), robust=True)
    return event


def _notify_transition(dossier_id, decision_id):
    # Notification interne après commit ; aucun envoi de courrier à partir de ce service.
    from apps.mobileapp.models import Notification
    dossier = DossierPhoenix.objects.select_related('norme', 'gt__sc', 'circuit__version').get(pk=dossier_id)
    users = {m.expert.user_id for m in MandatOrganisation.objects.filter(status='ACTIVE').filter(
        Q(poste__organe__version=dossier.circuit.version) | Q(groupe__sc__version=dossier.circuit.version)).select_related('expert__user')
        if has_organisation_action(m.expert.user, m, 'document.consulter', dossier.norme, dossier.gt)}
    for user_id in users:
        Notification.objects.create(user_id=user_id, title=f'Dossier {dossier.norme.reference_number}',
                                    body='Une décision du circuit Phoenix a été enregistrée.', notification_type='SYSTEM',
                                    data={'phoenix_dossier_id': dossier_id, 'decision_id': decision_id})


@transaction.atomic
def save_inquiry(user, mandate, dossier_id, expected_revision, reference, starts_at, ends_at, report_id=None, origin=None):
    dossier = _locked_dossier(dossier_id)
    require_action(user, mandate, 'st.enquete', dossier)
    _lock(dossier, expected_revision)
    report = PiecePhoenix.objects.get(pk=report_id, dossier=dossier, version=dossier.document_version) if report_id else None
    enquiry = EnquetePhoenix.objects.create(dossier=dossier, version=dossier.document_version, reference=reference,
        starts_at=starts_at, ends_at=ends_at, report=report, created_by=user)
    journal(user, dossier.circuit.version, 'PUBLIC_INQUIRY', f'dossier:{dossier.pk}', after={'inquiry_id': enquiry.pk, 'version_id': enquiry.version_id}, reason=reference, mandate=mandate, origin=origin)
    return enquiry


@transaction.atomic
def set_document_lock(user, mandate, dossier_id, expected_revision, locked, origin=None):
    dossier = _locked_dossier(dossier_id)
    require_action(user, mandate, 'document.verrouiller', dossier)
    _lock(dossier, expected_revision)
    until = timezone.now() + timedelta(minutes=30) if locked else None
    Norme.all_objects.filter(pk=dossier.norme_id).update(locked_by=user if locked else None, lock_timeout=until)
    journal(user, dossier.circuit.version, 'LOCK_DOCUMENT' if locked else 'UNLOCK_DOCUMENT', f'dossier:{dossier.pk}',
            after={'locked_by': user.pk if locked else None, 'until': str(until) if until else None}, reason='Verrou de rédaction explicite, valable trente minutes.', mandate=mandate, origin=origin)
    return dossier


@transaction.atomic
def plan_meeting(user, mandate, dossier_id, expected_revision, title, agenda, starts_at, location, participant_ids, origin=None):
    dossier = _locked_dossier(dossier_id)
    require_action(user, mandate, 'reunion.planifier', dossier)
    participants = list(MandatOrganisation.objects.filter(pk__in=participant_ids))
    if len(participants) != len(set(participant_ids)) or any(p.organisation_version.pk != dossier.circuit.version_id for p in participants):
        raise ValidationError('Les participants doivent avoir des mandats dans la même organisation.')
    _lock(dossier, expected_revision)
    meeting = ReunionPhoenix.objects.create(dossier=dossier, document_version=dossier.document_version, organizer=mandate,
        title=title, agenda=agenda, starts_at=starts_at, location=location, created_by=user)
    for participant in participants:
        ParticipationPhoenix.objects.create(reunion=meeting, mandate=participant, created_by=user)
    journal(user, dossier.circuit.version, 'PLAN_MEETING', f'dossier:{dossier.pk}', after={'meeting_id': meeting.pk, 'version_id': dossier.document_version_id, 'participants': participant_ids}, reason=title, mandate=mandate, origin=origin)
    return meeting


@transaction.atomic
def record_presence(user, mandate, dossier_id, expected_revision, participation_id, presence, origin=None):
    dossier = _locked_dossier(dossier_id)
    require_action(user, mandate, 'reunion.planifier', dossier)
    participant = ParticipationPhoenix.objects.select_for_update().get(pk=participation_id, reunion__dossier=dossier)
    _lock(dossier, expected_revision)
    before = participant.presence
    participant.presence = presence
    participant.updated_by = user
    participant.save()
    journal(user, dossier.circuit.version, 'MEETING_PRESENCE', f'dossier:{dossier.pk}', {'presence': before}, {'presence': presence, 'participant_id': participant.pk}, reason=participant.reunion.title, mandate=mandate, origin=origin)
    return participant
