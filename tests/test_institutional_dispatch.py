import uuid
from io import BytesIO
from unittest.mock import patch
import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from apps.governance.models import OrganisationVersion, Organe, GroupeCible, AffectationSousCommission, MandatOrganisation
from apps.governance.st_operations import reset_legacy_access, nominate_batch
from apps.messaging.dispatch_models import InstitutionalDispatch, DispatchRecipient, DispatchEmailAttempt
from apps.messaging.dispatch_services import send_dispatch, retry_dispatch_emails
from apps.messaging.dispatch_delivery import deliver_dispatch_emails
from apps.mobileapp.models import Notification


@pytest.fixture
def setup_dispatch(user_factory, expert_factory, settings, tmp_path, monkeypatch):
    settings.ST_COMMUNICATIONS_ROOT = tmp_path / 'private'
    monkeypatch.setattr('apps.messaging.dispatch_delivery.enqueue_dispatch_emails', lambda _: None)
    admin = user_factory(username='dispatch-admin', is_staff=True, is_superuser=True)
    reset_legacy_access(admin)
    catalog = OrganisationVersion.objects.create(code='dispatch-catalog', name='Catalogue', source_document='Test', status='VALIDATED')
    sc = Organe.objects.create(version=catalog, code='SC-TEST', name='Sous-commission', type='SC', status='VALIDATED', source_reference='Test')
    other = Organe.objects.create(version=catalog, code='SC-OTHER', name='Autre SC', type='SC', status='VALIDATED', source_reference='Test')
    gt = GroupeCible.objects.create(sc=sc, code='GT-1', name='Groupe un', activity='PRODUCTION', source_reference='Test')
    gt2 = GroupeCible.objects.create(sc=sc, code='GT-2', name='Groupe deux', activity='PRODUCTION', source_reference='Test')
    def expert(name, email=None):
        return expert_factory(user=user_factory(username=name, email=email if email is not None else f'{name}@example.invalid'))
    def assign(member, target=sc, status='MIGRATED'):
        return AffectationSousCommission.objects.create(version=target.version, expert=member, sc=target,
            source_key=uuid.uuid4().hex, batch_reference='TEST', source_kind='REPORT_PROPOSAL',
            source_database_sha256='a'*64, migration_reference='Test', status=status, effective_from=timezone.localdate(), source_snapshot={'test': True})
    def group_member(member, group):
        return MandatOrganisation.objects.create(expert=member, groupe=group, function='Membre du GT',
            appointment_reference='Test', start_date=timezone.localdate(), status='ACTIVE')
    def sender(number=19):
        member = expert(f'sender-{number}')
        nominate_batch(admin, [{'post_code': f'ST-V3-{number:02}', 'expert_id': member.pk,
            'start_date': timezone.localdate().isoformat(), 'appointment_reference': 'Test'}], apply=True)
        return member.user
    return {'admin': admin, 'sc': sc, 'other': other, 'gt': gt, 'gt2': gt2,
        'expert': expert, 'assign': assign, 'group_member': group_member, 'sender': sender}


def send(env, user=None, **extra):
    return send_dispatch(user or env['sender'](), subject='Communication', body='Texte du ST', sc_id=env['sc'].pk, **extra)


@pytest.mark.django_db
def test_all_st_holders_can_send_to_confirmed_sc_only(setup_dispatch):
    e = setup_dispatch
    member, outsider, review = (e['expert'](n) for n in ('member', 'outsider', 'review'))
    e['assign'](member)
    e['assign'](outsider, e['other'])
    e['assign'](review, status='REVIEW')
    result, created = send(e)
    assert created and result.recipients.count() == 1
    assert result.recipients.get().user == member.user
    assert Notification.objects.filter(data__dispatch_id=result.pk).count() == 1
    with pytest.raises(PermissionDenied):
        send(e, user=outsider.user)
    with pytest.raises(PermissionDenied):
        send(e, user=e['admin'])


