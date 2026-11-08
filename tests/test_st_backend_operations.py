from datetime import timedelta
from types import SimpleNamespace
import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from apps.governance.models import CTCMembership, TechnicalCell, MandatOrganisation, OrganisationVersion
from apps.governance.st_operations_models import STRecord, STRecordRevision, STConfirmation
from apps.governance.st_operations import reset_legacy_access, nominate_batch, write_record, confirm_record, visible_records
from apps.governance.phoenix_runtime import active_st_mandate, current_organisation_version, st_posts
from web.ctc_views import get_ctc_context


@pytest.fixture
def admin_user(user_factory):
    return user_factory(username='st-admin', is_staff=True, is_superuser=True)


@pytest.fixture
def st_setup(admin_user, expert_factory, user_factory):
    reset_legacy_access(admin_user)
    def actor(number, name=None):
        user = user_factory(username=name or f'st-{number}', email=f'st-{number}@example.invalid')
        expert = expert_factory(user=user)
        nominate_batch(admin_user, [{'post_code': f'ST-V3-{number:02}', 'expert_id': expert.pk,
            'start_date': timezone.localdate().isoformat(), 'appointment_reference': 'Test communiqué'}], apply=True)
        return user
    return actor


def data(kind='PTN', reference='PTN-01', **extra):
    return {'kind': kind, 'reference': reference, 'title': 'Travail réel', 'content': 'Valeur documentée',
        'source_reference': 'Rapport source', **extra}


@pytest.mark.django_db
def test_reset_keeps_history_and_admin_access_but_no_ctc_role(admin_user, expert_factory):
    old = expert_factory()
    old.user.is_ctc_staff = True
    old.user.save()
    row = CTCMembership.objects.create(ctc=TechnicalCell.objects.create(), expert=old, role='COORDINATOR')
    previous = OrganisationVersion.objects.create(code='previous', name='Previous', source_document='Source')
    result = reset_legacy_access(admin_user)
    assert result['retired_memberships'] == 1
    assert CTCMembership.all_objects.filter(pk=row.pk).exists()
    assert not CTCMembership.objects.exists()
    assert not MandatOrganisation.objects.filter(status='ACTIVE').exists()
    assert st_posts().count() == 19
    assert current_organisation_version() == previous
    old.user.refresh_from_db()
    assert not old.user.is_ctc_staff
    assert get_ctc_context(old) is None
    assert admin_user.is_staff
    assert reset_legacy_access(admin_user)['already_configured']


@pytest.mark.django_db(transaction=True)
def test_nomination_is_admin_only_atomic_and_explicit(st_setup, admin_user, user_factory, expert_factory, mailoutbox):
    expert = expert_factory(user=user_factory(username='named', email='named@example.invalid'))
    item = {'post_code': 'ST-V3-12', 'email': expert.user.email,
        'start_date': timezone.localdate().isoformat(), 'appointment_reference': 'Communiqué 003'}
    with pytest.raises(PermissionDenied):
        nominate_batch(expert.user, [item], apply=True)
    assert not nominate_batch(admin_user, [item])[0]['applied']
    assert not MandatOrganisation.objects.exists()
    with pytest.raises(ValidationError):
        nominate_batch(admin_user, [item, {**item, 'post_code': 'UNKNOWN'}], apply=True)
    assert not MandatOrganisation.objects.exists()
    result = nominate_batch(admin_user, [item], apply=True)
    assert result[0]['applied']
    assert active_st_mandate(expert).poste.code == 'ST-V3-12'
    assert get_ctc_context(expert)['st_can_manage_ptn']
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [expert.user.email]
    with pytest.raises(ValidationError):
        nominate_batch(admin_user, [item], apply=True)


@pytest.mark.django_db
def test_future_mandate_has_no_current_access(st_setup, admin_user, user_factory, expert_factory):
    expert = expert_factory(user=user_factory(username='future'))
    nominate_batch(admin_user, [{'post_code': 'ST-V3-01', 'expert_id': expert.pk,
        'start_date': (timezone.localdate() + timedelta(days=2)).isoformat(), 'appointment_reference': 'Nomination future'}], apply=True)
    assert active_st_mandate(expert) is None
    expert.user.refresh_from_db()
    assert not expert.user.is_ctc_staff
    assert get_ctc_context(expert) is None


