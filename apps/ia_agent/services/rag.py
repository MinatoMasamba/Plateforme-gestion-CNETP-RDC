"""Indexation et recherche documentaire RAG de première génération.

Cette couche est volontairement indépendante du fournisseur LLM. Elle garantit
que la recherche et les permissions sont exécutées avant la synthèse distante.
La recherche sémantique/embeddings pourra être ajoutée derrière ``search`` sans
modifier le contrat de l'outil IA.
"""

import hashlib
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.documents.models import DocumentFile
from apps.experts.models import Expert
from apps.governance.models import CTCMembership, PilotageMembreship
from apps.norms.models import Norme, NormeVersion

from ..models import RAGChunk, RAGDocument


MAX_CHUNK_CHARS = 1800
MAX_SEARCH_CANDIDATES = 5000
_WORD_RE = re.compile(r"[\wÀ-ÿ]{3,}", re.UNICODE)
_XML_NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
_PPT_NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}


def _terms(value):
    return [term.casefold() for term in _WORD_RE.findall(value or '')]


def _clean_text(value):
    return re.sub(r'\s+', ' ', value or '').strip()


def _split_text(text, page_number=None, section=''):
    """Découpe un passage en conservant sa page et son titre de section."""
    text = _clean_text(text)
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + MAX_CHUNK_CHARS, len(text))
        if end < len(text):
            boundary = text.rfind(' ', start, end)
            if boundary > start + 500:
                end = boundary
        piece = text[start:end].strip()
        if piece:
            chunks.append({
                'content': piece,
                'page_number': page_number,
                'section': section[:500],
            })
        start = end
    return chunks


def _extract_pdf(file_obj):
    import fitz

    chunks = []
    with fitz.open(stream=file_obj.read(), filetype='pdf') as pdf:
        for page_index, page in enumerate(pdf, start=1):
            text = page.get_text('text') or ''
            chunks.extend(_split_text(text, page_number=page_index))
    return chunks


