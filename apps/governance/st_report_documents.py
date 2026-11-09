"""Private reference documents and reusable, non-destructive report composition."""
from io import BytesIO
from pathlib import Path
import hashlib
import os
import subprocess
import tempfile
import uuid
import zipfile
from xml.etree import ElementTree

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db.models import Q

MAX_FILE = 20 * 1024 * 1024


def report_storage():
    return FileSystemStorage(location=Path(settings.BASE_DIR) / 'private' / 'report_sources')


def accessible_sources(user):
    from .st_report_models import STReportSource
    return STReportSource.objects.filter(Q(creator=user) | Q(creator__isnull=True) | Q(templates__isnull=False)).distinct()


def validate_delta(delta):
    if not isinstance(delta, list) or not 1 <= len(delta) <= 30000:
        raise ValidationError('Contenu enrichi invalide.')
    count = 0
    allowed = {'bold', 'italic', 'underline', 'strike', 'header', 'list', 'align', 'indent', 'color', 'background', 'size', 'font', 'blockquote', 'code-block', 'script', 'link'}
    for op in delta:
        if not isinstance(op, dict) or not set(op) <= {'insert', 'attributes'} or not isinstance(op.get('insert'), str):
            raise ValidationError('Seul le contenu textuel enrichi est accepté.')
        attrs = op.get('attributes', {})
        if not isinstance(attrs, dict) or not set(attrs) <= allowed or any(not isinstance(v, (str, int, bool)) for v in attrs.values()):
            raise ValidationError('Mise en forme non prise en charge.')
        count += len(op['insert'])
    if count > 100000 or not delta[-1]['insert'].endswith('\n'):
        raise ValidationError('Texte limité à 100 000 caractères et terminé par un saut de ligne.')


def validate_document(document, source):
    if document in ({}, None):
        return {}
    if not isinstance(document, dict) or set(document) - {'mode', 'fields', 'cover', 'source_start_page'} or document.get('mode') not in ('free', 'fixed'):
        raise ValidationError('Mode de rédaction invalide.')
    from .st_report_cover import validate_cover
    validate_cover(document.get('cover', {}))
    start = document.get('source_start_page', 0)
    if type(start) is not int or start < 0 or (start and (not source or start >= len(source.pages))):
        raise ValidationError('Première page du modèle invalide.')
    fields = document.get('fields', [])
    if not isinstance(fields, list) or len(fields) > 300:
        raise ValidationError('Maximum 300 champs sur le document.')
    if document['mode'] == 'fixed' and not source:
        raise ValidationError('Un document source est requis pour conserver sa présentation.')
    for field in fields:
        if not isinstance(field, dict) or set(field) != {'page', 'x', 'y', 'width', 'height', 'text', 'size'}:
            raise ValidationError('Champ de document invalide.')
        if not source or type(field['page']) is not int or not start <= field['page'] < len(source.pages):
            raise ValidationError('Page de document invalide.')
        if not isinstance(field['text'], str) or len(field['text']) > 4000:
            raise ValidationError('Champ limité à 4 000 caractères.')
        for key in ('x', 'y', 'width', 'height', 'size'):
            if type(field[key]) not in (int, float) or not 0 <= field[key] <= 1:
                raise ValidationError('Position de champ invalide.')
        if field['width'] < .02 or field['height'] < .01 or not .005 <= field['size'] <= .1 or field['x'] + field['width'] > 1.001 or field['y'] + field['height'] > 1.001:
            raise ValidationError('Le champ doit rester dans la page.')
    if sum(len(f['text']) for f in fields) > 100000:
        raise ValidationError('Texte trop volumineux.')
    return document


def docx_sections(raw, skip_cover=False):
    """Retain Word paragraph order and inline emphasis; tables retain cell text."""
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    document = Document(BytesIO(raw))
    groups = []
    current = {'title': 'Document', 'content': '', 'delta': []}
    def append_paragraph(paragraph):
        for run in paragraph.runs:
            if not run.text:
                continue
            marks = {key: True for key in ('bold', 'italic', 'underline') if getattr(run, key)}
            current['delta'].append({'insert': run.text, **({'attributes': marks} if marks else {})})
        attrs = {}
        style = paragraph.style.name if paragraph.style else ''
        if style.startswith('Heading'):
            attrs['header'] = 1 if style.endswith('1') else 2
        if 'List Bullet' in style:
            attrs['list'] = 'bullet'
        elif 'List Number' in style:
            attrs['list'] = 'ordered'
        if paragraph.alignment in (1, 2, 3):
            attrs['align'] = {1: 'center', 2: 'right', 3: 'justify'}[paragraph.alignment]
        current['delta'].append({'insert': '\n', **({'attributes': attrs} if attrs else {})})
    for index, element in enumerate(document.element.body):
        if skip_cover and index == 0:
            continue
        if element.tag.endswith('}p'):
            paragraph = Paragraph(element, document)
            if paragraph.style and paragraph.style.name == 'Heading 1' and len(groups) < 19:
                if ''.join(op['insert'] for op in current['delta']).strip():
                    groups.append(current)
                current = {'title': paragraph.text[:150] or 'Section', 'content': '', 'delta': []}
                continue
            append_paragraph(paragraph)
        elif element.tag.endswith('}tbl'):
            for row in Table(element, document).rows:
                seen, cells = set(), []
                for cell in row.cells:
                    cells.append(' '.join(cell.text.splitlines()) if cell._tc not in seen else '')
                    seen.add(cell._tc)
                current['delta'].append({'insert': ' | '.join(cells) + '\n'})
    if current['delta']:
        groups.append(current)
    for group in groups:
        group['content'] = ''.join(op['insert'] for op in group['delta']).rstrip('\n')
    return groups if groups and sum(len(g['content']) for g in groups) <= 100000 else None


