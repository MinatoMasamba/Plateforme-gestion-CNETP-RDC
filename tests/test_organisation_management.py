import pytest
from django.core.exceptions import ValidationError

from apps.governance.models import (
    OrganisationVersion, Organe, PosteOrganisation, PilotageMembreship, ComitePilotage,
    JournalMigration, NormeCadrage, CTCProcessus,
)
from apps.governance.organisation_permissions import can_manage_organisation


@pytest.fixture
def president(expert_factory):
    expert = expert_factory()
    membership = PilotageMembreship.objects.create(
        expert=expert, comite=ComitePilotage.objects.create(name='COPIL'), role='PRESIDENT',
    )
    return expert, membership


@pytest.fixture
def organisation():
    version = OrganisationVersion.objects.create(code='phoenix-2026-10', name='CNE-ITP', source_document='Note de cadrage')
    copil = Organe.objects.create(version=version, type='COPIL', code='COPIL', name='Comité de Pilotage', source_reference='Note de cadrage')
    PosteOrganisation.objects.create(organe=copil, code='P-1', category='PRESIDENCY', title='Président', source_reference='Note de cadrage')
    return version, copil


@pytest.mark.django_db
def test_president_can_edit_saved_organisation_and_every_change_is_audited(client, president, organisation):
    expert, membership = president
    version, copil = organisation
    assert not expert.user.has_perm('governance.manage_phoenix')
    client.force_login(expert.user)
    response = client.get('/pilotage/organisation/')
    assert response.status_code == 200 and response.context['can_manage']
    assert response.context['copil_post_count'] == 1  # Aucun effectif statique de 22.
    assert 'Organisation CNE-ITP' in response.content.decode()
    edit = f'/pilotage/organisation/configuration/organe/{copil.pk}/'
    assert client.get(edit).status_code == 200
    response = client.post(edit, {
        'code': copil.code, 'name': 'Comité de Pilotage actualisé', 'official_name': '', 'type': 'COPIL',
        'domain': 'Pilotage institutionnel', 'composition': 'Président : 1\nMembres : 5',
        'status': 'PROPOSED', 'source_reference': 'Note de cadrage complétée',
    })
    assert response.status_code == 302, response.content.decode()
    copil.refresh_from_db()
    assert copil.name == 'Comité de Pilotage actualisé'
    assert copil.composition == {'categories': ['Président', 'Membres'], 'effectifs': {'Président': 1, 'Membres': 5}}
    entry = JournalMigration.objects.get(operation='CONFIGURE_ORGANE')
    assert entry.actor_id == expert.user_id and entry.before['name'] == 'Comité de Pilotage'
    assert entry.after['name'] == copil.name
    assert 'Comité de Pilotage actualisé' in client.get('/pilotage/organisation/gestion/').content.decode()
    membership.role = 'VICE_PRESIDENT'
    membership.save(update_fields=['role'])
    assert client.get(edit).status_code == 403
    assert client.post(edit, {'name': 'Modification interdite'}).status_code == 403
    copil.refresh_from_db()
    assert copil.name == 'Comité de Pilotage actualisé'


@pytest.mark.django_db
def test_president_configuration_api_creates_real_organs_and_notes(client, president, organisation):
    expert, _ = president
    version, _ = organisation
    client.force_login(expert.user)
    response = client.post('/api/v2/organisation/configuration/organe/', {
        'code': 'SC-TEST', 'name': 'Sous-commission de recette', 'type': 'SC',
        'domain': 'Domaine de recette', 'source_reference': 'Référence de recette', 'status': 'PROPOSED',
    }, content_type='application/json')
    assert response.status_code == 201, response.content.decode()
    sc = Organe.objects.get(pk=response.json()['id'])
    assert sc.version_id == version.pk
    assert client.get('/pilotage/organisation/').context['sc_list'] == [sc]
    assert client.post('/pilotage/organisation/', {'operation': 'note', 'reason': 'Décision de préparation de recette'}).status_code == 302
    assert JournalMigration.objects.filter(operation='PREPARATION_NOTE', actor=expert.user, reason='Décision de préparation de recette').exists()
    # Le journal se complète par de nouvelles entrées, sans réécrire ses traces.
    entry = JournalMigration.objects.first()
    with pytest.raises(ValidationError):
        entry.save()


@pytest.mark.django_db
def test_president_management_does_not_allow_cross_version_edits_or_suspended_profiles(client, president, organisation):
    expert, _ = president
    other = OrganisationVersion.objects.create(code='other', name='Autre édition', source_document='Autre note')
    organ = Organe.objects.create(version=other, type='SC', code='SC-OTHER', name='Autre SC', source_reference='Autre note')
    client.force_login(expert.user)
    assert client.get(f'/pilotage/organisation/configuration/organe/{organ.pk}/').status_code == 404
    expert.status = 'SUSPENDED'
    expert.save(update_fields=['status'])
    assert not can_manage_organisation(expert.user)
    assert client.get('/pilotage/organisation/configuration/organe/').status_code == 403


@pytest.mark.django_db
def test_parent_cycles_are_rejected_without_saving(organisation):
    version, copil = organisation
    child = Organe.objects.create(version=version, type='SC', code='SC', name='Sous-commission', parent=copil, source_reference='Note')
    copil.parent = child
    with pytest.raises(ValidationError):
        copil.save()
    copil.refresh_from_db()
    assert copil.parent_id is None


@pytest.mark.django_db
def test_directoire_lists_real_cadrage_and_signed_ctc_data_without_mission_cards(client, president, norme_factory):
    expert, _ = president
    proposed = NormeCadrage.objects.create(norme=norme_factory(reference_number='CADRAGE-REEL'))
    final = NormeCadrage.objects.create(norme=norme_factory(reference_number='SIGNATURE-REELLE'), current_stage='FINAL_VALIDATION')
    incoming = CTCProcessus.objects.create(norme=norme_factory(reference_number='CTC-TRANSMIS'), current_stage='SIGNED_OUT')
    CTCProcessus.objects.create(norme=norme_factory(reference_number='CTC-PAS-TRANSMIS'), current_stage='RECEPTION')
    client.force_login(expert.user)
    response = client.get('/pilotage/bureau-directoire/')
    assert response.status_code == 200
    html = response.content.decode()
    assert 'crown' not in html and 'Autorité d’impulsion' not in html and 'Autorité d\'impulsion' not in html
    assert 'CADRAGE-REEL' in html and 'SIGNATURE-REELLE' in html and 'CTC-TRANSMIS' in html
    assert 'CTC-PAS-TRANSMIS' not in html
    assert [item['cadrage'].pk for item in response.context['postes'][0]['cadrage_groups'][0]['items']] == [proposed.pk]
    assert [item['cadrage'].pk for item in response.context['postes'][0]['cadrage_groups'][1]['items']] == [final.pk]
    assert [process.pk for process in response.context['pending_reception_president']] == [incoming.pk]
    incoming.refresh_from_db()
    assert incoming.received_by_president_id is None
