from datetime import date
from zipfile import ZipFile
from io import BytesIO

import pytest
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from apps.core.models import User
from apps.experts.models import Expert, Structure
from apps.governance.models import HabilitationAction, MandatOrganisation, Organe, OrganisationVersion, PosteOrganisation
from apps.reporting.models import Report, ReportTypePermission
from apps.reporting.services import reporting_mandates, require_action
from apps.reporting.catalog import fields_for


@pytest.mark.django_db
def test_reporting_requires_confirmed_phoenix_mandate_and_report_type(client):
    user = User.objects.create_user(username='report-agent', password='test')
    structure = Structure.objects.create(name='Structure rapports', acronym='SR', category='ADMIN')
    expert = Expert.objects.create(user=user, structure=structure, status='ACTIVE')
    version = OrganisationVersion.objects.create(
        code='report-test', name='Test rapports', status='PROPOSED', source_document='Test',
    )
    st = Organe.objects.create(version=version, code='ST', name='Secrétariat technique', type='ST', source_reference='Test')
    pole = Organe.objects.create(version=version, code='ST-TEST', name='Pôle test', type='ST_POLE', parent=st, source_reference='Test')
    post = PosteOrganisation.objects.create(organe=pole, code='ST-TEST-01', category='MEMBER', title='Agent', source_reference='Test')
    mandate = MandatOrganisation.objects.create(
        expert=expert, poste=post, function='Agent', appointment_reference='Décision test',
        start_date=date(2026, 1, 1), status='ACTIVE',
    )
    grant = HabilitationAction.objects.create(
        mandat=mandate, action='rapport.rediger', perimeter=pole, decision_reference='Décision test',
        start_date=date(2026, 1, 1), enabled=True,
    )
    ReportTypePermission.objects.create(habilitation=grant, report_type='N1', enabled=True)
    assert not reporting_mandates(user, 'rapport.rediger', version, pole, 'N1').exists()
    version.status = 'ACTIVE'
    version.activation_reference = 'Activation test'
    version.gt_catalogue_reference = 'GT test'
    version.permissions_reference = 'Permissions test'
    version.circuit_reference = 'Circuit test'
    version.save()
    assert reporting_mandates(user, 'rapport.rediger', version, pole, 'N1').exists()
    assert not reporting_mandates(user, 'rapport.rediger', version, pole, 'F3').exists()
    other_pole = Organe.objects.create(version=version, code='ST-AUTRE', name='Autre pôle', type='ST_POLE', parent=st, source_reference='Test')
    assert not reporting_mandates(user, 'rapport.rediger', version, other_pole, 'N1').exists()
    client.force_login(user)
    creation_page = client.get(reverse('reporting:create'))
    assert creation_page.status_code == 200
    assert b'N1' in creation_page.content
    assert b'F3' not in creation_page.content
    created = client.post(reverse('reporting:create'), {
        'report_type': 'N1', 'title': 'Réception test', 'pole': pole.pk,
        'period_start': '2026-10-01', 'period_end': '2026-10-28', 'recipient': 'Coordonnateur',
    })
    assert created.status_code == 302, created.context['form'].errors
    draft = Report.objects.get(title='Réception test', prepared_by=user, pole=pole)
    fields = {'revision': draft.revision}
    for key in fields_for('N1'):
        fields[f'mode_{key}'] = 'manual'
        fields[f'value_{key}'] = f'Constat contrôlable : {key}'
        fields[f'reference_{key}'] = 'Bordereau test'
    assert client.post(reverse('reporting:save_fields', args=[draft.pk]), fields).status_code == 302
    draft.refresh_from_db()
    assert draft.fields['origine']['source'] == 'Bordereau test'
    assert client.post(reverse('reporting:transition', args=[draft.pk]), {
        'revision': draft.revision, 'action': 'submit',
    }).status_code == 400
    assert client.post(reverse('reporting:add_evidence', args=[draft.pk]), {
        'title': 'Bordereau test', 'source_reference': 'B-01',
    }).status_code == 302
    draft.refresh_from_db()
    assert client.post(reverse('reporting:transition', args=[draft.pk]), {
        'revision': draft.revision, 'action': 'submit',
    }).status_code == 302
    draft.refresh_from_db()
    assert draft.status == Report.Status.SUBMITTED
    assert draft.source_snapshot['fields']['origine']['source'] == 'Bordereau test'
    report = Report.objects.create(
        reference='RPT-TEST', report_type='N1', title='Réception', version=version, pole=pole,
        period_start=date(2026, 10, 1), period_end=date(2026, 10, 28), recipient='Coordonnateur',
        prepared_by=user, prepared_mandate=mandate,
    )
    assert require_action(user, 'rapport.rediger', report) == mandate
    grant.enabled = False
    grant.save()
    with pytest.raises(PermissionDenied):
        require_action(user, 'rapport.rediger', report)


@pytest.mark.django_db
def test_unapproved_report_cannot_be_exported(client):
    user = User.objects.create_user(username='reader-report', password='test')
    client.force_login(user)
    response = client.get(reverse('reporting:index'))
    assert response.status_code == 200
    assert 'Aucun référentiel' in response.content.decode()


def test_word_export_has_valid_package_and_french_text():
    from apps.reporting.exports import build_docx

    class Author:
        pk = 1
        username = 'auteur'

        def get_full_name(self):
            return 'Éddy Masamba'

        def __str__(self):
            return self.get_full_name()

    author = Author()
    from types import SimpleNamespace

    report = SimpleNamespace(
        title='Fiche de formation', reference='RPT-2026-01', report_type='P4',
        period_start=date(2026, 10, 1), period_end=date(2026, 10, 28), recipient='Coordonnateur',
        prepared_by=author, prepared_by_id=1, approved_by=author, approved_by_id=1, reviewed_by=author,
        source_snapshot={'fields': {'participants': {'value': '24 personnes présentes', 'source': 'Feuille de présence'}},
                         'evidence': [], 'financial_lines': []},
        fields={}, reservations='', decision_requested='',
    )
    import xml.etree.ElementTree as ET

    with ZipFile(BytesIO(build_docx(report))) as package:
        document = package.read('word/document.xml')
        ET.fromstring(document)
        assert 'Éddy Masamba'.encode() in document
        assert b'24 personnes' in document