@pytest.mark.django_db
def test_single_gt_never_broadcasts_to_sc_or_another_gt(setup_dispatch):
    e = setup_dispatch
    one, two, sc_member = (e['expert'](n) for n in ('one', 'two', 'sc-member'))
    e['group_member'](one, e['gt'])
    e['group_member'](two, e['gt2'])
    e['assign'](sc_member)
    message, _ = send_dispatch(e['sender'](), subject='GT uniquement', body='Travail', gt_id=e['gt'].pk)
    assert list(message.recipients.values_list('user_id', flat=True)) == [one.user_id]


@pytest.mark.django_db
@pytest.mark.parametrize('case', ['both', 'none', 'empty', 'proposed'])
def test_invalid_targets_produce_no_delivery(setup_dispatch, case):
    e = setup_dispatch
    user = e['sender']()
    kwargs = {'sc_id': e['sc'].pk}
    if case == 'both':
        kwargs['gt_id'] = e['gt'].pk
    elif case == 'none':
        kwargs = {}
    elif case == 'proposed':
        e['sc'].status = 'PROPOSED'
        e['sc'].save()
    with pytest.raises(ValidationError):
        send_dispatch(user, subject='Test', body='Texte', **kwargs)
    assert not InstitutionalDispatch.objects.exists()
    assert not Notification.objects.filter(data__kind='institutional_dispatch').exists()


@pytest.mark.django_db
def test_idempotency_does_not_repeat_notifications(setup_dispatch):
    e = setup_dispatch
    e['assign'](e['expert']('receiver'))
    user, key = e['sender'](), uuid.uuid4()
    first, created = send(e, user=user, request_key=key)
    same, created_again = send(e, user=user, request_key=key)
    assert created and not created_again and same.pk == first.pk
    assert first.recipients.count() == 1
    with pytest.raises(ValidationError):
        send_dispatch(user, subject='Autre contenu', body='Texte', sc_id=e['sc'].pk, request_key=key)
    assert InstitutionalDispatch.objects.count() == 1


@pytest.mark.django_db
def test_private_pdf_and_history_authorizations(setup_dispatch, client):
    e = setup_dispatch
    recipient, outsider = e['expert']('receiver'), e['expert']('outside')
    e['assign'](recipient)
    message, _ = send(e, upload=SimpleUploadedFile('rapport.pdf', b'%PDF-1.4\n%%EOF'))
    client.force_login(recipient.user)
    root = f'/api/v1/communications/{message.pk}/'
    response = client.get(root + 'attachment/')
    assert response.status_code == 200
    assert b''.join(response.streaming_content) == b'%PDF-1.4\n%%EOF'
    assert response['Cache-Control'] == 'private, no-store'
    assert message.attachment.path.startswith(str(message.attachment.storage.location))
    assert client.post(root + 'read/').status_code == 200
    assert message.recipients.get().read_at
    assert Notification.objects.get(data__dispatch_id=message.pk).is_read
    client.force_login(outsider.user)
    assert client.get(root).status_code == 404
    assert client.get(root + 'attachment/').status_code == 404
    e['assign'](outsider)
    assert client.get(root).status_code == 404  # une adhésion ultérieure ne change pas les destinataires
    client.force_login(message.sender)
    assert client.patch(root, {'body': 'Modifié'}, content_type='application/json').status_code == 405
    assert client.delete(root).status_code == 405


@pytest.mark.django_db
@pytest.mark.parametrize('name,content', [('bad.exe', b'MZ'), ('fake.pdf', b'pas un PDF'), ('empty.txt', b''), ('bad.docx', b'pas un zip')])
def test_invalid_uploads_leave_no_history_or_file(setup_dispatch, name, content, settings):
    e = setup_dispatch
    e['assign'](e['expert']('receiver'))
    with pytest.raises(ValidationError):
        send(e, upload=SimpleUploadedFile(name, content))
    assert not InstitutionalDispatch.objects.exists()
    assert not list(settings.ST_COMMUNICATIONS_ROOT.rglob('*'))


