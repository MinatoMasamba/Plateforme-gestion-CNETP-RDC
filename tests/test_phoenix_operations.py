import copy
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.utils import timezone

from apps.core.models import User
from apps.governance.models import (OrganisationVersion, Organe, PosteOrganisation, GroupeCible, MandatOrganisation,
    HabilitationAction, CircuitOrganisation, DossierPhoenix, JournalMigration, RattachementDocumentaire, DecisionPhoenix, WG)
from apps.governance.phoenix_operations import configure, activate, suspend, readiness
from apps.governance.phoenix_rules import proposed_circuit
from apps.governance.phoenix_workflow import (create_dossier, save_version, attach_piece, decide, selected_mandate,
    accessible_dossiers, save_inquiry, set_document_lock, plan_meeting, record_presence, PhoenixConflict)
from apps.governance.phoenix_services import has_organisation_action
from apps.norms.models import Norme, NormeVersion


@pytest.fixture
def operational(expert_factory, user_factory, monkeypatch, tmp_path):
    from apps.governance.models import PiecePhoenix
    monkeypatch.setattr(PiecePhoenix._meta.get_field('file'), 'storage', FileSystemStorage(location=tmp_path))
    admin = user_factory(username='phx-admin', email='phx-admin@example.test', is_staff=True, is_superuser=True)
    version = OrganisationVersion.objects.create(code='phoenix-2026-10', name='Phoenix de recette', source_document='Décisions de recette')
    sc = Organe.objects.create(version=version, type='SC', code='SC-T', name='SC de recette', official_name='SC de recette', source_reference='Acte SC de recette', status='VALIDATED')
    copil = Organe.objects.create(version=version, type='COPIL', code='COPIL', name='COPIL de recette', official_name='COPIL de recette', status='VALIDATED', source_reference='Acte COPIL de recette')
    st = Organe.objects.create(version=version, type='ST', code='ST', name='ST de recette', official_name='ST de recette', status='VALIDATED', source_reference='Acte ST de recette')
    gt = GroupeCible.objects.create(sc=sc, code='GT-TEST', name='GT de recette', activity='PRODUCTION', source_reference='Catalogue de recette', status='VALIDATED')
    writer = expert_factory(user=user_factory(username='phx-writer', email='phx-writer@example.test'))
    reviewer = expert_factory(user=user_factory(username='phx-reviewer', email='phx-reviewer@example.test'))
    reviewer2 = expert_factory(user=user_factory(username='phx-reviewer2', email='phx-reviewer2@example.test'))
    today = timezone.localdate()
    def mandate(expert, groupe=None, organe=None, suffix='1'):
        post = PosteOrganisation.objects.create(organe=organe, code='POST-'+suffix, category='MEMBER', title='Membre confirmé de recette', source_reference='Acte de recette', status='VALIDATED') if organe else None
        return MandatOrganisation.objects.create(expert=expert, groupe=groupe, poste=post, function='Fonction de recette', appointment_reference='Nomination de recette', start_date=today, status='ACTIVE')
    writing = mandate(writer, groupe=gt)
    review = mandate(reviewer, organe=sc)
    review2 = mandate(reviewer2, organe=sc, suffix='2')
    coordination = mandate(reviewer, organe=st)
    steering = mandate(reviewer, organe=copil)
    homologation = MandatOrganisation.objects.create(expert=reviewer, poste=steering.poste, function='Homologation de recette', capacity='HOMOLOGATION', appointment_reference='Mandat d’homologation de recette', start_date=today, status='ACTIVE')
    publication = MandatOrganisation.objects.create(expert=reviewer, poste=steering.poste, function='Publication de recette', capacity='PUBLICATION', appointment_reference='Mandat de publication de recette', start_date=today, status='ACTIVE')
    def grant(mandat, action, perimeter=sc):
        return HabilitationAction.objects.create(mandat=mandat, action=action, perimeter=perimeter, decision_reference='Pouvoir de recette', start_date=today, enabled=True)
    for mandat in (writing, review, review2, coordination, steering, homologation, publication):
        grant(mandat, 'document.consulter')
        grant(mandat, 'document.joindre')
    for action in ('document.creer', 'document.editer', 'gt.soumettre', 'document.verrouiller', 'reunion.planifier'):
        grant(writing, action)
    grant(review, 'sc.examiner')
    grant(review2, 'sc.examiner')
    grant(coordination, 'st.transmettre')
    grant(coordination, 'st.enquete')
    for action in ('copil.valider', 'document.adopter', 'document.homologuer', 'document.publier'):
        grant(steering, action)
    grant(homologation, 'document.homologuer')
    grant(publication, 'document.publier')
    configuration = proposed_circuit()
    configuration['transitions'][1]['quorum'] = 2
    configuration['transitions'][1]['required_evidence'] = ['avis_sc']
    circuit = CircuitOrganisation.objects.create(version=version, code='recette-v1', name='Circuit de recette', configuration=configuration, decision_reference='Circuit de recette approuvé', status='VALIDATED')
    references = {'activation_reference': 'Activation de recette', 'gt_catalogue_reference': 'Catalogue de recette', 'permissions_reference': 'Pouvoirs de recette', 'circuit_reference': circuit.decision_reference}
    activate(admin, version, references)
    version.refresh_from_db()
    dossier = create_dossier(writer.user, writing, circuit, gt, 'PHX-RECETTE', 'Projet de recette', 'Texte initial', origin={'ip':'192.0.2.8', 'channel':'Recette'})
    return SimpleNamespace(admin=admin, version=version, sc=sc, gt=gt, writer=writer, reviewer=reviewer, reviewer2=reviewer2,
        writing=writing, review=review, review2=review2, coordination=coordination, steering=steering, homologation=homologation, publication=publication, circuit=circuit, dossier=dossier, grant=grant, references=references)