@pytest.mark.django_db
def test_ptn_versions_and_head_confirmation(st_setup):
    member, head, outsider = st_setup(12), st_setup(10), st_setup(9)
    record = write_record(member, data())
    with pytest.raises(PermissionDenied):
        confirm_record(member, record.pk, 1, 'CONFIRMED', 'Avis')
    with pytest.raises(PermissionDenied):
        write_record(outsider, data(reference='PTN-X'))
    confirm_record(head, record.pk, 1, 'CONFIRMED', 'Source vérifiée')
    with pytest.raises(ValidationError):
        confirm_record(head, record.pk, 1, 'CONFIRMED', 'Doublon')
    write_record(member, data(revision=1, content='Valeur révisée'), record.pk)
    assert record.versions.count() == 2
    assert record.versions.get(number=1).content == 'Valeur documentée'
    assert STConfirmation.objects.count() == 1
    with pytest.raises(ValidationError):
        write_record(member, data(revision=1), record.pk)
    with pytest.raises(ValidationError):
        record.versions.get(number=1).save()


@pytest.mark.django_db
@pytest.mark.parametrize('head_number', [13, 14])
def test_each_cohead_can_confirm_real_financial_records(st_setup, head_number):
    member, head = st_setup(15), st_setup(head_number)
    record = write_record(member, data('FINANCE', 'DEP-01', amount='125.50', currency='USD',
        movement='DEPENSE', operation_date=timezone.localdate().isoformat()))
    decision = confirm_record(head, record.pk, 1, 'CONFIRMED', 'Justificatif vérifié')
    assert str(decision.revision.amount) == '125.50'
    assert decision.author == head


@pytest.mark.django_db
@pytest.mark.parametrize('amount', ['-1', '0', 'NaN', 'Infinity', '1.234'])
def test_invalid_amounts_never_create_entries(st_setup, amount):
    with pytest.raises(ValidationError):
        write_record(st_setup(15), data('FINANCE', amount=amount, currency='USD', movement='DEPENSE', operation_date='2026-10-31'))
    assert not STRecord.objects.exists()


@pytest.mark.django_db
def test_audit_reader_cannot_change_or_confirm_other_pole(st_setup):
    member, own_head, auditor = st_setup(19), st_setup(17), st_setup(13)
    record = write_record(member, data('WORK'))
    assert visible_records(auditor).filter(pk=record.pk).exists()
    with pytest.raises(PermissionDenied):
        write_record(auditor, data('WORK', revision=1), record.pk)
    with pytest.raises(PermissionDenied):
        confirm_record(auditor, record.pk, 1, 'CONFIRMED', 'Avis')
    assert confirm_record(own_head, record.pk, 1, 'REJECTED', 'À compléter').decision == 'REJECTED'


@pytest.mark.django_db
def test_api_conflicts_permissions_and_official_ptn(st_setup, client):
    member, head = st_setup(12), st_setup(10)
    client.force_login(member)
    response = client.post('/api/v1/st/records/', data(), content_type='application/json')
    assert response.status_code == 201
    record_id = response.json()['id']
    url = f'/api/v1/st/records/{record_id}/'
    assert client.post(url + 'confirm/', {'revision': 1, 'decision': 'CONFIRMED', 'comment': 'Avis'}, content_type='application/json').status_code == 403
    assert client.post(url + 'revise/', data(revision=0), content_type='application/json').status_code == 409
    assert client.get('/api/v1/st/records/ptn-register/').json()['confirmed_count'] == 0
    client.force_login(head)
    assert client.post(url + 'confirm/', {'revision': 1, 'decision': 'CONFIRMED', 'comment': 'Avis'}, content_type='application/json').status_code == 200
    assert client.get('/api/v1/st/records/ptn-register/').json()['confirmed_count'] == 1


@pytest.mark.django_db
def test_finance_summary_is_real_and_currency_separated(st_setup, client):
    member, head = st_setup(15), st_setup(14)
    record = write_record(member, data('FINANCE', amount='17.25', currency='CDF', movement='ENGAGEMENT', operation_date='2026-10-31'))
    client.force_login(head)
    assert client.get('/api/v1/st/records/finance-summary/').json()['ledger'] == []
    confirm_record(head, record.pk, 1, 'CONFIRMED', 'Accord')
    summary = client.get('/api/v1/st/records/finance-summary/').json()
    assert summary['ledger'] == [{'currency': 'CDF', 'movement': 'ENGAGEMENT', 'amount': '17.25'}]
    assert summary['legacy']['currency'] is None
    assert summary['legacy']['cotisations_confirmed'] == '0'