@pytest.mark.django_db
def test_upload_size_limit_and_cleanup_on_database_failure(setup_dispatch, monkeypatch, settings):
    e = setup_dispatch
    e['assign'](e['expert']('receiver'))
    user = e['sender']()
    monkeypatch.setattr('apps.messaging.dispatch_services.MAX_FILE_SIZE', 20)
    with pytest.raises(ValidationError):
        send(e, user=user, upload=SimpleUploadedFile('large.txt', b'a'*21))
    with patch('apps.messaging.dispatch_services.Notification.objects.bulk_create', side_effect=RuntimeError('Échec simulé')):
        with pytest.raises(RuntimeError):
            send(e, user=user, upload=SimpleUploadedFile('ok.pdf', b'%PDF-1.4\n%%EOF'))
    assert not InstitutionalDispatch.objects.exists()
    assert not [p for p in settings.ST_COMMUNICATIONS_ROOT.rglob('*') if p.is_file()]


@pytest.mark.django_db
def test_email_and_attachment_are_sent_once_and_snapshotted(setup_dispatch, mailoutbox):
    e = setup_dispatch
    receiver = e['expert']('receiver')
    e['assign'](receiver)
    message, _ = send(e, upload=SimpleUploadedFile('rapport.pdf', b'%PDF-1.4\n%%EOF'))
    original_email = receiver.user.email
    receiver.user.email = 'new-address@example.invalid'
    receiver.user.save()
    deliver_dispatch_emails(message.pk)
    deliver_dispatch_emails(message.pk)
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [original_email]
    assert mailoutbox[0].attachments[0].filename == 'rapport.pdf'
    delivery = message.recipients.get()
    assert delivery.email_status == 'SENT' and delivery.email_attempts == 1
    assert DispatchEmailAttempt.objects.get(recipient=delivery).outcome == 'SENT'


@pytest.mark.django_db
def test_email_failure_and_retry_keep_attempt_history(setup_dispatch, mailoutbox):
    e = setup_dispatch
    e['assign'](e['expert']('receiver'))
    user = e['sender']()
    message, _ = send(e, user=user)
    with patch('apps.messaging.dispatch_delivery.EmailMessage.send', side_effect=RuntimeError('Échec simulé')):
        deliver_dispatch_emails(message.pk)
    assert message.recipients.get().email_status == 'FAILED'
    assert retry_dispatch_emails(user, message.pk) == 1
    deliver_dispatch_emails(message.pk)
    assert message.recipients.get().email_status == 'SENT'
    assert list(DispatchEmailAttempt.objects.values_list('outcome', flat=True)) == ['FAILED', 'SENT']
    assert len(mailoutbox) == 1


@pytest.mark.django_db
def test_missing_email_does_not_block_internal_delivery(setup_dispatch):
    e = setup_dispatch
    e['assign'](e['expert']('receiver', email=''))
    message, _ = send(e)
    delivery = message.recipients.get()
    assert delivery.email_status == 'SKIPPED'
    assert delivery.notification_id


@pytest.mark.django_db
def test_api_create_targets_and_no_impersonation(setup_dispatch, client):
    e = setup_dispatch
    receiver = e['expert']('receiver')
    e['assign'](receiver)
    sender = e['sender']()
    client.force_login(sender)
    assert client.get('/api/v1/communications/targets/').status_code == 200
    response = client.post('/api/v1/communications/', {'subject': 'Rapport', 'body': 'Texte',
        'sc_id': e['sc'].pk, 'sender': receiver.user_id}, content_type='application/json')
    assert response.status_code == 201
    assert response.json()['sender_id'] == sender.pk
    assert response.json()['channels'] == ['INTERNAL', 'EMAIL']
    assert client.get('/api/v1/communications/?direction=sent').json()['count'] == 1
    client.force_login(receiver.user)
    assert client.get('/api/v1/communications/?direction=received').json()['count'] == 1