def _xml_text(xml_bytes, namespace=None):
    root = ElementTree.fromstring(xml_bytes)
    if namespace == 'word':
        paragraphs = []
        for paragraph in root.findall('.//w:p', _XML_NS):
            text = ''.join(node.text or '' for node in paragraph.findall('.//w:t', _XML_NS))
            if text.strip():
                paragraphs.append(text)
        return paragraphs
    if namespace == 'ppt':
        return [
            ''.join(node.text or '' for node in shape.findall('.//a:t', _PPT_NS)).strip()
            for shape in root.findall('.//p:sp', {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'})
        ]
    return []


def _extract_office(file_obj, suffix):
    """Extraction sans dépendance obligatoire à python-docx/openpyxl/python-pptx."""
    chunks = []
    with zipfile.ZipFile(file_obj) as archive:
        if suffix == '.docx':
            paragraphs = _xml_text(archive.read('word/document.xml'), namespace='word')
            chunks.extend(_split_text('\n'.join(paragraphs)))
        elif suffix == '.pptx':
            slide_names = sorted(
                name for name in archive.namelist()
                if name.startswith('ppt/slides/slide') and name.endswith('.xml')
            )
            for index, name in enumerate(slide_names, start=1):
                text = '\n'.join(_xml_text(archive.read(name), namespace='ppt'))
                chunks.extend(_split_text(text, section=f'Diapositive {index}'))
        elif suffix == '.xlsx':
            shared = []
            if 'xl/sharedStrings.xml' in archive.namelist():
                root = ElementTree.fromstring(archive.read('xl/sharedStrings.xml'))
                shared = [
                    _clean_text(''.join(node.text or '' for node in item.iter()))
                    for item in root
                ]
            sheet_names = sorted(
                name for name in archive.namelist()
                if name.startswith('xl/worksheets/sheet') and name.endswith('.xml')
            )
            for index, name in enumerate(sheet_names, start=1):
                root = ElementTree.fromstring(archive.read(name))
                values = []
                for cell in root.iter():
                    if cell.tag.rsplit('}', 1)[-1] != 'c':
                        continue
                    value = next((node.text for node in cell if node.tag.rsplit('}', 1)[-1] == 'v'), None)
                    if value is not None:
                        if cell.attrib.get('t') == 's' and value.isdigit() and int(value) < len(shared):
                            value = shared[int(value)]
                        values.append(value)
                chunks.extend(_split_text(' | '.join(values), section=f'Feuille {index}'))
    return chunks


def extract_file_chunks(file_obj, filename):
    suffix = Path(filename or '').suffix.casefold()
    if suffix == '.pdf':
        return _extract_pdf(file_obj)
    if suffix in {'.docx', '.xlsx', '.pptx'}:
        return _extract_office(file_obj, suffix)
    if suffix in {'.txt', '.csv', '.md'}:
        return _split_text(file_obj.read().decode('utf-8', errors='replace'))
    return []


def _hash_chunks(chunks):
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk['content'].encode('utf-8'))
        digest.update(str(chunk.get('page_number') or '').encode('ascii'))
    return digest.hexdigest()


def _upsert_source(source_key, source_kind, title, chunks, metadata=None, mime_type=''):
    content_hash = _hash_chunks(chunks)
    source, _ = RAGDocument.objects.get_or_create(
        source_key=source_key,
        defaults={'source_kind': source_kind, 'title': title},
    )
    source.source_kind = source_kind
    source.title = title[:500]
    source.mime_type = mime_type or ''
    source.content_hash = content_hash
    source.metadata = metadata or {}
    source.extraction_error = ''
    source.status = 'INDEXED' if chunks else 'EMPTY'
    source.indexed_at = timezone.now()
    source.save()

    source.chunks.all().delete()
    RAGChunk.objects.bulk_create([
        RAGChunk(
            document=source,
            ordinal=index,
            content=chunk['content'],
            page_number=chunk.get('page_number'),
            section=chunk.get('section', ''),
            metadata=chunk.get('metadata', {}),
        )
        for index, chunk in enumerate(chunks)
    ])
    return source


@transaction.atomic
def index_document_file(document):
    try:
        with document.file.open('rb') as file_obj:
            chunks = extract_file_chunks(file_obj, document.file.name)
        metadata = {
            'document_id': document.id,
            'is_public': document.is_public,
            'uploaded_by_id': document.uploaded_by_id,
            'expert_id': document.expert_id,
            'norme_id': document.norme_id,
            'reunion_id': document.reunion_id,
        }
        return _upsert_source(
            f'document:{document.id}',
            'DOCUMENT',
            document.title,
            chunks,
            metadata=metadata,
            mime_type=document.mime_type,
        )
    except Exception as exc:
        source, _ = RAGDocument.objects.get_or_create(
            source_key=f'document:{document.id}',
            defaults={'source_kind': 'DOCUMENT', 'title': document.title},
        )
        source.status = 'ERROR'
        source.extraction_error = str(exc)[:2000]
        source.save(update_fields=['status', 'extraction_error', 'updated_at'])
        raise


@transaction.atomic
def index_norme(norme):
    chunks = _split_text(
        f'{norme.reference_number}\n{norme.title}\n{norme.description}\n'
        f'Famille: {norme.get_standard_family_display()}\n'
        f'Statut: {norme.get_status_display()}\nTags: {norme.tags}',
        section='Fiche norme',
    )
    return _upsert_source(
        f'norme:{norme.id}',
        'NORME',
        f'{norme.reference_number} — {norme.title}',
        chunks,
        metadata={
            'norme_id': norme.id,
            'is_public': norme.is_public,
            'status': norme.status,
            'ctm_id': norme.ctm_id,
            'wg_id': norme.wg_id,
        },
    )


@transaction.atomic
def index_norme_version(version):
    chunks = _split_text(version.content, section=f'Version {version.version_number}')
    return _upsert_source(
        f'norme-version:{version.id}',
        'NORME_VERSION',
        f'{version.norme.reference_number} — version {version.version_number}',
        chunks,
        metadata={
            'norme_id': version.norme_id,
            'version_id': version.id,
            'is_public': version.norme.is_public,
            'status': version.norme.status,
            'version_number': version.version_number,
        },
    )


@transaction.atomic
def index_expert_cv(expert):
    if not expert.cv:
        return _upsert_source(
            f'expert-cv:{expert.id}',
            'EXPERT_CV',
            f'CV — {expert.full_name}',
            [],
            metadata={
                'expert_id': expert.id,
                'expert_user_id': expert.user_id,
                'is_public': False,
            },
        )

    with expert.cv.open('rb') as file_obj:
        chunks = extract_file_chunks(file_obj, expert.cv.name)
    return _upsert_source(
        f'expert-cv:{expert.id}',
        'EXPERT_CV',
        f'CV — {expert.full_name}',
        chunks,
        metadata={
            'expert_id': expert.id,
            'expert_user_id': expert.user_id,
            'is_public': False,
            'structure': expert.structure.acronym if expert.structure else None,
        },
        mime_type='application/pdf',
    )


def _is_member_of_platform_scope(user):
    expert = Expert.objects.filter(user=user, status='ACTIVE').first()
    if not expert:
        return False
    return (
        CTCMembership.objects.filter(expert=expert).exists()
        or PilotageMembreship.objects.filter(expert=expert).exists()
    )


def accessible_source_ids(user, source_kind=None):
    """Retourne uniquement les sources que l'utilisateur peut consulter."""
    if not user or not user.is_authenticated:
        return RAGDocument.objects.none()

    sources = RAGDocument.objects.filter(status='INDEXED')
    if source_kind:
        sources = sources.filter(source_kind=source_kind)
    if user.is_staff or user.is_superuser:
        return sources

    member = _is_member_of_platform_scope(user)
    allowed = sources.filter(metadata__is_public=True)
    if member:
        # Les membres CTC/Pilotage peuvent consulter les sources métier indexées.
        return sources

    own_document_keys = RAGDocument.objects.filter(
        source_kind='DOCUMENT', metadata__uploaded_by_id=user.id,
    ).values('id')
    own_cv_keys = RAGDocument.objects.filter(
        source_kind='EXPERT_CV', metadata__expert_user_id=user.id,
    ).values('id')
    return allowed | sources.filter(id__in=own_document_keys) | sources.filter(id__in=own_cv_keys)


def _score_chunk(chunk, query_terms, phrase):
    content = chunk.content.casefold()
    title = chunk.document.title.casefold()
    score = sum(content.count(term) for term in query_terms)
    score += sum(title.count(term) * 3 for term in query_terms)
    if phrase and phrase.casefold() in content:
        score += 5
    return score


def search(user, query, limit=8, source_kind=None):
    query = _clean_text(query)
    query_terms = list(dict.fromkeys(_terms(query)))
    if not query_terms:
        return []

    sources = accessible_source_ids(user, source_kind=source_kind)
    from django.db.models import Q

    condition = Q()
    for term in query_terms:
        condition |= Q(content__icontains=term) | Q(document__title__icontains=term)

    candidates = list(
        RAGChunk.objects.filter(document__in=sources).filter(condition)
        .select_related('document')[:MAX_SEARCH_CANDIDATES]
    )
    candidates.sort(key=lambda chunk: _score_chunk(chunk, query_terms, query), reverse=True)

    results = []
    seen = defaultdict(int)
    for chunk in candidates:
        document_id = chunk.document_id
        # Un document peut fournir plusieurs passages, mais on évite qu'il monopolise la réponse.
        if seen[document_id] >= 3:
            continue
        seen[document_id] += 1
        results.append({
            'source_id': document_id,
            'source_key': chunk.document.source_key,
            'source_kind': chunk.document.source_kind,
            'title': chunk.document.title,
            'url': reverse('web:ia_rag_source', args=[document_id]),
            'link_label': f"Ouvrir la source : {chunk.document.title}",
            'excerpt': chunk.content[:1200],
            'page': chunk.page_number,
            'section': chunk.section or None,
            'score': _score_chunk(chunk, query_terms, query),
            'metadata': chunk.document.metadata,
        })
        if len(results) >= max(1, min(int(limit), 20)):
            break
    return results
