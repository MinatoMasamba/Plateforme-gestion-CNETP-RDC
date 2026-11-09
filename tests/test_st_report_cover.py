from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace
from zipfile import ZipFile
import fitz
import pytest
from django.core.exceptions import ValidationError
from docx import Document
from apps.governance.st_report_cover import cover_pdf, cover_data, validate_cover
from apps.governance.st_report_exports import export_report_pdf, export_report_docx


def version():
    return SimpleNamespace(document={'cover': {'recipient': 'Comité de pilotage', 'subject': 'Suivi des dossiers', 'stats': [{'value': '12', 'label': 'DOSSIERS CONTRÔLÉS'}]}}, title='Rapport personnalisé', author_name='Auteur de contrôle', created_at=datetime(2026, 11, 8, tzinfo=timezone.utc), number=2, report=SimpleNamespace(reference='CONTROLE'), period_start=None, period_end=None, sections=[{'title': 'Constats', 'content': 'Contenu rédigé par l’utilisateur.'}])


def test_cover_uses_supplied_gradient_and_personalized_fields():
    data = cover_data(version())
    first = cover_pdf(data)
    assert first == cover_pdf(data)
    with fitz.open(stream=first, filetype='pdf') as pdf:
        assert len(pdf) == 1
        text = pdf[0].get_text()
        assert 'Rapport personnalisé' in text and 'Comité de pilotage' in text
        assert 'KAMANGU' not in text and 'TCOE' not in text
        assert 'E. Luwenga' in text
        footer = pdf[0].get_text(clip=fitz.Rect(0, 780, 596, 842))
        assert footer.strip() == 'Consultant Emmany Luwenga'
        drawings = pdf[0].get_drawings()
        assert len(drawings) >= 220


def test_pdf_and_word_have_single_canonical_cover():
    v = version()
    with fitz.open(stream=export_report_pdf(v), filetype='pdf') as pdf:
        assert len(pdf) == 2
        assert 'Rapport personnalisé' in pdf[0].get_text()
        assert 'Contenu rédigé' in pdf[1].get_text()
    docx = export_report_docx(v)
    document = Document(BytesIO(docx))
    assert len(document.element.xpath('.//wp:anchor')) == 1
    assert any('Contenu rédigé' in p.text for p in document.paragraphs)
    with ZipFile(BytesIO(docx)) as archive:
        assert len([n for n in archive.namelist() if n.startswith('word/media/')]) == 1
    assert export_report_docx(v) == docx


@pytest.mark.parametrize('value', [{'stats': [dict(value='1', label='X')] * 5}, {'organization': 'A'*181}, {'unknown': 'x'}, {'stats': [{'value': 2, 'label': 'X'}]}])
def test_cover_rejects_invalid_values(value):
    with pytest.raises(ValidationError):
        validate_cover(value)


def test_free_exports_restore_editable_tables():
    v = version()
    v.sections = [{'title': 'Résultats', 'content': 'Indicateur | Valeur\nDossiers | 12\nVersions | 5\n'}]
    document = Document(BytesIO(export_report_docx(v)))
    assert len(document.tables) == 1
    assert document.tables[0].cell(1, 1).text == '12'
    with fitz.open(stream=export_report_pdf(v), filetype='pdf') as pdf:
        assert 'Dossiers' in pdf[1].get_text() and '12' in pdf[1].get_text()


def test_school_model_keeps_its_own_identity_in_the_body():
    v = version()
    v.document['cover'].update({'organization': 'SOURCE ACADÉMIQUE', 'department': 'Établissement scolaire', 'brand': 'Source Académique'})
    with fitz.open(stream=export_report_pdf(v), filetype='pdf') as pdf:
        assert 'SOURCE ACADÉMIQUE' in pdf[1].get_text()
        assert 'MINISTÈRE DES INFRASTRUCTURES' not in pdf[1].get_text()


def test_long_table_cells_continue_across_pdf_pages_without_losing_text():
    v = version()
    v.sections = [{'title': 'Constats', 'content': 'Champ | Texte\nConstat | ' + 'Observation vérifiée. ' * 250 + '\n'}]
    with fitz.open(stream=export_report_pdf(v), filetype='pdf') as pdf:
        assert len(pdf) > 2
        assert sum(p.get_text().count('Observation') for p in pdf) == 250