@pytest.mark.django_db
def test_report_templates_versions_and_exports(setup_dispatch, client):
    from apps.governance.st_report_models import STReportTemplate, STReportVersion
    from apps.governance.st_report_exports import export_report_pdf, export_report_docx
    from docx import Document
    e = setup_dispatch
    user = e['sender']()
    client.force_login(user)
    template = client.post('/api/v1/st/reports/templates/', {'name': 'Modèle réutilisable',
        'sections': [{'title': 'Activités', 'content': ''}]}, content_type='application/json')
    assert template.status_code == 201
    assert STReportTemplate.objects.filter(pk=template.json()['id']).count() == 1
    assert STReportTemplate.objects.filter(system_code='activity').exists()
    response = client.post('/api/v1/st/reports/', {'title': 'Rapport de suivi', 'template_id': template.json()['id'],
        'sections': [{'title': 'Activités', 'content': 'Travaux documentés.'}],
        'period_start': '2026-10-01', 'period_end': '2026-10-31'}, content_type='application/json')
    assert response.status_code == 201
    report_id = response.json()['id']
    url = f'/api/v1/st/reports/{report_id}/'
    revised = {'title': 'Rapport corrigé', 'revision': 1, 'sections': [{'title': 'Activités', 'content': 'Suite des travaux.'}]}
    assert client.post(url + 'revise/', revised, content_type='application/json').status_code == 200
    assert client.post(url + 'revise/', revised, content_type='application/json').status_code == 409
    original = STReportVersion.objects.get(report_id=report_id, number=1)
    assert original.title == 'Rapport de suivi'
    assert client.get(url + 'export/?file_format=pdf&revision=1').content.startswith(b'%PDF-')
    word = client.get(url + 'export/?file_format=docx&revision=1')
    assert word.status_code == 200
    doc = Document(BytesIO(word.content))
    assert any(p.text == 'Rapport de suivi' for p in doc.paragraphs)
    assert any(p.text == 'Travaux documentés.' for p in doc.paragraphs)
    assert export_report_pdf(original) == export_report_pdf(original)
    assert export_report_docx(original) == export_report_docx(original)
    with pytest.raises(ValidationError):
        original.save()


@pytest.mark.django_db
def test_report_permissions_and_ctc_entry_point(setup_dispatch, client):
    from apps.governance.st_reports import save_report
    e = setup_dispatch
    user, other = e['sender'](19), e['sender'](9)
    report = save_report(user, {'title': 'Rapport', 'sections': [{'title': 'Objet', 'content': 'Texte'}]})
    client.force_login(other)
    assert client.get(f'/api/v1/st/reports/{report.pk}/').status_code == 404
    client.force_login(user)
    response = client.get('/ctc/rapports/', follow=True)
    assert response.status_code == 200
    assert response.redirect_chain[0][0] == '/ctc/rapports/travail/'
    assert 'ctc-ctx-data' in response.content.decode()
    assert client.delete(f'/api/v1/st/reports/{report.pk}/').status_code == 405


@pytest.mark.django_db
def test_report_send_links_exact_version_and_is_idempotent(setup_dispatch, client):
    from apps.governance.st_reports import save_report
    from apps.governance.st_report_models import STReportDispatch
    e = setup_dispatch
    e['assign'](e['expert']('receiver'))
    user = e['sender']()
    report = save_report(user, {'title': 'Rapport transmis', 'sections': [{'title': 'Objet', 'content': 'Travaux'}]})
    client.force_login(user)
    url = f'/api/v1/st/reports/{report.pk}/send/'
    data = {'revision': 1, 'body': 'Veuillez trouver le rapport.', 'sc_id': e['sc'].pk, 'request_key': str(uuid.uuid4())}
    first = client.post(url, data, content_type='application/json')
    assert first.status_code == 201
    second = client.post(url, data, content_type='application/json')
    assert second.status_code == 200
    assert STReportDispatch.objects.count() == 1
    assert STReportDispatch.objects.get().version.number == 1
    assert InstitutionalDispatch.objects.get().attachment.name.endswith('.pdf')


