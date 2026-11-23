import json
from pathlib import Path

import pytest

from apps.norms.rich_text import (
    RichTextValidationError,
    content_metrics,
    parse_blocks,
    to_html,
    to_plain,
    validate,
)


CASES_PATH = Path(__file__).parent / 'fixtures' / 'rich_text_cases.json'


def _cases():
    return json.loads(CASES_PATH.read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', _cases(), ids=lambda case: case['name'])
def test_shared_rich_text_cases(case):
    content_format = case['content_format']
    if case.get('error'):
        with pytest.raises(RichTextValidationError):
            validate(case['source'], content_format)
        return

    assert to_plain(case['source'], content_format) == case['plain']
    assert to_html(case['source'], content_format)
    parse_blocks(case['source'], content_format)


def test_html_is_escaped_and_safe_styles_are_rendered():
    rendered = to_html(
        '[Très grand]{taille=tres-grand|surlignage=jaune|couleur=rouge}\n\n'
        '[Référence](https://example.cd/a?x=1&y=2)',
        'md',
    )

    assert '<font size="18" backColor="#FFF24B" color="#DB3832">' in rendered
    assert 'href="https://example.cd/a?x=1&amp;y=2"' in rendered
    assert '<script' not in rendered


def test_plain_format_does_not_interpret_markdown_or_html():
    content = '1. Liste héritée\n**Texte littéral**\n<script>'

    assert to_plain(content, 'plain') == content
    assert '**Texte littéral**' in to_html(content, 'plain')
    assert '&lt;script&gt;' in to_html(content, 'plain')


def test_metrics_and_excerpt_use_plain_text():
    metrics = content_metrics(
        '# Objet\n\nUne **obligation** [normative](https://example.cd).',
        'md',
    )

    assert metrics == {
        'characters': 32,
        'words': 4,
        'excerpt': 'Objet Une obligation normative.',
    }


@pytest.mark.django_db
def test_norme_version_exposes_plain_content_and_structured_blocks(norme_factory):
    from apps.norms.models import NormeVersion

    version = NormeVersion.all_objects.create(
        norme=norme_factory(),
        version_number=1,
        title='Version enrichie',
        content='# Objet\n\nLa clause **doit être appliquée**.',
        content_format='md',
    )

    assert version.content_plain == 'Objet\n\nLa clause doit être appliquée.'
    assert version.get_structured_content() == [
        {'type': 'section', 'title': 'Objet', 'content': 'La clause doit être appliquée.'}
    ]


@pytest.mark.django_db
def test_rich_norm_pdf_preserves_visible_text(norme_factory):
    import fitz

    from api.v1.pdf_utils import generate_norm_pdf
    from apps.norms.models import NormeVersion

    version = NormeVersion.all_objects.create(
        norme=norme_factory(),
        version_number=1,
        title='PDF enrichi',
        content=(
            '# Exigences\n\n'
            'Le texte **obligatoire** et [la référence](https://example.cd).\n\n'
            '- Premier contrôle\n- Deuxième contrôle'
        ),
        content_format='md',
    )

    pdf = generate_norm_pdf(version.norme, version)
    with fitz.open(stream=pdf, filetype='pdf') as document:
        text = '\n'.join(page.get_text() for page in document)

    assert 'Exigences' in text
    assert 'texte obligatoire et la référence.' in text
    assert 'Premier contrôle' in text
    assert 'Deuxième contrôle' in text


@pytest.mark.django_db
def test_rag_indexes_plain_text(monkeypatch, norme_factory):
    from apps.ia_agent.services import rag
    from apps.norms.models import NormeVersion

    version = NormeVersion.all_objects.create(
        norme=norme_factory(),
        version_number=1,
        title='Index RAG',
        content='## Objet\n\nTexte **sans balises**.',
        content_format='md',
    )
    captured = {}

    monkeypatch.setattr(
        rag,
        '_upsert_source',
        lambda *args, **kwargs: captured.update(
            chunks=args[3],
            args=args,
            kwargs=kwargs,
        ) or object(),
    )

    rag.index_norme_version(version)

    indexed = '\n'.join(chunk['content'] for chunk in captured['chunks'])
    assert 'Objet' in indexed
    assert 'sans balises' in indexed
    assert '**' not in indexed