def perform(state, mandate, transition, key=None):
    state.dossier.refresh_from_db()
    return decide(mandate.expert.user, mandate, state.dossier.pk, state.dossier.revision, transition,
                  'Décision de recette', 'Avis motivé de recette', key or uuid4().hex, {'ip':'192.0.2.9', 'channel':'Recette'})


@pytest.mark.django_db
def test_new_dossier_has_real_sc_gt_without_fake_ctm_and_v1_cannot_read_it(operational, client):
    state = operational
    assert not state.dossier.norme.ctm_id and not state.dossier.norme.wg_id
    assert not Norme.objects.filter(pk=state.dossier.norme_id).exists()
    assert Norme.all_objects.filter(pk=state.dossier.norme_id).exists()
    assert not NormeVersion.objects.filter(pk=state.dossier.document_version_id).exists()
    client.force_login(state.writer.user)
    assert client.get(f'/api/v1/norms/{state.dossier.norme_id}/').status_code == 404
    assert client.get(f'/api/v1/norm-versions/{state.dossier.document_version_id}/').status_code == 404
    response = client.get(f'/api/v2/organisation/dossiers/{state.dossier.pk}/')
    assert response.status_code == 200 and response.json()['versions'][0]['content'] == 'Texte initial'
    assert client.get(f'/phoenix/dossiers/{state.dossier.pk}/').status_code == 200


@pytest.mark.django_db
def test_workflow_checks_evidence_quorum_and_idempotence(operational):
    s = operational
    key = uuid4().hex
    first = perform(s, s.writing, 'soumettre', key)
    same = perform(s, s.writing, 'soumettre', key)
    assert first.pk == same.pk and DecisionPhoenix.objects.count() == 1
    with pytest.raises(ValidationError):
        perform(s, s.review, 'examiner')
    s.dossier.refresh_from_db()
    attach_piece(s.reviewer.user, s.review, s.dossier.pk, s.dossier.revision, 'avis_sc', 'Avis de recette', content='Avis technique motivé')
    vote = perform(s, s.review, 'examiner')
    assert not vote.completed
    s.dossier.refresh_from_db()
    assert s.dossier.state == 'SC'
    with pytest.raises(PhoenixConflict):
        perform(s, s.review, 'examiner')
    assert perform(s, s.review2, 'examiner').completed
    s.dossier.refresh_from_db()
    assert s.dossier.state == 'ST'
    assert s.dossier.decisions.count() == 3