def import_source(upload, creator=None, preview_pdf=None):
    from .st_report_models import STReportSource
    import fitz
    suffix = Path(upload.name).suffix.lower()
    if suffix not in ('.pdf', '.doc', '.docx', '.odt', '.rtf', '.txt', '.md', '.png', '.jpg', '.jpeg'):
        raise ValidationError('Formats acceptés : PDF, DOC, DOCX, ODT, RTF, TXT, Markdown, PNG et JPG.')
    raw = upload.read(MAX_FILE + 1)
    if not raw or len(raw) > MAX_FILE:
        raise ValidationError('Fichier vide ou supérieur à 20 Mo.')
    if suffix == '.doc' and not raw.startswith(bytes.fromhex('D0CF11E0A1B11AE1')):
        raise ValidationError('Le contenu ne correspond pas à un document Word DOC.')
    digest = hashlib.sha256(raw).hexdigest()
    old = STReportSource.objects.filter(sha256=digest, creator=creator).first()
    if old:
        return old
    if suffix in ('.docx', '.odt'):
        try:
            with zipfile.ZipFile(BytesIO(raw)) as archive:
                if sum(i.file_size for i in archive.infolist()) > 80 * 1024 * 1024 or len(archive.infolist()) > 10000:
                    raise ValueError('Archive trop volumineuse')
                if suffix == '.docx' and 'word/document.xml' not in archive.namelist():
                    raise ValueError('DOCX attendu')
                for name in archive.namelist():
                    if name.endswith('.rels'):
                        relations = ElementTree.fromstring(archive.read(name))
                        if any(r.get('TargetMode') == 'External' and not r.get('Type', '').endswith('/hyperlink') for r in relations):
                            raise ValueError('Ressources externes non prises en charge')
        except Exception as exc:
            raise ValidationError('Archive Office invalide, trop volumineuse ou contenant des liens externes.') from exc
    with tempfile.TemporaryDirectory(prefix='st-report-') as folder:
        root = Path(folder)
        incoming = root / ('source' + suffix)
        incoming.write_bytes(raw)
        if preview_pdf is not None:
            pdf = preview_pdf
        elif suffix == '.pdf':
            pdf = raw
        elif suffix in ('.png', '.jpg', '.jpeg'):
            try:
                with fitz.open(stream=raw) as image:
                    pdf = image.convert_to_pdf()
            except Exception as exc:
                raise ValidationError('Image illisible.') from exc
        else:
            profile = root / 'profile'
            profile.mkdir()
            (profile / 'registrymodifications.xcu').write_text('''<?xml version="1.0"?><oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop></item></oor:items>''')
            try:
                subprocess.run(['libreoffice', '-env:UserInstallation=' + profile.as_uri(), '--headless', '--norestore', '--nofirststartwizard', '--convert-to', 'pdf', '--outdir', str(root), str(incoming)], capture_output=True, timeout=120, check=True, env={**os.environ, 'SAL_USE_VCLPLUGIN': 'svp'})
                pdf = (root / 'source.pdf').read_bytes()
            except (OSError, subprocess.SubprocessError) as exc:
                raise ValidationError('Conversion indisponible : LibreOffice est requis pour les documents bureautiques.') from exc
    try:
        with fitz.open(stream=pdf, filetype='pdf') as reader:
            if reader.needs_pass or not 1 <= reader.page_count <= 200:
                raise ValueError('PDF chiffré ou plus de 200 pages')
            pages = [{'width': p.rect.width, 'height': p.rect.height} for p in reader]
            texts = [p.get_text().strip() for p in reader]
    except Exception as exc:
        raise ValidationError('Document illisible, protégé ou supérieur à 200 pages.') from exc
    # Each original page remains a section; long references are grouped, never silently truncated.
    combined = '\n\n'.join(texts)
    if len(combined) > 100000:
        sections = [{'title': 'Rédaction', 'content': ''}]
        note = 'Le texte dépasse 100 000 caractères : utilisez le modèle conservé ou rédigez un extrait.'
    else:
        group = max(1, (len(texts) + 19) // 20)
        sections = [{'title': f'Page {i + 1}' if group == 1 else f'Pages {i + 1} à {min(i + group, len(texts))}', 'content': '\n\n'.join(texts[i:i+group])} for i in range(0, len(texts), group)]
        note = '' if combined.strip() else 'Document numérisé : aucun texte natif détecté. Utilisez la présentation conservée ou saisissez le texte en rédaction libre.'
    if suffix == '.docx':
        structured = docx_sections(raw)
        if structured is not None:
            sections = structured
    source = STReportSource(name=Path(upload.name).name[:250], sha256=digest, creator=creator, pages=pages, sections=sections, note=note)
    storage = report_storage()
    token = uuid.uuid4().hex
    original_name = storage.save(token + suffix, ContentFile(raw))
    pdf_name = storage.save(token + '-preview.pdf', ContentFile(pdf))
    source.original = original_name
    source.preview = pdf_name
    try:
        source.save()
    except Exception:
        storage.delete(original_name)
        storage.delete(pdf_name)
        raise
    return source


def source_data(source):
    return {'id': source.pk, 'name': source.name, 'pages': source.pages, 'sections': source.sections, 'note': source.note, 'sha256': source.sha256}


def fixed_pdf(version):
    import fitz
    source = version.source
    with report_storage().open(source.preview, 'rb') as stream:
        reader = fitz.open(stream=stream.read(), filetype='pdf')
    with reader:
        for field in version.document.get('fields', []):
            page = reader[field['page']]
            rect = page.rect
            box = fitz.Rect(field['x'] * rect.width, field['y'] * rect.height, (field['x'] + field['width']) * rect.width, (field['y'] + field['height']) * rect.height)
            # A copy is composed; original content and original files are never modified.
            result = page.insert_textbox(box, field['text'], fontsize=field['size'] * rect.width, fontname='helv', color=(0, 0, 0), overlay=True)
            if result < 0:
                raise ValidationError('Un champ déborde : agrandissez-le ou réduisez son texte avant l’export.')
        start = getattr(version, 'document', {}).get('source_start_page', 0)
        if start:
            reader.delete_pages(0, start - 1)
        reader.set_metadata({'title': version.title, 'author': version.author_name, 'subject': 'Document de travail composé à partir d’un modèle conservé'})
        return reader.tobytes(garbage=4, deflate=True, no_new_id=True)


def fixed_docx(version):
    """Page images preserve the reference layout; editable fields remain versioned in the app."""
    import fitz
    from docx import Document
    from docx.shared import Pt
    document = Document()
    from .st_report_cover import add_word_cover
    first_body_section = add_word_cover(document, version)
    pdf = fitz.open(stream=fixed_pdf(version), filetype='pdf')
    for number, page in enumerate(pdf):
        section = first_body_section if number == 0 else document.add_section()
        section.page_width = Pt(page.rect.width)
        section.page_height = Pt(page.rect.height)
        section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Pt(0)
        section.header_distance = section.footer_distance = Pt(0)
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.line_spacing = 1
        # A small safety margin avoids a trailing blank Word page.
        paragraph.add_run().add_picture(BytesIO(page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).tobytes('png')), width=Pt(page.rect.width - 2), height=Pt(page.rect.height - 3))
    pdf.close()
    result = BytesIO()
    document.save(result)
    stable = BytesIO()
    with zipfile.ZipFile(result) as original, zipfile.ZipFile(stable, 'w', zipfile.ZIP_DEFLATED) as output:
        for name in sorted(original.namelist()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, original.read(name))
    return stable.getvalue()


def delta_lines(section):
    """Yield text runs and block attributes, with no executable markup."""
    runs = []
    for operation in section.get('delta', [{'insert': section['content'] + '\n'}]):
        parts = operation['insert'].split('\n')
        attrs = operation.get('attributes', {})
        for index, part in enumerate(parts):
            if part:
                runs.append((part, attrs))
            if index < len(parts) - 1:
                yield runs, attrs
                runs = []
    if runs:
        yield runs, {}


def report_blocks(section):
    """Recover contiguous Word table rows while retaining ordinary rich paragraphs."""
    pending = []
    for runs, attrs in delta_lines(section):
        plain = ''.join(text for text, _ in runs)
        if ' | ' in plain:
            pending.append((runs, attrs))
            continue
        if pending:
            if len(pending) > 1:
                yield 'table', [[cell.strip() for cell in ''.join(t for t, _ in row).split(' | ')] for row, _ in pending]
            else:
                yield 'paragraph', pending[0]
            pending = []
        yield 'paragraph', (runs, attrs)
    if pending:
        if len(pending) > 1:
            yield 'table', [[cell.strip() for cell in ''.join(t for t, _ in row).split(' | ')] for row, _ in pending]
        else:
            yield 'paragraph', pending[0]