@pytest.mark.django_db
def test_neuronne_admin_without_expert_can_use_nomination_tools(st_setup, admin_user):
    from apps.ia_agent.services.permissions import available_scopes
    from apps.ia_agent.tools.st_tools import list_st_posts
    assert 'expert' in available_scopes(admin_user)
    assert len(list_st_posts(SimpleNamespace(user=admin_user))) == 19


@pytest.mark.django_db
def test_admin_nomination_activates_only_selected_post(st_setup, admin_user, expert_factory, user_factory, client):
    expert = expert_factory(user=user_factory(username='admin-nominated'))
    post = st_posts().get(code='ST-V3-09')
    client.force_login(admin_user)
    response = client.post('/admin/governance/nominationctc/add/', {'expert': expert.pk, 'poste': post.pk,
        'function': post.title, 'capacity': 'ORGANISATION', 'appointment_reference': 'Communiqué 003',
        'start_date': timezone.localdate().isoformat(), 'status': 'ACTIVE', '_save': 'Enregistrer'})
    assert response.status_code == 302
    assert active_st_mandate(expert).poste == post
    assert not CTCMembership.objects.exists()


@pytest.mark.django_db
def test_audit_endpoint_excludes_reader_actions(st_setup, client):
    first, second = st_setup(13), st_setup(14)
    record = write_record(first, data('WORK'))
    confirm_record(second, record.pk, 1, 'CONFIRMED', 'Accord')
    client.force_login(first)
    result = client.get('/api/v1/st/records/audit/')
    assert result.status_code == 200
    assert not any(row['operation'] == 'ST_PREPARE' for row in result.json()['results'])
    assert any(row['operation'] == 'ST_CONFIRM' for row in result.json()['results'])


@pytest.mark.django_db
def test_admin_legacy_forms_are_retired(st_setup, admin_user, client):
    client.force_login(admin_user)
    assert client.get('/admin/governance/ctcmembership/add/').status_code == 403
    assert client.get('/admin/governance/postenominatifctc/add/').status_code == 403


@pytest.mark.django_db
def test_api_neuronne_activation_tools_reject_non_admin(st_setup, client):
    from apps.ia_agent.tools.st_tools import assign_st_posts
    user = st_setup(9)
    client.force_login(user)
    assert client.get('/api/v1/st/records/posts/').status_code == 403
    with pytest.raises(PermissionDenied):
        assign_st_posts(SimpleNamespace(user=user), [], apply=True)


@pytest.mark.django_db
def test_anonymous_finance_permission_denied_after_reset(st_setup):
    from django.contrib.auth.models import AnonymousUser
    from api.v1.permissions import IsSTFinance
    assert not IsSTFinance().has_permission(SimpleNamespace(user=AnonymousUser()), None)


@pytest.mark.django_db
def test_historical_leaders_not_serialized_as_current_roles(admin_user, expert_factory):
    from api.v1.hierarchy.serializers import TechnicalCellSerializer
    old = expert_factory()
    cell = TechnicalCell.objects.create(coordinator=old)
    CTCMembership.objects.create(ctc=cell, expert=old, role='COORDINATOR')
    reset_legacy_access(admin_user)
    data = TechnicalCellSerializer(cell).data
    assert data['coordinator'] is None
    assert data['members'] == []
    cell.refresh_from_db()
    assert cell.coordinator_id == old.pk


@pytest.mark.django_db
def test_existing_payment_confirmation_requires_cohead(st_setup, client):
    from apps.experts.models import Expert
    from apps.payments.models import Cotisation, Paiement
    member, head = st_setup(15), st_setup(14)
    structure = Expert.objects.get(user=member).structure
    cotisation = Cotisation.objects.create(structure=structure, annee=2026, montant='100', due_date='2026-10-31')
    payment = Paiement.objects.create(cotisation=cotisation, montant='20', methode_paiement='ESPECES', payment_date='2026-10-31')
    client.force_login(member)
    url = f'/api/v1/paiements/{payment.pk}/confirm/'
    assert client.post(url).status_code == 403
    payment.refresh_from_db()
    assert payment.status == 'PENDING'
    client.force_login(head)
    assert client.post(url).status_code == 200
    payment.refresh_from_db()
    assert payment.status == 'CONFIRMED'


@pytest.mark.django_db
def test_mark_paid_is_not_available_to_finance_member(st_setup, client):
    client.force_login(st_setup(15))
    assert client.post('/api/v1/jetons/999999/mark_as_paid/').status_code == 403