@pytest.mark.django_db
def test_same_person_with_two_mandates_cannot_vote_twice(operational):
    s = operational
    perform(s, s.writing, 'soumettre')
    s.dossier.refresh_from_db()
    attach_piece(s.reviewer.user, s.review, s.dossier.pk, s.dossier.revision, 'avis_sc', 'Avis de recette', content='Avis')
    perform(s, s.review, 'examiner')
    post = PosteOrganisation.objects.create(organe=s.sc, code='POST-DOUBLE', category='MEMBER', title='Autre fonction de recette', source_reference='Acte de recette', status='VALIDATED')
    other = MandatOrganisation.objects.create(expert=s.reviewer, poste=post, status='ACTIVE', start_date=timezone.localdate(), function=post.title, appointment_reference='Nomination de recette')
    s.grant(other, 'sc.examiner')
    with pytest.raises(PhoenixConflict):
        perform(s, other, 'examiner')


@pytest.mark.django_db
def test_adoption_homologation_and_publication_have_distinct_evidence(operational):
    s = operational
    perform(s, s.writing, 'soumettre')
    s.dossier.refresh_from_db()
    attach_piece(s.reviewer.user, s.review, s.dossier.pk, s.dossier.revision, 'avis_sc', 'Avis de recette', content='Avis')
    perform(s, s.review, 'examiner')
    perform(s, s.review2, 'examiner')
    perform(s, s.coordination, 'transmettre')
    perform(s, s.steering, 'valider')
    perform(s, s.steering, 'adopter')
    with pytest.raises(PermissionDenied):
        perform(s, s.steering, 'homologuer')
    perform(s, s.homologation, 'homologuer')
    with pytest.raises(ValidationError):
        perform(s, s.publication, 'publier')
    s.dossier.refresh_from_db()
    attach_piece(s.reviewer.user, s.steering, s.dossier.pk, s.dossier.revision, 'publication_jo', 'JO de recette', content='Publication officielle de recette')
    assert perform(s, s.publication, 'publier').completed
    s.dossier.norme.refresh_from_db()
    assert s.dossier.norme.status == 'PUBLISHED' and s.dossier.norme.is_public
    assert not Norme.objects.exists()


@pytest.mark.django_db
def test_stale_edit_is_atomic_and_keeps_the_previous_version(operational):
    s = operational
    old = s.dossier.document_version_id
    save_version(s.writer.user, s.writing, s.dossier.pk, 0, 'Texte nouveau', 'Modification de recette')
    with pytest.raises(PhoenixConflict):
        save_version(s.writer.user, s.writing, s.dossier.pk, 0, 'Texte obsolète', 'Mauvaise révision')
    assert NormeVersion.all_objects.filter(norme=s.dossier.norme).count() == 2
    assert NormeVersion.all_objects.get(pk=old).content == 'Texte initial'
    journal = JournalMigration.objects.get(operation='EDIT_DOCUMENT')
    assert journal.mandate_id == s.writing.pk and journal.actor_role


@pytest.mark.django_db
def test_no_implicit_access_foreign_mandate_and_suspension_keeps_read_only(operational, expert_factory, user_factory, client):
    s = operational
    outsider = expert_factory(user=user_factory(username='outside', email='outside@example.test', is_ctc_staff=True))
    client.force_login(outsider.user)
    assert client.get(f'/api/v2/organisation/dossiers/{s.dossier.pk}/').status_code == 404
    assert client.get(f'/phoenix/dossiers/{s.dossier.pk}/').status_code == 404
    assert client.get('/phoenix/export/').content.decode().count('PHX-RECETTE') == 0
    with pytest.raises(PermissionDenied):
        decide(outsider.user, s.writing, s.dossier.pk, 0, 'soumettre', 'Fausse décision', 'Faux mandat', 'foreign')
    suspend(s.admin, s.version, 'Suspension de recette')
    assert accessible_dossiers(s.writer.user).filter(pk=s.dossier.pk).exists()
    with pytest.raises(PermissionDenied):
        perform(s, s.writing, 'soumettre')
    assert DecisionPhoenix.objects.count() == 0


