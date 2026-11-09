from io import BytesIO
from types import SimpleNamespace
import hashlib
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from docx import Document
from apps.governance.st_report_documents import import_source, report_storage, validate_document, fixed_pdf
from apps.governance.st_report_models import validate_report_sections


def pdf_bytes():
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((60, 80), 'Reference source conservee')
    return doc.tobytes()


@pytest.mark.django_db
def test_import_preserves_original_and_deduplicates(settings, tmp_path):
    settings.BASE_DIR = tmp_path
    original = pdf_bytes()
    upload = lambda: SimpleUploadedFile('modele.pdf', original, content_type='application/pdf')
    source = import_source(upload())
    assert len(source.pages) == 1
    assert source.sha256 == hashlib.sha256(original).hexdigest()
    assert import_source(upload()).pk == source.pk
    with report_storage().open(source.original, 'rb') as stream:
        assert stream.read() == original
    version = SimpleNamespace(source=source, title='Essai', author_name='Test', report=SimpleNamespace(reference='TEST'), number=1, document={'mode': 'fixed', 'fields': [{'page': 0, 'x': .1, 'y': .3, 'width': .5, 'height': .1, 'size': .02, 'text': 'Champ rempli'}]})
    validate_document(version.document, source)
    import fitz
    assert fixed_pdf(version) == fixed_pdf(version)
    from apps.governance.st_report_documents import fixed_docx
    assert fixed_docx(version) == fixed_docx(version)
    with fitz.open(stream=fixed_pdf(version), filetype='pdf') as result:
        assert 'Champ rempli' in result[0].get_text()
        assert 'Reference source conservee' in result[0].get_text()
    with report_storage().open(source.original, 'rb') as stream:
        assert stream.read() == original


def test_rich_sections_reject_untrusted_embeds_and_mismatched_text():
    valid = {'title': 'Objet', 'content': 'Essai', 'delta': [{'insert': 'Essai', 'attributes': {'bold': True}}, {'insert': '\n'}]}
    validate_report_sections([valid])
    for delta in [[{'insert': {'image': 'http://example.invalid'}}], [{'insert': 'Autre\n'}]]:
        with pytest.raises(ValidationError):
            validate_report_sections([{**valid, 'delta': delta}])


def test_fixed_fields_are_bounded_and_do_not_overflow():
    source = SimpleNamespace(pages=[{'width': 595, 'height': 842}])
    field = {'page': 0, 'x': .9, 'y': .2, 'width': .5, 'height': .1, 'size': .02, 'text': 'Texte'}
    with pytest.raises(ValidationError):
        validate_document({'mode': 'fixed', 'fields': [field]}, source)
    with pytest.raises(ValidationError):
        validate_document({'mode': 'fixed', 'fields': []}, None)


def test_rich_docx_exports_styles():
    from datetime import datetime, timezone
    from apps.governance.st_report_exports import export_report_docx
    section = {'title': 'Objet', 'content': 'Texte en gras', 'delta': [{'insert': 'Texte en gras', 'attributes': {'bold': True, 'italic': True}}, {'insert': '\n'}]}
    version = SimpleNamespace(document={}, sections=[section], title='Contrôle', author_name='Test', period_start=None, period_end=None, report=SimpleNamespace(reference='TEST'), number=1, created_at=datetime(2026, 11, 8, tzinfo=timezone.utc))
    result = Document(BytesIO(export_report_docx(version)))
    run = next(r for p in result.paragraphs for r in p.runs if r.text == 'Texte en gras')
    assert run.bold and run.italic
    from apps.governance.st_report_exports import export_report_pdf
    assert export_report_pdf(version).startswith(b'%PDF-')


from tests.test_institutional_dispatch import setup_dispatch  # noqa: E402,F401


@pytest.mark.django_db
def test_source_api_is_private_and_version_preserves_composition(setup_dispatch, settings, tmp_path):
    from rest_framework.test import APIClient
    from apps.governance.st_report_models import STReportVersion
    settings.BASE_DIR = tmp_path
    actor = setup_dispatch['sender'](11)
    other = setup_dispatch['sender'](12)
    api = APIClient()
    api.force_authenticate(actor)
    response = api.post('/api/v1/st/reports/import-document/', {'file': SimpleUploadedFile('reference.pdf', pdf_bytes())}, format='multipart')
    assert response.status_code == 201, response.data
    source_id = response.data['id']
    source_url = f'/api/v1/st/reports/sources/{source_id}/'
    assert api.get(source_url, {'page': 0}).status_code == 200
    api.force_authenticate(other)
    assert api.get(source_url).status_code == 404
    api.force_authenticate(actor)
    payload = {'title': 'Document rempli', 'source_id': source_id, 'sections': [{'title': 'Objet', 'content': ''}], 'document': {'mode': 'fixed', 'fields': [{'page': 0, 'x': .1, 'y': .3, 'width': .5, 'height': .1, 'size': .02, 'text': 'Version un'}]}}
    saved = api.post('/api/v1/st/reports/', payload, format='json')
    assert saved.status_code == 201, saved.data
    report_id = saved.data['id']
    assert saved.data['versions'][0]['source_id'] == source_id
    assert saved.data['versions'][0]['document']['fields'][0]['text'] == 'Version un'
    payload['document']['fields'][0]['text'] = 'Version deux'
    payload['revision'] = 1
    revised = api.post(f'/api/v1/st/reports/{report_id}/revise/', payload, format='json')
    assert revised.status_code == 200, revised.data
    assert STReportVersion.objects.get(report_id=report_id, number=1).document['fields'][0]['text'] == 'Version un'
    exported = api.get(f'/api/v1/st/reports/{report_id}/export/', {'file_format': 'pdf', 'revision': 1})
    assert exported.status_code == 200
    import fitz
    with fitz.open(stream=exported.content, filetype='pdf') as result:
        assert 'Version un' in '\n'.join(p.get_text() for p in result)
        assert 'Version deux' not in '\n'.join(p.get_text() for p in result)
        assert result.page_count == 2
        assert 'Document rempli' in result[0].get_text()

    template = api.post('/api/v1/st/reports/templates/', {'name': 'Formulaire réutilisable', 'sections': payload['sections'], 'source_id': source_id, 'document': payload['document']}, format='json')
    assert template.status_code == 201, template.data
    assert template.data['document']['mode'] == 'fixed'
    assert template.data['document']['fields'][0]['text'] == 'Version deux'

    inherited = api.post('/api/v1/st/reports/', {'title': 'Rapport depuis le modèle', 'template_id': template.data['id']}, format='json')
    assert inherited.status_code == 201, inherited.data
    assert inherited.data['versions'][0]['document'] == template.data['document']
    assert inherited.data['versions'][0]['source_id'] == source_id
    next_version = api.post(f"/api/v1/st/reports/{inherited.data['id']}/revise/", {'title': 'Révision sans perte de couverture', 'revision': 1, 'sections': payload['sections']}, format='json')
    assert next_version.status_code == 200, next_version.data
    assert next_version.data['versions'][0]['document'] == template.data['document']
    assert next_version.data['versions'][0]['source_id'] == source_id