@pytest.mark.django_db
@pytest.mark.parametrize('extra', [
    {'sections': []},
    {'sections': [{'title': '', 'content': ''}]},
    {'period_start': '2026-10-31', 'period_end': '2026-10-01'},
])
def test_report_rejects_invalid_sections_and_periods(setup_dispatch, client, extra):
    client.force_login(setup_dispatch['sender']())
    result = client.post('/api/v1/st/reports/', {'title': 'Essai', 'sections': [{'title': 'Objet', 'content': ''}], **extra}, content_type='application/json')
    assert result.status_code == 400


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_ctc_report_creation_browser(setup_dispatch, live_server, client):
    from pathlib import Path
    from django.conf import settings
    from playwright.sync_api import sync_playwright, expect
    from apps.governance.st_report_models import STReportTemplate
    e = setup_dispatch
    user = e['sender']()
    STReportTemplate.objects.create(name='Rapport d’activité', system_code='activity', sections=[{'title': 'Objet', 'content': ''}, {'title': 'Activités', 'content': ''}])
    client.force_login(user)
    destination = Path(settings.BASE_DIR) / 'reports' / 'st_reports_browser'
    destination.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
        context.add_cookies([{'name': settings.SESSION_COOKIE_NAME, 'value': client.cookies[settings.SESSION_COOKIE_NAME].value, 'url': live_server.url}])
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        assert page.goto(live_server.url + '/ctc/rapports/', wait_until='networkidle').status == 200
        page.screenshot(path=str(destination / 'initial.png'), full_page=True)
        assert not errors, errors
        expect(page.locator('#view-rapports')).to_be_visible()
        page.get_by_role('button', name='Page blanche', exact=True).click()
        page.locator('#st-report-title').fill('Rapport de contrôle du parcours CTC')
        page.locator('.st-section-content').first.fill('Ce contenu sert uniquement à vérifier la rédaction et les exports.')
        page.get_by_role('button', name='Prévisualiser', exact=True).click()
        page.get_by_role('button', name='Fermer', exact=True).click()
        page.get_by_role('button', name='Sauvegarder', exact=True).click()
        expect(page.locator('#st-report-message')).to_contain_text('Rapport enregistré')
        page.locator('#st-report-model-name').fill('Modèle de contrôle')
        page.get_by_role('button', name='Enregistrer comme modèle', exact=True).click()
        expect(page.locator('#st-report-message')).to_contain_text('Modèle enregistré')
        with page.expect_download() as info:
            page.get_by_role('link', name='Exporter', exact=True).click()
        info.value.save_as(destination / 'rapport.pdf')
        with page.expect_download() as info:
            page.get_by_role('link', name='Exporter en Word', exact=True).click()
        info.value.save_as(destination / 'rapport.docx')
        page.screenshot(path=str(destination / 'desktop.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.screenshot(path=str(destination / 'mobile.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
        assert not errors, errors
        browser.close()


@pytest.mark.django_db
def test_official_communique_exact_html_pdf_and_unique_members(setup_dispatch, mailoutbox):
    from apps.messaging.official_dispatch import archive_official_communique, official_asset
    e = setup_dispatch
    recipient = e['expert']('official-reader')
    e['assign'](recipient)
    e['assign'](recipient, e['other'])
    dispatch, created = archive_official_communique()
    repeated, again = archive_official_communique()
    assert created and not again and repeated.pk == dispatch.pk
    assert dispatch.sender_id is None and dispatch.mandate_id is None
    assert dispatch.target_all_sc and dispatch.recipients.count() == 1
    manifest, source, text, html = official_asset()
    assert dispatch.body == text and dispatch.html_body == html
    assert dispatch.attachment_sha256 == manifest['sha256']
    with dispatch.attachment.open('rb') as stream:
        assert stream.read() == source.read_bytes()
    deliver_dispatch_emails(dispatch.pk)
    assert len(mailoutbox) == 1
    assert mailoutbox[0].alternatives[0].content == html
    assert '<strong>' in html and '**' not in html
    assert mailoutbox[0].attachments[0].content == source.read_bytes()
    assert not MandatOrganisation.objects.filter(poste__code__startswith='ST-V3-', status='ACTIVE').exists()


@pytest.mark.django_db
def test_official_communique_does_not_mail_same_address_twice(setup_dispatch, mailoutbox):
    from apps.messaging.official_dispatch import archive_official_communique
    e = setup_dispatch
    for name in ('duplicate-one', 'duplicate-two'):
        e['assign'](e['expert'](name, email='shared@example.invalid'))
    dispatch, _ = archive_official_communique()
    assert dispatch.recipients.count() == 2
    assert dispatch.recipients.filter(email_status='SKIPPED').count() == 1
    deliver_dispatch_emails(dispatch.pk)
    assert len(mailoutbox) == 1