@pytest.mark.django_db
def test_api_and_web_reject_forged_roles_and_stale_revision(operational, client):
    s = operational
    client.force_login(s.writer.user)
    payload = {'operation':'decision','mandate':s.writing.pk,'revision':0,'transition':'examiner','decision_reference':'Faux avis','reason':'Faux rôle','request_key':'bad', 'allowed_actions':['sc.examiner']}
    assert client.post(f'/api/v2/organisation/dossiers/{s.dossier.pk}/operation/', payload, content_type='application/json').status_code == 409
    perform(s, s.writing, 'soumettre')
    payload.update(operation='edit', content='Édition trop tardive', summary='Erreur de révision')
    assert client.post(f'/api/v2/organisation/dossiers/{s.dossier.pk}/operation/', payload, content_type='application/json').status_code == 400
    assert client.post('/api/v2/organisation/mise-en-service/', s.references, content_type='application/json').status_code == 403


@pytest.mark.django_db
def test_management_forms_api_and_exports_work_without_moving_old_groups(operational, client, wg_factory):
    s = operational
    wg = wg_factory()
    before = list(WG.objects.values())
    client.force_login(s.admin)
    for path in ('/pilotage/organisation/gestion/', '/pilotage/organisation/configuration/gt/', '/pilotage/organisation/configuration/mandat/',
                 '/pilotage/organisation/configuration/habilitation/', '/pilotage/organisation/configuration/circuit/', '/pilotage/organisation/mise-en-service/'):
        assert client.get(path).status_code == 200, path
    response = client.post('/api/v2/organisation/configuration/gt/', {'sc':s.sc.pk,'code':'GT-SECOND','name':'GT officiel de recette', 'activity':'WATCH','source_reference':'Catalogue de recette', 'status':'VALIDATED'}, content_type='application/json')
    assert response.status_code == 201, response.content
    assert list(WG.objects.values()) == before
    assert client.get(f'/phoenix/dossiers/{s.dossier.pk}/export/').status_code == 200
    assert client.get('/phoenix/').status_code == 200
    assert client.get('/phoenix/', {'from':'2026-99-99'}).status_code == 200


@pytest.mark.django_db
def test_delegation_revocation_and_suspended_expert_remove_action(operational):
    s = operational
    today = timezone.localdate()
    source = s.writing.habilitations.get(action='document.joindre')
    delegation = HabilitationAction.objects.create(mandat=s.review2, action=source.action, perimeter=s.sc, decision_reference='Délégation de recette', start_date=today,
                                                  delegated_from=source, enabled=True)
    s.review2.habilitations.filter(action='document.joindre', delegated_from__isnull=True).update(enabled=False)
    assert has_organisation_action(s.reviewer2.user, s.review2, 'document.joindre', s.dossier.norme)
    source.enabled = False
    source.save()
    assert not has_organisation_action(s.reviewer2.user, s.review2, 'document.joindre', s.dossier.norme)
    s.writer.status = 'SUSPENDED'
    s.writer.save(update_fields=['status'])
    assert not has_organisation_action(s.writer.user, s.writing, 'gt.soumettre', s.dossier.norme)


@pytest.mark.django_db
def test_lock_meetings_and_private_piece_access(operational, client):
    s = operational
    set_document_lock(s.writer.user, s.writing, s.dossier.pk, 0, True)
    s.dossier.refresh_from_db()
    with pytest.raises(PhoenixConflict):
        attach_piece(s.reviewer.user, s.review, s.dossier.pk, s.dossier.revision, 'avis', 'Pièce', content='Texte')
    set_document_lock(s.writer.user, s.writing, s.dossier.pk, s.dossier.revision, False)
    s.dossier.refresh_from_db()
    meeting = plan_meeting(s.writer.user, s.writing, s.dossier.pk, s.dossier.revision, 'Réunion de recette', 'Ordre du jour', timezone.now()+timedelta(days=1), 'Salle de recette', [s.writing.pk,s.review.pk])
    s.dossier.refresh_from_db()
    participant = meeting.participants.first()
    record_presence(s.writer.user, s.writing, s.dossier.pk, s.dossier.revision, participant.pk, 'PRESENT')
    participant.refresh_from_db()
    assert participant.presence == 'PRESENT'
    s.dossier.refresh_from_db()
    piece = attach_piece(s.writer.user, s.writing, s.dossier.pk, s.dossier.revision, 'annexe', 'Annexe de recette', upload=SimpleUploadedFile('preuve.txt', b'preuve'))
    assert piece.sha256 and piece.file.storage.exists(piece.file.name)
    client.force_login(s.writer.user)
    assert client.get(f'/phoenix/pieces/{piece.pk}/').status_code == 200


