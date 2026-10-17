import pytest
from datetime import timedelta
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.governance.models import (
    CTM, WG, OrganisationVersion, PosteOrganisation, Organe, GroupeCible,
    MandatOrganisation, HabilitationAction, RattachementDocumentaire,
    CorrespondanceGroupe, CorrespondanceStructure, JournalMigration,
    ComitePilotage, PilotageMembreship,
)
from apps.governance.phoenix_services import seed_phoenix, propose_mapping, has_organisation_action


@pytest.fixture
def phoenix(ctm_factory, wg_factory):
    for number in range(1, 9):
        ctm = ctm_factory(number=number)
        for wg_number in range(1, 4):
            wg_factory(ctm=ctm, number=wg_number)
    before = list(WG.objects.order_by('pk').values())
    version, missing = seed_phoenix()
    assert not missing
    assert list(WG.objects.order_by('pk').values()) == before
    return version


@pytest.mark.django_db
def test_seed_preserves_groups_and_prepares_exact_catalogue(phoenix):
    assert CTM.objects.count() == 8 and WG.objects.count() == 24
    assert phoenix.status == 'PROPOSED'
    assert PosteOrganisation.objects.filter(organe__type='COPIL').count() == 22
    assert PosteOrganisation.objects.exclude(organe__type='COPIL').count() == 24
    assert list(PosteOrganisation.objects.filter(organe__type='COPIL').values_list('category', flat=True)).count('INVITED') == 3
    assert Organe.objects.filter(type='ST_POLE').count() == 5
    assert Organe.objects.filter(type='SC').count() == 7
    assert PosteOrganisation.objects.filter(category='UNKNOWN', title='').count() == 15
    assert phoenix.ctm_mappings.count() == 15
    assert phoenix.wg_mappings.count() == 24
    assert not GroupeCible.objects.exists()
    assert not MandatOrganisation.objects.exists()
    assert not HabilitationAction.objects.exists()
    assert not RattachementDocumentaire.objects.exists()
    seed_phoenix()
    assert OrganisationVersion.objects.count() == 1
    assert JournalMigration.objects.count() == 1


@pytest.mark.django_db
def test_mapping_changes_are_explicit_audited_and_do_not_reassign(phoenix, expert_factory, norme_factory):
    expert = expert_factory()
    mapping = phoenix.wg_mappings.first()
    norme = norme_factory(ctm=mapping.wg.ctm, wg=mapping.wg)
    wg_before = list(WG.objects.order_by('pk').values())
    with pytest.raises(PermissionDenied):
        propose_mapping(expert.user, 'wg', mapping.pk, None, 'Essai', '')
    expert.user.user_permissions.add(Permission.objects.get(codename='prepare_phoenix'))
    # Reload the user to clear Django's cached permissions.
    expert.user.refresh_from_db()
    del expert.user._perm_cache
    del expert.user._user_perm_cache
    del expert.user._group_perm_cache
    sc = phoenix.organes.filter(type='SC').first()
    propose_mapping(expert.user, 'wg', mapping.pk, sc.pk, 'Périmètre ajusté', 'Correspondance à examiner')
    mapping.refresh_from_db()
    assert mapping.sc_id == sc.pk and mapping.status == 'PROPOSED'
    entry = JournalMigration.objects.get(operation='PROPOSE_MAPPING')
    assert entry.actor_id == expert.user_id and entry.after['domain'] == 'Périmètre ajusté'
    seed_phoenix()
    assert phoenix.wg_mappings.count() == 24
    assert list(WG.objects.order_by('pk').values()) == wg_before
    norme.refresh_from_db()
    assert norme.wg_id == mapping.wg_id and norme.ctm_id == mapping.wg.ctm_id


@pytest.mark.django_db
def test_activation_requires_official_references(phoenix):
    phoenix.status = 'ACTIVE'
    with pytest.raises(ValidationError):
        phoenix.save()
    assert OrganisationVersion.objects.get(pk=phoenix.pk).status == 'PROPOSED'


@pytest.mark.django_db
def test_invalid_cross_version_or_unconfirmed_mapping_is_rejected(phoenix):
    other = OrganisationVersion.objects.create(code='other', name='Autre', source_document='Acte')
    sc = Organe.objects.create(version=other, type='SC', code='SC-OTHER', name='Autre SC', source_reference='Acte')
    mapping = phoenix.ctm_mappings.first()
    mapping.sc = sc
    with pytest.raises(ValidationError):
        mapping.save()
    mapping.refresh_from_db()
    mapping.status = 'VALIDATED'
    with pytest.raises(ValidationError):
        mapping.save()


@pytest.mark.django_db
@pytest.mark.parametrize('category', ['MEMBER', 'INVITED', 'APPOINT'])
def test_category_alone_never_grants_document_action(phoenix, expert_factory, norme_factory, category):
    expert = expert_factory()
    post = PosteOrganisation.objects.filter(category=category).first()
    mandate = MandatOrganisation.objects.create(expert=expert, poste=post)
    assert not has_organisation_action(expert.user, mandate, 'document.publier', norme_factory(ctm=CTM.objects.first(), wg=WG.objects.first()))


@pytest.mark.django_db
def test_grants_require_active_version_dates_and_explicit_document_binding(phoenix, expert_factory, norme_factory):
    expert = expert_factory()
    post = PosteOrganisation.objects.filter(category='PRESIDENCY').first()
    sc = phoenix.organes.filter(type='SC').first()
    today = timezone.localdate()
    mandate = MandatOrganisation.objects.create(expert=expert, poste=post, function=post.title,
                                               appointment_reference='Nomination test', start_date=today, status='ACTIVE')
    grant = HabilitationAction.objects.create(mandat=mandate, action='document.consulter', perimeter=sc,
                                             decision_reference='Décision test', start_date=today, enabled=True)
    norme = norme_factory(ctm=CTM.objects.first(), wg=WG.objects.first())
    assert not has_organisation_action(expert.user, mandate, 'document.consulter', norme)
    for field in ('activation_reference', 'gt_catalogue_reference', 'permissions_reference', 'circuit_reference'):
        setattr(phoenix, field, 'Acte de test')
    phoenix.status = 'ACTIVE'
    phoenix.save()
    mandate = MandatOrganisation.objects.get(pk=mandate.pk)
    assert not has_organisation_action(expert.user, mandate, 'document.consulter', norme)
    RattachementDocumentaire.objects.create(norme=norme, version=phoenix, sc=sc, role='OWNER', status='VALIDATED', decision_reference='Rattachement test')
    assert has_organisation_action(expert.user, mandate, 'document.consulter', norme)
    grant.start_date = today + timedelta(days=1)
    grant.save()
    assert not has_organisation_action(expert.user, mandate, 'document.consulter', norme)


@pytest.mark.django_db
def test_portal_is_visible_to_supervisor_but_edits_need_specific_permission(client, phoenix, expert_factory):
    expert = expert_factory()
    membership = PilotageMembreship.objects.create(expert=expert, comite=ComitePilotage.objects.create(name='Pilotage'), role='VICE_PRESIDENT')
    client.force_login(expert.user)
    response = client.get('/pilotage/organisation/')
    assert response.status_code == 200
    assert response.context['legacy_group_count'] == 24
    mapping = CorrespondanceStructure.objects.first()
    assert client.post(f'/pilotage/organisation/correspondance/ctm/{mapping.pk}/', {'domain': 'Pirate'}).status_code == 403
    membership.role = 'PARTENAIRE_SOC_CIV'
    membership.save()
    assert client.get('/pilotage/organisation/').status_code == 403
