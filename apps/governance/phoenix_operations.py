"""Services partagés web/API/IA : préparation, activation et suspension auditées."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from ipaddress import ip_address
from .models import (OrganisationVersion, Organe, PosteOrganisation, GroupeCible, MandatOrganisation,
                     HabilitationAction, CorrespondanceStructure, CorrespondanceGroupe,
                     RattachementDocumentaire, CircuitOrganisation, JournalMigration)
from .phoenix_rules import ACTIONS
from .organisation_permissions import can_manage_organisation, can_activate_organisation

CONFIG_MODELS = {'version': OrganisationVersion, 'organe': Organe, 'poste': PosteOrganisation, 'gt': GroupeCible, 'mandat': MandatOrganisation,
                 'habilitation': HabilitationAction, 'circuit': CircuitOrganisation,
                 'rattachement': RattachementDocumentaire}
CONFIG_FIELDS = {
    'version': ['name', 'source_document'],
    'organe': ['code', 'name', 'official_name', 'type', 'parent', 'domain', 'composition', 'status', 'source_reference'],
    'poste': ['organe', 'code', 'category', 'title', 'origin_label', 'required_structure', 'source_reference', 'status'],
    'gt': ['sc', 'code', 'name', 'activity', 'source_reference', 'status'],
    'mandat': ['expert', 'poste', 'groupe', 'function', 'capacity', 'appointment_reference', 'start_date', 'end_date', 'status'],
    'habilitation': ['mandat', 'action', 'perimeter', 'decision_reference', 'start_date', 'end_date', 'enabled', 'delegated_from'],
    'circuit': ['code', 'name', 'configuration', 'decision_reference', 'status'],
    'rattachement': ['norme', 'sc', 'gt', 'role', 'status', 'decision_reference', 'effective_from', 'effective_to'],
}


def object_version(obj):
    if isinstance(obj, OrganisationVersion):
        return obj
    if isinstance(obj, (Organe, CircuitOrganisation, CorrespondanceStructure, CorrespondanceGroupe, RattachementDocumentaire)):
        return obj.version
    if isinstance(obj, PosteOrganisation):
        return obj.organe.version
    if isinstance(obj, GroupeCible):
        return obj.sc.version
    if isinstance(obj, HabilitationAction):
        return obj.mandat.organisation_version
    return obj.organisation_version


def snapshot(obj, names):
    return {name: (getattr(obj, name).pk if hasattr(getattr(obj, name), 'pk') else str(getattr(obj, name)) if getattr(obj, name) is not None else None)
            for name in names}


def journal(user, version, operation, target, before=None, after=None, reason='', mandate=None, origin=None):
    if origin is None:
        from apps.core.ctc_audit import current_audit_request
        request = current_audit_request()
        if request is not None and request.user.pk == user.pk:
            origin = {'ip': request.META.get('REMOTE_ADDR', ''), 'channel':'API' if request.path.startswith('/api/') else 'Web'}
    origin = origin or {}
    try:
        address = str(ip_address(origin.get('ip', '')))
    except ValueError:
        address = None
    return JournalMigration.objects.create(version=version, actor=user,
        actor_name=user.get_full_name() or user.username, operation=operation, target=target,
        before=before or {}, after=after or {}, reason=reason, mandate=mandate,
        actor_role=(mandate.function + (' · ' + mandate.get_capacity_display() if mandate.capacity != 'ORGANISATION' else ''))[:250] if mandate else '', ip_address=address, channel=origin.get('channel', ''))


@transaction.atomic
def configure(user, version, kind, data, pk=None):
    if not can_manage_organisation(user):
        raise PermissionDenied('La gestion de l’organisation CNE-ITP est réservée au Président ou à un gestionnaire habilité.')
    version = OrganisationVersion.objects.select_for_update().get(pk=version.pk)
    if version.status == 'ARCHIVED':
        raise ValidationError('Cette édition est archivée.')
    if kind not in CONFIG_MODELS:
        raise ValidationError('Objet de préparation invalide.')
    if kind == 'version' and pk != version.pk:
        raise ValidationError('Modifier l’édition courante du référentiel.')
    model = CONFIG_MODELS[kind]
    obj = model.objects.select_for_update().get(pk=pk) if pk else model()
    if pk and object_version(obj).pk != version.pk:
        raise PermissionDenied('Cet objet appartient à une autre organisation.')
    before = snapshot(obj, CONFIG_FIELDS[kind]) if pk else {}
    for name in CONFIG_FIELDS[kind]:
        if name in data:
            setattr(obj, name, data[name])
    if kind in ('organe', 'circuit', 'rattachement'):
        obj.version = version
    if object_version(obj).pk != version.pk:
        raise ValidationError('La cible appartient à une autre organisation.')
    if kind == 'habilitation' and obj.action not in ACTIONS:
        raise ValidationError('Action d’habilitation inconnue.')
    if kind == 'mandat' and obj.status == 'ACTIVE':
        target = obj.poste if obj.poste_id else obj.groupe
        if target.status not in ('VALIDATED', 'ACTIVE'):
            raise ValidationError('La fonction ou le groupe doit être validé avant la nomination.')
        organ = obj.poste.organe if obj.poste_id else obj.groupe.sc
        if organ.status not in ('VALIDATED', 'ACTIVE'):
            raise ValidationError('Confirmer l’organe de rattachement avant la nomination.')
        if obj.expert.status != 'ACTIVE' or not obj.expert.user.is_active:
            raise ValidationError('Le titulaire doit avoir un compte et un profil expert actifs.')
        if obj.poste_id and obj.poste.required_structure_id and obj.poste.required_structure_id != obj.expert.structure_id:
            raise ValidationError('La nomination ne correspond pas à la structure d’origine requise.')
    if kind == 'habilitation' and obj.enabled and obj.mandat.status != 'ACTIVE':
        raise ValidationError('Une habilitation exige un mandat en cours.')
    if kind == 'organe' and obj.status in ('VALIDATED', 'ACTIVE') and not obj.official_name.strip():
        raise ValidationError('Renseigner la dénomination confirmée par la source.')
    if kind == 'poste' and obj.status in ('VALIDATED', 'ACTIVE') and not obj.title.strip():
        raise ValidationError('La fonction de ce poste doit être confirmée.')
    if kind == 'rattachement' and obj.status == 'VALIDATED' and not obj.effective_from:
        raise ValidationError('Le rattachement validé exige une date de prise d’effet.')
    obj.updated_by = user
    if not pk:
        obj.created_by = user
    obj.save()
    journal(user, version, 'CONFIGURE_' + kind.upper(), f'{kind}:{obj.pk}', before, snapshot(obj, CONFIG_FIELDS[kind]), 'Modification du référentiel CNE-ITP.')
    return obj


@transaction.atomic
def validate_mapping(user, kind, pk, decision_reference, sc_id=None, gt_id=None):
    if not can_manage_organisation(user):
        raise PermissionDenied('Une habilitation de gestion Phoenix est nécessaire.')
    if kind not in ('ctm', 'wg') or not decision_reference.strip():
        raise ValidationError('Préciser la correspondance et sa décision.')
    model = CorrespondanceStructure if kind == 'ctm' else CorrespondanceGroupe
    try:
        obj = model.objects.select_for_update().get(pk=pk)
    except model.DoesNotExist as error:
        raise ValidationError('La correspondance demandée est introuvable.') from error
    before = snapshot(obj, ['status', 'sc', 'decision_reference'])
    if obj.status != 'PROPOSED':
        raise ValidationError('La décision de cette correspondance a déjà été enregistrée.')
    if sc_id:
        try:
            obj.sc = Organe.objects.get(pk=sc_id, version=obj.version, type='SC')
        except Organe.DoesNotExist as error:
            raise ValidationError('La SC cible est introuvable dans cette organisation.') from error
    if kind == 'wg' and gt_id:
        try:
            obj.gt = GroupeCible.objects.get(pk=gt_id, sc__version=obj.version)
        except GroupeCible.DoesNotExist as error:
            raise ValidationError('Le GT cible est introuvable dans cette organisation.') from error
        if not obj.sc_id:
            obj.sc = obj.gt.sc
    if not obj.sc_id or obj.sc.status not in ('VALIDATED', 'ACTIVE'):
        raise ValidationError('La SC cible doit être confirmée.')
    if kind == 'wg' and (not obj.gt_id or obj.gt.status not in ('VALIDATED', 'ACTIVE')):
        raise ValidationError('Le catalogue doit fournir le GT cible confirmé.')
    obj.status = 'VALIDATED'
    obj.decision_reference = decision_reference.strip()
    obj.updated_by = user
    obj.save()
    journal(user, obj.version, 'VALIDATE_MAPPING', f'{kind}:{obj.pk}', before, snapshot(obj, ['status', 'sc', 'decision_reference']), decision_reference)
    return obj


def readiness(version):
    issues = []
    for field, label in (('activation_reference', 'Décision de mise en service'), ('gt_catalogue_reference', 'Catalogue GT'),
                         ('permissions_reference', 'Matrice des habilitations'), ('circuit_reference', 'Circuit approuvé')):
        if not getattr(version, field).strip():
            issues.append(label + ' : référence manquante.')
    if not GroupeCible.objects.filter(sc__version=version, sc__status__in=['VALIDATED', 'ACTIVE'], status__in=['VALIDATED', 'ACTIVE']).exists():
        issues.append('Aucun GT confirmé avec une SC confirmée.')
    today = timezone.localdate()
    mandates = MandatOrganisation.objects.filter(status='ACTIVE', start_date__lte=today, expert__status='ACTIVE', expert__user__is_active=True).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)).filter(Q(poste__organe__version=version) | Q(groupe__sc__version=version))
    if not mandates.exists():
        issues.append('Aucun mandat nommé et en cours.')
    if not HabilitationAction.objects.filter(mandat__in=mandates, enabled=True, action='document.creer', start_date__lte=today).exists():
        issues.append('Aucune habilitation de création de dossier.')
    circuits = list(version.circuits.filter(status='VALIDATED', decision_reference=version.circuit_reference))
    if not circuits:
        issues.append('Aucun circuit validé correspondant à la référence approuvée.')
    groups = list(GroupeCible.objects.filter(sc__version=version, sc__status__in=['VALIDATED', 'ACTIVE'], status__in=['VALIDATED', 'ACTIVE']))
    candidates = list(mandates.select_related('expert__user', 'poste__organe', 'groupe__sc'))
    grants = list(HabilitationAction.objects.filter(mandat__in=mandates, enabled=True, start_date__lte=today).filter(Q(end_date__isnull=True) | Q(end_date__gte=today)).select_related('delegated_from__mandat__expert__user', 'perimeter'))
    for circuit in circuits:
        for group in groups:
            for rule in circuit.configuration['transitions']:
                eligible = set()
                capacity = {'document.homologuer':'HOMOLOGATION', 'document.publier':'PUBLICATION'}.get(rule['action'], 'ORGANISATION')
                for candidate in candidates:
                    target = candidate.poste if candidate.poste_id else candidate.groupe
                    organ = candidate.poste.organe if candidate.poste_id else candidate.groupe.sc
                    kind = organ.type if candidate.poste_id else 'GT'
                    if target.status not in ('VALIDATED', 'ACTIVE') or organ.status not in ('VALIDATED', 'ACTIVE') or candidate.capacity != capacity or kind not in rule['organe_types']:
                        continue
                    if candidate.groupe_id and candidate.groupe_id != group.pk:
                        continue
                    if kind == 'SC' and organ.pk != group.sc_id and not rule.get('allow_contributors'):
                        continue
                    if rule.get('categories') and (not candidate.poste_id or candidate.poste.category not in rule['categories']):
                        continue
                    for grant in grants:
                        if grant.mandat_id != candidate.pk or grant.action != rule['action'] or not grant.decision_reference:
                            continue
                        if grant.perimeter.type == 'SC' and grant.perimeter_id != group.sc_id:
                            continue
                        if grant.perimeter.type not in ('SC', 'ST', 'COPIL'):
                            continue
                        if grant.delegated_from_id:
                            source = grant.delegated_from
                            origin = source.mandat
                            if not source.enabled or source.start_date > today or (source.end_date and source.end_date < today) or origin.status != 'ACTIVE' or not origin.start_date or origin.start_date > today or (origin.end_date and origin.end_date < today) or origin.expert.status != 'ACTIVE' or not origin.expert.user.is_active:
                                continue
                        eligible.add(candidate.expert_id)
                if len(eligible) < rule['quorum']:
                    issues.append(f'{group.code} · {rule["label"]} : {len(eligible)} personne(s) habilitée(s), quorum {rule["quorum"]}.')
    return issues


@transaction.atomic
def activate(user, version, references):
    if not can_activate_organisation(user):
        raise PermissionDenied('Une habilitation de mise en service Phoenix est nécessaire.')
    version = OrganisationVersion.objects.select_for_update().get(pk=version.pk)
    if version.status not in ('PROPOSED', 'VALIDATED', 'SUSPENDED'):
        raise ValidationError('Cette édition ne peut pas être mise en service.')
    before = {'status': version.status}
    for name in ('activation_reference', 'gt_catalogue_reference', 'permissions_reference', 'circuit_reference'):
        setattr(version, name, str(references.get(name, '')).strip())
    issues = readiness(version)
    if issues:
        raise ValidationError(issues)
    version.status = 'ACTIVE'
    version.activated_at = timezone.now()
    version.updated_by = user
    version.save()
    journal(user, version, 'ACTIVATE', version.code, before, {**references, 'status': 'ACTIVE'}, version.activation_reference)
    return version


@transaction.atomic
def suspend(user, version, reason):
    if not can_activate_organisation(user):
        raise PermissionDenied('Une habilitation de mise en service Phoenix est nécessaire.')
    if not reason.strip():
        raise ValidationError('Le motif de suspension doit être renseigné.')
    version = OrganisationVersion.objects.select_for_update().get(pk=version.pk)
    if version.status != 'ACTIVE':
        raise ValidationError('Cette organisation n’est pas en vigueur.')
    version.status = 'SUSPENDED'
    version.updated_by = user
    version.save()
    journal(user, version, 'SUSPEND', version.code, {'status': 'ACTIVE'}, {'status': 'SUSPENDED'}, reason)
    return version