@pytest.mark.django_db
def test_ai_returns_only_authorised_context_and_a_human_review_link(operational):
    from apps.ia_agent.tools.phoenix_tools import search_phoenix_dossiers, prepare_phoenix_decision
    s = operational
    results = search_phoenix_dossiers(SimpleNamespace(user=s.writer.user), 'recette')
    assert len(results) == 1 and results[0]['version_id'] == s.dossier.document_version_id
    outcome = prepare_phoenix_decision(SimpleNamespace(user=s.writer.user), s.dossier.pk, s.writing.pk, 'soumettre')
    assert outcome['decision_recorded'] is False and not DecisionPhoenix.objects.exists()


@pytest.mark.django_db
def test_immutable_circuit_mandate_and_binding_preserve_history(operational):
    s = operational
    s.circuit.configuration = copy.deepcopy(s.circuit.configuration)
    s.circuit.configuration['initial'] = 'SC'
    with pytest.raises(ValidationError):
        s.circuit.save()
    s.writing.expert = s.reviewer
    with pytest.raises(ValidationError):
        s.writing.save()
    binding = RattachementDocumentaire.objects.get(norme=s.dossier.norme)
    binding.decision_reference = 'Réécriture interdite'
    with pytest.raises(ValidationError):
        binding.save()


@pytest.mark.django_db
def test_activation_refuses_an_unstaffed_quorum(operational):
    s = operational
    suspend(s.admin, s.version, 'Préparation du quorum de recette')
    s.review2.habilitations.filter(action='sc.examiner').update(enabled=False)
    with pytest.raises(ValidationError, match='quorum 2'):
        activate(s.admin, s.version, s.references)
    s.version.refresh_from_db()
    assert s.version.status == 'SUSPENDED'


@pytest.mark.django_db
def test_notification_is_emitted_only_after_a_committed_transition(operational, django_capture_on_commit_callbacks):
    from apps.mobileapp.models import Notification
    s = operational
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        perform(s, s.writing, 'soumettre')
        assert Notification.objects.count() == 0
    assert len(callbacks) == 1
    assert Notification.objects.count() > 0
    count = Notification.objects.count()
    with pytest.raises(ValidationError), django_capture_on_commit_callbacks(execute=True):
        perform(s, s.review, 'examiner')
    assert Notification.objects.count() == count


@pytest.mark.django_db(transaction=True)
def test_concurrent_duplicate_has_only_one_committed_decision(operational):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections, OperationalError
    s = operational
    barrier = Barrier(2)
    key = uuid4().hex
    def worker():
        close_old_connections()
        try:
            user = User.objects.get(pk=s.writer.user_id)
            mandate = selected_mandate(user, s.writing.pk)
            barrier.wait(timeout=10)
            result = decide(user, mandate, s.dossier.pk, 0, 'soumettre', 'Décision concurrente de recette', 'Avis concurrent de recette', key)
            return result.pk
        except (PhoenixConflict, OperationalError):
            return None
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _:worker(), range(2)))
    assert s.dossier.decisions.count() <= 1
    # SQLite peut refuser deux écrivains simultanés ; la reprise avec la même clé est sûre.
    if not s.dossier.decisions.exists():
        decide(s.writer.user, s.writing, s.dossier.pk, 0, 'soumettre', 'Décision concurrente de recette', 'Avis concurrent de recette', key)
    assert s.dossier.decisions.count() == 1
    s.dossier.refresh_from_db()
    assert s.dossier.state == 'SC'
